"""Isolated synthetic codec fixtures; no product/model execution evidence."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("feature_builder", SCRIPTS / "build_feature_media.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg fixture tooling required")
class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature-codec-fixture-")
        self.root = Path(self.temp.name)
        self.source = self.root / "synthetic-codec-fixture.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
                        "testsrc2=size=160x120:rate=10:duration=5", "-f", "lavfi", "-i",
                        "sine=frequency=440:sample_rate=44100:duration=5", "-c:v", "libx264",
                        "-threads", "1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        str(self.source)], check=True, capture_output=True)
        self.source_hash = builder.sha256(self.source)
        self.manifest = {"schema": "feature-media/v1", "feature_id": "codec-fixture-only", "run_id": "edit-fixture",
                         "source": {"path": self.source.name, "sha256": self.source_hash,
                                    "kind": "full-recording", "complete": True},
                         "model_execution": None, "no_inference_reason": "Synthetic codec fixture; no product or model execution",
                         "proof_interval_s": [2, 5], "mp4": {"crop_px": [0, 0, 80, 80], "width": 80},
                         "gif": {"start_s": 1, "duration_s": 4, "crop_px": [0, 0, 80, 80],
                                 "width": 80, "fps": 10, "max_bytes": 3 * 1024 * 1024}}

    def tearDown(self):
        self.temp.cleanup()

    def args(self, format="both", version="v1", fixture=True):
        path = self.root / "feature.json"
        path.write_text(json.dumps(self.manifest))
        return argparse.Namespace(manifest=str(path), output=str(self.root / version), format=format,
                                  execution_route="work", expected_host=None, fixture=fixture, timeout_s=30)

    def model_summary(self, mode="live", operation="fresh-recording"):
        evidence = {"schema": "feature-model-execution/v1", "mode": mode, "operation": operation,
                    "run_id": "source-fixture", "current_live_e2e": "pass" if mode == "live" else "not-run",
                    "source_live_e2e": None if mode == "live" else {"status": "pass", "run_id": "older-fixture"},
                    "raw": {"sha256": self.source_hash},
                    "disclosure": {"label": "Live model" if mode == "live" else "Recorded model response · real tools",
                                   "visible_evidence": "fixture-label-proof.txt"}}
        (self.root / "fixture-label-proof.txt").write_text("Only a schema fixture; not visual or product evidence")
        (self.root / "model-fixture.json").write_text(json.dumps(evidence))
        self.manifest["model_execution"] = {"mode": mode, "operation": operation, "run_id": evidence["run_id"],
                                            "evidence": "model-fixture.json", "current_live_e2e": evidence["current_live_e2e"],
                                            "source_live_e2e": evidence["source_live_e2e"],
                                            "disclosure": evidence["disclosure"]["label"]}
        return evidence

    def test_both_formats_crop_full_audio_hashes_and_reproducibility(self):
        result = builder.encode(builder.make_plan(self.args()), self.args())
        self.assertEqual(result["status"], "fixture-only", result)
        self.assertTrue(result["source"]["unchanged"])
        self.assertEqual(builder.sha256(self.source), self.source_hash)
        self.assertEqual({o["kind"] for o in result["outputs"]}, {"gif", "mp4"})
        for output in result["outputs"]:
            path = self.root / "v1" / output["path"]
            self.assertEqual(output["sha256"], builder.sha256(path))
            self.assertEqual((output["probe"]["width"], output["probe"]["height"]), (80, 80))
        mp4 = next(o for o in result["outputs"] if o["kind"] == "mp4")
        self.assertAlmostEqual(mp4["probe"]["duration_s"], 5, delta=0.15)
        self.assertEqual(mp4["probe"]["audio_streams"], 1)
        self.assertEqual(mp4["probe"]["pix_fmt"], "yuv420p")
        self.assertEqual(result["gates"]["visual"], "pending")
        rerun_args = self.args(version="v2")
        rerun = builder.encode(builder.make_plan(rerun_args), rerun_args)
        self.assertEqual([o["sha256"] for o in result["outputs"]], [o["sha256"] for o in rerun["outputs"]])

    def test_gif_is_real_continuous_window_with_actual_crop(self):
        args = self.args(format="gif")
        result = builder.encode(builder.make_plan(args), args)
        self.assertEqual(result["status"], "fixture-only", result)
        self.assertFalse((self.root / "v1" / "demo.mp4").exists())
        raw_source = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.source), "-vf", "crop=80:80:0:0",
                                     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        raw_gif = subprocess.run(["ffmpeg", "-v", "error", "-ignore_loop", "1", "-i", str(self.root / "v1" / "feature.gif"),
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        frame_size = 80 * 80 * 3
        self.assertEqual(len(raw_gif) // frame_size, 40)
        for output_index in (0, 10, 20, 39):
            source_index = output_index + 10  # Source starts at 1 second, both sampled at 10 fps.
            before = raw_source[source_index * frame_size:(source_index + 1) * frame_size]
            after = raw_gif[output_index * frame_size:(output_index + 1) * frame_size]
            mean_palette_error = sum(abs(a - b) for a, b in zip(before, after)) / frame_size
            self.assertLess(mean_palette_error, 6)
        self.assertEqual(result["outputs"][0]["time_map"], {"kind": "continuous-source", "source_start_s": 1.0,
                                                           "speed": 1, "editorial_hold_s": 0})

    def test_mp4_only_and_existing_output_no_clobber(self):
        args = self.args(format="mp4")
        result = builder.encode(builder.make_plan(args), args)
        self.assertEqual(result["status"], "fixture-only", result)
        self.assertFalse((self.root / "v1" / "feature.gif").exists())
        receipt_hash = builder.sha256(self.root / "v1" / "manifest.json")
        with self.assertRaisesRegex(builder.Invalid, "already exists"):
            builder.make_plan(args)
        self.assertEqual(builder.sha256(self.root / "v1" / "manifest.json"), receipt_hash)
        (self.root / "dangling-output").symlink_to(self.root / "missing-output")
        args.output = str(self.root / "dangling-output")
        with self.assertRaisesRegex(builder.Invalid, "symlink"):
            builder.make_plan(args)
        self.assertFalse((self.root / "missing-output").exists())

    def test_invalid_bounds_hold_hash_and_unsupported_edit_are_refused(self):
        mutations = [({"gif": {**self.manifest["gif"], "duration_s": 8}}, "exceeds"),
                     ({"mp4": {"crop_px": [100, 0, 80, 80]}}, "exceeds"),
                     ({"proof_interval_s": [3, 5]}, "at least 3"),
                     ({"source": {**self.manifest["source"], "sha256": "0" * 64}}, "does not match"),
                     ({"gif": {**self.manifest["gif"], "speed": 2}}, "Unsupported")]
        original = dict(self.manifest)
        for update, error in mutations:
            with self.subTest(update=update):
                self.manifest = {**original, **update}
                args = self.args()
                with self.assertRaisesRegex(builder.Invalid, error):
                    builder.make_plan(args)
                self.assertFalse((self.root / "v1").exists())
        self.assertEqual(builder.sha256(self.source), self.source_hash)

    def test_budget_failure_preserves_attempts_and_source(self):
        self.manifest["gif"]["max_bytes"] = 1
        args = self.args(format="gif")
        result = builder.encode(builder.make_plan(args), args)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["attempts"]), 2)  # Requested 10, then 8; neither fits.
        self.assertFalse((self.root / "v1" / "feature.gif").exists())
        self.assertTrue((self.root / "v1" / "manifest.json").is_file())
        for attempt in result["attempts"]:
            self.assertEqual(attempt["sha256"], builder.sha256(self.root / "v1" / attempt["path"]))
        self.assertEqual(builder.sha256(self.source), self.source_hash)

    def test_bounded_timeout_keeps_partial_output_and_failure_receipt(self):
        args = self.args(format="mp4")
        plan = builder.make_plan(args)
        real_run = subprocess.run

        def timeout_encode(command, *positional, **kwargs):
            if command[0] == "ffmpeg" and "-i" in command:
                Path(command[-1]).write_bytes(b"partial-codec-fixture")
                raise subprocess.TimeoutExpired(command, args.timeout_s)
            return real_run(command, *positional, **kwargs)

        with patch.object(builder.subprocess, "run", side_effect=timeout_encode):
            result = builder.encode(plan, args)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"][0]["timed_out_s"], 30)
        self.assertEqual(result["attempts"][0]["sha256"], builder.sha256(self.root / "v1" / "demo.mp4"))
        self.assertTrue((self.root / "v1" / "manifest.json").is_file())
        self.assertEqual(builder.sha256(self.source), self.source_hash)

    def test_existing_derivative_cannot_replace_missing_full_original(self):
        self.manifest["source"]["kind"] = "existing-derivative"
        with self.assertRaisesRegex(builder.Invalid, "existing derivatives"):
            builder.make_plan(self.args(format="mp4"))

    def test_model_claims_cannot_be_laundered_as_fixture_or_null(self):
        self.model_summary()
        with self.assertRaisesRegex(builder.Invalid, "fixtures cannot carry"):
            builder.make_plan(self.args(fixture=True))
        self.manifest["model_execution"]["mode"] = "scripted"
        with self.assertRaisesRegex(builder.Invalid, "Only real"):
            builder.make_plan(self.args(fixture=False))
        self.manifest["model_execution"] = None
        self.manifest["no_inference_reason"] = None
        with self.assertRaisesRegex(builder.Invalid, "observed no_inference_reason"):
            builder.make_plan(self.args())

    def test_replay_requires_current_not_run_and_native_disclosure_preserved(self):
        self.model_summary("captured-replay", "replay-recording")
        self.manifest["replay_disclosure"] = {"source_rect_px": [0, 90, 80, 20]}
        with self.assertRaisesRegex(builder.Invalid, "remove the mandatory"):
            builder.make_plan(self.args(fixture=False))
        self.manifest["replay_disclosure"] = {"source_rect_px": [0, 0, 80, 20]}
        plan = builder.make_plan(self.args(fixture=False))
        self.assertEqual(plan["edits"][0]["replay_disclosure"]["visual_readability"], "pending")
        self.manifest["model_execution"]["current_live_e2e"] = "pass"
        with self.assertRaisesRegex(builder.Invalid, "differs|not-run"):
            builder.make_plan(self.args(fixture=False))
        self.manifest["model_execution"]["current_live_e2e"] = "not-run"
        del self.manifest["replay_disclosure"]
        with self.assertRaisesRegex(builder.Invalid, "source_rect_px"):
            builder.make_plan(self.args(fixture=False))

    def test_historical_live_reedit_preserves_original_pass_without_new_live_claim(self):
        evidence = self.model_summary()
        original_bytes = (self.root / "model-fixture.json").read_bytes()
        self.manifest["model_execution"].update(operation="re-edit", current_live_e2e="not-run", edit_run_id="new-edit",
                                                 source_live_e2e={"status": "pass", "run_id": evidence["run_id"],
                                                                  "evidence": "model-fixture.json",
                                                                  "sha256": hashlib.sha256(original_bytes).hexdigest()})
        plan = builder.make_plan(self.args(fixture=False))
        self.assertEqual(plan["model_execution"]["current_live_e2e"], "not-run")
        self.assertEqual(plan["model_execution"]["source_live_e2e"]["status"], "pass")
        self.assertEqual((self.root / "model-fixture.json").read_bytes(), original_bytes)

    def test_historical_source_fail_cannot_be_treated_as_successful_reference(self):
        self.model_summary()
        self.manifest["model_execution"].update(operation="re-edit", current_live_e2e="not-run", edit_run_id="fixture-edit",
                                                 source_live_e2e={"status": "fail", "run_id": "source-fixture"})
        args = self.args(format="gif", fixture=False)
        result = builder.encode(builder.make_plan(args), args)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["gates"]["source_provenance"].startswith("blocked"))
        self.assertEqual(result["gates"]["model_provenance"], "pending")
        self.manifest["model_execution"]["source_live_e2e"] = "pass"
        with self.assertRaisesRegex(builder.Invalid, "explicit source status"):
            builder.make_plan(self.args(version="v2", fixture=False))

    def test_replay_reedit_cannot_replace_an_original_failed_source_reference(self):
        evidence = self.model_summary("captured-replay", "replay-recording")
        evidence["source_live_e2e"]["status"] = "fail"
        (self.root / "model-fixture.json").write_text(json.dumps(evidence))
        self.manifest["model_execution"].update(operation="re-edit", edit_run_id="fixture-reedit",
                                                 source_live_e2e={"status": "pass", "run_id": "unrelated-source-fixture"})
        self.manifest["replay_disclosure"] = {"source_rect_px": [0, 0, 80, 20]}
        with self.assertRaisesRegex(builder.Invalid, "must match the original"):
            builder.make_plan(self.args(fixture=False))

    def test_original_replay_outcome_failure_remains_blocked_on_reedit(self):
        evidence = self.model_summary("captured-replay", "replay-recording")
        evidence["outcome"] = {"status": "fail"}
        (self.root / "model-fixture.json").write_text(json.dumps(evidence))
        self.manifest["model_execution"].update(operation="re-edit", edit_run_id="fixture-reedit")
        self.manifest["replay_disclosure"] = {"source_rect_px": [0, 0, 80, 20]}
        args = self.args(format="gif", fixture=False)
        result = builder.encode(builder.make_plan(args), args)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["model_execution"]["current_live_e2e"], "not-run")


if __name__ == "__main__":
    unittest.main()
