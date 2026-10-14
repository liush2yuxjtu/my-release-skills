---
name: select-release
description: "Internal feature_shortlist helper for the sole chatcut-release entry. After ALL release PR/diff and user-aware features are verified, hand the complete feature table to a human to choose the important few. Preserve the old skill name as a helper alias; do not ask humans to select release versions. Present and confirm four editorial categories as well as highlights. Persist and reuse a scope-bound explicit selection."
---

# Select Release Highlights

Status: IMPLEMENTED · Scope: human_feature_selection

This is the ONE business HITL. MUST handoff to human for feature highlights, AFTER complete automatic
collection and feature classification. The event/baseline/channel are already evidenced by the entry.

## Prepare the full handoff

- Read the real GitHub event OR resolved Desktop release-context.json, full pr-index.json, feature-matrix.json, actual PASS audit report and captured
  manifest.json. Reconcile every source audit_refs with exact commit/PR sets. Do not accept a handful
  of seed PRs or a self-reported completeness flag as the full release.
- Run the sibling select-release-features validator. Present EVERY full_scope item, stable ID,
  benefit, before/after, sources, availability, limits, recommendation reason and suggested media.
  Provide excluded/unverified counts and full inventory/evidence links. Never hide nonrecommended
  eligible features. Mark potentially user-aware unresolved items separately.
- Recommend about 20%, normally 1–5; don't invent a quota or enforce the ratio on a human decision.
  The matrix shortlist is advisory. Preserve announcement_required items as separate required notices.
- Use assets/handoff.template.json as a contract, not fabricated execution evidence. Prepare JSON/md
  and show the concrete full table through current chat or an already authorized review surface.
  A Feishu webhook delivery does not implement callbacks or prove that the human selected anything.

Run from the repo root, substituting real absolute paths:

```bash
python3 skills/select-release/scripts/selection_gate.py prepare \
  --event EVENT --input PR_INDEX --matrix FEATURE_MATRIX \
  --audit AUDIT_REPORT --manifest FULL_DIFF_MANIFEST --output HANDOFF

python3 skills/select-release/scripts/selection_gate.py select \
  --event EVENT --input PR_INDEX --matrix FEATURE_MATRIX \
  --audit AUDIT_REPORT --manifest FULL_DIFF_MANIFEST \
  --decision HUMAN_DECISION --output SELECTION
```

For Desktop use --context RELEASE_CONTEXT instead of --event EVENT in both commands. No GitHub
Release ID is required or permitted for this source. The live CLI rechecks the collector's actual
publishing jobs/steps, pointer-advance logs and immutable manifests with GETs before preparing or
reusing selection. The handoff pins run/attempt/full source SHA and verified platform transactions.
Keep collect-release-diff/scripts/publication_identity.py, collect_release_diff.py and the project
verifier's release_diff_audit.py available from the same pinned revision. Staged builds/promotions
remain unresolved until a matching publication adapter verifies the actual production advance.

The script imports the sibling validate_feature_matrix.py; include that dependency in a standalone
entry's cache. --fixture explicitly permits synthetic gate tests and labels the output; it cannot
establish live source coverage, UI availability or delivery. Keep the actual verifier/tool trace.

Use [communication-decision.template.json](assets/communication-decision.template.json) only as an unapproved template; fill provenance from the actual human message.

## Confirm the four groups and highlights together

For new runs require the matrix communication extension. Display EVERY outcome, including excluded
and pending items, in four groups: 主打功能 / 体验改善 / 问题修复 / 不必提及. Show stable IDs,
agent category/reason, source, availability and pending checks. Do not collapse excluded or pending
items into an unexplained count. Keep required notices visible, separately from promotional quota.
Read the human's actual response; let them move eligible outcomes between groups, choose headline
IDs and accept the recommendation explicitly. Do not equate category headline_features with final
selected_feature_ids. Selected highlights may also come from improvements or fixes.

The same decision records `communication_confirmed: true` and either a complete
`communication_categories` map (feature ID → category) or `communication_mode:
accept_recommendation`. Only encode acceptance if the source human message explicitly confirms
both the displayed four groups and the highlighted IDs. Generic GO or acceptance of highlights
alone cannot establish category approval. Unknown/missing IDs, promoted unverified outcomes,
hidden required notices and chosen not_mentioned highlights are rejected by the actual gate.
Return confirmed categories/buckets alongside the selection. Decline remains closed.
Historical unextended inputs/decisions retain the old exact scope; do not fabricate their approval.

## Ask and resume once

Ask once: 「全部更新已分成主打功能、体验改善、问题修复、不必提及。请确认或调整四类，并指定这次宣传重点的功能 ID；也可以明确采用展示的分类和重点推荐。」

An explicit human message can name any eligible IDs or accept the displayed recommendation.
Record gate_id feature_shortlist, origin human, scope_hash, mode explicit_ids/accept_recommendation,
selected_feature_ids, reviewer, timezone-aware decided_at and evidence kind human_message with its
reference and exact text. Never fabricate this record. Ordinary GO, event fields, agent suggestions
and bot receipt code 0 are not choices. Declined/timeout/pending never unlock selected downstream work.

Persist feature-selection.json in the configured durable run state. The select command revalidates
the current event/matrix/source/audit/manifest and rejects stale pins. Match the saved scope_hash on
resume; reuse a valid decision, don't ask again. Changed scope returns to this SAME gate. Empty
full_scope is no_user_aware_changes and needs no human question. An explicit empty human selection
skips promotional assets; still preserve required notices and factual docs.

After selection return selected IDs, actual ratio, required notices and downstream_allowed. The
entry continues its implemented helpers automatically without recording/draft/send approval prompts.
Public publishing is outside the entry. Version resolution and source collection remain automatic.

For explicit plan-only tasks only return a handoff plan (placeholder, missing_inputs, todo,
planned_outputs:[feature-selection-handoff.json, feature-selection-handoff.md, feature-selection.json],
completed_actions:[]). Do not send a review or forge a human decision.
