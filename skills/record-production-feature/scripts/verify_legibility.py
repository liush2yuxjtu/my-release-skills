#!/usr/bin/env python3
"""Fail-closed, region-bound legibility checks on a delivered GIF's native pixels.

Usage: verify_legibility.py GIF NEW_OUTPUT_DIR LABEL --spec spec.json
LEGIBILITY_SPEC is retained as a fallback. See references/legibility-spec.md.
OCR upscaling is recognition-only. Pixel measurements always use a declared native
glyph crop at the beat frame; auxiliary windows cannot repair that frame's FAIL.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import unicodedata
import uuid
from decimal import Decimal

PIL_IMPORT_ERROR = None
try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError as error:
    PIL_IMPORT_ERROR = str(error)


SCHEMA_VERSION = 2
ROLE_MINIMUMS = {"hero": ("cap_height", 16), "control": ("x_height", 9),
                 "cta": ("x_height", 7), "supporting": ("x_height", 7)}
X_HEIGHT_LETTERS = frozenset("acemnorsuvwxz")
TSV_HEADER = "level page_num block_num par_num line_num word_num left top width height conf text".split()


class VerificationError(ValueError):
    """Missing or unverifiable evidence; never an automatic PASS."""


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_token(value):
    value = unicodedata.normalize("NFKC", value).replace("’", "'").strip()
    while value and unicodedata.category(value[0]).startswith("P"):
        value = value[1:]
    while value and unicodedata.category(value[-1]).startswith("P"):
        value = value[:-1]
    return value.casefold()


def rectangle(value, name, size):
    if not isinstance(value, list) or len(value) != 4 or any(type(v) is not int for v in value):
        raise VerificationError(f"{name} must be [x, y, width, height] in integer delivered pixels")
    x, y, width, height = value
    if min(x, y) < 0 or min(width, height) <= 0 or x + width > size[0] or y + height > size[1]:
        raise VerificationError(f"{name} is empty or outside the delivered frame")
    return value


def contains(outer, inner, tolerance=0):
    x, y, width, height = outer
    a, b, w, h = inner
    return (a >= x - tolerance and b >= y - tolerance and
            a + w <= x + width + tolerance and b + h <= y + height + tolerance)


def crop_box(rect):
    x, y, width, height = rect
    return x, y, x + width, y + height


def native_rgb(path):
    with Image.open(path) as image:
        return image.convert("RGB")


def cjk_languages(glyph):
    codepoint = ord(glyph)
    if 0x3400 <= codepoint <= 0x9FFF or 0x20000 <= codepoint <= 0x323AF:
        return {"chi_sim", "chi_tra", "jpn", "jpn_vert", "kor", "kor_vert"}
    if 0x3040 <= codepoint <= 0x30FF:
        return {"jpn", "jpn_vert"}
    if 0xAC00 <= codepoint <= 0xD7AF:
        return {"kor", "kor_vert"}
    return set()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_spec(spec, size, label):
    if not isinstance(spec, dict) or type(spec.get("schema_version")) is not int or spec["schema_version"] != SCHEMA_VERSION:
        raise VerificationError("schema_version 2 with explicit semantic and glyph ROIs is required")
    if (spec.get("frame_size_px") != list(size) or not isinstance(spec["frame_size_px"], list) or
            any(type(value) is not int for value in spec["frame_size_px"])):
        raise VerificationError("frame_size_px must exactly match the delivered GIF's native dimensions")
    texts = spec.get("texts")
    if not isinstance(texts, list) or not texts:
        raise VerificationError("texts must be a nonempty list")
    languages = spec.get("ocr_languages", ["eng"])
    if (not isinstance(languages, list) or not languages or
            any(not isinstance(v, str) or not v or not all(c.isalnum() or c == "_" for c in v) for v in languages) or
            len(languages) != len(set(languages))):
        raise VerificationError("ocr_languages must name unique installed Tesseract languages")
    beat_maps = spec.get("beat_t_gif_s")
    if not isinstance(beat_maps, dict) or not isinstance(beat_maps.get(label), dict):
        raise VerificationError(f"Missing beat_t_gif_s map for label {label!r}")
    beats, ids = beat_maps[label], []
    for key in texts:
        if not isinstance(key, dict):
            raise VerificationError("Each text check must be an object")
        identifier = key.get("id")
        if (not isinstance(identifier, str) or not identifier or
                any(not (c.isascii() and (c.isalnum() or c in "_-")) for c in identifier) or identifier in ids):
            raise VerificationError("Text ids must be unique nonempty ASCII letters, numbers, underscores or hyphens")
        ids.append(identifier)
        for field in ("text", "region_name", "measure_word", "glyph_text"):
            if not isinstance(key.get(field), str) or not key[field].strip():
                raise VerificationError(f"{identifier}: {field} must be a nonempty string")
        semantic = rectangle(key.get("semantic_roi_px"), f"{identifier}.semantic_roi_px", size)
        glyph = rectangle(key.get("measure_roi_px"), f"{identifier}.measure_roi_px", size)
        if not contains(semantic, glyph):
            raise VerificationError(f"{identifier}: measure_roi_px must be inside semantic_roi_px")
        role, metric = key.get("role"), key.get("metric")
        if role not in ROLE_MINIMUMS:
            raise VerificationError(f"{identifier}: role must be hero, control, cta or supporting")
        threshold = key.get("threshold_px")
        if not number(threshold) or threshold <= 0:
            raise VerificationError(f"{identifier}: threshold_px must be positive")
        word, glyph_text = key["measure_word"], key["glyph_text"]
        if any(c.isspace() for c in word):
            raise VerificationError(f"{identifier}: measure_word must be one OCR token")
        if metric == "full_glyph_height":
            if (not isinstance(key.get("threshold_source"), str) or not key["threshold_source"].strip() or
                    glyph_text not in word or len(glyph_text) != 1 or not cjk_languages(glyph_text)):
                raise VerificationError(f"{identifier}: full_glyph_height needs one native CJK glyph and threshold_source")
            if not cjk_languages(glyph_text).intersection(languages):
                raise VerificationError(f"{identifier}: full_glyph_height needs the actual CJK OCR language in ocr_languages")
        else:
            expected_metric, minimum = ROLE_MINIMUMS[role]
            if metric != expected_metric or threshold < minimum:
                raise VerificationError(f"{identifier}: {role} requires {expected_metric} >= {minimum}px")
            if metric == "cap_height" and (len(glyph_text) != 1 or not glyph_text.isascii() or
                                            not glyph_text.isupper() or not word.startswith(glyph_text)):
                raise VerificationError(f"{identifier}: cap_height must crop the word's first capital letter")
            if metric == "x_height" and (not set(glyph_text) <= X_HEIGHT_LETTERS or glyph_text not in word):
                raise VerificationError(f"{identifier}: x_height glyph_text must select only x-height letters in measure_word")
        if "xh_slice" in key:
            raise VerificationError(f"{identifier}: xh_slice is obsolete; declare the native glyph measure_roi_px")
        tokens = key.get("ocr_tokens")
        if (not isinstance(tokens, list) or not tokens or
                any(not isinstance(token, str) or not normalize_token(token) or any(c.isspace() for c in token) for token in tokens)):
            raise VerificationError(f"{identifier}: ocr_tokens must be nonempty single-token strings")
        normalized = [normalize_token(token) for token in tokens]
        if len(normalized) != len(set(normalized)) or normalize_token(word) not in normalized:
            raise VerificationError(f"{identifier}: ocr_tokens must be unique and include measure_word")
        if key.get("ocr_min", 1.0) != 1.0:
            raise VerificationError(f"{identifier}: all required beat-frame tokens must match; ocr_min must be 1.0")
        times = key.get("t_window_s", [])
        if not isinstance(times, list) or any(not number(t) or t < 0 for t in times):
            raise VerificationError(f"{identifier}: t_window_s must contain nonnegative finite seconds")
        if not number(beats.get(identifier)) or beats[identifier] < 0:
            raise VerificationError(f"{identifier}: a nonnegative finite beat timestamp is required")
    if set(beats) != set(ids):
        raise VerificationError("The selected beat map must contain exactly the declared text ids")
    return languages


def decode_gif(media, output):
    """Pillow composites disposal frames; retain original positive per-frame delays."""
    frames, elapsed = [], 0
    output.mkdir()
    with Image.open(media) as gif:
        if gif.format != "GIF":
            raise VerificationError("Input must be the actual delivered GIF")
        size = gif.size
        for index in range(gif.n_frames):
            gif.seek(index)
            delay = gif.info.get("duration")
            if type(delay) is not int or delay <= 0:
                raise VerificationError(f"Frame {index + 1} has missing/nonpositive delay; playback time is unverifiable")
            image = gif.convert("RGB")
            if image.size != size:
                raise VerificationError("GIF frame dimensions changed")
            path = output / f"f{index + 1:05d}.png"
            image.save(path)
            frames.append({"frame": index + 1, "start_ms": elapsed, "end_ms": elapsed + delay,
                           "duration_ms": delay, "path": str(path)})
            elapsed += delay
    if not frames:
        raise VerificationError("GIF contains no frames")
    return size, frames


def frame_at_time(frames, seconds):
    timestamp = Decimal(str(seconds)) * 1000
    for frame in frames:
        if frame["start_ms"] <= timestamp < frame["end_ms"]:
            return frame
    raise VerificationError(f"Timestamp {seconds}s is outside the GIF's [0, {frames[-1]['end_ms'] / 1000})s playback")


def ocr_metadata(languages):
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True, timeout=10)
    installed = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=True, timeout=10)
    available = set(installed.stdout.splitlines()[1:])
    missing = set(languages) - available
    if missing:
        raise VerificationError("Requested OCR languages are unavailable: " + ", ".join(sorted(missing)))
    return {"engine": version.stdout.splitlines()[0], "languages": languages,
            "psm": [11, 6], "polarities": ["normal", "inverted"], "recognition_scale": 3}


def parse_tsv(tsv, crop_size, pass_name):
    lines = tsv.splitlines()
    if not lines or lines[0].lstrip("\ufeff").split("\t") != TSV_HEADER:
        raise VerificationError(f"OCR {pass_name}: missing/invalid TSV header (check Tesseract configs/tsv)")
    words = []
    for line in lines[1:]:
        if not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) != len(TSV_HEADER):
            raise VerificationError(f"OCR {pass_name}: malformed TSV row")
        try:
            level, x, y, width, height = (int(columns[i]) for i in (0, 6, 7, 8, 9))
            confidence = float(columns[10])
        except ValueError as error:
            raise VerificationError(f"OCR {pass_name}: nonnumeric TSV geometry/confidence") from error
        if not math.isfinite(confidence) or not -1 <= confidence <= 100 or not 1 <= level <= 5:
            raise VerificationError(f"OCR {pass_name}: invalid TSV confidence/level")
        text = columns[11].strip()
        if level != 5 or confidence < 0 or not text:
            continue
        if (min(x, y) < 0 or min(width, height) <= 0 or
                x + width > crop_size[0] * 3 or y + height > crop_size[1] * 3):
            raise VerificationError(f"OCR {pass_name}: word box outside recognition crop")
        words.append({"text": text, "conf": confidence,
                      "box_px": [v / 3 for v in (x, y, width, height)], "ocr_pass": pass_name})
    return words


def run_ocr(image, output, languages):
    words = []
    big = image.convert("L").resize((image.width * 3, image.height * 3), Image.Resampling.LANCZOS)
    for polarity, recognition in (("normal", big), ("inverted", ImageOps.invert(big))):
        path = output / f"recognition-{polarity}-3x.png"
        recognition.save(path)
        for psm in (11, 6):
            name = f"{polarity}-psm{psm}"
            result = subprocess.run(["tesseract", str(path), "-", "-l", "+".join(languages),
                                     "--psm", str(psm), "tsv"], capture_output=True, text=True, timeout=30)
            (output / f"ocr-{name}.tsv").write_text(result.stdout, encoding="utf-8")
            (output / f"ocr-{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
            if result.returncode or any(error in result.stderr.lower() for error in
                                        ("error", "failed loading", "can't open", "read_params_file")):
                raise VerificationError(f"OCR {name} failed (exit {result.returncode}): {result.stderr.strip()[:2000]}")
            words.extend(parse_tsv(result.stdout, image.size, name))
    return words


def same_location(first, second):
    a, b = first["box_px"], second["box_px"]
    overlap = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])) * max(
        0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return overlap >= 0.6 * min(a[2] * a[3], b[2] * b[3])


def occurrences(words, token):
    """Deduplicate repeated OCR passes, never choose the largest duplicate's ink."""
    groups = []
    for word in words:
        if normalize_token(word["text"]) != normalize_token(token):
            continue
        group = next((group for group in groups if all(same_location(word, other) for other in group)), None)
        if group is None:
            groups.append([word])
        else:
            group.append(word)
    return [{"box_px": [statistics.median(word["box_px"][i] for word in group) for i in range(4)],
             "observations": group} for group in groups]


