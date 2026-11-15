# 镜头分镜 (shot list) output schema

Every run writes `runs/<take>/shotlist.json` **before** the camera pass (plan) and updates it **after** verification (measured `legibility_px`, centering). `handoff.json.shot_list[]` is a copy of `shots[]`. Template: `assets/shotlist.template.json`.

Declare `timeline_kind` as `gif` or `mp4`; times are in that delivered file's seconds (0 = its first frame). Add `t_raw_start` for the GT/master timeline. Declare `coordinate_space` as `css-px` only when the actual viewport/DPR is known, or `decoded-source-px` for measured existing footage. Use `crop_px`/`roi_px` in the latter case; do not invent DOM coordinates or DPR from a historical GIF.

## File

| field | type | notes |
|---|---|---|
| `take`, `edit` | string | e.g. `generative-v1-take5`, `edits/zoom-v6` |
| `timeline_kind`, `coordinate_space` | string | actual delivered timeline and declared pixel coordinates |
| `gif` / `mp4` | `{width,height,fps,frames,duration_s,window_raw_s:[t0,t1]}` or null | actual format; unrequested format null; variable GIF delays recorded separately |
| `click_gif_s` / `click_mp4_s` | number or null | actual action in that timeline; unknown remains null |
| `camera` | string or null | actual camera script, or null for unchanged/static framing |
| `coords` | string | coordinate space note |
| `shots` | `shot[]` | in time order, covering 0…duration without gaps |

## shot

| field | type | notes |
|---|---|---|
| `id` | string | `S1`,`S2`…; transitions `T23` (between S2 and S3) |
| `t_start`, `t_end` | number s | declared delivered timeline |
| `t_raw_start` | number s | master/GT time |
| `beat` | string | `B0 establish` / `B1 before` / `B2 action` / `B3 result` / `B4 payoff` / `transition` |
| `framing` | `full` \| `medium` \| `close` | full = whole viewport (zoom≈1); medium ≈1.2–2.5×; close ≥2.5× on one ROI |
| `zoom` | number | camera zoom at the hold (1 = full viewport) |
| `crop_css` / `crop_px` | `[x,y,w,h]` | crop rect at the hold in the declared coordinate space |
| `roi_css` / `roi_px` | `[x,y,w,h]` \| null | subject rect; must be inside its crop |
| `roi_center_offset_pct` | `[dx,dy]` | (ROI centre − crop centre) / crop size × 100; gate ≤10 |
| `roi_in_frame` | bool | |
| `focus` | string | the UI label(s) in focus, verbatim, e.g. `Tweaks > Prepared for this design > Mood: Editorial / SaaS / Playful` |
| `pointer` | string | pointer action: idle / glide to X / click X at t / parked off frame |
| `text_expected` | string[] | on-screen text that should be readable in this shot (verbatim) |
| `legibility` | string \| null | id of the legibility check this shot carries |
| `legibility_px` | `{metric,measured,threshold,frame,pass}` \| null | measured at the delivered size (SKILL §6.1) |
| `transition_in` | string | e.g. `push-in 0.6 s`, `pull-out 0.3 s then push-in 0.3 s`, `cut` |
| `ease` | string | e.g. `cosine, log-zoom` |
| `hold_s` | number | settled hold (camera still) |
| `purpose` | string | why this shot exists in the story (one sentence) |

## Design rules

- Cover each claimed key text: before-state, clicked control, result and changed CTA. Use a close-up only when needed for readability; one static framing may cover all of them. Do not invent camera motion unsupported by the actual editor.
- The clicked control must be readable at the action; the pointer must not cover its label.
- Readable result (pixel gate) must last **at least 3 continuous seconds** after the framing settles. An attractive loop cannot waive the action/result proof.
- Any actual camera transitions are eased and ≤0.6 s; pure-screen by default. External speed changes or editorial holds require explicit source mapping under the delivered-video contract; the bundled builder implements neither.

## Optional chat rendering

Keep the full list in the handoff. When requested, render a compact table, one row per shot (transitions may be merged into the next row's 转场 column):

| # | 时间 s | beat | 景别/倍数 | 焦点 | 指针 | 画面文字 (px) | 转场 | 停留 s |
|---|---|---|---|---|---|---|---|---|
| S2 | 0.5–1.9 | 前 | close 5.8× | hero h1+CTA | — | "Coffee that tastes like the trail." cap 38 | push 0.6 | 0.8 |

## Bot rendering

Only when an agent notification is explicitly authorized: `SHOTS: S1 full 0-0.5 | S2 close5.8x hero 0.5-1.9 | ...`; its JSON includes `shot_list`. Otherwise provide forwardable text without sending it.
