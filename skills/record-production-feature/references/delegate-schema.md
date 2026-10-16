# Inbound delegate schema — `delegate_to_feature_recorder` (v1.1)

How **another agent** asks this skill to record one production feature.
This is **inbound** (request into the recorder). Outbound delivery after a run is
[`handoff-schema.md`](handoff-schema.md) — do not mix the two.

**Current schema id:** `delegate_to_feature_recorder/v1.1`  
**Still accepted:** `delegate_to_feature_recorder/v1` (see [Compatibility](#compatibility-v1)).

Carrier (v1.1): a **YAML file** (preferred) **and** a compact English
`SendToAgent` message body that mirrors the same fields. Either may arrive first;
both must agree when both are present. Prefer the YAML file as the source of
truth when values conflict.

## Required fields (v1.1)

| field | type | notes |
|---|---|---|
| `schema` | string | Prefer `delegate_to_feature_recorder/v1.1`; `…/v1` still accepted |
| `repo` | string | GitHub `owner/name` (or clone URL) of the product / release source that proves the feature is in production |
| `branch` | string | Branch that contains the feature (not necessarily `main`) |
| `commit` **or** `pr` | string | At least one required. `commit` = full or abbrev SHA; `pr` = PR number or URL. Prefer both when known |
| `user_outcome` | string | One sentence: what the viewer must see at the end of the recording (maps to §1 `user_outcome`) |
| `reply_to` | string | Agent id to receive the outbound B-message (`SendToAgent`) after the run finishes |

Missing any required field ⇒ **do not start recording**. Respond with
`status: blocked`, a decision table of what is missing / how to fix it, and wait.
Never blind-record from partial context.

## Recommended tips (optional but preferred)

Callers should include these when known. Absence does **not** block; the recorder
fills the defaults below and records each fill in outbound `deviations`.

| field | values / default | notes |
|---|---|---|
| `record_machine` | `box` \| `mac_mini` \| `auto` | Where to run capture/encode. Default when omitted: `auto` (prefer Mac mini for ChatCut Desktop / ui-demo; box only when the task is truly box-local) |
| `publish_programs_repo` | GitHub `owner/name` | Where recording **programs** (scripts, shotlists, run metadata that are not the product repo) are saved after a run. Default when omitted: `liush2yuxjtu/feature-recorder` |

## Optional tips (not required)

Callers may include these; the recorder may ignore or fill defaults. Do **not**
block solely because they are absent:

| field | tip |
|---|---|
| `entry_url` | Deep link or app route where the feature lives |
| `feature_slug` | Stable id / folder name for artifacts |
| `ui_hooks` | Selectors, accessible names, or rehearsal notes |
| `demo_prompt` | Suggested story beat or demo script seed |
| `format` | `gif` \| `mp4` \| `both` (skill default: both) |
| `cut_policy` | GIF window / hold hints |
| `constraints` | Hard limits (no zoom, fixed crop, etc.) |

### Ignored / legacy tips

| field | status |
|---|---|
| `llm_provider` | **Ignored** (legacy). Accepted if present for forward-compat, but does not change model selection or story scoring. Do not send on new v1.1 delegates. |

Any other keys are ignored (forward-compatible).

## Compatibility (v1)

When inbound `schema` is `delegate_to_feature_recorder/v1` (or the message line
`DELEGATE: …/v1`):

1. Accept the payload; do **not** block solely for the old schema id.
2. If `record_machine` / `publish_programs_repo` are missing, fill defaults
   (`auto` and `liush2yuxjtu/feature-recorder`) and append a short note to
   outbound `deviations`, e.g. `inbound v1: filled record_machine=auto;
   publish_programs_repo=liush2yuxjtu/feature-recorder`.
3. Prefer callers upgrade to `…/v1.1` and set the recommended tips explicitly.

## YAML example

See also [`assets/delegate.template.yaml`](../assets/delegate.template.yaml).

```yaml
schema: delegate_to_feature_recorder/v1.1
repo: owner/product-repo
branch: feat/example-feature
commit: abcdef0123456789abcdef0123456789abcdef01
pr: "https://github.com/owner/product-repo/pull/123"
user_outcome: >-
  Viewer sees the user open the feature, apply it once, and the final result
  hold readable for at least 3 seconds.
reply_to: <agent-id-to-B-message>

# recommended tips (omit → defaults + note in deviations)
record_machine: auto          # box | mac_mini | auto
publish_programs_repo: liush2yuxjtu/feature-recorder

# optional tips (omit freely)
# entry_url:
# feature_slug:
# ui_hooks: []
# demo_prompt:
# format: both
# cut_policy:
# constraints: []
# llm_provider:   # ignored / legacy — do not send
```

## SendToAgent compact English lines (inbound)

When the caller also (or only) sends a message body, use these fixed labels,
one field per line. Order is fixed; unknown lines go under `OPTIONAL:` as
`key=value` pairs.

```
DELEGATE: delegate_to_feature_recorder/v1.1
REPO: <owner/name>
BRANCH: <branch>
COMMIT: <sha or "">   # empty only if PR is set
PR: <number|url or "">  # empty only if COMMIT is set
OUTCOME: <user_outcome one line>
REPLY_TO: <agent id>
OPTIONAL: record_machine=auto; publish_programs_repo=liush2yuxjtu/feature-recorder; entry_url=...; feature_slug=...; format=both; ...
```

Rules for the message body:

- `DELEGATE`, `REPO`, `BRANCH`, `OUTCOME`, `REPLY_TO` are always required.
- At least one of `COMMIT` or `PR` must be non-empty.
- `DELEGATE: …/v1` is still accepted (see [Compatibility](#compatibility-v1)).
- `OPTIONAL:` may be omitted entirely, or list semicolon-separated `key=value`
  for the tip fields above (`llm_provider` if present is ignored).
- Prefer attaching / pointing at the YAML file path in the same thread; when
  both exist, YAML wins on conflicts.

## Blocked behavior (missing required)

1. Do **not** acquire the recording lock, launch ChatCut, or write a take.
2. Set outbound handoff-style status to `blocked` (when producing a reply).
3. Reply to `reply_to` (if present) or to the caller with a **decision table**:

   | missing / invalid | why it blocks | how to unblock |
   |---|---|---|
   | `repo` | no production source to verify | send `owner/name` |
   | `branch` | cannot locate the change | send branch name |
   | `commit` and `pr` | no ship evidence | send SHA and/or PR |
   | `user_outcome` | no acceptance target for the GIF | one-sentence visible result |
   | `reply_to` | nowhere to B-message after | agent id for SendToAgent |

4. Do not invent defaults for required fields. Recommended / optional tips may
   be defaulted (and noted in `deviations`); they never replace required fields.

## Relationship to outbound handoff

| direction | schema | carrier |
|---|---|---|
| **Inbound** (this doc) | `delegate_to_feature_recorder/v1.1` (accepts v1) | YAML file + SendToAgent lines |
| **Outbound** | [`handoff-schema.md`](handoff-schema.md) | `runs/<take>/handoff.json` + chat A-message + bot B-message |

After a successful (or blocked mid-run) recording, render the normal handoff and
B-message **to `reply_to`**. Inbound `user_outcome` seeds §1; it does not replace
handoff `user_story` / QA fields. Programs belonging to the recording run are
published under `publish_programs_repo` (default `liush2yuxjtu/feature-recorder`).
