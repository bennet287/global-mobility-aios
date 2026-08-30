package gmai.r3.authority

import rego.v1

default decision := {"decision": "DENY", "reason_class": "UNKNOWN_ACTION"}

decision := {"decision": "DENY", "reason_class": deny_reason} if {
    deny_reason != ""
}

decision := {"decision": "ALLOW", "reason_class": "AUTHORIZED"} if {
    deny_reason == ""
}

deny_reason := "MISSING_ACTOR" if {
    object.get(input.actor, "id", "") == ""
} else := "UNKNOWN_ACTION" if {
    not input.context.known_action
} else := "CROSS_TENANT" if {
    not input.context.same_tenant
} else := "SELF_ESCALATION" if {
    input.context.self_grant_attempt
} else := "SELF_ESCALATION" if {
    input.action == "authority.grant"
    input.actor.id == input.acting_for
} else := "CAPABILITY_MISSING" if {
    not input.technical_capability
} else := "DELEGATION_INVALID" if {
    input.delegation.status in {"expired", "revoked"}
} else := "JURISDICTION_MISMATCH" if {
    input.context.required_jurisdiction != null
    input.jurisdiction != input.context.required_jurisdiction
} else := "AUTHORITY_MISSING" if {
    input.context.authority_required
    not input.context.authority_present
} else := "HUMAN_APPROVAL_REQUIRED" if {
    input.context.human_approval_required
    not input.human_approval
} else := ""
