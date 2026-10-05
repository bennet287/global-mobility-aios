from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationPosition, OrganizationalWorkItem
from app.services import organization_rea_catalog as catalog
from app.services.organization_agent_runtime import RuntimeProfileDisabled, bind_employee_runtime
from app.services.organization_command import canonical_json
from app.services.organization_context_broker import build_work_item_context_bundle


def _observation(*, declarations: bool = False) -> dict:
    tools = [tool.contract() for tool in catalog.discover_rea_tools()]
    if not declarations:
        tools = [{key: value for key, value in tool.items() if key in catalog.ADVERTISED_FIELDS} for tool in tools]
    return {"tools": tools}


def _compare(value: dict):
    return catalog.compare_rea_tools_observation(catalog._canonical(value))


def test_all_122_exact_qualified_tools_and_lossless_contracts() -> None:
    tools = catalog.discover_rea_tools()
    assert len(tools) == len({tool.name for tool in tools}) == 122
    contracts = [tool.contract() for tool in tools]
    assert hashlib.sha256(catalog._canonical(contracts)).hexdigest() == catalog.REA_LOCAL_CATALOG_SHA256
    for tool in tools:
        assert tool.tool_id == f"engineering.reverse_engineering.rea.{tool.name}"
        assert catalog.get_rea_tool(tool.tool_id) == tool
        contract = tool.contract()
        assert set(contract) == catalog.CONTRACT_FIELDS
        assert set(contract["effects"]) == catalog.EFFECT_FIELDS
        assert set(contract["annotations"]) == catalog.ANNOTATION_FIELDS
    # Coverage includes mutation, process capture, replay and reconstruction, not just static inspection.
    names = {tool.name for tool in tools}
    assert {"inspect_managed_artifact", "capture_process_scenario", "set_address_name", "run_controlled_replay", "verify_reconstruction", "get_evidence_bundle"} <= names
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog.get_rea_tool(catalog.REA_CAPABILITY)
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog.get_rea_tool(catalog.REA_TOOL_PREFIX + "*")


def test_detached_contracts_and_frozen_descriptors() -> None:
    tool = catalog.discover_rea_tools()[0]
    detached = tool.contract()
    detached["inputSchema"]["type"] = "forged"
    detached["effects"]["mutatesTarget"] = "forged"
    assert catalog.get_rea_tool(tool.tool_id).contract()["inputSchema"]["type"] == "object"
    assert type(tool.contract()["effects"]["mutatesTarget"]) is bool
    with pytest.raises(FrozenInstanceError):
        tool.name = "forged"


def test_plain_and_extended_observations_remain_unauthenticated() -> None:
    plain = _compare(_observation())
    assert plain.advertised_contract_matches
    assert not plain.source_declarations_supplied
    assert plain.source_declarations_match is None
    extended = _compare(_observation(declarations=True))
    assert extended.advertised_contract_matches and extended.source_declarations_supplied
    assert extended.source_declarations_match
    for result in (plain, extended):
        assert not result.authenticated and not result.execution_authorized
    reordered = _observation()
    reordered["tools"].reverse()
    assert _compare(reordered).advertised_contract_matches


@pytest.mark.parametrize("change", ["duplicate", "rename", "extra", "input", "output", "annotations", "title", "description", "unknown_field", "missing_field", "numeric_bool", "numeric_schema_bool"])
def test_advertised_contract_drift_rejected(change: str) -> None:
    observed = _observation()
    tool = observed["tools"][0]
    if change == "duplicate":
        observed["tools"][-1] = tool
    elif change in ("rename", "extra"):
        tool["name"] = "renamed_unreviewed_tool"
    elif change in ("input", "output"):
        tool[f"{change}Schema"]["properties"]["unreviewed"] = {"type": "string"}
    elif change == "annotations":
        tool["annotations"]["readOnlyHint"] = not tool["annotations"]["readOnlyHint"]
    elif change in ("title", "description"):
        tool[change] += " changed"
    elif change == "unknown_field":
        tool["execution_allowed"] = True
    elif change == "missing_field":
        del tool["outputSchema"]
    elif change == "numeric_bool":
        tool["annotations"]["readOnlyHint"] = int(tool["annotations"]["readOnlyHint"])
    else:
        tool["inputSchema"]["additionalProperties"] = 0
    assert not _compare(observed).advertised_contract_matches


