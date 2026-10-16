# Handoff output schema (mandatory)

Every run ends with one file, `runs/<take>/handoff.json`, as the **single source of truth**. Both the user chat message and the bot message are rendered from it; never add facts that are not in the file.

## C3 — handoff.json fields

| field | type | notes |
|---|---|---|
| `status` | `ready` \| `ready-with-notes` \| `blocked` | |
| `user_story` | string | 【谁】在【场景】用【功能】完成了【什么】 |
| `funnel_url` | URL | public gallery page |
| `funnel_checks` | `[{url, status}]` | every published URL, HTTP status actually observed (must be 200). **Hard gate:** must cover page + gif + mp4 + handoff.json (see below) |
| `gif`, `mp4`, `poster` | URL | funnel URLs |
| `commit`, `branch`, `pr` | string | feature branch, never `main` |
| `story_scores` | `[{candidate, R1..R7, total}]` | rubric in `story-research.md` |
| `winner` | string | candidate id |
| `shot_list` | `shot[]` | 镜头分镜, copy of `runs/<take>/shotlist.json` `shots[]`; fields in `shot-list-schema.md` (id, t_start, t_end, beat, framing, zoom, crop_css, roi_css, focus, pointer, text_expected, legibility_px, transition_in, ease, hold_s, purpose) |
| `legibility` | `{verdict, file, checks:[{id, metric, measured_px, threshold_px, ocr, pass}], readable_result_s, centering_pass, story_test:{independent, pass, answer}}` | §7.1 gate summary; full evidence in `runs/<take>/verify/legibility.json` |
| `qa` | `{verdict, hold_s, cjk_frames, notes}` | verdict `pass` \| `pass-with-notes` \| `fail` |
| `deviations` | string[] | differences from the request (include inbound v1 default fills when applicable) |
| `artifacts` | string[] | repo paths (A6, not in chat) |
| `known_weaknesses` | string[] | (A9, not in chat) |
| `issues_for` | `{agent_id: [issue,...]}` | issues routed to other bots |
| `next` | string or `[{option, effect}]` | |

Unknown R1–R7 sub-scores: use `null`, keep `total`.

### `funnel_checks` hard gate (required for `ready`)

`funnel_checks` must include **at least these four** URLs, each with observed HTTP **200** from outside the box:

| role | must match |
|---|---|
| **page** | gallery / feature page (`funnel_url`) |
| **gif** | published GIF (`gif` field) |
| **mp4** | published MP4 (`mp4` field) |
| **handoff.json** | published `handoff.json` on the funnel |

Missing any of the four entries, or any non-200 status ⇒ **not** `status: ready` (use `blocked` or `ready-with-notes` only when the missing piece is explicitly documented and the run is otherwise complete — default is not `ready`). Extra URLs (e.g. poster) may appear in `funnel_checks` but do not replace the four.

## A — user chat message (Chinese prose, code/paths English), in this order

1. **A1 状态**: `ready` / `ready-with-notes` / `blocked`
2. **A2 结果**（用户故事）: 【谁】在【场景】用【功能】完成了【什么】
3. **A3 Funnel**: link, only after HTTP 200 verified
4. **A4 GIF**: inline attachment
5. **A5 故事评分表**: one row per candidate, R1–R7 + total, winner marked
6. **A6s 镜头分镜**: compact table right after A5, one row per shot from `shot_list` (# · 时间 s · beat · 景别/倍数 · 焦点 · 指针 · 画面文字 (px) · 转场 · 停留 s); see `shot-list-schema.md`
7. **A7 QA**: verdict, result hold seconds, CJK check, legibility gate (pass/fail + the measured px per key text, cold-viewer result)
8. **A8 偏差**: deviations from the request
9. **A10 下一步**: one sentence, or a decision table if several options

A6 (artifacts) and A9 (weaknesses) are NOT in the chat message. A6s (shot table) IS.

## B — bot message (SendToAgent)

B1 fixed English lines:

```
STATUS: <status>
RESULT: <user_story>
FUNNEL: <funnel_url>
COMMIT: <commit> (<branch>)
ARTIFACTS: <comma-separated artifacts>
QA: <verdict>, hold <hold_s>s, CJK frames <cjk_frames>
LEGIBILITY: <verdict>; <id> <measured>/<threshold>px, ...; cold-viewer <pass|fail|provisional>
SHOTS: <id> <framing><zoom>x <t_start>-<t_end> | ...
ISSUES_FOR_YOU: <issues_for[recipient agent_id] or "none">
NEXT: <next>
```

B2: a fenced ```json block with the same fields (status, result, funnel, commit, artifacts, qa, legibility, shot_list, issues_for_you, next).

B3: `handoff.json: <repo path>` and `<funnel URL of handoff.json>`.

## Rules

- Write, commit (feature branch), and publish `handoff.json` before sending either message.
- Verify every URL in `funnel_checks` returns 200 from outside the box (the box cannot TLS to its own funnel; use the Mac mini or WebFetch).
- Missing required field, missing/failed `legibility` gate, empty `shot_list`, incomplete `funnel_checks` (page + gif + mp4 + handoff.json), or unverified funnel ⇒ not `ready`.
