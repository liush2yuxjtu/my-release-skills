---
name: chatcut-release
description: "The only public entry for ChatCut beta and production release work. Use for /chatcut-release, release events, release drafts, WeChat article drafts, platform MCP setup, Feishu workflow motion, single-card candidate review via Grokbot/Mac mini, or continuing a ChatCut release. Hot-load only the helper skills needed now. Automatically verify the release interval and ALL user-aware changes, ask one human question to select the important few, persist that selection, then continue recording, drafts, Feishu review and web content PRs."
---

# ChatCut Release

Status: IMPLEMENTED · Role: sole public entry · Default: agent_orchestrated

Own the complete run. Do not ask the user to invoke helpers, select a version, approve analysis,
approve recording, or approve a draft. The one business HITL is **feature_shortlist**.
Keep public publishing outside this workflow; leave 公众号发表 to the user.

## Load skills when needed

Read [loading.md](references/loading.md) for local/standalone loading, revision pinning and recovery.
Locate the trusted repo root; read its AGENTS.md, config/release-policy.json and config/skills.json.
Load prompts/prefight.md only for the current stage. Load prompts/router.md when resolving a route.
Do not read every helper or install the entire skills collection. When only this entry is installed,
fetch the needed helper and its referenced resources from the same pinned GitHub revision.

## Mandatory writing workflow

Before drafting any human-facing text, MUST load unslop and execute [the pstack release writing playbook](references/unslop-playbook.md) from the same pinned revision. Apply it as you write, then audit the final copy. This includes candidate reviews, every requested channel, captions, platform previews, docs, PR text and replies, including targeted branches and manual drafts.
Preserve verified facts, selected scope, required notices and uncertainty. Missing unslop resources block writing and delivery, not independent evidence collection. This is automatic and adds no human approval gate.

## Targeted workflow motion

For a requested schematic workflow GIF or Feishu motion card, load send-feishu-motion from the
router now. Use the user's short steps, default to a 6-second illustration, and prepare its offline
card; do not invent a Release event or product/build claims for a general workflow example.
No feature-selection question is needed for a supplied schematic. If the animation presents actual
release outcomes, follow the full release flow below and validate the matching feature_shortlist
BEFORE creating or sending promotional motion; continue only evidence preparation until selected.

Send only under existing/current explicit authorization for THIS motion task. The ten-channel review
grant does not cover a separate motion card. Without that authorization, keep the prepared preview;
do not introduce another approval gate. Reuse fixed sender and durable receipts; never resend old
examples. Follow the helper's upload/readback, visual QA and deduplication contract and return its
actual artifacts/receipt. This is an on-demand branch of the same public entry.

## Targeted WeChat article draft

For an idea + text + assets task requesting a real Official Account draft, load
create-wechat-article from the router and config/wechat-article.json now. Reuse the supplied
text/assets and trusted existing account connection; do not invent a Release for a general
idea. If this article promotes release features, first revalidate the matching existing
feature_shortlist through the full release flow. Missing auth/tools only blocks upload;
continue the article package. The helper creates/updates one draft, reads back the same
media_id and returns its actual temporary preview plus editor/mobile human checks.
Leave QR/identity prompts and final publication to the user in the backend; never use an
API publication tool. This is the same public entry, not another business approval gate.

## Targeted single-card candidate review

For an explicit one-card readability correction or Grokbot/Mac mini candidate-review request,
hot-load review-release-features-in-feishu and its references/single-card.md mode.
The old send-single-feishu-card name forwards to that same implementation. Reuse the frozen
full candidate package, original shared review and designated Mac sender history. The helper
checks one complete card on Grokbot, uses the existing Mac mini sender under the current/applicable
grant, then reads back and archives its native receipt. It displays the SAME feature_shortlist
handoff; preserve existing human choices. An accepted receipt is already_sent, not a new send;
pending/unknown/conflicting history blocks retry. Read current direct tool schemas rather than
requiring an Executor adapter. Reuse recorded release evidence for layout maintenance.

## Targeted platform MCP setup

For requested platform connections, read [the shared MCP setup](../../docs/platform-mcp.md)
and inspect this revision's .mcp.json / .codex/config.toml. Configure and authorize on the
actual client host; a personal laptop is supported and Mac mini is not required for these
remote MCPs. Standalone installation follows the loading reference for active client config.
Reuse installed authenticated connections before adding duplicates; keep OAuth in the client's
native store. Load the project verifier's platform-mcp surface now. Distinguish configured
endpoints, pending auth, live read verification, saved drafts and publication. Setup itself does not need a
fabricated Release or feature_shortlist. Preserve existing APIs, global client settings,
credentials and publication policy. Missing auth only blocks its dependent channel;
continue local drafts. Never publish or schedule test content to verify a connection.

## 1. Resolve the event and resume

