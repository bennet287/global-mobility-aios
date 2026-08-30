permit (
    principal is Agent,
    action == Action::"read_case",
    resource is Case
)
when {
    principal in Team::"austria"
    && resource in Team::"austria"
    && context.sameTenant
};

permit (
    principal is Agent,
    action == Action::"submit_case",
    resource is Case
)
when {
    principal in Team::"austria"
    && resource in Team::"austria"
    && context.sameTenant
    && context.authorityPresent
    && context.humanApproved
};

forbid (
    principal is Agent,
    action == Action::"submit_case",
    resource is Case
)
unless {
    context.authorityPresent
    && context.humanApproved
};

permit (
    principal is Agent,
    action == Action::"invoke_tool",
    resource is Tool
)
when {
    principal in Team::"austria"
    && resource in Team::"austria"
    && context.sameTenant
    && context.authorityPresent
};