@pytest.mark.parametrize("field", sorted(catalog.DECLARATION_FIELDS))
def test_source_declaration_drift_and_partial_declarations(field: str) -> None:
    observed = _observation(declarations=True)
    tool = observed["tools"][0]
    if field == "effects":
        tool[field]["mutatesTarget"] = int(tool[field]["mutatesTarget"])
    elif field == "requiresSession":
        tool[field] = not tool[field]
    else:
        tool[field] = "changed"
    result = _compare(observed)
    assert not result.advertised_contract_matches
    assert result.source_declarations_match is False
    del observed["tools"][0][field]
    assert not _compare(observed).advertised_contract_matches


@pytest.mark.parametrize("raw", [b'{"tools":[],"tools":[]}', b'{"tools":NaN}', b'{"tools":Infinity}', b'{"tools":1e999}', b'\xff', b'{', b'[]', b'{"tools":"\\ud800"}'])
def test_invalid_json_and_nonfinite_numbers_rejected(raw: bytes) -> None:
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog.compare_rea_tools_observation(raw)


def test_observation_byte_depth_node_and_pagination_limits(monkeypatch) -> None:
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog.compare_rea_tools_observation(b" " * (catalog.MAX_JSON_BYTES + 1))
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog.compare_rea_tools_observation(b"[" * 90 + b"0" + b"]" * 90)
    observed = _observation()
    observed["nextCursor"] = "more"
    with pytest.raises(catalog.ReaCatalogInvalid):
        _compare(observed)
    for count in (121, 123):
        observed = _observation()
        observed["tools"] = (observed["tools"] + [observed["tools"][0]])[:count]
        with pytest.raises(catalog.ReaCatalogInvalid):
            _compare(observed)
    monkeypatch.setattr(catalog, "MAX_JSON_NODES", 10)
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog._bounded_json(b"[0,0,0,0,0,0,0,0,0,0]")


@pytest.mark.parametrize("change", ["effects", "schema", "delete", "duplicate", "extra", "source"])
def test_checked_in_snapshot_tampering_fails_before_discovery(change: str) -> None:
    manifest = json.loads(catalog._SNAPSHOT.read_bytes())
    if change == "effects":
        manifest["nodes"][0] = ["object", []]
    elif change == "schema":
        manifest["nodes"][-1] = ["array", []]
    elif change == "delete":
        manifest["roots"].pop()
    elif change == "duplicate":
        manifest["roots"][0] = manifest["roots"][1]
    elif change == "extra":
        manifest["nodes"].append(["object", []])
    else:
        manifest["source"]["commit"] = "0" * 40
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog._load_catalog(catalog._canonical(manifest))


@pytest.mark.parametrize("node", [["array", [["ref", 0]]], ["array", [["ref", 9]]], ["array", [["ref", True]]], ["object", [["x", ["value", 1]], ["x", ["value", 2]]]], ["unknown", []]])
def test_pool_reference_cycles_invalid_refs_and_duplicates_fail(node: list) -> None:
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog._decode_pool({"nodes": [node], "roots": [["ref", 0]] * 122})


def test_pool_expansion_and_unused_nodes_bounded(monkeypatch) -> None:
    pool = {"nodes": [["array", [["value", 0]]]], "roots": [["ref", 0]] * 122}
    monkeypatch.setattr(catalog, "MAX_JSON_NODES", 10)
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog._decode_pool(pool)
    monkeypatch.setattr(catalog, "MAX_JSON_NODES", 300_000)
    pool["nodes"].append(["object", []])
    with pytest.raises(catalog.ReaCatalogInvalid):
        catalog._decode_pool(pool)