- Accept either a genuine GitHub published/released payload or a verified Desktop collector context.
  Use the canonical collect-release-diff/scripts/publication_identity.py for Desktop identity;
  scripts/release_identity.py forwards it for plan/state/package keys. GitHub identity retains its positive release ID;
  Desktop identity uses repository/channel/actual publication run ID/attempt/full packaged source SHA.
  Never put an Actions run ID in release_id. macOS/Windows proofs are child observations of one run.
- Load collect-release-diff. Resolve the previous actual publication of the SAME channel and full
  packaged SHAs; preserve literal versions. For a scheduled discovered event, use resolve with
  --publication-run-id and --run-attempt, so superseded/same-version publications are not collapsed
  into the current feed. Staged promotion without its exact binding remains BLOCKED.
- On the designated Mac sender, use scripts/release_run_state.py and the configured durable SQLite
  store to register/claim/checkpoint the publication_key. Resume the recorded skills revision,
  saved handoff, actual human selection and original sender receipts. Read the store even when no
  new updater version appears. Worker reservations do not expire into another send; reconcile a
  crashed owner from saved artifacts. Optional Gist is not required by the existing hourly watch.
  Store errors block dependent automatic work; local read-only analysis can continue.
  The existing ChatGPT watch is hourly polling, not a native GitHub Release webhook. Python plan
  builders and materializers do not run agents or enable listeners.
- Explicit plan-only requests and synthetic planning evals return plans with no completed actions.

## 2. Build ALL user-aware features before asking

1. Collect every in-range commit and associated PR, paginate to exhaustion, read bodies and diffs.
   Keep direct commits, mixed PRs, reverts, critical fixes, limitations and mandatory behavior notices.
2. Load verify-chatcut-release-skill for the full diff surface. Preserve the four surfaces: release
   net, every commit, each PR landing delta, each recorded PR source diff. Run actual capture/audit.
   CAPTURED, a truncated API response or a matrix of a few seed PRs does not establish completeness.
3. Load read-resend-funnel only for useful ranking feedback. Unavailable data does not stop work.
4. Load select-release-features. For new batches require its communication_schema_version: 1 four-category recommendations, including every excluded/pending outcome with reasons. Generate pr-index.json and feature-matrix.json from ALL source
   items. full_scope contains every verified user-aware outcome; shortlist is recommendation only.
   Keep excluded/needs_verification with reasons and verify every source is accounted for.
5. Reconcile each input change's audit_refs with the audited manifest, then run the matrix validator.
   Preserve unknown availability as needs_verification; do not market it as shipped. Show unresolved
   potential outcomes separately. Missing diff coverage blocks the claim that the list is complete.

When the user requests same-style bilingual cards for ALL user-aware outcomes, hot-load
create-release-social-cards to prepare the review batch, editable templates and offline gallery.
Keep include/needs_verification candidates, complete source inventory and availability limits;
this reversible review preparation does not establish shipped features or a human shortlist.
Do not require the user to invoke the helper. Promotional downstream work still uses the selection below.

## 3. Make the ONE human handoff

Load select-release **now**, after complete collection and matrix verification.
For Desktop, pass --context RELEASE_CONTEXT to selection_gate.py; GitHub uses --event.
The live CLI rechecks the actual publication with the canonical collector adapter. It chooses feature
highlights, not release versions. Prepare feature-selection-handoff.json/md with EVERY full_scope
item, stable IDs, user benefit, before/after, PR links, availability, limitations, evidence and agent
recommendations. Include excluded/unverified counts and links to the complete PR/diff inventory.

Recommend roughly 20% of eligible outcomes, normally 1–5; do not fill a quota or hide nonrecommended
items. Show the selected/total ratio. Treat the ratio as advice, and honor the human's explicit IDs.
Keep required notices separately even when they are not chosen as promotional highlights.

Ask one question: **「全部更新已分成主打功能、体验改善、问题修复、不必提及。请确认或调整四类，并指定宣传重点的功能 ID，或明确采用展示的分类和重点推荐。」**
Use the current conversation or an already authorized Feishu review surface. Hot-load
review-release-features-in-feishu only if that shared surface is useful; it carries this SAME question,
not an additional per-channel or sending gate. Honor channel restrictions stated in the same answer. A webhook card is a
review display, not a callback handler; accept explicit human message/record, not delivery code 0.
Do not invent clickable approval controls without a working callback.
Group-webhook cards stay display-only. Cards sent by the app bot per feishu-bot-card-callback, with the
chatcut-release-cards listener running, may use callback buttons; a click records the human's explicit choice
and never replaces it. No answer/timeout/decline
means no selected downstream work. Continue independent evidence repair and reversible preparation.

Persist feature-selection.json with repository/release/channel/SHAs, scope_hash, explicit selected
IDs, reviewer, timestamp and source message. A plain GO is not selection. A matching prior decision
resumes without asking again. Changed event/channel/SHAs/matrix invalidates it and returns to the
same feature_shortlist gate, never a second type of approval. Empty full_scope needs no question.

