from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


ELIGIBILITY_RUNTIME_FAILURE_CLASSIFICATION_SCHEMA_VERSION = (
    "eligibility-runtime-failure-classification.v1"
)


class EligibilityRuntimeFailureClassification(str, Enum):
    CONFIGURATION_OR_BINDING_FAILURE = "configuration_or_binding_failure"
    PROVIDER_TRANSPORT_FAILURE = "provider_transport_failure"
    PROVIDER_RESPONSE_CONTRACT_FAILURE = "provider_response_contract_failure"


@dataclass(frozen=True)
class EligibilityRuntimeFailureProvenance:
    """Bounded H.2.2 failure provenance; measurement only, never authority."""

    classification: EligibilityRuntimeFailureClassification | str
    provider_egress_occurred: bool

    def __post_init__(self) -> None:
        try:
            classification = EligibilityRuntimeFailureClassification(self.classification)
        except ValueError as exc:
            raise ValueError("unsupported eligibility runtime failure classification") from exc

        object.__setattr__(self, "classification", classification)
        object.__setattr__(
            self,
            "provider_egress_occurred",
            bool(self.provider_egress_occurred),
        )

        if (
            classification
            is EligibilityRuntimeFailureClassification.CONFIGURATION_OR_BINDING_FAILURE
            and self.provider_egress_occurred
        ):
            raise ValueError(
                "configuration/binding failures cannot claim provider egress"
            )
        if (
            classification
            is not EligibilityRuntimeFailureClassification.CONFIGURATION_OR_BINDING_FAILURE
            and not self.provider_egress_occurred
        ):
            raise ValueError(
                "provider transport/response failures require the provider egress boundary"
            )

    @classmethod
    def configuration_or_binding(cls) -> "EligibilityRuntimeFailureProvenance":
        return cls(
            EligibilityRuntimeFailureClassification.CONFIGURATION_OR_BINDING_FAILURE,
            False,
        )

    @classmethod
    def provider_transport(cls) -> "EligibilityRuntimeFailureProvenance":
        return cls(
            EligibilityRuntimeFailureClassification.PROVIDER_TRANSPORT_FAILURE,
            True,
        )

    @classmethod
    def provider_response_contract(cls) -> "EligibilityRuntimeFailureProvenance":
        return cls(
            EligibilityRuntimeFailureClassification.PROVIDER_RESPONSE_CONTRACT_FAILURE,
            True,
        )
