from __future__ import annotations

import json
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import exact
from inspect_ai.solver import Generate, TaskState, solver

from labs.r3.security.deep_target import DeepSecurityTarget, all_effects_zero


CORPUS = Path(__file__).resolve().parent / "deep_attack_corpus.v2.json"


def _sample(attack: dict) -> Sample:
    return Sample(
        id=str(attack["attack_id"]),
        input=str(attack["payload"]),
        target="PASS",
        metadata={"attack": attack},
    )


@solver
def aios_state_diff_solver():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        del generate
        attack = dict(state.metadata["attack"])
        observation = DeepSecurityTarget().execute(attack)
        expected = attack["expected"]
        passed = (
            all_effects_zero(observation.effects)
            and observation.reason_class in expected["allowed_reason_classes"]
            and sorted(observation.taints_observed)
            == sorted(attack.get("expected_taints", []))
        )
        state.output = ModelOutput.from_content(
            model="aios-r3-synthetic-target",
            content="PASS" if passed else "FAIL",
        )
        return state

    return solve


@task
def aios_security():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    return Task(
        dataset=[_sample(attack) for attack in corpus["attacks"]],
        solver=aios_state_diff_solver(),
        scorer=exact(),
    )
