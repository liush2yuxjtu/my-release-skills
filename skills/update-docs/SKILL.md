---
name: update-docs
description: "Internal chatcut-release helper to prepare evidenced documentation changes, real screenshots and rollbackable content PRs/previews after feature selection. Keep required behavior instructions even outside promotional highlights. Do not deploy or mutate live docs. Explicit plan-only tasks only prepare plans."
---

# Prepare Docs

Status: IMPLEMENTED · Scope: draft_preparation

For the existing ChatCut Landing production target, hot-load update-release-docs from this same pinned repo revision and reuse its actual content/build/PR conventions. Call it once for both changelog and docs, reusing the same PR. Beta produces isolated draft content only; no production edits. Do not invoke its scheduled-only Feishu notification unless the current task already authorizes it; otherwise report not_sent and continue.

Read release facts, the complete verified feature matrix, docs_needed items and scope-bound human
selection. Selected highlights determine promotional scope; required user actions, compatibility
and important behavior instructions must remain documented even outside those highlights.

Discover the evidenced existing docs target and conventions. Read affected pages. Update actual
UI steps, terminology, prerequisites, platform/flag limits, upgrade references and bilingual
content where the target supports it. Use real version-matched screenshots; never fabricate completed
UI actions or claim a GIF proves audio. No docs edit is needed for a change with no user instruction.

Prepare web/docs/ content diff, referenced asset manifest, link checks, preview and revert plan.
Create or update a rollbackable content branch/PR with the existing writing capability when target
is known. Verify the actual PR/files/preview under target repo checks. Do not merge/deploy or change
live docs. Missing target blocks only this branch; retain an inspectable diff and continue release work.
For explicit plan-only tasks return placeholder, missing_inputs, todo, planned_outputs:[web/docs/
content diff, image references and preview] and completed_actions:[]. No second business HITL.
