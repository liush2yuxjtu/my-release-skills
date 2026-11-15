"""Fixture-only verifier tests. Generated glyphs are never product/model evidence."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image, ImageDraw, ImageFont


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_legibility.py"
module_spec = importlib.util.spec_from_file_location("verify_legibility", SCRIPT)
verify = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(verify)
FONT = next((path for path in (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
) if path.exists()), None)


class LegibilityChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gif = self.root / "fixture-only.gif"
        self.spec_path = self.root / "fixture-only-spec.json"
        self.output = self.root / "evidence"

    def save_gif(self, images=None, durations=None):
        images = images or [Image.new("RGB", (320, 160), "white")]
        images[0].save(self.gif, save_all=True, append_images=images[1:],
                       duration=durations or [1000] * len(images), loop=0)

    def base_spec(self, glyph_height=9):
        # Deliberately simple black shapes isolate native-height and ROI logic.
        image = Image.new("RGB", (320, 160), "white")
        ImageDraw.Draw(image).rectangle((20, 100, 27, 99 + glyph_height), fill="black")
        self.save_gif([image])
        return {"schema_version": 2, "frame_size_px": [320, 160], "ocr_languages": ["eng"],
                "texts": [{"id": "todo_count", "text": "completed", "region_name": "Fixture TODO summary",
                           "role": "supporting", "metric": "x_height", "threshold_px": 7,
                           "semantic_roi_px": [10, 90, 180, 50], "measure_roi_px": [19, 98, 10, glyph_height + 4],
                           "glyph_text": "m", "measure_word": "completed", "ocr_tokens": ["completed"],
                           "ocr_min": 1.0, "t_window_s": []}],
                "beat_t_gif_s": {"fixture": {"todo_count": 0.1}}}

    def engine(self, spec, full_frame_words):
        """Fixture OCR returns only words wholly contained in the supplied crop."""
        roi = spec["texts"][0]["semantic_roi_px"]

        def recognize(image, output, languages):
            self.assertEqual(image.size, tuple(roi[2:]))
            return [{"text": token, "conf": 99.0,
                     "box_px": [box[0] - roi[0], box[1] - roi[1], *box[2:]], "ocr_pass": name}
                    for token, box, name in full_frame_words if verify.contains(roi, box)]
        return recognize

    def inspect(self, spec, words=None, engine=None, output=None):
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        if engine is None:
            words = words or [("completed", [20, 100, 65, 9], "fixture-pass")]
            engine = self.engine(spec, words)
        return verify.inspect(self.gif, output or self.output, "fixture", self.spec_path, ocr_engine=engine)

    def test_larger_duplicate_outside_todo_roi_cannot_pass_small_native_glyph(self):
        spec = self.base_spec(glyph_height=6)
        image = verify.native_rgb(self.gif)
        ImageDraw.Draw(image).rectangle((20, 20, 50, 55), fill="black")
        self.save_gif([image])
        result = self.inspect(spec, [("completed", [20, 100, 65, 6], "small-todo"),
                                     ("completed", [20, 20, 200, 36], "large-reply")])
        check = result["checks"][0]
        self.assertFalse(result["pass"])
        self.assertTrue(check["pass_ocr"])
        self.assertEqual(check["measured_px"], 6)
        self.assertFalse(check["pass_px"])
        self.assertEqual(check["selected_word_box_px"], [20, 100, 65, 6])
        proof = Path(check["proof_dir"])
        self.assertEqual(verify.native_rgb(proof / "glyph-native.png").size, (10, 10))
        self.assertTrue((proof / "selected-boxes-native.png").exists())
        self.assertTrue((proof / "glyph-ink-mask.png").exists())

    def test_wrong_region_cannot_supply_required_tokens(self):
        spec = self.base_spec()
        result = self.inspect(spec, [("completed", [20, 20, 120, 20], "outside-intended-region")])
        check = result["checks"][0]
        self.assertFalse(result["pass"])
        self.assertEqual(check["ocr_missing"], ["completed"])
        self.assertEqual(check["ocr_ratio"], 0)
        self.assertIsNone(check["measured_px"])

    def test_duplicates_inside_semantic_roi_are_ambiguous_even_if_one_is_large(self):
        spec = self.base_spec()
        spec["texts"][0]["semantic_roi_px"] = [10, 10, 280, 140]
        result = self.inspect(spec, [("completed", [20, 100, 65, 9], "todo"),
                                     ("completed", [20, 20, 200, 36], "reply")])
        check = result["checks"][0]
        self.assertFalse(result["pass"])
        self.assertEqual(check["ocr_ambiguous"], ["completed"])
        self.assertEqual(len(check["token_locations"]["completed"]), 2)
        self.assertIsNone(check["selected_word_box_px"])

    def test_repeated_ocr_passes_at_one_location_are_one_occurrence(self):
        spec = self.base_spec()
        result = self.inspect(spec, [("completed", [20, 100, 65, 9], "normal-psm11"),
                                     ("completed", [20, 100, 65, 9], "inverted-psm6")])
        self.assertTrue(result["pass"], result)
        check = result["checks"][0]
        self.assertEqual(check["measured_px"], 9)
        self.assertEqual(len(check["token_locations"]["completed"]), 1)
        self.assertEqual(result["visual_verdict"], "pending")

    def test_measurement_must_belong_to_selected_word_in_same_region(self):
        spec = self.base_spec()
        spec["texts"][0]["semantic_roi_px"] = [10, 10, 280, 140]
        result = self.inspect(spec, [("completed", [20, 20, 120, 20], "wrong-word-location")])
        check = result["checks"][0]
        self.assertTrue(check["pass_ocr"])
        self.assertFalse(result["pass"])
        self.assertIsNone(check["measured_px"])
        self.assertIn("outside the selected OCR word", check["errors"][0])

    def test_exact_tokens_do_not_accept_substrings_or_fuzzy_similar_words(self):
        spec = self.base_spec()
        result = self.inspect(spec, [("uncompleted", [20, 100, 65, 9], "substring"),
                                     ("compieted", [20, 100, 65, 9], "fuzzy")])
        self.assertFalse(result["pass"])
        self.assertEqual(result["checks"][0]["ocr_ratio"], 0)

    def test_variable_frame_delays_and_exact_boundary_select_actual_frame(self):
        spec = self.base_spec(glyph_height=6)
        first = verify.native_rgb(self.gif)
        second, third = first.copy(), first.copy()
        ImageDraw.Draw(second).rectangle((300, 0, 310, 10), fill="blue")
        ImageDraw.Draw(third).rectangle((300, 0, 310, 10), fill="red")
        self.save_gif([first, second, third], [100, 700, 200])
        spec["gif_fps"] = 1000  # Intentionally wrong nominal metadata must have no effect.
        spec["beat_t_gif_s"]["fixture"]["todo_count"] = 0.1
        result = self.inspect(spec, [("completed", [20, 100, 65, 6], "fixture")])
        self.assertEqual([f["duration_ms"] for f in result["frame_timing_ms"]], [100, 700, 200])
        self.assertEqual(result["checks"][0]["frame"], 2)
        self.assertEqual(result["checks"][0]["frame_start_ms"], 100)
        self.assertEqual(verify.frame_at_time(result["frame_timing_ms"], 0.799)["frame"], 2)
        self.assertEqual(verify.frame_at_time(result["frame_timing_ms"], 0.8)["frame"], 3)
        with self.assertRaises(verify.VerificationError):
            verify.frame_at_time(result["frame_timing_ms"], 1.0)

    def test_auxiliary_ocr_success_never_repairs_beat_failure_or_measures_later_frame(self):
        spec = self.base_spec(glyph_height=6)
        first = verify.native_rgb(self.gif)
        second = first.copy()
        ImageDraw.Draw(second).rectangle((20, 100, 27, 115), fill="black")
        self.save_gif([first, second], [500, 500])
        spec["texts"][0]["t_window_s"] = [0.6]

        def engine(image, output, languages):
            if output.name == "beat":
                return []
            return [{"text": "completed", "box_px": [10, 10, 65, 16], "conf": 99, "ocr_pass": "fixture"}]

        result = self.inspect(spec, engine=engine)
        check = result["checks"][0]
        self.assertFalse(result["pass"])
        self.assertEqual(check["frame"], 1)
        self.assertEqual(check["ink_measurement"]["measured_px"], 6)
        self.assertEqual(check["ocr_full_match_frames"], [2])
        auxiliary = check["auxiliary_observations"][0]
        self.assertTrue(auxiliary["pass_ocr"])
        self.assertFalse(auxiliary["measurement_performed"])
        self.assertIsNone(auxiliary["measured_px"])
        self.assertNotIn("ink_measurement", auxiliary)

    def test_bad_or_missing_spec_fail_closed_with_receipt(self):
        base = self.base_spec()
        bad_specs = []
        for field, value in (("texts", []), ("schema_version", 1), ("frame_size_px", [640, 320])):
            broken = copy.deepcopy(base)
            broken[field] = value
            bad_specs.append(broken)
        for field, value in (("semantic_roi_px", None), ("measure_roi_px", [0, 0, 5, 5]),
                             ("threshold_px", 6), ("ocr_min", 0.8), ("glyph_text", "d")):
            broken = copy.deepcopy(base)
            broken["texts"][0][field] = value
            bad_specs.append(broken)
        broken = copy.deepcopy(base)
        broken["beat_t_gif_s"]["fixture"]["todo_count"] = 99
        bad_specs.append(broken)
        for index, broken in enumerate(bad_specs):
            with self.subTest(index=index):
                output = self.root / f"bad-{index}"
                result = self.inspect(broken, output=output, engine=lambda image, output, languages: [])
                self.assertFalse(result["pass"])
                self.assertIn("error", result)
                self.assertEqual(json.loads((output / "legibility.json").read_text())["machine_verdict"], "FAIL")
        missing = verify.inspect(self.gif, self.root / "missing-spec", "fixture", self.root / "absent.json")
        self.assertFalse(missing["pass"])
        self.assertTrue((self.root / "missing-spec/legibility.json").exists())

    def test_role_thresholds_cannot_be_weakened(self):
        for role, metric, minimum, word, glyph in (
            ("hero", "cap_height", 16, "Coffee", "C"),
            ("control", "x_height", 9, "completed", "m"),
            ("cta", "x_height", 7, "completed", "m"),
        ):
            spec = self.base_spec()
            key = spec["texts"][0]
            key.update(role=role, metric=metric, threshold_px=minimum - 1, measure_word=word,
                       glyph_text=glyph, ocr_tokens=[word])
            with self.subTest(role=role), self.assertRaises(verify.VerificationError):
                verify.validate_spec(spec, (320, 160), "fixture")

    def test_cjk_metric_is_distinct_and_requires_source_and_installed_language(self):
        spec = self.base_spec()
        key = spec["texts"][0]
        key.update(metric="full_glyph_height", measure_word="完成", glyph_text="完", ocr_tokens=["完成"])
        with self.assertRaises(verify.VerificationError):
            verify.validate_spec(spec, (320, 160), "fixture")
        key["threshold_source"] = "Fixture-only independently declared full-glyph requirement"
        with self.assertRaises(verify.VerificationError):
            verify.validate_spec(spec, (320, 160), "fixture")
        spec["ocr_languages"] = ["chi_sim"]
        self.assertEqual(verify.validate_spec(spec, (320, 160), "fixture"), ["chi_sim"])
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        listed = subprocess.CompletedProcess([], 0, "List of available languages (1):\neng\n", "")
        version = subprocess.CompletedProcess([], 0, "tesseract fixture\n", "")
        with mock.patch.object(verify.subprocess, "run", side_effect=[version, listed]):
            result = verify.inspect(self.gif, self.output, "fixture", self.spec_path)
        self.assertFalse(result["pass"])
        self.assertIn("unavailable", result["error"])

    def test_full_glyph_measurement_preserves_disconnected_cjk_strokes(self):
        glyph = Image.new("L", (14, 16), "white")
        draw = ImageDraw.Draw(glyph)
        draw.rectangle((2, 2, 11, 4), fill="black")
        draw.rectangle((2, 11, 11, 13), fill="black")
        details, _ = verify.measure_ink(glyph, "full_glyph_height")
        self.assertEqual(details["measured_px"], 12)
        latin_details, _ = verify.measure_ink(glyph, "x_height")
        self.assertIsNone(latin_details["measured_px"])

    def test_existing_evidence_is_preserved_and_collision_has_own_fail_receipt(self):
        spec = self.base_spec()
        first = self.inspect(spec)
        previous = {path.relative_to(self.output): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        second = self.inspect(spec)
        self.assertTrue(first["pass"])
        self.assertFalse(second["pass"])
        self.assertNotEqual(second["evidence_dir"], first["evidence_dir"])
        self.assertTrue((Path(second["evidence_dir"]) / "legibility.json").exists())
        current = {path.relative_to(self.output): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(previous, current)

    def test_bad_tsv_and_nonzero_ocr_exit_are_not_empty_successful_runs(self):
        with self.assertRaises(verify.VerificationError):
            verify.parse_tsv("completed\n", (100, 20), "fixture")
        spec = self.base_spec()
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        for index, process in enumerate((subprocess.CompletedProcess([], 0, "completed\n", ""),
                                         subprocess.CompletedProcess([], 1, "", "Failed loading language"))):
            with self.subTest(index=index), mock.patch.object(verify.subprocess, "run", return_value=process):
                result = verify.inspect(self.gif, self.root / f"ocr-error-{index}", "fixture", self.spec_path,
                                        ocr_engine=verify.run_ocr)
            self.assertFalse(result["pass"])
            self.assertIn("OCR", result["error"])
            self.assertTrue((Path(result["evidence_dir"]) / "legibility.json").exists())

    def test_missing_media_and_invalid_json_get_nonzero_cli_and_fail_receipt(self):
        spec = self.base_spec()
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        for index, source in enumerate((self.root / "absent.gif", self.gif)):
            if index == 1:
                self.spec_path.write_text('{"schema_version": 2, "schema_version": 2}', encoding="utf-8")
            output = self.root / f"cli-fail-{index}"
            process = subprocess.run([sys.executable, str(SCRIPT), str(source), str(output), "fixture",
                                      "--spec", str(self.spec_path)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 1, process.stderr)
            self.assertEqual(json.loads((output / "legibility.json").read_text())["machine_verdict"], "FAIL")

    def test_missing_pillow_writes_fail_receipt_instead_of_import_traceback(self):
        self.base_spec()
        process = subprocess.run([sys.executable, "-S", str(SCRIPT), str(self.gif), str(self.output),
                                  "fixture", "--spec", str(self.spec_path)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 1, process.stderr)
        receipt = json.loads((self.output / "legibility.json").read_text())
        self.assertIn("Pillow dependency unavailable", receipt["error"])
        self.assertEqual(receipt["machine_verdict"], "FAIL")
        self.assertNotIn("Traceback", process.stderr)

    def test_source_change_during_ocr_invalidates_otherwise_passing_evidence(self):
        spec = self.base_spec()
        recognize = self.engine(spec, [("completed", [20, 100, 65, 9], "fixture")])

        def mutate(image, output, languages):
            # Even a decoder-ignored trailing byte must change the source binding.
            with self.gif.open("ab") as stream:
                stream.write(b"fixture-only mutation")
            return recognize(image, output, languages)

        result = self.inspect(spec, engine=mutate)
        self.assertTrue(result["checks"][0]["pass"])
        self.assertFalse(result["pass"])
        self.assertFalse(result["source_unchanged"])
        self.assertNotEqual(result["sha256"], result["sha256_after"])
        self.assertIn("changed during verification", result["source_integrity_error"])

    def test_ocr_timeout_retains_fail_receipt(self):
        spec = self.base_spec()
        with mock.patch.object(verify.subprocess, "run", side_effect=subprocess.TimeoutExpired("tesseract", 30)):
            result = self.inspect(spec, engine=verify.run_ocr)
        self.assertFalse(result["pass"])
        self.assertIn("TimeoutExpired", result["error"])
        self.assertTrue((self.output / "legibility.json").exists())

    def test_zero_or_missing_gif_delay_is_unverifiable(self):
        spec = self.base_spec()
        image = verify.native_rgb(self.gif)
        image.info.clear()
        image.save(self.gif, format="GIF")
        result = self.inspect(spec)
        self.assertFalse(result["pass"])
        self.assertIn("delay", result["error"])

    @unittest.skipUnless(shutil.which("tesseract") and FONT, "Actual Tesseract and a fixture font required")
    def test_actual_ocr_large_reply_duplicate_cannot_inflate_small_todo_height(self):
        image = Image.new("RGB", (520, 200), "white")
        draw = ImageDraw.Draw(image)
        large = ImageFont.truetype(str(FONT), 36)
        small = ImageFont.truetype(str(FONT), 11)
        draw.text((20, 60), "completed", font=large, fill="black", anchor="ls")
        draw.text((20, 150), "completed", font=small, fill="black", anchor="ls")
        self.save_gif([image])
        # Crop the native m's vertical ink. Neighboring ascenders/descenders stay outside.
        start = 20 + small.getlength("co")
        box = draw.textbbox((start, 150), "m", font=small, anchor="ls")
        glyph = [math.ceil(box[0]), box[1] - 2, max(2, math.floor(box[2]) - math.ceil(box[0]) - 1), box[3] - box[1] + 4]
        spec = {"schema_version": 2, "frame_size_px": [520, 200], "ocr_languages": ["eng"],
                "texts": [{"id": "todo", "text": "completed", "region_name": "Fixture small TODO row",
                           "role": "supporting", "metric": "x_height", "threshold_px": 7,
                           "semantic_roi_px": [10, 125, 130, 45], "measure_roi_px": glyph,
                           "glyph_text": "m", "measure_word": "completed", "ocr_tokens": ["completed"]}],
                "beat_t_gif_s": {"fixture": {"todo": 0.1}}}
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        result = verify.inspect(self.gif, self.output, "fixture", self.spec_path)
        self.assertNotIn("error", result, result)
        check = result["checks"][0]
        self.assertTrue(check["pass_ocr"], check)
        self.assertLess(check["measured_px"], 7)
        self.assertFalse(result["pass"])
        self.assertGreater(check["selected_word_box_px"][1], 125)
        proof = Path(check["proof_dir"])
        self.assertEqual(verify.native_rgb(proof / "semantic-native.png").size, (130, 45))
        self.assertTrue((proof / "ocr-normal-psm11.tsv").exists())
        # A blank intended region must not borrow the large word elsewhere either.
        blank = copy.deepcopy(spec)
        blank["texts"][0]["semantic_roi_px"] = [250, 125, 130, 45]
        blank["texts"][0]["measure_roi_px"] = [260, 135, 10, 20]
        self.spec_path.write_text(json.dumps(blank), encoding="utf-8")
        wrong = verify.inspect(self.gif, self.root / "wrong-region", "fixture", self.spec_path)
        self.assertFalse(wrong["pass"])
        self.assertEqual(wrong["checks"][0]["ocr_missing"], ["completed"])
        # The same exact OCR/native-pixel pipeline can PASS an actually large control.
        large_spec = copy.deepcopy(spec)
        start = 20 + large.getlength("co")
        box = draw.textbbox((start, 60), "m", font=large, anchor="ls")
        large_spec["texts"][0].update(
            role="control", threshold_px=9, semantic_roi_px=[10, 10, 300, 80],
            measure_roi_px=[math.ceil(box[0]), box[1] - 2,
                            math.floor(box[2]) - math.ceil(box[0]) - 1, box[3] - box[1] + 4])
        self.spec_path.write_text(json.dumps(large_spec), encoding="utf-8")
        large_result = verify.inspect(self.gif, self.root / "large-control", "fixture", self.spec_path)
        self.assertTrue(large_result["pass"], large_result)
        self.assertTrue(large_result["source_unchanged"])
        self.assertGreaterEqual(large_result["checks"][0]["measured_px"], 9)
        # A real threshold failure must also propagate through the CLI status.
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        process = subprocess.run([sys.executable, str(SCRIPT), str(self.gif), str(self.root / "cli-small"),
                                  "fixture", "--spec", str(self.spec_path)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
