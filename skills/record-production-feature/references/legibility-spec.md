# Delivered GIF legibility spec, version 2

Run against the actual delivery bytes, writing a fresh evidence directory:

```sh
python scripts/verify_legibility.py delivery.gif verify/legibility-take2 take2 --spec run/legibility-spec.json
```

`--spec` takes precedence over `LEGIBILITY_SPEC`; otherwise the script looks for
`legibility_spec.json` beside itself. The adjacent example is illustrative schema
geometry, never a ready-made product receipt. Old full-frame specs fail closed;
they must be re-annotated from the native delivered frames.

## Required source and text fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `2`. |
| `frame_size_px` | Exact native GIF `[width, height]`; no CSS, screenshot, or OCR-upscale coordinates. |
| `ocr_languages` | Tesseract model names, e.g. `["eng"]` or `["eng", "chi_sim"]`. Every requested model must be installed. Defaults to `eng`. |
| `texts` | Nonempty list of the checks below. Empty checks cannot PASS. |
| `beat_t_gif_s[label][id]` | Seconds within the GIF's first playback, one timestamp per check. |
| `texts[].id` | Unique ASCII letters, numbers, `_` and `-`. |
| `text`, `region_name` | Expected text and a human-readable name of its intended product region. |
| `role` | `hero`, `control`, `cta` or `supporting`. Select the role from the actual function in the story; an operated control is always `control`. |
| `metric`, `threshold_px` | Hero `cap_height >=16`; control `x_height >=9`; CTA/supporting `x_height >=7`. Larger requirements are allowed. The script refuses lower Latin thresholds. |
| `semantic_roi_px` | `[x, y, width, height]` around this one semantic region. Every required OCR token must occur inside it. Exclude similar text elsewhere. |
| `measure_roi_px` | Native glyph crop inside the semantic ROI, with background padding above/below. It must contain only the declared glyph's appropriate height, not the whole word, another line, or a border. |
| `measure_word` | One exact OCR token in this region, also included in `ocr_tokens`. The glyph ink must lie inside its selected OCR word box (1px raster tolerance). |
| `glyph_text` | Capital metric: the word's first uppercase ASCII letter. X-height: a substring using only `acemnorsuvwxz`; exclude capitals, ascenders, descenders, punctuation and dots. |
| `ocr_tokens` | Nonempty, unique exact required tokens. Case and surrounding punctuation are normalized; substring/fuzzy matches are rejected. |
| `ocr_min` | Optional; only `1.0` is accepted. All required tokens must match on the beat. |
| `t_window_s` | Optional auxiliary OCR times. These observations are recorded separately and never contribute a glyph measurement or replace a failing beat. |

Use the crop's actual glyph ink, not its bounding-box height. Latin glyph crops
may bound horizontal columns of the declared glyph; preserve clean background
above and below and enough stroke width to cover every ink row. A crop touching
ink at its top/bottom, containing separated ink-row runs, or lacking contrasting
ink is unverifiable. Full-glyph CJK crops require background on all four sides.
The old proportional `xh_slice` approximation is rejected.

The machine checks spatial containment and physical duplicate locations. It cannot
prove that a human-declared rectangle is the intended product widget, or that a
chosen vertical slice represents the declared character. Review the native full
frame, semantic crop, glyph crop, mask and selected boxes together. Do not move a
crop onto a larger reply or relabel a control as supporting text to manufacture a
PASS. If one required token occurs at multiple physical locations inside the
semantic ROI, verification fails as ambiguous; annotate the intended region more
precisely. Multiple OCR passes at the same location are deduplicated, never ranked
by their largest ink height. Required tokens from another region cannot satisfy
the check.

## Timing, evidence, and failure behavior

GIF frame selection uses the actual positive per-frame delays, with intervals
`[frame_start_ms, frame_end_ms)`. A timestamp exactly at a boundary selects the
next frame; a timestamp at or beyond the total duration fails. `gif_fps`, if
retained as nominal metadata in a migrated spec, never determines frame selection.
Missing/zero delays fail rather than guessing how a player renders them.

`legibility.json` records the source and archived spec hashes, source rehash after
verification, all frame timings, selected physical OCR word boxes, token location
candidates, native measured ink box, beat results and auxiliary observations.
Each check's proof directory preserves `semantic-native.png`, `glyph-native.png`,
the beat's `glyph-ink-mask.png`, `selected-boxes-native.png`, recognition-only 3x
crops, and the raw TSV/error output for every OCR pass. Original decoded frames
and the beat contact strip remain at delivered pixel dimensions. Cumulative row
coordinates in the strip are presentation only; measurement uses untouched native
frame pixels.

Missing files/specs/models, malformed TSV, OCR failures/timeouts, ambiguous matches,
invalid geometry, changed source bytes, and failed thresholds retain machine
`FAIL` and a nonzero CLI exit. OCR metadata calls are bounded to 10s each; each OCR
pass to 30s. `visual_verdict` remains `pending` even when machine checks PASS. A
machine PASS establishes neither native playback quality nor story comprehension.

Earlier evidence is never overwritten. If the requested output already exists or
cannot be created, the script returns nonzero and writes a separate uniquely
named failure directory; stdout names its actual `evidence_dir`. If the parent is
unwritable, the failure receipt uses a new temporary directory. Runtime errors can
leave partial crops, but never convert missing checks to PASS. Unit tests create
isolated graphics solely to exercise the verifier; they are not model-execution,
product-runtime or release evidence.

## Native Chinese, Japanese, and Korean

Latin cap-height/x-height measurements do not apply to native CJK. Use
`metric: "full_glyph_height"`, one native CJK `glyph_text` inside `measure_word`,
a positive `threshold_px`, and a concrete `threshold_source` explaining that
full-glyph requirement. Supply the appropriate actual OCR models in
`ocr_languages` (e.g. `chi_sim`/`chi_tra` for Chinese, `jpn` for Japanese, `kor`
for Korean). The metric stays distinct in the receipt. Full glyphs may contain
separated strokes; measure their complete native ink extent, with padding on all
four sides. This route does not redefine the Latin 16/9/7 thresholds.

If the required model/config is unavailable, or native typography remains an OCR
false negative, retain the machine FAIL and exact native ROI/frame/crop evidence.
A separate named independent reader may transcribe every required character and
adjudicate that evidence explicitly, following the independent-review route in
the skill. Keep the reviewer, transcription, glyph/ROI measurements, reason and
scope of the exception. This is a separate visual adjudication, never an invented
OCR PASS or an overwritten machine receipt. Other scripts/metrics unsupported by
this verifier remain blocked for automation and need an explicit independent
exact-text/ROI review.
