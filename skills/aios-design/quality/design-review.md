# AIOS V2 Design Review

Every redesigned surface must pass all applicable gates.

## 1. User goal
Can the intended user tell what the surface is for?

## 2. Attention
Is the most important state/action visually dominant?

## 3. Hick
Are there too many equal-weight actions?

## 4. Fitts
Are pointer/touch targets comfortable?

## 5. Tesler
Is complexity at the correct information depth?

## 6. Recognition
Can users recognize instead of memorize?

## 7. Truth
Could presentation misrepresent:
- authority
- certainty
- history
- memory
- prediction
- presence
- canonical state?

## 8. Consistency
Does it use V2 tokens, primitives, and domain objects?

## 9. Character
If applicable:
- adult/professional
- role-readable
- identity-readable
- state truthful

## 10. Spatial
Does space communicate useful organizational relationships?

## 11. Motion
Does motion communicate cause/continuity rather than decoration?

## 12. Accessibility
Can the task be completed without:
- mouse
- hover
- motion
- 3D
- color alone?

## 13. Responsive
Does it work across target layout modes?

## 14. Performance
Does visual quality preserve responsiveness?

## 15. Distinctiveness
Could the screenshot plausibly be any generic SaaS template?

If yes: redesign.

## 16. Governance
Are mutations/authority controls explicit and protected?

## 17. Provenance
Can users reach evidence/provenance when needed without it dominating the primary task?

## 18. Testability
Are critical states and truth-sensitive behavior represented in automated/visual tests?

---

## Review result

A surface receives one of:

- PASS
- PASS WITH FOLLOW-UP
- FAIL — UX
- FAIL — UI
- FAIL — TRUTH
- FAIL — ACCESSIBILITY
- FAIL — PERFORMANCE
- FAIL — DISTINCTIVENESS

No implementation is “done” solely because it compiles.
