# Phase 22 External Network Verifier — Operational Runbook

This runbook configures the **off-host, signed Phase 22 public-network verifier**. The verifier observes public DNS/TCP/HTTP/TLS state only. It does not deploy a release, write a Phase 22 receipt, authorize promotion, or prove rollback.

## Trust boundary

Operational verifier runs are allowed only from:

\`\`\`text
repository = bennet287/global-mobility-aios
workflow   = .github/workflows/phase22-external-network-verifier.yml
ref        = refs/heads/main
runner     = GitHub-hosted ubuntu-latest
\`\`\`

The active repository ruleset **Production proof enforcement** must continue to include \`refs/heads/main\` and require the repository-policy, SQLite backend, frontend build, and PostgreSQL governance checks.

The workflow contains a runtime ruleset check, but that does not replace GitHub Environment protection.

## Required GitHub Environment

Before creating the real signing secret, create a GitHub Environment named:

\`\`\`text
phase22-external-network-verifier
\`\`\`

Configure the Environment so deployments are permitted from **\`main\` only**. Add required human reviewers if the repository plan supports them.

Do **not** provision the operational signing key until the Environment branch restriction is active.

The repository connector used by AIOS development does not expose GitHub Environment/secret administration, so this account-level setting must be performed by an authorized repository administrator in GitHub Settings.

## Signing key

Use one Ed25519 raw private key (32 bytes), generated outside the target VPS.

Store only its strict base64 encoding in the Environment secret:

\`\`\`text
PHASE22_EXTERNAL_VERIFIER_ED25519_PRIVATE_KEY_B64
\`\`\`

The private key must never be committed, uploaded as an artifact, written to the target host, printed in logs, or placed in AIOS runtime secrets.

The corresponding raw public key is non-secret. Compute:

\`\`\`text
public_key_fingerprint = sha256(raw_32_byte_public_key)
\`\`\`

Pin that lowercase 64-character SHA-256 fingerprint in the **prepared Phase 22 networking contract** before running the verifier.

Key rotation requires a **fresh deployment acceptance run** with the new public-key fingerprint. Never mutate a prepared run in place.

## Workflow inputs

Dispatch **Phase 22 External Network Verifier** from \`main\` with the exact prepared contract values:

- deployment-run UUID;
- networking-contract fingerprint;
- web hostname;
- API hostname;
- expected globally routable IPv4;
- allowed public TCP ports: exactly \`80,443\` or \`22,80,443\`;
- pinned verifier public-key fingerprint.

The workflow does not accept a candidate Git ref and never checks out candidate code. It checks out only its own trusted \`github.sha\` on \`main\`.

## Observation contract

The verifier independently records:

- public A/AAAA DNS answers for web/API hostnames;
- a full TCP 1–65535 scan of the prepared public IPv4;
- port-80 redirect status and Location for both hostnames;
- TLS chain/hostname validation on port 443;
- certificate SHA-256 and validity window;
- HTTPS status for web \`/\` and API \`/health\`.

Probe failures still produce a **signed manifest**. A failed probe must not turn into an absent artifact.

## Artifact

A successful verifier execution uploads:

\`\`\`text
envelope.json
summary.json
\`\`\`

\`envelope.json\` contains the signed canonical manifest, public key, and Ed25519 signature.

The artifact transport is not authoritative. The API-side validator must independently verify:

- signature;
- pinned public-key fingerprint;
- exact deployment run/networking identity;
- trusted repository/workflow/ref provenance;
- observation freshness;
- DNS/TCP/HTTP/TLS contract semantics.

The external verifier does not write \`ProductionDeploymentAcceptanceCheckReceipt\`.

## Remaining Phase 22 boundary

A valid external manifest is necessary but insufficient for \`release_networking=satisfied\`.

The target-host/deployment owner must still reconcile the signed manifest with:

- exact running release/configuration identity;
- restart behavior;
- actual rollback to the prepared rollback release;
- post-rollback health and schema/data compatibility;
- candidate restoration/revalidation when required.

Only the stronger target-host executor may eventually create the immutable satisfied receipt through the existing Phase 22 owner.
