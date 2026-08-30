@id("aios-r3-authority")
permit (
    principal,
    action,
    resource
)
when {
    context.actor_present
    && context.known_action
    && context.same_tenant
    && !context.self_grant_attempt
    && context.technical_capability
    && context.delegation_valid
    && context.jurisdiction_valid
    && (!context.authority_required || context.authority_present)
    && (!context.human_approval_required || context.human_approval)
};
