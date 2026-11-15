# Verify the delivered videos, not just their GIF previews

Apply this gate to every delivered language and every delivered format. A GIF PASS never promotes the complete MP4 to PASS. Machine decoding, real player playback and independent visual understanding are separate results. Bind every receipt to the exact media SHA-256.

## Lock the scope before testing

List the actual files, intended native UI language, source identity and observable result. Separate a fresh recording from a historical raw re-edit; separate a real-model session from native prepared UI behavior. Preserve original bytes and failed edits. Do not silently remove a failed file from the set, relax an expected result, or use a previous version's PASS.

## Run the file gate

```bash
python scripts/verify_delivery.py assets/feature-en.mp4 qa/en-file-1
python scripts/verify_delivery.py assets/feature-zh.mp4 qa/zh-file-1
```

The bundled script probes codec, resolution, duration and actual decoded frame count, decodes the entire file with error output checked, checks H.264/yuv420p and faststart atom order, and exports 16 evenly spaced native frames plus an anonymous contact sheet. GIF checks report real per-frame duration and loop metadata. Apply the requested duration/size/loop specification separately; do not assume every GIF is eight seconds. Output directories must be new.

The script deliberately leaves visual and playback verdicts pending. File PASS is not delivery PASS.

## Play every complete MP4 at normal speed

From a project with Node, Playwright and ffprobe available, save a private, nonempty JSON array such as `[{"path":"assets/feature-en.mp4"},{"path":"assets/feature-zh.mp4"}]`, then run:

```bash
node scripts/verify_playback.mjs assets.json qa/player-1
```

Paths in this array are relative to the current project directory. An optional `sha256` on each entry freezes the expected source bytes. Every selected entry gets its own `asset-N.json`; `summary.json` retains the complete selected scope and the overall player result. Empty or malformed lists, missing files, missing modules and browser launch failures exit nonzero and retain a failure summary whenever a new output directory can be created. An existing output directory or file is never changed. Keep the new private directory and its receipts outside this public distribution.

The script resolves project-local `playwright` by default. `--playwright-module PATH` or `PLAYWRIGHT_MODULE_PATH` may identify an already installed Playwright/Playwright Core package directory or entry file; these are filesystem paths relative to the current project, not package names. `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` may explicitly select an installed Chromium. No dependencies or browsers are downloaded. The v2 receipts bind the resolved package entry/version, launch executable, actual running executable SHA-256 and metadata, binary version and Chromium-reported version. A launcher script and its browser binary are reported separately. The running version must match the actual executable version; an override is never presented as the Playwright default.

Each file uses a fresh isolated Chromium context and a tokenized loopback server exposing only that selected media plus a fixed local player. The server supports GET, HEAD and single byte ranges, rejects invalid ranges, and never exposes a workspace directory. The browser can request only those two local URLs. Playback begins at the start, stays at 1× without seeking and runs until `ended`. The receipt records media errors, duration, terminal currentTime, intrinsic dimensions, decoded and total frame counters, an explicitly labeled displayed-frame estimate, dropped frames, frame callbacks and wall-clock checkpoints. The observed duration and dimensions must match ffprobe metadata. These checks do not replace the full file/decoder gate.

The source is opened read-only and kept bound to the selected file descriptor. Independent SHA-256 reads before and after playback, file identity, size, modification/change times and the selected path must all match. Sources are never rewritten. The defaults are at most 32 selected entries, 2 GiB per file, a 1 MiB list and 180,000 ms per playback. `--timeout-ms` accepts 1,000–600,000 ms; a file longer than the selected bound fails. Setup, hashing, subprocess and cleanup waits are also bounded. The script adds no browser policy-disabling flags and uses no saved profile.

Player PASS concerns only full normal-speed playback of the exact bytes in the recorded Chromium environment. Audio is muted, so audibility stays pending. Visual review stays pending and model execution stays unevaluated on both PASS and FAIL receipts. Do not copy a player result into those separate gates.

Dropped frames are recorded, not hidden. A resource-starved cloud browser is not proof of a broken source file. If motion looks wrong or drop rates are high, pause concurrent rendering and replay the same SHA at light load before diagnosing the asset. `video.play()` resolving, metadata loaded, seeking to the end, or FFmpeg decoding alone do not establish full player playback.

## Inspect pixels and meaning

Inspect the full-film contact sheet and native-size frames for the opening, actual click, camera transitions, readable result start/end and final frame. Add dense frames around the click and each camera boundary. Then inspect the actual GIF separately at its delivered size.

