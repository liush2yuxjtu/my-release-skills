# Handoff output contract

Every run, including a blocked one, writes `runs/<take>/handoff.json` as its single source of truth. User-facing summaries and any authorized agent notification are rendered from it. Do not add claims absent from the file. The [template](../assets/handoff.template.json) starts pending; its values are not evidence.

Local or private delivery is the default. Public hosting, a feature branch, a commit, a PR, a gallery and a bot message are conditional on the actual request. No public URL is required for local/private media readiness. An explicit request to publish is authorization to perform that publication within scope; do not ask again merely because publishing is optional by default.

## Required fields

| Field | Type / meaning |
|---|---|
| `schema` | `feature-handoff/v2`; legacy handoffs may be read without silently changing their evidence |
| `status` | `ready`, `ready-with-notes`, `needs-visual-review`, `blocked`, or `fixture-only` |
| `user_story` | One visible outcome, in the user's language |
| `workflow` | `{lane, source_run_id, change_summary, reused_evidence[]}`; lane `verified-reuse`, `re-edit`, or `new-recording`; each reused receipt retains its original date and SHA |
| `delivery` | `{target, requested_formats[], root, persistence, access_evidence[]}`; target `local`, `private`, or `public`; paths relative to the run/archive where practical |
| `source` | `{product, version, channel, surface, commit, branch, pr, evidence[], raw[]}`; actual source identity, unknown fields null; raw entries include path, SHA-256, source take and `full-recording` / `existing-derivative`. Default channel production; an explicitly requested beta/preview/PR/Working Alpha stays labeled as that channel |
| `gates` | Separate `production_source`, `model_source`, `current_environment`, `current_live_e2e`, `file`, `playback`, `visual`, `legibility`, `cold_reader`, `delivery_access` results (see below) |
| `gif`, `mp4`, `poster` | Actual path or authorized URL, null for unrequested/unavailable formats. An existing GIF is not a full-original MP4 |
| `artifact_checks` | Per file: `{path,sha256,ui_language,file,playback,visual,legibility,cold_reader,readable_result_intervals_s,evidence[]}`; each check uses the gate result below. GIF player checks may be not-applicable; actual decoded GIF frames still require visual/readability review. One format's PASS never promotes another |
| `publication` | `{requested, status, destination, requested_roles[], evidence[]}`; status `not-requested`, `pending`, `complete`, or `blocked` |
| `funnel_url` | Public gallery URL only if requested and actually published; otherwise null |
| `funnel_checks` | Observed public checks only when publishing: `{role,url,status,mime,sha256,evidence}`; empty for local/private |
| `commit`, `branch`, `pr` | Optional recording-program repository receipts, null when no repository publication was requested; product provenance is in `source` |
| `story_scores` | `{candidate,R1..R7,total,basis}` entries when comparison occurred; `[]` valid for unchanged reuse with explanation in workflow. Unknown historical sub-scores use null; do not invent a total |
| `winner` | Selected candidate/story id or null when none selected |
| `research_mode` | `verified-reuse`, `standard`, `deep`, or pending null; no fabricated research/scores for fixed-scope reuse |
| `shot_list` | Copy of the applicable verified shots from `shotlist.json`; fields in [shot-list-schema.md](shot-list-schema.md). Time base explicitly identifies GIF or MP4. Empty only before a blocked plan exists |
| `legibility` | Summary `{verdict,file,checks[],readable_result_s,centering_pass,story_test}`; full ROI/strict-beat evidence in [legibility-spec.md](legibility-spec.md). Machine OCR failure and independent visual adjudication remain distinct |
| `qa` | `{verdict,hold_s,ui_language,notes}`; `pending`, `pass`, `pass-with-notes` or `fail`. CJK is evaluated against the requested native language, never an automatic failure |
| `model_execution` | `{mode,operation,run_id,edit_run_id,evidence,current_live_e2e,source_live_e2e,disclosure}` or null, as below. `run_id` identifies the original model recording and must match its evidence; reuse/re-edit adds `edit_run_id` for the current edit. `workflow.source_run_id` may separately identify the same original take |
| `no_inference_reason` | Observed reason when model summary is null. Missing provenance/credentials is not such a reason; an unfilled template remains blocked |
| `deviations`, `artifacts`, `known_weaknesses` | Lists of actual deviations, artifact paths and limitations. Do not hide a required gate failure as a note |
| `issues_for` | Optional routing metadata `{agent_id:[issues]}`, empty by default; it does not authorize messages |
| `next` | Concrete next step or completion note; include blocker resolution when unfinished |

## Gate results and reuse

Each gate is `{status,basis,required,evidence[],reason}`. Status is `pass | fail | blocked | not-run | not-applicable`; basis is `current | reused | none`; `required` is set from the actual request/product rules, never from which checks happen to pass. A reused PASS requires the actual readable receipt, exact SHA-256 and unchanged scope, language, dimensions and expected result. Retain its original timestamp/checker; never claim it ran now. Missing or stale receipts require that layer to be completed, not an invented PASS. Record per-file details in `artifact_checks` rather than flattening mixed results.

