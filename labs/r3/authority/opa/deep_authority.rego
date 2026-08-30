package gmai.r3.authority_deep

import rego.v1

default decision := {
    "decision": "DENY",
    "reason_class": "UNKNOWN_ACTION",
    "policy_revision": object.get(data.aios, "revision", "missing"),
}

actions := object.get(data.aios, "actions", {})
action_name := object.get(input, "action", "")
metadata := object.get(actions, action_name, null)
actor_id := object.get(object.get(input, "actor", {}), "id", "")
tenant_id := object.get(input, "tenant_id", "")
resource_tenant_id := object.get(object.get(input, "resource", {}), "tenant_id", "")
technical_capability := object.get(input, "technical_capability", false)
authority_present := object.get(object.get(input, "context", {}), "authority_present", false)
human_approval := object.get(input, "human_approval", false)
jurisdiction := object.get(input, "jurisdiction", "")
delegation_status := object.get(object.get(input, "delegation", {}), "status", "missing")
self_grant := object.get(object.get(input, "context", {}), "self_grant_attempt", false)

same_tenant if {
    tenant_id != ""
    resource_tenant_id != ""
    tenant_id == resource_tenant_id
}

delegation_valid if {
    delegation_status != "expired"
    delegation_status != "revoked"
}

jurisdiction_valid if {
    metadata != null
    metadata.required_jurisdiction == null
}

jurisdiction_valid if {
    metadata != null
    metadata.required_jurisdiction != null
    jurisdiction == metadata.required_jurisdiction
}

authority_valid if {
    metadata != null
    not metadata.authority_required
}

authority_valid if {
    metadata != null
    metadata.authority_required
    authority_present
}

approval_valid if {
    metadata != null
    not metadata.human_approval_required
}

approval_valid if {
    metadata != null
    metadata.human_approval_required
    human_approval
}

deny_reason := "MISSING_ACTOR" if {
    actor_id == ""
} else := "UNKNOWN_ACTION" if {
    metadata == null
} else := "CROSS_TENANT" if {
    not same_tenant
} else := "SELF_ESCALATION" if {
    self_grant
} else := "CAPABILITY_MISSING" if {
    not technical_capability
} else := "DELEGATION_INVALID" if {
    not delegation_valid
} else := "JURISDICTION_MISMATCH" if {
    not jurisdiction_valid
} else := "AUTHORITY_MISSING" if {
    not authority_valid
} else := "HUMAN_APPROVAL_REQUIRED" if {
    not approval_valid
} else := ""

decision := {
    "decision": "DENY",
    "reason_class": deny_reason,
    "policy_revision": object.get(data.aios, "revision", "missing"),
} if {
    deny_reason != ""
}

decision := {
    "decision": "ALLOW",
    "reason_class": "AUTHORIZED",
    "policy_revision": object.get(data.aios, "revision", "missing"),
} if {
    deny_reason == ""
}