def measure_ink(image, metric="x_height"):
    """Measure declared glyph ink at native size; clipped/contaminated crops fail."""
    gray = image.convert("L")
    width, height = gray.size
    if width < 2 or height < 3:
        raise VerificationError("Glyph crop needs at least two columns and vertical background padding")
    pixels = gray.load()
    border = [pixels[x, y] for x in range(width) for y in (0, height - 1)]
    if metric == "full_glyph_height":
        border += [pixels[x, y] for y in range(1, height - 1) for x in (0, width - 1)]
    modal_bin = Counter(value // 16 for value in border).most_common(1)[0][0]
    background = statistics.median(value for value in border if value // 16 == modal_bin)
    difference = [abs(value - background) for value in gray.tobytes()]
    threshold = max(40, 0.5 * max(difference))
    mask = Image.new("L", gray.size)
    mask.putdata([255 if value > threshold else 0 for value in difference])
    bounds = mask.getbbox()
    details = {"background_gray": background, "contrast_cutoff": threshold,
               "ink_box_in_crop_px": list(bounds) if bounds else None, "measured_px": None}
    if bounds is None:
        details["error"] = "No verifiable contrasting glyph ink"
    elif bounds[1] == 0 or bounds[3] == height or (metric == "full_glyph_height" and
                                                (bounds[0] == 0 or bounds[2] == width)):
        details["error"] = "Glyph ink touches crop edge; clipping or a neighbouring edge is unverifiable"
    else:
        rows = [y for y in range(bounds[1], bounds[3]) if mask.crop((0, y, width, y + 1)).getbbox()]
        if metric != "full_glyph_height" and len(rows) != bounds[3] - bounds[1]:
            details["error"] = "Disjoint ink rows; glyph crop is fragmented or contaminated"
        else:
            details["measured_px"] = bounds[3] - bounds[1]
    return details, mask


def observe(frame, seconds, key, output, languages, engine, measure):
    output.mkdir(parents=True)
    image = native_rgb(frame["path"])
    semantic, glyph = key["semantic_roi_px"], key["measure_roi_px"]
    region = image.crop(crop_box(semantic))
    region.save(output / "semantic-native.png")
    native_glyph = image.crop(crop_box(glyph))
    native_glyph.save(output / "glyph-native.png")
    result = {"t_gif_s": seconds, "frame": frame["frame"], "frame_start_ms": frame["start_ms"],
              "frame_end_ms": frame["end_ms"], "semantic_roi_px": semantic, "measure_roi_px": glyph,
              "measurement_performed": measure, "measured_px": None, "selected_word_box_px": None,
              "proof_dir": str(output), "errors": []}
    if measure:
        details, mask = measure_ink(native_glyph, key["metric"])
        mask.save(output / "glyph-ink-mask.png")
        result["ink_measurement"] = details
    words = engine(region, output, languages)
    for word in words:
        word["box_px"] = [word["box_px"][0] + semantic[0], word["box_px"][1] + semantic[1],
                          *word["box_px"][2:]]
        if not contains(semantic, word["box_px"], 0.01):
            raise VerificationError("OCR engine returned a box outside the declared semantic ROI")
    token_locations = {token: occurrences(words, token) for token in key["ocr_tokens"]}
    result["token_locations"] = token_locations
    result["ocr_found"] = [token for token, locations in token_locations.items() if locations]
    result["ocr_missing"] = [token for token, locations in token_locations.items() if not locations]
    result["ocr_ambiguous"] = [token for token, locations in token_locations.items() if len(locations) > 1]
    result["ocr_ratio"] = len(result["ocr_found"]) / len(key["ocr_tokens"])
    result["pass_ocr"] = not result["ocr_missing"] and not result["ocr_ambiguous"]
    selected = occurrences(words, key["measure_word"])
    if len(selected) == 1:
        box = selected[0]["box_px"]
        if measure:
            details = result["ink_measurement"]
            ink_box = details["ink_box_in_crop_px"]
            if ink_box:
                native_ink_box = [glyph[0] + ink_box[0], glyph[1] + ink_box[1],
                                  ink_box[2] - ink_box[0], ink_box[3] - ink_box[1]]
                result["measured_ink_box_px"] = native_ink_box
                if not contains(box, native_ink_box, tolerance=1):
                    result["errors"].append("Declared glyph ink is outside the selected OCR word box")
                elif details.get("error"):
                    result["errors"].append(details["error"])
                else:
                    result["selected_word_box_px"] = box
                    result["measured_px"] = details["measured_px"]
            else:
                result["errors"].append(details["error"])
        else:
            result["selected_word_box_px"] = box
    else:
        result["errors"].append("measure_word has no unique physical occurrence in the semantic ROI")
    if result["ocr_ambiguous"]:
        result["errors"].append("Duplicate token locations are ambiguous; tighten the semantic ROI")
    if result["ocr_missing"]:
        result["errors"].append("Required tokens are missing from the declared semantic ROI")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(crop_box(semantic), outline="lime", width=1)
    draw.rectangle(crop_box(glyph), outline="orange", width=1)
    for locations in token_locations.values():
        for location in locations:
            draw.rectangle(crop_box(location["box_px"]), outline="magenta", width=1)
    overlay.save(output / "selected-boxes-native.png")
    return result


def contact_strip(checks, frames, output, size):
    if not checks:
        return
    width, height = size
    strip = Image.new("RGB", (width, (height + 36) * len(checks)), (20, 20, 20))
    draw = ImageDraw.Draw(strip)
    for index, check in enumerate(checks):
        image = native_rgb(frames[check["frame"] - 1]["path"])
        offset = index * (height + 36)
        strip.paste(image, (0, offset + 36))
        draw.text((4, offset + 3), f"{check['id']} beat {check['t_gif_s']}s frame {check['frame']} "
                  f"{'PASS' if check['pass'] else 'FAIL'}", fill="white")
        draw.text((4, offset + 18), f"{check['metric']}={check['measured_px']}px >= {check['threshold_px']} "
                  f"OCR={check['ocr_ratio']:.2f}", fill="white")
    strip.save(output / "legibility-strip.png")


def new_output_directory(requested):
    """A collision creates a separate FAIL receipt, preserving every prior byte."""
    requested = Path(requested).resolve()
    try:
        requested.mkdir(parents=True, exist_ok=False)
        return requested, None
    except OSError as error:
        message = f"Cannot create fresh output directory {requested}: {error}"
        candidate = requested.with_name(requested.name + ".failed-" + uuid.uuid4().hex[:12])
        try:
            candidate.mkdir(parents=True, exist_ok=False)
        except OSError:
            candidate = Path(tempfile.mkdtemp(prefix="legibility-failure-"))
        return candidate, message


def inspect(media, output, label, spec_path=None, *, ocr_engine=None):
    output, collision = new_output_directory(output)
    media = Path(media).resolve()
    spec_path = Path(spec_path or os.environ.get("LEGIBILITY_SPEC") or
                     Path(__file__).with_name("legibility_spec.json")).resolve()
    result = {"schema_version": SCHEMA_VERSION, "gif": str(media), "label": label,
              "evidence_dir": str(output), "spec_path": str(spec_path), "pass": False,
              "machine_verdict": "FAIL", "visual_verdict": "pending", "checks": [],
              "method": "Exact unique OCR tokens within each semantic ROI; declared native glyph ink at the beat frame. "
                        "OCR 3x resize is recognition-only. Auxiliary OCR never replaces beat evidence."}
    try:
        if collision:
            raise VerificationError(collision)
        if PIL_IMPORT_ERROR:
            raise VerificationError("Pillow dependency unavailable: " + PIL_IMPORT_ERROR)
        result["sha256"] = hashlib.sha256(media.read_bytes()).hexdigest()
        spec_bytes = spec_path.read_bytes()
        result["spec_sha256"] = hashlib.sha256(spec_bytes).hexdigest()
        (output / "spec-input.json").write_bytes(spec_bytes)
        spec = json.loads(spec_bytes, object_pairs_hook=no_duplicate_keys)
        size, frames = decode_gif(media, output / "frames")
        result.update(size=list(size), frames=len(frames), duration_ms=frames[-1]["end_ms"],
                      frame_timing_ms=[{k: value for k, value in frame.items() if k != "path"} for frame in frames])
        languages = validate_spec(spec, size, label)
        # Validate every requested time before producing any successful per-check result.
        for key in spec["texts"]:
            for seconds in [spec["beat_t_gif_s"][label][key["id"]], *key.get("t_window_s", [])]:
                frame_at_time(frames, seconds)
        result["ocr"] = (ocr_metadata(languages) if ocr_engine is None else
                         {"engine": "injected test callable", "languages": languages})
        engine = ocr_engine or run_ocr
        for key in spec["texts"]:
            seconds = spec["beat_t_gif_s"][label][key["id"]]
            beat = observe(frame_at_time(frames, seconds), seconds, key, output / "checks" / key["id"] / "beat",
                           languages, engine, measure=True)
            auxiliary = []
            seen_frames = {beat["frame"]}
            for time_s in key.get("t_window_s", []):
                frame = frame_at_time(frames, time_s)
                if frame["frame"] not in seen_frames:
                    auxiliary.append(observe(frame, time_s, key, output / "checks" / key["id"] /
                                             f"aux-frame-{frame['frame']:05d}", languages, engine, measure=False))
                    seen_frames.add(frame["frame"])
            pass_px = beat["measured_px"] is not None and beat["measured_px"] >= key["threshold_px"]
            check = {"id": key["id"], "text": key["text"], "region_name": key["region_name"],
                     "role": key["role"], "metric": key["metric"], "threshold_px": key["threshold_px"],
                     "glyph_text": key["glyph_text"], "measure_word": key["measure_word"], **beat,
                     "beat_frame_measured": True, "pass_px": pass_px,
                     "pass": pass_px and beat["pass_ocr"] and not beat["errors"],
                     "auxiliary_observations": auxiliary,
                     "ocr_full_match_frames": [item["frame"] for item in [beat, *auxiliary] if item["pass_ocr"]]}
            if "threshold_source" in key:
                check["threshold_source"] = key["threshold_source"]
            result["checks"].append(check)
        contact_strip(result["checks"], frames, output, size)
        result["pass"] = bool(result["checks"]) and all(check["pass"] for check in result["checks"])
        result["machine_verdict"] = "PASS" if result["pass"] else "FAIL"
    except Exception as error:
        # This is the receipt boundary: unexpected decoder/OCR errors must retain FAIL too.
        result["error"] = f"{type(error).__name__}: {error}"
        result["pass"] = False
        result["machine_verdict"] = "FAIL"
    finally:
        if "sha256" in result:
            try:
                result["sha256_after"] = hashlib.sha256(media.read_bytes()).hexdigest()
                result["source_unchanged"] = result["sha256_after"] == result["sha256"]
                if not result["source_unchanged"]:
                    raise VerificationError("Delivered GIF changed during verification; evidence is not bound to one source")
            except Exception as error:
                result["source_unchanged"] = False
                result["source_integrity_error"] = f"{type(error).__name__}: {error}"
                result["pass"] = False
                result["machine_verdict"] = "FAIL"
    write_json(output / "legibility.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gif")
    parser.add_argument("output", help="Fresh evidence directory; existing evidence is never overwritten")
    parser.add_argument("label", help="Key in beat_t_gif_s")
    parser.add_argument("--spec", help="Version 2 spec; falls back to LEGIBILITY_SPEC then adjacent legibility_spec.json")
    arguments = parser.parse_args(argv)
    report = inspect(arguments.gif, arguments.output, arguments.label, arguments.spec)
    print(json.dumps({"machine_verdict": report["machine_verdict"], "evidence_dir": report["evidence_dir"],
                      "error": report.get("error") or report.get("source_integrity_error"), "checks": [
                          {field: check[field] for field in ("id", "measured_px", "ocr_ratio", "frame", "pass")}
                          for check in report["checks"]]}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
