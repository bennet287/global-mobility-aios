from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import timedelta
from html.parser import HTMLParser
from io import BytesIO
from typing import Any, Callable, Iterable, Optional
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import (
    OfficialSource,
    SourceMonitor,
    SourceRetrievalRun,
    now_utc,
)
from app.schemas import SourceSnapshotCaptureRequest
from app.services.audit_log import record_audit
from app.services.regulatory_intelligence import capture_source_snapshot


Resolver = Callable[..., Iterable[tuple]]
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
SUPPORTED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "application/json",
    "application/pdf",
    "application/xml",
    "text/xml",
}


class SourceRetrievalError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FetchResult:
    status_code: int
    final_url: str
    content_type: Optional[str]
    content: bytes
    etag: Optional[str]
    last_modified: Optional[str]


@dataclass(frozen=True)
class ParsedSourceContent:
    text: str
    parser_version: str
    metadata: dict[str, Any]


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "svg"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        return "\n".join(self._parts)


class _GazetteTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._focus_depth = 0
        self._all_parts: list[str] = []
        self._focus_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        name = tag.lower()
        if name in {"script", "style", "noscript", "template", "svg", "nav", "header", "footer", "aside"}:
            self._ignored_depth += 1
        if name in {"main", "article"}:
            self._focus_depth += 1

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in {"main", "article"} and self._focus_depth:
            self._focus_depth -= 1
        if name in {"script", "style", "noscript", "template", "svg", "nav", "header", "footer", "aside"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if not self._ignored_depth and value:
            self._all_parts.append(value)
            if self._focus_depth:
                self._focus_parts.append(value)

    def text(self) -> str:
        return "\n".join(self._focus_parts or self._all_parts)


def _allowed_domains(monitor: SourceMonitor, source: OfficialSource) -> list[str]:
    try:
        values = json.loads(monitor.allowed_domains_json or "[]")
    except json.JSONDecodeError:
        values = []
    domains = [str(value).strip().lower().rstrip(".") for value in values if str(value).strip()]
    source_domain = (urlparse(source.url).hostname or "").lower().rstrip(".")
    return domains or ([source_domain] if source_domain else [])


def _domain_allowed(hostname: str, allowed_domains: Iterable[str]) -> bool:
    hostname = hostname.lower().rstrip(".")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)