- **Source provenance**: requested channel/model evidence missing or mismatched ⇒ source gate `blocked`, even if every local media test passes. The compatibility field `production_source` verifies the actual requested availability channel; a verified Working Alpha recording can be ready for that labeled target, never proof of production deployment. Official package/build/deployment evidence can suffice without a formal GitHub Release.
- **Current environment**: unavailable target UI, credentials or browser is an environment result. It does not make an existing file corrupt. State whether the gate is required for the requested operation; unused new-capture access may be `not-run` for valid reuse.
- **Current live E2E**: only an actual current product live run can pass. Reuse, re-edit, replay, direct API ping and codec tests cannot set it to pass. When fresh live is not required, `not-run` is an honest nonblocking value with the reason. A requested/required fresh live gate remains blocking.
- **Local file tests**: decoder, real player, pixels, continuous reading time, independent full-film cold read and native language are separate evidence. Local tests can proceed while a source gate is blocked; they cannot repair provenance.
- **Delivery**: local checks read persistent exact files; private checks use authorized read/download and hash verification. HTTP is not a prerequisite for either.

`ready`/`ready-with-notes` require all applicable requested gates. Notes may describe historical reuse or an editorial hold, not waive failed source, playback, legibility, independent review or requested publication. `needs-visual-review` is not ready. A blocked run still reports actual passing local layers and completed files.

## Model source gate

Follow [model-execution.md](model-execution.md). Scripted/mock replies, prefilled Assistant/TODO/tool events and historical fixtures cannot be feature demonstrations, including PR demos. Browser automation scripts and isolated unit/codec tests are allowed.

Each media take is bound to its own immutable raw hash and original execution record. A separate live run cannot establish this media's origin. In a fresh `live` take only actual successful product execution may set current live E2E PASS. `captured-replay` requires the original successful live source, strict step-match report, real tool execution, zero outgoing model-provider requests and readable `Recorded model response · real tools` label in every derivative; this operation's live E2E is `not-run`. The playbooks do not supply a generic replay adapter.

A historical re-edit or unchanged reuse preserves the full original model evidence and its original result/date. In the current media summary use `operation=reuse` or `re-edit`, keep the original mode and `run_id`, add a separate `edit_run_id` for this edit, and set `model_execution.current_live_e2e` and `gates.current_live_e2e.status` to `not-run`; `source_live_e2e` references the verified original live result. `workflow.source_run_id` still identifies the original take; do not replace the original evidence identity with an edit ID. When the original run ID is unavailable, leave both original-ID fields null in the blocked handoff and retain the edit ID only in `edit_run_id`; this incomplete summary cannot pass the encoder's source checks. Do not infer the original live result when receipts are absent: use null and block model provenance. Reuse is neither a new replay execution nor a new live call. Fresh takes use `operation=fresh-recording`; new replay takes use `replay-recording`. A null summary is only for observed no-inference product behavior and needs a reason, never missing credentials or unknown provenance.

## Optional public publication

`publication.requested=false` and `status=not-requested` is the normal local/private case. Use null URLs and `funnel_checks=[]`; do not create public hosting to fill fields. Do not commit private receipts or upload source assets to the public skill repository.

When public publication is requested, verify every required published resource with an anonymous GET from a client that can reach the destination. Record observed HTTP 200, MIME, nonempty bytes and SHA-256 compared with the tested file. A page/HTML is checked as HTML rather than assigned a media hash. Check only the requested formats. A gallery page and published `handoff.json` are required only if that delivery was requested. Extra poster URLs do not replace requested resources. A login page, protected preview or inaccessible URL cannot be presented as public media.

If public publication fails, keep local file QA results, set `publication.status=blocked`, and mark the overall requested public delivery blocked. Do not ask the user to authorize an already requested upload again. Repository commit/branch/PR receipts are optional and only apply when that repository work was requested.

## User summary and conditional agent summary

Use the user's language and scale the response to the work: status and one user result; actual download links/inline GIF; source/reuse disclosure; per-format QA and unrun gates; deviations/blocker; next step. Public links appear only after verification. Keep full scores/shot lists and weaknesses in the file, showing compact tables when useful or requested. Do not bury a simple reuse result under mandatory A/B/C tables.

Only send a bot/agent message when explicitly authorized by the user or by an explicitly invoked authorized workflow. `reply_to` alone is routing metadata, not authority. Otherwise include a forwardable summary in the deliverable. An authorized agent summary uses the same facts:

```text
STATUS: <status>
RESULT: <user_story>
DELIVERY: <local|private|public; verified paths/URLs>
WORKFLOW: <lane; original run; actual changes>
SOURCE: <requested channel/model provenance status and evidence>
QA: <per-format file/player/visual/legibility/reading/cold-reader results>
LIVE: <current live E2E; original source context if applicable>
PUBLICATION: <not-requested|pending|complete|blocked>
ISSUES_FOR_YOU: <routed issues or none>
NEXT: <next>
HANDOFF: <actual path; public URL only when requested and verified>
```
