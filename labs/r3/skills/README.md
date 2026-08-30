# R3 Skill Registry Lane

This lane proves the AIOS-native Skill Registry lifecycle using synthetic data.

Permanent boundary:

```text
SKILL = KNOWS HOW
CAPABILITY = CAN TECHNICALLY
AUTHORITY = MAY DO

SKILL != AUTHORITY
CAPABILITY != AUTHORITY
```

Run:

```powershell
python -m pytest labs/r3/skills/tests -q

python -m labs.r3.skills.run_lifecycle `
  --run-id skills-lifecycle-20260830-001 `
  --output labs/r3/skills/results/skills-lifecycle-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/skills/results/*.json
```

The lifecycle covers external quarantine, malicious-content rejection, reviewed
immutable activation, tenant/position assignment, exact runtime manifest
version/hash, reduced A2A projection, v1→v2 coexistence, assignment revocation,
historical lineage and the skill/capability/authority matrix.

No registry operation grants product authority, autonomy or credentials.