def validate_retrieval_url(
    url: str,
    *,
    allowed_domains: Iterable[str],
    resolver: Resolver = socket.getaddrinfo,
) -> None:
    parsed = urlparse(url)
    allowed_schemes = {"https"} | ({"http"} if settings.source_monitor_allow_http else set())
    if parsed.scheme.lower() not in allowed_schemes:
        raise SourceRetrievalError("scheme_not_allowed", "Only approved HTTP(S) source URLs may be retrieved")
    if parsed.username or parsed.password:
        raise SourceRetrievalError("credentials_not_allowed", "Source URLs cannot contain credentials")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname or not _domain_allowed(hostname, allowed_domains):
        raise SourceRetrievalError("domain_not_allowed", f"Domain is not on the monitor allowlist: {hostname or 'missing'}")
    default_port = 443 if parsed.scheme.lower() == "https" else 80
    if parsed.port not in {None, default_port}:
        raise SourceRetrievalError("port_not_allowed", "Only the standard port for the URL scheme is allowed")
    try:
        addresses = resolver(hostname, default_port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceRetrievalError("dns_resolution_failed", f"Could not resolve approved source domain: {hostname}") from exc
    resolved_ips = {entry[4][0] for entry in addresses if entry and len(entry) > 4 and entry[4]}
    if not resolved_ips:
        raise SourceRetrievalError("dns_resolution_failed", f"No addresses resolved for approved source domain: {hostname}")
    for value in resolved_ips:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise SourceRetrievalError("invalid_resolved_address", f"Invalid resolved address for {hostname}") from exc
        if not address.is_global:
            raise SourceRetrievalError("private_address_blocked", f"Non-public address blocked for {hostname}")


def fetch_official_source(
    monitor: SourceMonitor,
    source: OfficialSource,
    *,
    transport: Optional[httpx.BaseTransport] = None,
    resolver: Resolver = socket.getaddrinfo,
) -> FetchResult:
    allowed_domains = _allowed_domains(monitor, source)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/json,application/pdf,text/plain,application/xml;q=0.9",
        "User-Agent": "GlobalMobilityAIOS-OfficialSourceMonitor/1.0",
    }
    if monitor.etag:
        headers["If-None-Match"] = monitor.etag
    if monitor.last_modified:
        headers["If-Modified-Since"] = monitor.last_modified

    current_url = source.url
    with httpx.Client(
        timeout=settings.source_monitor_timeout_seconds,
        follow_redirects=False,
        transport=transport,
    ) as client:
        for redirect_count in range(monitor.max_redirects + 1):
            validate_retrieval_url(current_url, allowed_domains=allowed_domains, resolver=resolver)
            try:
                with client.stream("GET", current_url, headers=headers) as response:
                    if response.status_code in REDIRECT_STATUSES:
                        location = response.headers.get("location")
                        if not location:
                            raise SourceRetrievalError("redirect_without_location", "Redirect response did not include Location")
                        if redirect_count >= monitor.max_redirects:
                            raise SourceRetrievalError("redirect_limit_exceeded", "Source exceeded the configured redirect limit")
                        current_url = urljoin(current_url, location)
                        continue

                    if response.status_code == 304:
                        return FetchResult(
                            status_code=304,
                            final_url=str(response.url),
                            content_type=None,
                            content=b"",
                            etag=response.headers.get("etag") or monitor.etag,
                            last_modified=response.headers.get("last-modified") or monitor.last_modified,
                        )
                    if response.status_code != 200:
                        raise SourceRetrievalError(
                            "http_error",
                            f"Official source returned HTTP {response.status_code}",
                        )

                    media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if media_type not in SUPPORTED_CONTENT_TYPES:
                        raise SourceRetrievalError(
                            "content_type_not_allowed",
                            f"Unsupported source content type: {media_type or 'missing'}",
                        )
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > settings.source_monitor_max_bytes:
                        raise SourceRetrievalError("response_too_large", "Source response exceeds the configured size limit")
                    chunks: list[bytes] = []
                    received = 0
                    for chunk in response.iter_bytes():
                        received += len(chunk)
                        if received > settings.source_monitor_max_bytes:
                            raise SourceRetrievalError("response_too_large", "Source response exceeds the configured size limit")
                        chunks.append(chunk)
                    return FetchResult(
                        status_code=200,
                        final_url=str(response.url),
                        content_type=response.headers.get("content-type"),
                        content=b"".join(chunks),
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified"),
                    )
            except httpx.TimeoutException as exc:
                raise SourceRetrievalError("timeout", "Official source retrieval timed out") from exc
            except httpx.RequestError as exc:
                raise SourceRetrievalError("request_failed", "Official source retrieval failed") from exc

    raise SourceRetrievalError("redirect_limit_exceeded", "Source exceeded the configured redirect limit")


def _charset(content_type: Optional[str]) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type or "", re.IGNORECASE)
    return match.group(1).strip('"\'') if match else "utf-8"


def _path_value(value: Any, path: str) -> Any:
    current = value
    for part in [item for item in path.split(".") if item]:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current


def _structured_program_catalog(decoded: str, config: dict[str, Any]) -> ParsedSourceContent:
    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise SourceRetrievalError("json_parse_failed", "Official JSON response could not be parsed") from exc
    records_path = str(config.get("records_path") or "programs")
    records = _path_value(payload, records_path)
    if not isinstance(records, list):
        raise SourceRetrievalError(
            "program_catalog_path_invalid",
            f"Configured program catalog path did not resolve to a list: {records_path}",
        )
    id_field = str(config.get("id_field") or "id")
    name_field = str(config.get("name_field") or "name")
    status_field = str(config.get("status_field") or "status")
    summary_field = str(config.get("summary_field") or "summary")
    effective_date_field = str(config.get("effective_date_field") or "effective_date")
    retired_values = {
        str(value).strip().lower()
        for value in (config.get("retired_values") or ["retired", "closed", "removed", "inactive"])
    }
    programs: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise SourceRetrievalError("program_catalog_record_invalid", f"Program record {index} is not an object")
        program_id = str(_path_value(record, id_field) or "").strip()
        name = str(_path_value(record, name_field) or "").strip()
        if not program_id or not name:
            raise SourceRetrievalError(
                "program_catalog_record_invalid",
                f"Program record {index} is missing its configured identifier or name",
            )
        status = str(_path_value(record, status_field) or "unknown").strip().lower()
        programs.append({
            "program_id": program_id,
            "name": name,
            "status": status,
            "active": status not in retired_values,
            "summary": str(_path_value(record, summary_field) or "").strip(),
            "effective_date": str(_path_value(record, effective_date_field) or "").strip() or None,
        })
    programs.sort(key=lambda item: item["program_id"])
    if not programs:
        raise SourceRetrievalError("empty_program_catalog", "The structured program catalog contained no programs")
    return ParsedSourceContent(
        text=json.dumps(programs, ensure_ascii=False, indent=2, sort_keys=True),
        parser_version="structured-program-catalog-v1",
        metadata={
            "parser_profile": "structured_program_catalog_v1",
            "program_catalog": programs,
            "missing_means_retired": bool(config.get("missing_means_retired", False)),
        },
    )


