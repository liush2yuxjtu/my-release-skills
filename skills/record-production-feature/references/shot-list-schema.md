# 镜头分镜 (shot list) output schema

Every run writes `runs/<take>/shotlist.json` **before** the camera pass (plan) and updates it **after** verification (measured `legibility_px`, centering). `handoff.json.shot_list[]` is a copy of `shots[]`. Template: `assets/shotlist.template.json`.

Times are in **delivered-GIF seconds** (0 = first GIF frame). Add `t_raw_start` for the GT/master timeline. Coordinates are CSS px of the recorded viewport (e.g. 1920×1080), independent of DPR.

## File

| field | type | notes |
|---|---|---|
| `take`, `edit` | string | e.g. `generative-v1-take5`, `edits/zoom-v6` |
| `gif` | `{width,height,fps,frames,duration_s,window_raw_s:[t0,t1]}` | delivered GIF |
| `click_gif_s` | number | the one action moment |
| `camera` | string | camera script path |
| `coords` | string | coordinate space note |
| `shots` | `shot[]` | in time order, covering 0…duration without gaps |

## shot

| field | type | notes |
|---|---|---|
| `id` | string | `S1`,`S2`…; transitions `T23` (between S2 and S3) |
| `t_start`, `t_end` | number s | GIF time |
| `t_raw_start` | number s | master/GT time |
| `beat` | string | `B0 establish` / `B1 before` / `B2 action` / `B3 result` / `B4 payoff` / `transition` |
| `framing` | `full` \| `medium` \| `close` | full = whole viewport (zoom≈1); medium ≈1.2–2.5×; close ≥2.5× on one ROI |
| `zoom` | number | camera zoom at the hold (1 = full viewport) |
| `crop_css` | `[x,y,w,h]` | crop rect at the hold |
| `roi_css` | `[x,y,w,h]` \| null | the subject rect (DOM box / OCR box); must be inside `crop_css` |
| `roi_center_offset_pct` | `[dx,dy]` | (ROI centre − crop centre) / crop size × 100; gate ≤10 |
| `roi_in_frame` | bool | |
| `focus` | string | the UI label(s) in focus, verbatim, e.g. `Tweaks > Prepared for this design > Mood: Editorial / SaaS / Playful` |
| `pointer` | string | pointer action: idle / glide to X / click X at t / parked off frame |
| `text_expected` | string[] | on-screen text that should be readable in this shot (verbatim) |
| `legibility` | string \| null | id of the legibility check this shot carries |
| `legibility_px` | `{metric,measured,threshold,frame,pass}` \| null | measured at the delivered size (§7.1) |
| `transition_in` | string | e.g. `push-in 0.6 s`, `pull-out 0.3 s then push-in 0.3 s`, `cut` |
| `ease` | string | e.g. `cosine, log-zoom` |
| `hold_s` | number | settled hold (camera still) |
| `purpose` | string | why this shot exists in the story (one sentence) |

## Design rules

- One **close** shot per key text: before-state, the clicked control (at the click moment), the result, and the CTA if it changed. Zoom = `threshold_px ÷ (glyph_css_px × gif_width/viewport_width)`; record at DPR 2 when zoom > ~3.
- The click happens inside a close shot of the control; the pointer must not cover the label.
- Readable result (px-gate) ≥3 s total across result shots; end on the same framing as the first shot so the loop is seamless.
- Transitions ≤0.6 s, eased; no speed-up, no captions (pure-screen).

## Chat rendering (A6s 镜头分镜, right after A5 故事评分表)

Compact Markdown table, one row per shot (transitions may be merged into the next row's 转场 column):

| # | 时间 s | beat | 景别/倍数 | 焦点 | 指针 | 画面文字 (px) | 转场 | 停留 s |
|---|---|---|---|---|---|---|---|---|
| S2 | 0.5–1.9 | 前 | close 5.8× | hero h1+CTA | — | "Coffee that tastes like the trail." cap 38 | push 0.6 | 0.8 |

## Bot rendering

B1 line: `SHOTS: S1 full 0-0.5 | S2 close5.8x hero 0.5-1.9 | ...` ; B2 JSON includes `shot_list`.
