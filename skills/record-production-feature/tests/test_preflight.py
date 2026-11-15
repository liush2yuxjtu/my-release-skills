"""Dependency probes only; never production/model/visual acceptance fixtures."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight.py"
spec = importlib.util.spec_from_file_location("feature_preflight", SCRIPT)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def args(self, project, phase="encode", format="gif"):
        return argparse.Namespace(project=str(project), phase=phase, format=format, execution_route="work",
                                  expected_host=None, min_free_gib=0, ocr_languages="eng")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg dependency probe required")
    def test_gif_encode_does_not_require_node_playwright_or_ocr(self):
        with tempfile.TemporaryDirectory(prefix="feature-preflight-") as project:
            real_which = shutil.which
            with patch.object(preflight.shutil, "which", side_effect=lambda name: None if name in ("node", "tesseract") else real_which(name)):
                result = preflight.inspect(self.args(project))
            self.assertEqual(result["status"], "dependencies-ready", result)
            self.assertFalse(any(c["name"] in ("node", "project-playwright", "tesseract") for c in result["checks"]))
            self.assertIn("visual, reading-time and independent review", result["unassessed"])

    def test_missing_dependencies_are_concrete_json_gaps(self):
        with tempfile.TemporaryDirectory(prefix="feature-preflight-") as project:
            with patch.object(preflight.shutil, "which", return_value=None):
                result = preflight.inspect(self.args(project, phase="verify", format="both"))
            self.assertEqual(result["status"], "blocked")
            self.assertTrue({"ffmpeg", "ffprobe", "node", "tesseract"}.issubset({g["name"] for g in result["gaps"]}))
            self.assertTrue(all(g["remedy"] for g in result["gaps"]))
            json.dumps(result)  # Machine-readable even when every optional route is unavailable.

    def test_wrong_host_and_fake_mac_route_fail(self):
        with tempfile.TemporaryDirectory(prefix="feature-preflight-") as project:
            args = self.args(project)
            args.execution_route, args.expected_host = "mac-mini", "not-the-measured-host"
            with patch.object(preflight.platform, "system", return_value="Linux"), patch.object(preflight.shutil, "which", return_value=None):
                result = preflight.inspect(args)
            self.assertTrue({"expected-host", "execution-route"}.issubset({g["name"] for g in result["gaps"]}))


if __name__ == "__main__":
    unittest.main()
