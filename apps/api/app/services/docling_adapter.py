from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

try:
    from docling.document_converter import DocumentConverter  # type: ignore[import-untyped]
except ImportError:
    DocumentConverter = None  # type: ignore[misc,assignment]

STATUS_DISABLED = "disabled"
STATUS_UNAVAILABLE = "unavailable"
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"


@dataclass(frozen=True)
class DoclingResult:
    status: str
    normalized_text: str = ""
    title: str = ""
    page_count: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "normalized_text": self.normalized_text[:500] if self.normalized_text else "",
            "title": self.title,
            "page_count": self.page_count,
            "warnings": self.warnings,
            "error": self.error,
        }


def _file_suffix(filename: str | None, mime_type: str | None) -> str:
    if filename and "." in filename:
        suffix = filename.rsplit(".", 1)[-1].lower()
        if suffix:
            return f".{suffix}"
    mime_suffixes = {
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "text/html": ".html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/msword": ".doc",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/tiff": ".tiff",
    }
    return mime_suffixes.get((mime_type or "").lower().split(";")[0], "")


def normalize_document_bytes(
    content: bytes,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
) -> DoclingResult:
    """Optionally normalize a document to markdown using Docling.

    Disabled by default. When enabled, missing or failing Docling is treated as
    a graceful degradation signal so the rest of the extraction pipeline can fall
    back to the existing pypdf / tesseract / text extractors.
    """
    if not settings.docling_enabled:
        return DoclingResult(status=STATUS_DISABLED)

    if not content:
        return DoclingResult(status=STATUS_ERROR, error="Empty document content")

    if DocumentConverter is None:
        return DoclingResult(
            status=STATUS_UNAVAILABLE,
            error="docling package is not installed",
            warnings=["docling optional dependency is unavailable; falling back to legacy extraction."],
        )

    tmp_path: str | None = None
    try:
        suffix = _file_suffix(filename, mime_type)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        converter = DocumentConverter()
        conv_result = converter.convert(tmp_path)

        document = conv_result.document
        normalized_text = document.export_to_markdown() if hasattr(document, "export_to_markdown") else str(document)

        warnings: list[str] = []
        if not normalized_text.strip():
            warnings.append("Docling produced no normalized text; falling back to legacy extraction.")

        page_count = 0
        if hasattr(conv_result, "input") and hasattr(conv_result.input, "page_count"):
            page_count = int(conv_result.input.page_count or 0)

        title = ""
        if hasattr(document, "name"):
            title = str(document.name or "")

        return DoclingResult(
            status=STATUS_SUCCESS,
            normalized_text=normalized_text.strip(),
            title=title,
            page_count=page_count,
            warnings=warnings,
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return DoclingResult(
            status=STATUS_ERROR,
            error=str(exc)[:2000],
            warnings=["Docling normalization failed; falling back to legacy extraction."],
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
