# Implementation review

Use the existing design, accessibility, performance, responsive and acceptance
references. This checklist binds them to observable implementation evidence.

1. Map every displayed fact to a typed source and every join to an exact key.
   Exercise a populated response, empty response, partial source failure, refresh
   failure and obsolete response arriving after a new selection.
2. Trace actions separately from selection. Test explicit confirmation,
   supersession before submission, denied authority and ambiguous submission
   failure. Never retry a material action automatically.
3. Check desktop, tablet, mobile, browser zoom, light/dark, reduced motion and
   keyboard focus. Inspect screenshots; a screenshot file alone is not review.
4. Show important facts in structured UI. Spatial framing, LOD and animation
   may reduce visual detail but cannot hide a required decision or evidence gap.
5. Record measured build/runtime and browser results for the actual working
   tree or commit tested. Label fixtures as fixtures. Capture candidate/head
   before and after formal acceptance; do not transfer earlier proof to later edits.

References inspire analysis rather than override AIOS truth. Apply hierarchy,
spacing, typography and progressive disclosure principles using first-party
tokens and components. Do not install multiple competing UI or tour systems.

Delivery documentation distinguishes implementation, local verification,
independent human review and release acceptance. Keep open requirements in the
programme ledger; never turn route availability into whole-programme completion.