- Essential controls, selected states and complete claimed results must be readable. A panel close-up should not leave unrelated body paragraphs cut in half beside it.
- Show the clicked label before the UI changes its name; leave a context bridge connecting the revealed panel to its control.
- Native card ellipsis is not necessarily a defect. If the story claims the full answer, show that full answer in a separate readable view; do not call an abbreviated card the complete result.
- Treat each retained close-up as a composition. Cropping during a brief camera transition is different from holding a clipped essential sentence.
- Distinguish an editorial click ring, the real pointer and native UI annotations. A native pinned comment must not be misreported as a broken cursor.
- Check each promised text, including secondary results when claimed. A heading PASS does not imply CTA microcopy PASS.

Use the existing legibility gate and actual glyph ink metrics, not OCR word-box height. Latin cap-height and x-height do not apply to CJK. For CJK, define and report a full-glyph ink-height threshold and inspect the strokes at delivery size; keep the metric distinct. OCR requires the actual language data and configuration files. Verify TSV headers and errors: missing `configs/tsv` can return ordinary text instead of TSV. Missing OCR is pending/blocked for that layer; it is never an empty successful OCR run. If a stylized native title remains an OCR false negative, retain its OCR FAIL, exact frames and glyph measurements. A separate named independent reader may adjudicate the text character by character; record an explicit visual exception, not an invented OCR PASS. Do not change the product merely to satisfy an OCR engine.

Give an independent new-context reader only the anonymous 16-frame sheet, with no intended brief, expected answer, filename clues or prior verdict. Ask what happened, what changed, who it is for and what is unreadable. Preserve the literal answer. A FAIL must trigger a targeted fix and another new-context review. A dense action strip may supplement investigation, but cannot replace the blind full-film review.

## Reading time and honest final-frame holds

Measure continuous readable time on the delivered timeline after the camera settles and the essential result is actually visible. Keep source evidence duration separate from delivery reading duration. Results need at least three readable seconds; report multiple intervals separately when a card and complete answer are both promised.

An editorial final-frame hold may extend reading time when it repeats an actual final frame. Preserve the immutable raw, disclose the hold duration and source-to-output mapping in the manifest, and label it in the handoff as an editorial hold. It is not new recording time, a longer observed model run or additional proof of runtime behavior. Never use frozen frames to hide missing actions or fabricate progress.

## Repair and delivery

1. Save the first FAIL and its source SHA.
2. Fix the demonstrated root cause into a new edit/take; preserve the prior version.
3. Re-run the affected file's complete file, player, pixel, timing and independent-reader checks. Unchanged files keep their SHA-bound receipts.
4. Publish the verified exact bytes. Re-download persistent attachments or public media and compare hashes.
5. Replace current download/embed references in every related Page and README. Preserve explicitly labeled history; do not leave a current stale link paired with a new PASS claim.
6. Report a matrix per artifact, with separate file/player/visual/timing/source results and the changed/unchanged decision. Never invent a required production or real-API PASS from video QA.

## Four-video regression case

A review of two Sidebar History and two Atelier complete MP4s found that earlier independent checks covered GIFs but had not established full-film visual PASS. The two Sidebar MP4s failed because the card close-up included clipped body copy and the complete answer was not held readably. New edits isolated the full card, then showed the complete answer, with a disclosed three-second final-frame reading hold. Fresh readers passed both. The two Atelier MP4s passed without altering their video bytes. All four final files passed full decode and actual Chromium 1× playback to `ended`.

Keep detailed per-run receipts, media paths, account identifiers and private attachments outside this public distribution. The example is a method and failure pattern, not a production-release or new model-call claim.


### Observed final MP4 matrix

| Artifact | First full-film visual review | Repair | Final duration | Full decoder frames | Final independent review and player |
| --- | --- | --- | ---: | ---: | --- |
| Sidebar English | FAIL | Isolate card, show full reply, disclose final-frame hold | 14.03s | 421 | PASS |
| Sidebar Chinese | FAIL | Same composition fix using its own Chinese source | 13.67s | 410 | PASS |
| Atelier English | PASS | Retain identical video bytes | 19.43s | 583 | PASS |
| Atelier Chinese | PASS | Retain identical video bytes | 17.77s | 533 | PASS |

These are media QA observations, not proof of order-data correctness, new model calls, production deployment or a release gate. The complete final replies became separately readable for about 4.23s and 4.07s in the repaired Sidebar edits. Their original raw recordings were unchanged.
