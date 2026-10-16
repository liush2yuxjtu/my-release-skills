# Handoff output schema (mandatory)

Every run ends with one file, `runs/<take>/handoff.json`, as the **single source of truth**. Both the user chat message and the bot message are rendered from it; never add facts that are not in the file.

## C3 — handoff.json fields

| field | type | notes |
|---|---|---|
| `status` | `ready` \| `ready-with-notes` \| `blocked` | |
| `user_story` | string | 【谁】在【场景】用【功能】完成了【什么】 |
| `funnel_url` | URL | public gallery page |
| `funnel_checks` | `[{url, status}]` | every published URL, HTTP status actually observed (must be 200) |
| `gif`, `mp4`, `poster` | URL | funnel URLs |
| `commit`, `branch`, `pr` | string | feature branch, never `main` |
| `story_scores` | `[{candidate, R1..R7, total}]` | rubric in `story-research.md` |
| `winner` | string | candidate id |
| `qa` | `{verdict, hold_s, cjk_frames, notes}` | verdict `pass` \| `pass-with-notes` \| `fail` |
| `deviations` | string[] | differences from the request |
| `artifacts` | string[] | repo paths (A6, not in chat) |
| `known_weaknesses` | string[] | (A9, not in chat) |
| `issues_for` | `{agent_id: [issue,...]}` | issues routed to other bots |
| `next` | string or `[{option, effect}]` | |

Unknown R1–R7 sub-scores: use `null`, keep `total`.

## A — user chat message (Chinese prose, code/paths English), in this order

1. **A1 状态**: `ready` / `ready-with-notes` / `blocked`
2. **A2 结果**（用户故事）: 【谁】在【场景】用【功能】完成了【什么】
3. **A3 Funnel**: link, only after HTTP 200 verified
4. **A4 GIF**: inline attachment
5. **A5 故事评分表**: one row per candidate, R1–R7 + total, winner marked
6. **A7 QA**: verdict, result hold seconds, CJK check
7. **A8 偏差**: deviations from the request
8. **A10 下一步**: one sentence, or a decision table if several options

A6 (artifacts) and A9 (weaknesses) are NOT in the chat message.

## B — bot message (SendToAgent)

B1 fixed English lines:

```
STATUS: <status>
RESULT: <user_story>
FUNNEL: <funnel_url>
COMMIT: <commit> (<branch>)
ARTIFACTS: <comma-separated artifacts>
QA: <verdict>, hold <hold_s>s, CJK frames <cjk_frames>
ISSUES_FOR_YOU: <issues_for[recipient agent_id] or "none">
NEXT: <next>
```

B2: a fenced ```json block with the same fields (status, result, funnel, commit, artifacts, qa, issues_for_you, next).

B3: `handoff.json: <repo path>` and `<funnel URL of handoff.json>`.

## Rules

- Write, commit (feature branch), and publish `handoff.json` before sending either message.
- Verify every URL in `funnel_checks` returns 200 from outside the box (the box cannot TLS to its own funnel; use the Mac mini or WebFetch).
- Missing required field or unverified funnel ⇒ not `ready`.