## 4. Continue automatically after selection

- Pass selected IDs as the promotional scope to every downstream helper. Preserve full_scope and
  the full PR ledger for traceability. Critical notices remain in release notes/docs, outside ratio.
- Load release-draft-in-feishu for complete copy for WeChat, Discord and the eight social channels.
  Use templates/release-text.md/json for unified copy and bilingual changelog/docs. Build ten complete
  texts, not placeholder sentences. Honor any channel limits in the actual human answer; never fill
  unrequested channels just to satisfy the ten-channel sender. If those limits prevent a complete
  ten-channel card, retain the scoped draft/linked review instead. If already authorized, deliver the review card automatically
  through scripts/deliver_feishu_review.py with the validated feature-selection.json AND full-scope
  handoff; bind the draft scope_hash, selected_feature_ids and required_notice_ids to that selection,
  and persist/read back its receipt;
  Desktop drafts preserve source_kind and the full publication from selection.release, and
  scripts/deliver_feishu_review.py receives --context for live read-only recheck. Legacy version
  receipts still block an ambiguous resend; platform transactions remain children of one run; do not ask again or resend accepted
  identities. Otherwise prepare the review payload and report not_sent without inventing permission.
- For requested real wechat-official draft-box output, load create-wechat-article and reuse
  the latest article copy from the text helper plus verified assets. Pin the existing account,
  check live MCP, preserve durable draft receipts, upload/save/read back and inspect the real
  preview. No extra draft permission is needed; report blocked upload accurately and leave
  final backend publication to the user. A Feishu text card is a review copy, not a saved
  Official Account article. Do not assume API publish enforces QR or human review.
- Default to image/text: load create-image-text-assets, which forwards to create-release-social-cards.
  Promotional scope is selected and replays the gate; explicitly requested full review stays all-user-aware.
  Load recording only when an outcome needs a real operation demo or the user requests video/GIF.
  Load record-production-feature for selected, verified production outcomes; load record-full-walkthrough
  for beta/whole-release UI work. Hot-load existing /ui-demo and its real platform/renderer references.
  Use the existing shared Mac mini queue/authorization when configured (docs/shared-macmini-recorder.md);
  otherwise reuse the existing /ui-demo execution route without enabling a new public service.
  Prepare templates/recording-TODO.md and recording-plan.template.json; discover, rehearse, record,
  inspect frames and archive immutable raw MP4 plus full MP4/8-second GIF. Do not request a second
  recording approval. Skip media for text-only outcomes. Use focus-recorded-feature for genuine zoom
  derivatives only when required, and preview-gif-tweaks only when a design preview is useful.
- Load update-release-docs for the existing production Landing target; its shared routine prepares
  Current Versions, changelog and related docs in one rollbackable content PR/preview. Use update-web-changelog
  and update-docs only as adapters for other evidenced targets or isolated beta drafts. Missing target
  blocks that branch; continue other work. Do not use the scheduled-only PR notification grant.
- Load handoff-release-pack when verified GT/GIF assets exist to prepare ZIPs, per-file manifests
  and download QA. Reuse an already authorized destination. A separate asset card or new Site without
  existing authorization stays prepared/not_sent; do not add a second approval question.
- Use implemented shared helpers instead of executing every legacy placeholder. Preserve TODO and
  blocked reasons for unimplemented effects; never claim a recording/upload/PR/delivery is done
  unless the real artifact, URL and receipt were checked.

## Platform-box image previews

For requests to show actual release text/images inside email or social-platform mock-up boxes,
hot-load preview-release-content after the matching feature selection, or for explicitly supplied
manual draft copy. Use the supplied/current approved copy; respect any requested human copy
confirmation before filling the final preview. This helper does not implement or claim the separate
future copy/final-preview approval gates. Default to image/text; video remains a labelled placeholder.
Reproduce the specific reference interface with measured HTML/CSS, not a new design system.
Return editable mock-ups, full screenshots and honest pixel-comparison scope. Missing independent
references means approximate/blocked fidelity, never pixel-level verified. It does not publish/send.

## 5. Verify and finish

Use the internal project verifier at the closest applicable real surface. The verify-release-pack
compatibility route runs its actual release-pack CLI and retains a fresh report plus a tamper probe. Check selected IDs against
the persisted decision, channel/version claims, ten drafts, raw/derived hashes, actual GIF duration,
visual QA, saved links, PRs and bot deduplication. Verify one adjacent invalid or repeated-use case.
Checkpoint real run artifacts in the designated durable store and save release-pack.json.
Mark completed only after the actual pack CLI passes; pending/blocked branches remain unfinished. Report actual completion, artifacts, technical gaps
and the pending selection if any. Do not introduce a final approval question.

Use [run-contract.md](references/run-contract.md) for state, selection/diff pins and artifact names.
