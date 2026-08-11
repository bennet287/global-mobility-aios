from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DepartmentRuntimeSpec:
    """Declarative organization-department runtime contract.

    `allowed_actions=None` means the department owns its existing general runtime;
    an empty set means it is registered for governance but deliberately held.
    """

    department: str
    executive_position: str
    allowed_actions: frozenset[str] | None = frozenset()
    contract_position: str | None = None
    contract_authority_level: str | None = None
    contract_repair_label: str | None = None
    unavailable_description: str | None = None
    preflight_audit_action: str | None = None


_INTERNAL_ANALYSIS = frozenset({"internal.analysis"})

DEPARTMENT_RUNTIMES: dict[str, DepartmentRuntimeSpec] = {
    "executive": DepartmentRuntimeSpec("executive", "ceo"),
    "operations": DepartmentRuntimeSpec("operations", "coo", allowed_actions=None),
    "technology": DepartmentRuntimeSpec(
        "technology",
        "cto",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="cto",
        contract_authority_level="L3",
        contract_repair_label="CTO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_technology_preflight",
    ),
    "product": DepartmentRuntimeSpec(
        "product",
        "cpo",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="cpo",
        contract_authority_level="L3",
        contract_repair_label="CPO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_product_preflight",
    ),
    "security": DepartmentRuntimeSpec(
        "security",
        "ciso",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="ciso",
        contract_authority_level="L3",
        contract_repair_label="CISO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_security_preflight",
    ),
    "security operations": DepartmentRuntimeSpec(
        "security operations",
        "ciso",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="ciso",
        contract_authority_level="L3",
        contract_repair_label="CISO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_security_operations_preflight",
    ),
    "marketing": DepartmentRuntimeSpec(
        "marketing",
        "cmo",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="cmo",
        contract_authority_level="L3",
        contract_repair_label="CMO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_marketing_preflight",
    ),
    "finance": DepartmentRuntimeSpec(
        "finance",
        "cfo",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="cfo",
        contract_authority_level="L3",
        contract_repair_label="CFO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_finance_preflight",
    ),
    "communications": DepartmentRuntimeSpec(
        "communications",
        "cco",
        allowed_actions=_INTERNAL_ANALYSIS,
        contract_position="cco",
        contract_authority_level="L3",
        contract_repair_label="CCO",
        unavailable_description="only bounded internal.analysis is enabled",
        preflight_audit_action="organization_work_held_communications_preflight",
    ),
    "people": DepartmentRuntimeSpec("people", "chro"),
    "legal": DepartmentRuntimeSpec("legal", "clo"),
}


def department_runtime_spec(department: str) -> DepartmentRuntimeSpec | None:
    return DEPARTMENT_RUNTIMES.get(department.strip().lower())
