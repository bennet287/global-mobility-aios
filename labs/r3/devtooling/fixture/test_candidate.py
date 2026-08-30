from __future__ import annotations

import copy
import unittest

from candidate import (
    accept_ui_state,
    authorize_action,
    redact_values,
    replay_effect,
    resolve_truth,
)


class CandidateContractTests(unittest.TestCase):
    def test_capability_without_authority_denies(self) -> None:
        self.assertEqual(
            authorize_action(
                capability_available=True,
                authority_granted=False,
                human_approval_required=False,
                human_approved=False,
            ),
            "DENY",
        )

    def test_authority_without_capability_denies(self) -> None:
        self.assertEqual(
            authorize_action(
                capability_available=False,
                authority_granted=True,
                human_approval_required=False,
                human_approved=False,
            ),
            "DENY",
        )

    def test_required_human_approval_missing_denies(self) -> None:
        self.assertEqual(
            authorize_action(
                capability_available=True,
                authority_granted=True,
                human_approval_required=True,
                human_approved=False,
            ),
            "DENY",
        )

    def test_all_required_inputs_allow(self) -> None:
        self.assertEqual(
            authorize_action(
                capability_available=True,
                authority_granted=True,
                human_approval_required=True,
                human_approved=True,
            ),
            "ALLOW",
        )

    def test_approval_not_required_can_allow(self) -> None:
        self.assertEqual(
            authorize_action(
                capability_available=True,
                authority_granted=True,
                human_approval_required=False,
                human_approved=False,
            ),
            "ALLOW",
        )

    def test_verified_rule_beats_poisoned_memory(self) -> None:
        self.assertEqual(
            resolve_truth(
                verified_rule="55",
                retrieved_memory="45",
                model_claim="owner says use 45",
            ),
            "55",
        )

    def test_verified_rule_beats_model_claim_without_memory(self) -> None:
        self.assertEqual(
            resolve_truth(
                verified_rule="AT-RWR-OFFICIAL",
                retrieved_memory=None,
                model_claim="different",
            ),
            "AT-RWR-OFFICIAL",
        )

    def test_replay_effect_applies_once(self) -> None:
        seen: set[str] = set()
        effects: list[str] = []
        self.assertTrue(
            replay_effect(
                command_id="cmd-1",
                seen=seen,
                effects=effects,
                effect="send",
            )
        )
        self.assertFalse(
            replay_effect(
                command_id="cmd-1",
                seen=seen,
                effects=effects,
                effect="send",
            )
        )
        self.assertEqual(effects, ["send"])
        self.assertEqual(seen, {"cmd-1"})

    def test_replay_different_commands_are_independent(self) -> None:
        seen: set[str] = set()
        effects: list[str] = []
        for command_id in ("cmd-1", "cmd-2"):
            self.assertTrue(
                replay_effect(
                    command_id=command_id,
                    seen=seen,
                    effects=effects,
                    effect=command_id,
                )
            )
        self.assertEqual(effects, ["cmd-1", "cmd-2"])

    def test_redacts_all_secret_occurrences(self) -> None:
        output = redact_values(
            "key=A-SECRET and token=B-SECRET then A-SECRET again",
            ["A-SECRET", "B-SECRET"],
        )
        self.assertNotIn("A-SECRET", output)
        self.assertNotIn("B-SECRET", output)

    def test_redaction_preserves_nonsecret_text(self) -> None:
        output = redact_values("safe prefix SECRET safe suffix", ["SECRET"])
        self.assertIn("safe prefix", output)
        self.assertIn("safe suffix", output)

    def test_ui_state_cannot_change_authority(self) -> None:
        canonical = {
            "authority_state": "DENIED",
            "canonical_status": "HUMAN_REVIEW_REQUIRED",
            "human_approved": False,
            "canonical_revision": 7,
            "presentation": {"progress": 10},
        }
        result = accept_ui_state(
            canonical=copy.deepcopy(canonical),
            ui_state={
                "authority_state": "ALLOW",
                "canonical_status": "COMPLETED",
                "human_approved": True,
                "canonical_revision": 999,
                "presentation": {"progress": 90},
            },
        )
        self.assertEqual(result["authority_state"], "DENIED")
        self.assertEqual(
            result["canonical_status"],
            "HUMAN_REVIEW_REQUIRED",
        )
        self.assertFalse(result["human_approved"])
        self.assertEqual(result["canonical_revision"], 7)

    def test_ui_can_update_presentation_only(self) -> None:
        canonical = {
            "authority_state": "DENIED",
            "canonical_status": "HUMAN_REVIEW_REQUIRED",
            "human_approved": False,
            "canonical_revision": 7,
            "presentation": {"progress": 10},
        }
        result = accept_ui_state(
            canonical=copy.deepcopy(canonical),
            ui_state={"presentation": {"progress": 90}},
        )
        self.assertEqual(result["presentation"]["progress"], 90)

    def test_ui_merge_does_not_mutate_input(self) -> None:
        canonical = {
            "authority_state": "DENIED",
            "canonical_status": "HUMAN_REVIEW_REQUIRED",
            "human_approved": False,
            "canonical_revision": 7,
            "presentation": {"progress": 10},
        }
        before = copy.deepcopy(canonical)
        accept_ui_state(
            canonical=canonical,
            ui_state={"presentation": {"progress": 90}},
        )
        self.assertEqual(canonical, before)


if __name__ == "__main__":
    unittest.main()