def test_full_catalog_profile_disabled_and_canonical_binding_never_expands_authority(db_session: Session) -> None:
    profile = catalog.disabled_rea_runtime_profile()
    assert not profile.enabled and len(profile.available_tools) == 122
    assert profile.technical_capabilities == (catalog.REA_CAPABILITY,)
    allowed = profile.available_tools[0]
    position = OrganizationPosition(position_key="rea-test-engineer", title="Engineer", department="Engineering", reports_to_position_key="engineering_lead", role_card_name="engineer", authority_level="L2", contract_json=canonical_json({"context_authority": {"allowed_tools": [allowed]}}), status="active", created_by="pytest")
    db_session.add(position)
    work = OrganizationalWorkItem(idempotency_key="rea-catalog-test", tenant_key="tenant-a", title="Investigate", objective="Investigate authorized artifact", department="Engineering", authority_level="L2", assigned_position_key=position.position_key, risk_level="routine", context_json="{}", created_by="pytest")
    db_session.add(work)
    db_session.commit()
    context = build_work_item_context_bundle(db_session, tenant_key="tenant-a", position_key=position.position_key, work_item_id=work.id)
    with pytest.raises(RuntimeProfileDisabled):
        bind_employee_runtime(db_session, context=context, profile=profile)
    # Existing generic runtime contracts allow constructing another profile. Even
    # that test-only profile and a forged bundle cannot expand canonical authority.
    forged = replace(context, allowed_tools=profile.available_tools)
    binding = bind_employee_runtime(db_session, context=forged, profile=replace(profile, enabled=True))
    assert binding.allowed_tools == (allowed,)
    position.contract_json = canonical_json({"context_authority": {"allowed_tools": [catalog.REA_CAPABILITY, catalog.REA_TOOL_PREFIX + "*"]}})
    db_session.add(position)
    db_session.commit()
    current = build_work_item_context_bundle(db_session, tenant_key="tenant-a", position_key=position.position_key, work_item_id=work.id)
    assert bind_employee_runtime(db_session, context=current, profile=replace(profile, enabled=True)).allowed_tools == ()


def _importer():
    script = Path(__file__).resolve().parents[3] / "scripts" / "import_rea_catalog.py"
    spec = importlib.util.spec_from_file_location("rea_catalog_import_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_importer_deterministic_lossless_and_rejects_wrong_dirty_altered_source(tmp_path: Path, monkeypatch) -> None:
    importer = _importer()
    contracts = [tool.contract() for tool in catalog.discover_rea_tools()]
    payload = json.dumps({"catalog": contracts})
    files = {name: b"fixture\n" for name in importer.SOURCE_FILES}
    files["src/generatedMcpToolCatalog.ts"] = f"const GENERATED_PAYLOAD_JSON = {payload!r};".encode()
    files["package.json"] = b'{"name":"rea-agents","version":"3.2.1"}'
    files["docs/product-catalog.json"] = b'{"runtime_catalog":{"digests":{"combined_sha256":"source-declared"}}}'
    for name, data in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    status = b""
    commit = importer.SOURCE_COMMIT

    def fake_git(source, *args):
        if args[0] == "rev-parse":
            return commit.encode()
        if args[0] == "status":
            assert "--untracked-files=no" in args
            return status
        assert args[0] == "show"
        return files[args[1].split(":", 1)[1]]

    monkeypatch.setattr(importer, "git", fake_git)
    first, license_text = importer.generate(tmp_path)
    assert importer.generate(tmp_path) == (first, license_text)
    generated = catalog._bounded_json(first)
    assert catalog._decode_pool(generated) == contracts
    assert generated["local_catalog_sha256"] == catalog.REA_LOCAL_CATALOG_SHA256
    assert license_text == files["LICENSE"]
    commit = "0" * 40
    with pytest.raises(ValueError, match="reviewed commit"):
        importer.generate(tmp_path)
    commit = importer.SOURCE_COMMIT
    status = b" M package.json"
    with pytest.raises(ValueError, match="dirty"):
        importer.generate(tmp_path)
    status = b""
    (tmp_path / "package.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="bytes differ"):
        importer.generate(tmp_path)
    (tmp_path / "package.json").unlink()
    (tmp_path / "package.json").symlink_to(tmp_path / "server.json")
    with pytest.raises(ValueError, match="bytes differ"):
        importer.generate(tmp_path)
