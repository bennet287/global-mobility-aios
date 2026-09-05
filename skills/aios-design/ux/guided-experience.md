# Guided experience

The first-party adapter is `apps/web/components/v2/V2Guide.tsx`; dependency intake
is recorded in `docs/aios-v2/AIOS_V2_PROGRAMME_EXECUTION.md`.

Guidance starts from Help. Provide the same information as readable text, so
highlights are optional. Load Driver.js only after the user starts highlights.
Use static reviewed copy and stable `data-guide` anchors; skip absent or hidden
targets. Do not interpolate case text into the library's HTML fields.

Guidance may explain controls but never activate them, submit a form, grant
authority, start a model call or write organizational state. Disable interaction
with highlighted controls while the guide is active. Preserve keyboard dismissal,
return focus to Help, clean up on navigation and honor reduced motion.

No automatic tours, completion streaks, artificial urgency or retention counters.
Test opt-in loading, keyboard dismissal, missing anchors, text access and zero
domain writes. Review actual popover contrast and narrow-screen layout.
