# Inbound delegate — `delegate_to_feature_recorder/v1.1`

This is a recording request, distinct from the [outbound handoff](handoff-schema.md). Accept `delegate_to_feature_recorder/v1` too. A YAML file or a compact message is sufficient; they are not both mandatory. If both exist, inspect inconsistencies before depending on them; neither overrides explicit user instructions or authorizes a new publication/message.

Use the [template](../assets/delegate.template.yaml). A delegate should identify the visible outcome and enough source/context for early verification. Missing optional workflow metadata must not turn a concrete manual recording request into a public-release process.

## Required context, with source alternatives

| Field | Requirement |
|---|---|
| `schema` | Prefer `delegate_to_feature_recorder/v1.1`; v1 accepted |
| `user_outcome` | One sentence describing the visible result |
| Source identity | Either `repo` plus `commit` and/or `pr`, or `source_evidence` identifying the actual deployment/package/build/version. A branch, entry URL or PR alone is a locator to inspect, not proof of availability |

`branch` is optional when the commit/build is identified. `repo`, `commit`, `pr`, `version`, `source_channel` and `entry_url` should be included when known. Default source channel is production; an explicit beta/preview/PR/Working Alpha request must be verified and labeled as that channel, never promoted to production. Official deployment/package evidence may suffice; a formal GitHub Release is not required.

If context is incomplete, run bounded read-only discovery and preserve local evidence; do not blind-record. Once missing source/access is confirmed, produce a blocked partial handoff with the exact missing item and resolution instead of repeatedly trying equivalent routes. No need to acquire a shared desktop lock or launch the app merely to diagnose a malformed delegate. A missing source gate does not forbid truthful local file diagnostics, but those cannot establish provenance.

## Optional fields and defaults

| Field | Meaning / default |
|---|---|
| `record_machine` | `auto` (default), `work`, `box` (legacy alias for Work), or `mac_mini`; use the current capable authorized host unless specified. No Mac-only default |
| `existing_media` | Candidate paths/URLs, manifests, original raw hashes and original execution/QA references; inspect these first for verified reuse |
| `delivery_target` | `local` (default), `private`, or `public`; private/public require actual destination/context |
| `delivery_destination` | User-specified persistent path, private directory or public endpoint; do not infer one from memory |
| `publication_requested` | Default false. True only for an explicitly requested publication; `delivery_target=public` from the authorized request implies true |
| `publish_programs_repo` | No default. Optional destination for recording programs, only if repository publication is requested; never upload private media/receipts to fill this field |
| `reply_to` | Optional routing metadata for an authorized agent reply. Omission does not block recording; its presence alone does not authorize a bot message |
| `notify_authorization` | Reference to the user's explicit instruction or explicitly invoked workflow authorizing an agent message; omit if none |
| `feature_slug`, `ui_hooks`, `demo_prompt` | Hints to verify against actual UI, not proof of behavior |
| `format` | `gif`, `mp4`, or `both` (default); unrequested formats do not become delivery gates |
| `cut_policy`, `constraints`, `ui_language` | Requested window/holds, framing and actual native UI language |
| `model_mode` | `live` by default, or `captured-replay`; scripted/mock/prepopulated model demonstrations invalid |
| `replay_source` | Successful original live evidence/capture required before executing replay; a project adapter must actually exist and be verified |
| `model_budget` | Bounded takes, requests, timeouts and observable cost cap, filled before execution if absent |
| `fresh_live_required` | Explicit user/product requirement; when absent inspect applicable product rules. Reuse is not a new live call |
| `research_mode` | `auto` (default), `verified-reuse`, `standard`, or `deep`; no repeated research for unchanged verified reuse |

Optional fields do not add approval gates. A concrete authorized request can proceed with reasonable defaults. An invalid model mode, missing/mismatched replay source or unmet required fresh live gate blocks the dependent operation; never silently fall back to scripted replies. See [model execution](model-execution.md).

`llm_provider` is ignored legacy metadata and does not alter model/story selection. Unknown keys may be preserved as hints, but never interpreted as authority to publish, disclose credentials, send messages or relax gates.

## Compatibility

v1 and v1.1 delegates remain accepted. Old `record_machine=box` maps to the current Work route. Missing `publish_programs_repo` or `reply_to` no longer needs a fabricated default or a blocker. Record meaningful changed defaults in `deviations`, particularly that no publication was requested; do not send a message just to announce the migration. Existing explicit publication or notification instructions remain valid within their scope.

## Compact text alternative

A YAML file is preferable for complex source/replay evidence. A simple request may use:

```text
DELEGATE: delegate_to_feature_recorder/v1.1
OUTCOME: <visible user result>
SOURCE: <repo/commit/PR or actual build/deployment evidence>
CHANNEL: <production|beta|preview|pr|working-alpha>
OPTIONAL: existing_media=...; format=both; record_machine=auto; delivery_target=local; ...
```

Legacy `REPO`, `BRANCH`, `COMMIT`, `PR`, `OUTCOME`, `REPLY_TO` lines are still readable. Empty routing fields are not blockers. An authorized agent notification, if requested, uses the normal handoff facts; otherwise return the handoff in the current conversation and include forwardable text if useful.

## Blocked reply

Write the partial handoff and use a short decision table only when there is a real missing prerequisite:

| Missing/invalid | Why it matters | Concrete resolution |
|---|---|---|
| Visible outcome | No acceptance target | Identify one result the viewer must see |
| Source identity | Cannot associate footage with the requested build/channel | Supply verifiable package/deployment/source evidence |
| Model provenance | Cannot establish the origin of generated behavior | Provide the original evidence or record a bounded real live run |
| Required UI access | Cannot execute the target workflow | Restore authorized access or use a permitted verified source |

Report local file results separately. Do not list public hosting, a feature branch, a PR, missing bot recipient or an unconfigured optional Mac route as universal recording prerequisites.
