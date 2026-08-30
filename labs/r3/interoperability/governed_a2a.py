from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.protobuf.json_format import MessageToDict

from a2a.helpers.proto_helpers import get_artifact_text, new_text_message
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandlerV2
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    Task,
)

from labs.r3.common.harness import fingerprint
from labs.r3.interoperability.a2a_fixture import (
    ExecutorCounters,
    SyntheticRemoteAgentExecutor,
)


PRIVILEGED_LOCAL_ACTIONS = {
    "client.communication.send",
    "government_application.submit",
    "authority.grant",
    "verified_rule.write",
    "evidence.write",
    "secret.read",
}

SAFE_REMOTE_SKILLS = {"mobility_analysis"}


@dataclass(frozen=True)
class AgentTrustRecord:
    agent_name: str
    expected_version: str
    card_fingerprint: str


@dataclass(frozen=True)
class A2AResult:
    decision: str
    reason_class: str
    remote_called: bool
    replayed: bool
    task_state: int | None
    artifact_count: int
    remote_observation_untrusted: bool
    canonical_workitem_created: bool
    canonical_authority_effects: int
    canonical_business_effects: int
    task_id: str | None
    response_fingerprint: str | None


def card_fingerprint(card: AgentCard) -> str:
    return fingerprint(
        MessageToDict(
            card,
            preserving_proto_field_name=True,
        )
    )


def trust_record(card: AgentCard) -> AgentTrustRecord:
    return AgentTrustRecord(
        agent_name=card.name,
        expected_version=card.version,
        card_fingerprint=card_fingerprint(card),
    )


class GovernedA2AGateway:
    def __init__(
        self,
        *,
        card: AgentCard,
        trust: AgentTrustRecord,
        hostile_executor: bool = False,
    ) -> None:
        self.card = card
        self.trust = trust
        self.counters = ExecutorCounters()
        self.task_store = InMemoryTaskStore()
        self.executor = SyntheticRemoteAgentExecutor(
            counters=self.counters,
            hostile=hostile_executor,
        )
        self.handler = DefaultRequestHandlerV2(
            agent_executor=self.executor,
            task_store=self.task_store,
            agent_card=self.card,
        )
        self._replay: dict[str, A2AResult] = {}

    def inspect_card(self) -> dict[str, Any]:
        identity_ok = (
            self.card.name == self.trust.agent_name
            and self.card.version == self.trust.expected_version
            and card_fingerprint(self.card) == self.trust.card_fingerprint
        )
        advertised = sorted(skill.id for skill in self.card.skills)
        safe = sorted(
            skill_id for skill_id in advertised if skill_id in SAFE_REMOTE_SKILLS
        )
        return {
            "identity_ok": identity_ok,
            "agent_name": self.card.name,
            "version": self.card.version,
            "advertised_skills": advertised,
            "accepted_discovery_skills": safe if identity_ok else [],
            "authority_granted": False,
            "autonomy_granted": False,
            "canonical_skill_assignments_created": 0,
            "card_fingerprint": card_fingerprint(self.card),
        }

    async def send_task(
        self,
        *,
        actor_tenant: str,
        target_tenant: str,
        local_action: str,
        request_text: str,
        idempotency_key: str,
    ) -> A2AResult:
        replay = self._replay.get(idempotency_key)
        if replay is not None:
            return A2AResult(
                **{
                    **replay.__dict__,
                    "remote_called": False,
                    "replayed": True,
                }
            )

        card = self.inspect_card()
        if not card["identity_ok"]:
            result = A2AResult(
                decision="DENY",
                reason_class="A2A_AGENT_IDENTITY_MISMATCH",
                remote_called=False,
                replayed=False,
                task_state=None,
                artifact_count=0,
                remote_observation_untrusted=True,
                canonical_workitem_created=False,
                canonical_authority_effects=0,
                canonical_business_effects=0,
                task_id=None,
                response_fingerprint=None,
            )
            self._replay[idempotency_key] = result
            return result

        if actor_tenant != target_tenant:
            result = A2AResult(
                decision="DENY",
                reason_class="A2A_CROSS_TENANT_DENIED",
                remote_called=False,
                replayed=False,
                task_state=None,
                artifact_count=0,
                remote_observation_untrusted=True,
                canonical_workitem_created=False,
                canonical_authority_effects=0,
                canonical_business_effects=0,
                task_id=None,
                response_fingerprint=None,
            )
            self._replay[idempotency_key] = result
            return result

        if local_action in PRIVILEGED_LOCAL_ACTIONS:
            result = A2AResult(
                decision="DENY",
                reason_class="A2A_REMOTE_CLAIM_CANNOT_AUTHORIZE_LOCAL_ACTION",
                remote_called=False,
                replayed=False,
                task_state=None,
                artifact_count=0,
                remote_observation_untrusted=True,
                canonical_workitem_created=False,
                canonical_authority_effects=0,
                canonical_business_effects=0,
                task_id=None,
                response_fingerprint=None,
            )
            self._replay[idempotency_key] = result
            return result

        message = new_text_message(request_text, role=Role.ROLE_USER)
        request = SendMessageRequest(
            message=message,
            configuration=SendMessageConfiguration(return_immediately=False),
        )
        context = ServerCallContext(
            tenant=actor_tenant,
            state={"headers": {"a2a-version": "1.0"}},
        )
        response = await self.handler.on_message_send(request, context)
        if not isinstance(response, Task):
            raise ValueError("synthetic A2A fixture expected a Task response")

        artifacts = [get_artifact_text(item) for item in response.artifacts]
        payload = {
            "task_id": response.id,
            "context_id": response.context_id,
            "state": int(response.status.state),
            "artifacts": artifacts,
        }
        result = A2AResult(
            decision="ALLOW",
            reason_class="A2A_REMOTE_RESULT_OBSERVED_NOT_CANONICAL",
            remote_called=True,
            replayed=False,
            task_state=int(response.status.state),
            artifact_count=len(response.artifacts),
            remote_observation_untrusted=True,
            canonical_workitem_created=False,
            canonical_authority_effects=0,
            canonical_business_effects=0,
            task_id=response.id,
            response_fingerprint=fingerprint(payload),
        )
        self._replay[idempotency_key] = result
        return result

    async def close(self) -> None:
        await self.handler.aclose()
