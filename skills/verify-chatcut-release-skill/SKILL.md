---
name: verify-chatcut-release-skill
description: Public, read-only release verification contract. Use as the canonical /verify and /verify-chatcut-release-skill alias to check source coverage, evidence boundaries, artifact integrity, and human decision state before a release handoff.
---

# Verify Release Skill

Use this Skill for a read-only verification pass over a release work package. The aliases `/verify` and `/verify-chatcut-release-skill` mean the same contract.

This public Skill defines the verification boundary. Runtime adapters, credentials, customer data, internal receipts, and machine-specific recording implementation stay outside this repository.

## Verification contract

Verify the chain:

`task bundle → Skill instructions → agent/tool actions → artifacts → evidence`

For each material claim, require a source reference and one of these states:

| State | Required interpretation |
| --- | --- |
| `planned` | specified, not executed |
| `prepared` | reversible draft or input exists |
| `recorded` | real media exists and passed checks |
| `sent` | real delivery receipt was read back |
| `published` | destination confirms publication |
| `blocked` | required surface, permission, or fact is unavailable |

Never upgrade a state because a prompt, recommendation, webhook, or “GO” message sounds confident.

## Required checks

1. **Candidate identity** — record the exact source revision, release range, and changed files under review.
2. **Complete coverage** — compare the candidate against the full release diff; list missing PRs, commits, files, or unresolved features.
3. **User-value claims** — every selected feature and user story points to source evidence; planned outcomes remain labeled as planned.
4. **Artifact integrity** — check file existence, format, duration, size, dimensions, and source SHA binding where applicable.
5. **Human boundary** — distinguish prepared A/B/C options from an explicit human selection. Do not assume a choice.
6. **Delivery state** — distinguish draft, sent, and published; read back receipts only when the relevant surface is available.
7. **Repeat probe** — rerun a safe read-only check or adjacent negative case and report any mismatch.

## Verdicts

- **PASS** — required checks are satisfied and evidence supports the stated scope.
- **FAIL** — a check contradicts the claim or a required artifact is invalid.
- **BLOCKED** — verification cannot complete because a required surface, permission, or fact is unavailable.
- **SKIP** — the check is explicitly out of scope; record why.

A PASS verifies the checked scope. It does not prove conversion uplift, market impact, model parity, or future reliability.

## Report format

Return:

- candidate revision and release range
- checks performed and evidence references
- missing or unresolved items
- evidence-state table
- verdict: PASS, FAIL, BLOCKED, or SKIP
- next action, if any

## Safety boundary

Do not send email, publish externally, change permissions, access credentials, or invent receipts during verification. Keep internal operational details out of public artifacts.
