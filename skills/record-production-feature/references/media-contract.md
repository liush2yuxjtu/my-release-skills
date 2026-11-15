# Media manifest and executable contract

The package's encoder transforms existing local source bytes. It does not record a UI, call a model, implement replay, create runtime markers, reconstruct missing originals, or decide whether a story is true or readable. Use it after discovery and an actual recorded take. Keep private run evidence outside this public package.

## Check the selected route first

Run from the skill directory, using the real project for `--project`:

```bash
python3 scripts/preflight.py --phase encode --format both --execution-route work --project .
python3 scripts/build_feature_media.py --help
```

Preflight always emits `feature-media-preflight/v1` JSON and exits 1 on concrete gaps. `dependencies-ready` means the requested layer's dependencies were found; the `unassessed` list remains. `--phase record` additionally checks Node, project-local Playwright and an existing Chromium executable. `--phase verify --format mp4` checks the actual Node playback route; GIF verification checks Pillow, Tesseract 5 and `--ocr-languages eng` (use the actual language codes, joined with `+`). GIF encoding does not require Node, Playwright or OCR.

`--execution-route work` supports actual Cloud/Work hosts on Linux or macOS. `mac-mini` requires actual Darwin. `--expected-host` optionally asserts the measured hostname; the script never substitutes one. The default space check is 10 GiB. `PLAYWRIGHT_MODULE_PATH` can select an existing module directory/entry by filesystem path (relative to the actual project or absolute; package name overrides are unsupported). `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` can select an existing browser executable. Preflight and playback use the same resolver; absent an override they resolve project-local `playwright`. Preflight does not install or launch them, authenticate, inspect model access or certify UI operation.

## Input: `feature-media/v1`

Copy [feature.template.json](../assets/feature.template.json) into the run as `feature.json`. Its nulls/placeholders deliberately do not pass validation. All input paths resolve relative to that manifest's directory. Freeze the SHA-256 of actual bytes before editing.

| Field | Meaning |
| --- | --- |
| `schema` | Exactly `feature-media/v1`. |
| `feature_id`, `run_id` | One visible result and this edit's identity. A recut is a new edit, not a new model invocation. |
| `source.path`, `source.sha256` | Existing immutable source and its actual SHA-256. Source bytes are read, never moved, rewritten or chmodded. |
| `source.kind` | `full-recording` or `existing-derivative`, explicitly chosen from provenance. |
| `source.complete` | `true` is required for full MP4. A GIF, still image or existing excerpt cannot replace a missing complete original. |
| `source.origin_raw_sha256` | For a model-dependent existing derivative, its documented original raw hash, matching the original model evidence. It is not proof that the unavailable original has been inspected. |
| `model_execution` | Explicit existing summary or `null`; never inferred as live. See below. |
| `no_inference_reason` | Required observed reason when `model_execution=null`; a prefilled/generated result is not a no-model operation. |
| `proof_interval_s` | `[start,end]` in actual source-video seconds, at least 3 continuous seconds. The GIF must contain all of it. This declares the intended result interval; encoding does not prove readability. |
| `mp4` | Optional `crop_px:[x,y,w,h]`, `width` (even). Defaults to the full frame at the source crop width rounded down to even. Full duration and all source audio streams are retained; audio is encoded as AAC. |
| `gif` | `start_s` (default 0), `duration_s` (8), `width` (520), `fps` (12), `max_bytes` (3 MiB), optional `crop_px`. Explicit widths are allowed; verify actual delivery size. |
| `ui_language`, evidence and take metadata | Preserve observed production, language, discovery/rehearsal, marker, take and relevant cutout evidence. These are human/runtime inputs; the encoder does not fill them or promote them to PASS. |

Crop values use decoded source pixels, with origin at the top left. Bounds come from ffprobe, not a claimed viewport. The static crop and Lanczos scale are applied to pixels. Different per-format crops are allowed. Rotation must first be normalized into a separately preserved and declared source; the helper refuses implicit rotation.

The only edit timeline is a continuous interval at 1×: full source for MP4, one selected source window for GIF. No stitching, speed changes, generated frames, camera keyframes, synthetic pointer, annotation overlays or editorial holds are implemented. Unsupported per-format settings are rejected. A separate future editor must disclose and map any editorial reading hold; a hold cannot add recording time, runtime behavior or proof.

### Preserve model provenance and native replay disclosure

