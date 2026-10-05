"""Complete reviewed REA catalog discovery, deliberately without execution authority.

Schemas are the donor's generated SDK advertisement projection. A matching tools/list
observation is contract recognition, not build/provider/session authentication.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass

REA_CAPABILITY = "engineering.reverse_engineering"
REA_TOOL_PREFIX = f"{REA_CAPABILITY}.rea."
REA_TOOL_COUNT = 122
REA_SOURCE_COMMIT = "4c8dc39f439b5283b077c6aa47f262714d7c4bbd"
REA_SNAPSHOT_SHA256 = "c794c19e339aeb6ba936d1284ebf048679f29212f1e65b900cef68c3314153af"
REA_LOCAL_CATALOG_SHA256 = "bdf2d28109fe5684584d644ab8b5e54fd7ec823a3f9aeeec989bf9abc2b25fa4"
MAX_JSON_BYTES = 4_000_000
MAX_JSON_NODES = 300_000
MAX_JSON_DEPTH = 80
MAX_POOL_NODES = 10_000
CONTRACT_FIELDS = frozenset({"name", "title", "description", "inputSchema", "outputSchema", "annotations", "effects", "kind", "requiresSession", "analysisOperation"})
ADVERTISED_FIELDS = frozenset({"name", "title", "description", "inputSchema", "outputSchema", "annotations"})
DECLARATION_FIELDS = CONTRACT_FIELDS - ADVERTISED_FIELDS
EFFECT_FIELDS = frozenset({"mutatesTarget", "mutatesSession", "writesFilesystem", "launchesProcess", "accessesNetwork", "changesUiState", "mayDiscardData", "idempotent"})
ANNOTATION_FIELDS = frozenset({"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"})
_SNAPSHOT = Path(__file__).parent / "rea_catalog" / "catalog.json"


class ReaCatalogInvalid(ValueError):
    """An untrusted catalog or observation is invalid or exceeds local bounds."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReaCatalogInvalid("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ReaCatalogInvalid("non-finite JSON number")


def _bounded_json(raw: bytes) -> Any:
    if not isinstance(raw, bytes) or len(raw) > MAX_JSON_BYTES:
        raise ReaCatalogInvalid("JSON byte limit or type invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        stack = [(value, 0)]
        count = 0
        while stack:
            item, depth = stack.pop()
            count += 1
            if count > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
                raise ReaCatalogInvalid("JSON structure exceeds bounds")
            if isinstance(item, float) and not (-float("inf") < item < float("inf")):
                raise ReaCatalogInvalid("non-finite JSON number")
            if isinstance(item, str):
                item.encode("utf-8")
            if isinstance(item, dict):
                for key in item:
                    key.encode("utf-8")
                stack.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                stack.extend((child, depth + 1) for child in item)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError, ValueError) as exc:
        raise ReaCatalogInvalid("invalid bounded JSON") from exc


def _decode_pool(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    nodes, roots = manifest.get("nodes"), manifest.get("roots")
    if not isinstance(nodes, list) or len(nodes) > MAX_POOL_NODES or not isinstance(roots, list) or len(roots) != REA_TOOL_COUNT:
        raise ReaCatalogInvalid("invalid catalog pool")
    visited: set[int] = set()
    expanded = 0

    def unpack(value: Any, ancestry: frozenset[int] = frozenset(), depth: int = 0) -> Any:
        nonlocal expanded
        expanded += 1
        if expanded > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise ReaCatalogInvalid("catalog expansion exceeds bounds")
        if not isinstance(value, list) or len(value) != 2:
            raise ReaCatalogInvalid("invalid pool value")
        tag, payload = value
        if tag == "value":
            if payload is not None and type(payload) not in (str, bool, int, float):
                raise ReaCatalogInvalid("invalid pool scalar")
            return payload
        if tag != "ref" or type(payload) is not int or not 0 <= payload < len(nodes) or payload in ancestry:
            raise ReaCatalogInvalid("invalid or cyclic pool reference")
        visited.add(payload)
        node = nodes[payload]
        if not isinstance(node, list) or len(node) != 2 or not isinstance(node[1], list):
            raise ReaCatalogInvalid("invalid pool node")
        ancestry = ancestry | {payload}
        if node[0] == "array":
            return [unpack(child, ancestry, depth + 1) for child in node[1]]
        if node[0] != "object":
            raise ReaCatalogInvalid("unknown pool node type")
        result = {}
        for pair in node[1]:
            if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str) or pair[0] in result:
                raise ReaCatalogInvalid("invalid pool object")
            result[pair[0]] = unpack(pair[1], ancestry, depth + 1)
        return result

    tools = [unpack(root) for root in roots]
    if len(visited) != len(nodes):
        raise ReaCatalogInvalid("unreferenced catalog content")
    return tools


@dataclass(frozen=True)
class ReaToolDescriptor:
    tool_id: str
    name: str
    contract_json: bytes

    def contract(self) -> dict[str, Any]:
        """Return a detached view; caller mutation cannot modify the reviewed catalog."""
        return json.loads(self.contract_json)


@dataclass(frozen=True)
class ReaObservationComparison:
    advertised_contract_matches: bool
    source_declarations_supplied: bool
    source_declarations_match: bool | None
    issues: tuple[str, ...]
    authenticated: bool = False
    execution_authorized: bool = False


