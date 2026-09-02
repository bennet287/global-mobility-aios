from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "Prepare-CoverageTranche.ps1"


def test_tranche_script_defaults_to_dry_run_and_requires_explicit_apply() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "SupportsShouldProcess = $true" in text
    assert "[switch]$ApplyBaselineQueues" in text
    assert "dry_run = -not $apply" in text
    assert "queue_eligible_baselines = [bool]$ApplyBaselineQueues" in text
    assert "$PSCmdlet.ShouldProcess" in text


def test_tranche_script_does_not_call_review_or_publish_endpoints() -> None:
    text = SCRIPT.read_text(encoding="utf-8").lower()
    assert "/assistant/prepare" in text
    assert "/review" not in text
    assert "/publish" not in text
    assert "capture-baselines" not in text