def parse_source_content(
    result: FetchResult,
    *,
    profile: str = "generic",
    config: Optional[dict[str, Any]] = None,
) -> ParsedSourceContent:
    media_type = (result.content_type or "").split(";", 1)[0].strip().lower()
    config = config or {}
    if profile == "structured_program_catalog_v1":
        if media_type != "application/json":
            raise SourceRetrievalError(
                "parser_profile_content_type_mismatch",
                "The structured program catalog profile requires application/json",
            )
        try:
            decoded = result.content.decode(_charset(result.content_type), errors="replace")
        except LookupError as exc:
            raise SourceRetrievalError("charset_not_supported", "Source declared an unsupported character set") from exc
        return _structured_program_catalog(decoded, config)

    if profile not in {"generic", "gazette_html_v1"}:
        raise SourceRetrievalError("parser_profile_unknown", f"Unknown source parser profile: {profile}")
    if profile == "gazette_html_v1" and media_type not in {"text/html", "application/xhtml+xml"}:
        raise SourceRetrievalError(
            "parser_profile_content_type_mismatch",
            "The gazette HTML profile requires HTML content",
        )
    if media_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise SourceRetrievalError("pdf_parser_unavailable", "PDF parsing dependency is unavailable") from exc
        try:
            reader = PdfReader(BytesIO(result.content))
            text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        except Exception as exc:
            raise SourceRetrievalError("pdf_parse_failed", "Official PDF could not be parsed") from exc
        parser_version = "pypdf-v1"
    else:
        try:
            decoded = result.content.decode(_charset(result.content_type), errors="replace")
        except LookupError as exc:
            raise SourceRetrievalError("charset_not_supported", "Source declared an unsupported character set") from exc
        if media_type in {"text/html", "application/xhtml+xml"}:
            parser = _GazetteTextParser() if profile == "gazette_html_v1" else _VisibleTextParser()
            parser.feed(decoded)
            text = parser.text()
            parser_version = "gazette-html-v1" if profile == "gazette_html_v1" else "stdlib-html-v1"
        elif media_type == "application/json":
            try:
                text = json.dumps(json.loads(decoded), ensure_ascii=False, indent=2, sort_keys=True)
            except json.JSONDecodeError as exc:
                raise SourceRetrievalError("json_parse_failed", "Official JSON response could not be parsed") from exc
            parser_version = "json-v1"
        else:
            text = decoded.strip()
            parser_version = "text-v1"
    if not text.strip():
        raise SourceRetrievalError("empty_extracted_content", "No usable text was extracted from the official source")
    return ParsedSourceContent(
        text=text,
        parser_version=parser_version,
        metadata={"parser_profile": profile},
    )


