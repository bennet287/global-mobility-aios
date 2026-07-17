from pathlib import Path


def test_remediation_script_avoids_detached_orm_access_after_session() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = (repo_root / "scripts" / "Repair-CoverageSourceCanonicalUrl.ps1").read_text()

    assert "result = None" in script
    assert "print(json.dumps(result, indent=2))" in script
    assert '"already_corrected": url_already_corrected and not changed' in script
    assert 'source="coverage_source_remediation_v10_18_2"' in script

    print_section = script.split("print(json.dumps(result, indent=2))", 1)[1]
    assert "source.id" not in print_section
    assert "monitor.id" not in print_section
    assert "monitor.status" not in print_section
