package gmai.r3.authority

import rego.v1

default decision := {"decision": "DENY", "reason_class": "UNKNOWN_ACTION"}

canonical_actions := {
    "case.read": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "case.note.write": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "client.communication.draft": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "client.communication.send": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": null},
    "legal.conclusion.publish": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": "AT"},
    "government_application.submit": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": "AT"},
    "verified_rule.read": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "verified_rule.write": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": "AT"},
    "evidence.read": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "evidence.write": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": null},
    "secret.read": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": null},
    "authority.grant": {"authority_required": true, "human_approval_required": true, "required_jurisdiction": null},
    "tool.discover": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "tool.invoke": {"authority_required": true, "human_approval_required": false, "required_jurisdiction": null},
    "mcp.tool.invoke": {"authority_required": true, "human_approval_required": false, "required_jurisdiction": null},
    "a2a.task.delegate": {"authority_required": true, "human_approval_required": false, "required_jurisdiction": null},
    "document.prepare": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "eligibility.calculate": {"authority_required": true, "human_approval_required": false, "required_jurisdiction": "AT"},
    "organization.activity.read": {"authority_required": false, "human_approval_required": false, "required_jurisdiction": null},
    "organization.activity.write": {"authority_required": true, "human_approval_required": false, "required_jurisdiction": null},
}

actor_id := object.get(object.get(input, "actor", {}), "id", "")
action_name := object.get(input, "action", "")
action_metadata := object.get(canonical_actions, action_name, null)
tenant_id := object.get(input, "tenant_id", "")
resource_tenant_id := object.get(object.get(input, "resource", {}), "tenant_id", "")
technical_capability := object.get(input, "technical_capability", false)
human_approval := object.get(input, "human_approval", false)
jurisdiction := object.get(input, "jurisdiction", "")
authority_present := object.get(object.get(input, "context", {}), "authority_present", false)
self_grant_flag := object.get(object.get(input, "context", {}), "self_grant_attempt", false)
acting_for := object.get(input, "acting_for", "")
delegation_status := object.get(object.get(input, "delegation", {}), "status", "missing")

tenant_mismatch if {
    tenant_id == ""
}
tenant_mismatch if {
    resource_tenant_id == ""
}
tenant_mismatch if {
    tenant_id != resource_tenant_id
}

self_escalation if {
    self_grant_flag
}
self_escalation if {
    action_name == "authority.grant"
    actor_id == acting_for
}

delegation_invalid if {
    delegation_status == "expired"
}
delegation_invalid if {
    delegation_status == "revoked"
}

jurisdiction_mismatch if {
    action_metadata != null
    action_metadata.required_jurisdiction != null
    jurisdiction != action_metadata.required_jurisdiction
}

authority_missing if {
    action_metadata != null
    action_metadata.authority_required
    not authority_present
}

approval_missing if {
    action_metadata != null
    action_metadata.human_approval_required
    not human_approval
}

deny_reason := "MISSING_ACTOR" if {
    actor_id == ""
} else := "UNKNOWN_ACTION" if {
    action_metadata == null
} else := "CROSS_TENANT" if {
    tenant_mismatch
} else := "SELF_ESCALATION" if {
    self_escalation
} else := "CAPABILITY_MISSING" if {
    not technical_capability
} else := "DELEGATION_INVALID" if {
    delegation_invalid
} else := "JURISDICTION_MISMATCH" if {
    jurisdiction_mismatch
} else := "AUTHORITY_MISSING" if {
    authority_missing
} else := "HUMAN_APPROVAL_REQUIRED" if {
    approval_missing
} else := ""

decision := {"decision": "DENY", "reason_class": deny_reason} if {
    deny_reason != ""
}

decision := {"decision": "ALLOW", "reason_class": "AUTHORIZED"} if {
    deny_reason == ""
}
