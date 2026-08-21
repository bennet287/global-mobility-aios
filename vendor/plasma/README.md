# Plasma AI donor snapshots

This directory contains frozen, read-only upstream donor snapshots used by Global Mobility AIOS for controlled evaluation and adaptation.

- `wiki/v1.2.0/` — Context Broker / organizational-knowledge donor.
- `fractal/v1.1.0/` — recursive Mission decomposition / execution-runtime donor.

## Import status

The pinned donor source trees are now present under each versioned `upstream/` directory, with Apache-2.0 license copies, deterministic SHA-256 `SOURCE_MANIFEST.txt` files, archive provenance records, and read-only markers.

The source import intentionally excludes generated/cache material and binary documentation artwork (`*.png`) that is unnecessary for donor-code inspection. The first Plasma Wiki pilot also forbids repository-local executable `.wiki/wiki.py` hooks.

Vendoring is not production adoption. The imported trees are reference material only and must not be modified into canonical AIOS implementation code.

AIOS owns organizational meaning and authority. Nothing under `vendor/plasma/` is canonical AIOS production implementation and nothing here may bypass Evidence, VerifiedRules, Capability/Authority/Autonomy/Risk, A0–A5 Earned Autonomy, R0–R5 risk, Decision Readiness, the Organizational Immune System, Command Gateway, Transparency, or Board authority.

Vendor snapshots are read-only. Adapt useful mechanics into AIOS-owned modules behind explicit ports/adapters and governance contracts.