For model-dependent media, preserve the source `mode`, `run_id`, `evidence` and `disclosure`; declare `operation` as `fresh-recording`, `reuse`, `re-edit` or `replay-recording`. `evidence` names a real `feature-model-execution/v1` file relative to the run. `disclosure` is that file's label string. Fresh/replay recording summaries' current/source statuses must match that run's original evidence. Reuse/re-edit keeps the original evidence unchanged, adds a separate `edit_run_id`, sets this operation's `current_live_e2e=not-run`, and references the original verified live receipt in `source_live_e2e` (null leaves the source gate blocked). Historical live media remains mode `live`; recutting it does not imply a new live run. The helper rejects scripted/mock modes, inconsistent summaries, missing evidence and a raw hash that does not identify this source (or its explicit derivative origin). It hashes the evidence and records these limited checks. It does **not** authenticate the provider, review capture/request matching, verify real tools, or infer a new live run. Missing original logs remain a source/provenance gate; successful encoding cannot supply them.

Replay must retain `current_live_e2e=not-run`, the original `source_live_e2e.status=pass` reference, the exact label `Recorded model response · real tools` and an existing `disclosure.visible_evidence` file. Add:

```json
"replay_disclosure": {
  "source_rect_px": [0, 0, 640, 28],
  "min_output_height_px": 12
}
```

Replace this example rectangle with the observed native-label region. The helper refuses any crop that removes part of it and refuses scaling its region below the configured minimum (at least 12 px). This geometry does not establish glyph height or label visibility. Inspect the label's actual pixels through the entire relevant delivered interval and measure text at delivered size. Never add a label after cropping away native provenance, invent a live receipt, or rename replay as live.

## Build into a new version

```bash
python3 scripts/build_feature_media.py --manifest feature.json --output edits/v1 --execution-route work --format both --dry-run
python3 scripts/build_feature_media.py --manifest feature.json --output edits/v1 --execution-route work --format both
```

Use `--format mp4` or `gif` for the requested artifact alone. `--fixture` is solely for isolated synthetic codec tests, disallows model provenance, and labels every successful output `fixture-only`. It never authorizes synthetic product evidence. `--timeout-s` bounds each encoding attempt (default 300, maximum 3600). Dry-run validates paths, hash, schema, intervals, crop and model-summary consistency without creating outputs.

MP4 uses deterministic single-threaded H.264, yuv420p, CRF 18, AAC, stripped metadata and faststart. GIF uses palettegen/paletteuse, infinite looping and a recorded continuous source interval. It tries the requested FPS, then lower 10/8 FPS when applicable, while retaining every attempt. It does not silently shrink width to satisfy a budget. If all attempts exceed `max_bytes`, the build fails and keeps them. Review text after any FPS fallback. GIF frame sampling and centisecond delay rounding are disclosed; they are not a new timing/performance measurement. Reproducibility applies to the same source/settings and FFmpeg build; versions are recorded, and different encoder builds may differ.

The new output directory contains:

| Artifact | Purpose |
| --- | --- |
| `demo.mp4` | Complete recording derivative when requested and available. Never reconstructed from a GIF/excerpt. |
| `feature.gif` | Selected continuous preview; the name does not claim exactly 8 seconds when another duration was requested. |
| `input-manifest.json` | Exact frozen input manifest bytes. |
| `manifest.json` | Build receipt: source before/after hashes, encoder version, commands, bounded failures, output hashes/probes and continuous source-to-output maps. |
| `attempts/` and `*.stderr.txt` | Preserved budget attempts, partial failed encodes and diagnostics. |

Existing output paths are refused, including failed versions. Choose `edits/v2` for a repair. FFmpeg uses `-n`; no original or prior artifact is overwritten. Each attempt is hashed, even when it failed. Source bytes are hashed again after encoding; any change fails the build. Initial input-validation failures emit machine-readable `blocked` JSON without creating an output directory. Encoding failures retain `manifest.json` and all generated bytes. Exit 0 means a plan/encode completed, 1 means encoding failed or a known model failure remains blocked, and 2 means validation/dependency failure.

`needs-visual-review` is the highest non-fixture encoder result. Source provenance, model authenticity, production/live E2E, native disclosure readability, full decode, actual player completion, independent visual review, reading time and publication byte identity remain separate gates. Run [delivered-video-verification.md](delivered-video-verification.md) for each exact final MP4/GIF. Do not turn valid metadata, declared intervals or matching hashes into a visual/source/model PASS.