def _complete_not_modified(
    session: Session,
    monitor: SourceMonitor,
    run: SourceRetrievalRun,
    result: FetchResult,
) -> SourceRetrievalRun:
    checked_at = now_utc()
    monitor.status = "active"
    monitor.last_checked_at = checked_at
    monitor.next_check_at = checked_at + timedelta(minutes=monitor.schedule_minutes)
    monitor.last_http_status = 304
    monitor.last_error = None
    monitor.etag = result.etag
    monitor.last_modified = result.last_modified
    monitor.updated_at = checked_at
    run.status = "not_modified"
    run.final_url = result.final_url
    run.http_status = 304
    run.completed_at = checked_at
    session.add(monitor)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def execute_source_monitor(
    session: Session,
    monitor_id: UUID,
    *,
    retrieval_run_id: UUID | None = None,
    transport: Optional[httpx.BaseTransport] = None,
    resolver: Resolver = socket.getaddrinfo,
) -> SourceRetrievalRun:
    monitor = session.get(SourceMonitor, monitor_id)
    if monitor is None:
        raise ValueError("Source monitor not found")
    source = session.get(OfficialSource, monitor.official_source_id)
    if source is None:
        raise ValueError("Official source not found")
    if retrieval_run_id is not None:
        run = session.get(SourceRetrievalRun, retrieval_run_id)
        if run is None:
            raise ValueError("Source retrieval run not found")
        if run.monitor_id != monitor.id or run.official_source_id != source.id:
            raise ValueError("Source retrieval run does not belong to the selected monitor")
        if run.status in {"baseline", "unchanged", "changed", "not_modified"}:
            return run
        run.status = "running"
        run.error_code = None
        run.error_message = None
        run.completed_at = None
        session.add(run)
        session.commit()
        session.refresh(run)
    else:
        prior_attempts = len(session.exec(
            select(SourceRetrievalRun).where(SourceRetrievalRun.monitor_id == monitor.id)
        ).all())
        run = SourceRetrievalRun(
            monitor_id=monitor.id,
            official_source_id=source.id,
            status="running",
            attempt=prior_attempts + 1,
            requested_url=source.url,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

    try:
        result = fetch_official_source(monitor, source, transport=transport, resolver=resolver)
        if result.status_code == 304:
            return _complete_not_modified(session, monitor, run, result)
        try:
            parser_config = json.loads(monitor.parser_config_json or "{}")
        except json.JSONDecodeError as exc:
            raise SourceRetrievalError("parser_config_invalid", "Source monitor parser configuration is invalid") from exc
        if not isinstance(parser_config, dict):
            raise SourceRetrievalError("parser_config_invalid", "Source monitor parser configuration must be an object")
        parsed = parse_source_content(
            result,
            profile=monitor.parser_profile,
            config=parser_config,
        )
        snapshot, change, unchanged = capture_source_snapshot(
            session,
            source.id,
            SourceSnapshotCaptureRequest(
                content_text=parsed.text,
                http_status=result.status_code,
                retrieval_method="http",
                parser_version=parsed.parser_version,
                metadata={
                    "retrieval_run_id": str(run.id),
                    "final_url": result.final_url,
                    "content_type": result.content_type,
                    "bytes_received": len(result.content),
                    **parsed.metadata,
                },
                actor="source-retrieval-worker",
            ),
        )
        completed_at = now_utc()
        monitor.status = "active"
        monitor.last_error = None
        monitor.last_http_status = result.status_code
        monitor.etag = result.etag
        monitor.last_modified = result.last_modified
        monitor.updated_at = completed_at
        run.status = "changed" if change else ("unchanged" if unchanged else "baseline")
        run.final_url = result.final_url
        run.http_status = result.status_code
        run.content_type = result.content_type
        run.bytes_received = len(result.content)
        run.snapshot_id = snapshot.id
        run.regulatory_change_id = change.id if change else None
        run.completed_at = completed_at
        session.add(monitor)
        session.add(run)
        record_audit(
            session,
            action="source_retrieval_completed",
            entity_type="source_retrieval_run",
            entity_id=run.id,
            after_state={"status": run.status, "source_id": source.id, "snapshot_id": snapshot.id},
            actor="source-retrieval-worker",
            source="controlled_source_retrieval_v7.1",
        )
        session.commit()
        session.refresh(run)
        return run
    except Exception as exc:
        error = exc if isinstance(exc, SourceRetrievalError) else SourceRetrievalError("retrieval_failed", str(exc))
        failed_at = now_utc()
        monitor.status = "error"
        monitor.last_checked_at = failed_at
        monitor.next_check_at = failed_at + timedelta(minutes=min(monitor.schedule_minutes, 60))
        monitor.last_error = str(error)
        monitor.updated_at = failed_at
        run.status = "failed"
        run.error_code = error.code
        run.error_message = str(error)
        run.completed_at = failed_at
        session.add(monitor)
        session.add(run)
        record_audit(
            session,
            action="source_retrieval_failed",
            entity_type="source_retrieval_run",
            entity_id=run.id,
            after_state={"status": "failed", "error_code": error.code, "source_id": source.id},
            reason=str(error),
            actor="source-retrieval-worker",
            source="controlled_source_retrieval_v7.1",
        )
        session.commit()
        session.refresh(run)
        return run
