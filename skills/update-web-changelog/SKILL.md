---
name: update-web-changelog
description: "Internal chatcut-release helper to prepare evidenced beta/production changelog content diffs and rollbackable content PRs/previews after feature selection. Use verified user outcomes and required notices; do not deploy or rewrite live content. Explicit plan-only tasks only return plans."
---

# Prepare Web Changelog

Status: IMPLEMENTED · Scope: draft_preparation

For the existing ChatCut Landing production target, hot-load update-release-docs from this same pinned repo revision and reuse its actual content/build/PR conventions. Call it once for both changelog and docs, reusing the same PR. Beta produces isolated draft content only; no production edits. Do not invoke its scheduled-only Feishu notification unless the current task already authorizes it; otherwise report not_sent and continue.

Read release-context.json, the complete verified feature matrix and scope-bound human selection.
Use templates/release-text.md/json to draft bilingual version notes. Put selected highlights first;
retain factual important fixes/behavior changes and limitations, not an invented marketing claim.
Keep beta preview entries separate from production and use exact tags/package/upgrade links.

Discover the existing target repository and content conventions from trusted configuration/source.
Read the current entry before editing. Prepare web/changelog/ content diff with checked asset links,
preview and revert instructions. Create a branch/content PR if the target and writing capability
are already evidenced. Do not merge, deploy, request new access or mutate live content here.

Missing target is BLOCKED for this branch; preserve an inspectable local diff and continue other
release branches. Mark a PR ready only after fetching its actual changed files/URL and validating
build/links under target repo rules. Reuse an existing matching PR on resume; never duplicate it.
For explicit plan-only tasks return placeholder, missing_inputs, todo, planned_outputs:[web/changelog/
content diff and preview] and completed_actions:[]. No second business HITL.
