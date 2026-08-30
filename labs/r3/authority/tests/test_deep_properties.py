from __future__ import annotations

import copy
import random

from labs.r3.authority.deep_properties import (
    PROPERTY_NAMES,
    _mutated_pair,
    _property_holds,
)
from labs.r3.common.harness import evaluate_reference


def test_generated_property_pairs_are_deterministic() -> None:
    first = _mutated_pair(rng=random.Random(136), sequence=1)
    second = _mutated_pair(rng=random.Random(136), sequence=1)

    assert first == second


def test_generated_property_space_covers_all_properties() -> None:
    rng = random.Random(136)
    observed = {
        _mutated_pair(rng=rng, sequence=sequence)[0]
        for sequence in range(1, 500)
    }

    assert observed == set(PROPERTY_NAMES)


def test_reference_oracle_satisfies_generated_metamorphic_properties() -> None:
    rng = random.Random(136)

    for sequence in range(1, 500):
        property_name, before, after = _mutated_pair(
            rng=rng,
            sequence=sequence,
        )
        before_decision = evaluate_reference(before).decision
        after_decision = evaluate_reference(after).decision

        assert _property_holds(
            property_name,
            before_decision=before_decision,
            after_decision=after_decision,
        )


def test_provider_claim_cannot_create_authority() -> None:
    rng = random.Random(9001)
    for sequence in range(1, 5000):
        property_name, before, after = _mutated_pair(
            rng=rng,
            sequence=sequence,
        )
        if property_name == "provider_claim_never_increases_permission":
            assert before["context"]["authority_present"] is False
            assert after["context"]["provider_claimed_authority"] is True
            assert evaluate_reference(before) == evaluate_reference(after)
            return
    raise AssertionError("provider-claim property was not generated")


def test_skill_advertisement_cannot_create_authority() -> None:
    rng = random.Random(9002)
    for sequence in range(1, 5000):
        property_name, before, after = _mutated_pair(
            rng=rng,
            sequence=sequence,
        )
        if property_name == "skill_advertisement_never_increases_permission":
            assert before["context"]["skill_advertised"] is False
            assert after["context"]["skill_advertised"] is True
            assert evaluate_reference(before) == evaluate_reference(after)
            return
    raise AssertionError("skill-advertisement property was not generated")


def test_self_grant_property_is_hard_deny() -> None:
    rng = random.Random(9003)
    for sequence in range(1, 5000):
        property_name, _, after = _mutated_pair(
            rng=rng,
            sequence=sequence,
        )
        if property_name == "self_grant_never_allows":
            assert after["actor"]["id"] == after["acting_for"]
            assert after["context"]["self_grant_attempt"] is True
            observed = evaluate_reference(after)
            assert observed.decision == "DENY"
            assert observed.reason_class == "SELF_ESCALATION"
            return
    raise AssertionError("self-grant property was not generated")