def _validate_contract(tool: Any) -> None:
    if not isinstance(tool, dict) or set(tool) != CONTRACT_FIELDS:
        raise ReaCatalogInvalid("tool contract fields differ")
    if not isinstance(tool["name"], str) or re.fullmatch(r"[a-z][a-z0-9_]*", tool["name"]) is None:
        raise ReaCatalogInvalid("tool name invalid")
    for field in ("title", "description", "kind"):
        if not isinstance(tool[field], str) or not tool[field]:
            raise ReaCatalogInvalid("tool text invalid")
    if type(tool["requiresSession"]) is not bool or (tool["analysisOperation"] is not None and not isinstance(tool["analysisOperation"], str)):
        raise ReaCatalogInvalid("tool session/operation invalid")
    for field in ("inputSchema", "outputSchema"):
        if not isinstance(tool[field], dict):
            raise ReaCatalogInvalid("tool schema invalid")
    for field, fields in (("effects", EFFECT_FIELDS), ("annotations", ANNOTATION_FIELDS)):
        if not isinstance(tool[field], dict) or set(tool[field]) != fields or any(type(item) is not bool for item in tool[field].values()):
            raise ReaCatalogInvalid("tool effects/annotations invalid")


def _load_catalog(raw: bytes) -> tuple[ReaToolDescriptor, ...]:
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != REA_SNAPSHOT_SHA256:
        raise ReaCatalogInvalid("reviewed snapshot integrity mismatch")
    manifest = _bounded_json(raw)
    if not isinstance(manifest, dict) or manifest.get("format") != "aios-rea-catalog.v1" or manifest.get("source", {}).get("commit") != REA_SOURCE_COMMIT or manifest.get("tool_count") != REA_TOOL_COUNT:
        raise ReaCatalogInvalid("reviewed snapshot identity mismatch")
    tools = _decode_pool(manifest)
    names = []
    for tool in tools:
        _validate_contract(tool)
        names.append(tool["name"])
    if names != sorted(set(names)) or len(names) != REA_TOOL_COUNT:
        raise ReaCatalogInvalid("reviewed catalog membership differs")
    digest = hashlib.sha256(_canonical(tools)).hexdigest()
    if digest != REA_LOCAL_CATALOG_SHA256 or manifest.get("local_catalog_sha256") != digest:
        raise ReaCatalogInvalid("reviewed catalog semantic integrity mismatch")
    return tuple(ReaToolDescriptor(REA_TOOL_PREFIX + tool["name"], tool["name"], _canonical(tool)) for tool in tools)


@lru_cache(maxsize=1)
def discover_rea_tools() -> tuple[ReaToolDescriptor, ...]:
    """Discover all reviewed tools; discovery grants no entitlement or connection."""
    with _SNAPSHOT.open("rb") as source:
        return _load_catalog(source.read(MAX_JSON_BYTES + 1))


def get_rea_tool(tool_id: str) -> ReaToolDescriptor:
    for tool in discover_rea_tools():
        if tool.tool_id == tool_id:
            return tool
    raise ReaCatalogInvalid("unknown exact REA tool identity")


def disabled_rea_runtime_profile() -> AgentRuntimeProfile:
    """Technical candidate only; no enable parameter or production selector registration."""
    return AgentRuntimeProfile(
        profile_key="rea-reviewed-catalog-candidate-v1", runtime_class=RuntimeClass.DONOR_ADAPTER,
        adapter_key="rea-unconnected", provider_key="rea-unadmitted",
        technical_capabilities=(REA_CAPABILITY,), available_tools=tuple(tool.tool_id for tool in discover_rea_tools()),
        independence_group="rea-unadmitted", enabled=False,
    )


def compare_rea_tools_observation(raw: bytes) -> ReaObservationComparison:
    """Compare one complete tools/list result, never trust/admit its provider.

    Standard MCP advertises schemas/annotations but omits REA effects, kind, session
    and operation declarations. If all four are supplied on every tool, compare them
    separately. Pagination, partial declarations, unknown fields and drift fail match.
    """
    observed = _bounded_json(raw)
    if not isinstance(observed, dict) or set(observed) != {"tools"} or not isinstance(observed["tools"], list) or len(observed["tools"]) != REA_TOOL_COUNT:
        raise ReaCatalogInvalid("expected one complete bounded 122-tool tools/list result")
    expected = {tool.name: tool.contract() for tool in discover_rea_tools()}
    issues: list[str] = []
    seen: set[str] = set()
    declaration_count = 0
    declarations_match = True
    for tool in observed["tools"]:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            raise ReaCatalogInvalid("invalid advertised tool")
        name = tool["name"]
        if name in seen or name not in expected:
            issues.append("duplicate or unknown tool name")
            continue
        seen.add(name)
        fields = set(tool)
        has_declarations = DECLARATION_FIELDS <= fields
        if has_declarations:
            declaration_count += 1
            if any(_canonical(tool[key]) != _canonical(expected[name][key]) for key in DECLARATION_FIELDS):
                declarations_match = False
        if fields not in (ADVERTISED_FIELDS, CONTRACT_FIELDS):
            issues.append(f"{name}: incomplete or unknown fields")
        if not ADVERTISED_FIELDS <= fields or any(_canonical(tool[key]) != _canonical(expected[name][key]) for key in ADVERTISED_FIELDS if key in tool):
            issues.append(f"{name}: advertised contract differs")
    if seen != set(expected):
        issues.append("catalog membership differs")
    if declaration_count not in (0, REA_TOOL_COUNT):
        issues.append("incomplete source declarations")
    if not declarations_match:
        issues.append("source declarations differ")
    supplied = declaration_count == REA_TOOL_COUNT
    return ReaObservationComparison(not issues, supplied, declarations_match if supplied else None, tuple(issues))
