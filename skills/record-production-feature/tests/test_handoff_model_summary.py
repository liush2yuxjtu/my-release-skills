"""Portable handoff/builder contract fixtures, never product or live evidence.

These tests exercise only structural identity/hash checks. They do not encode
media, invoke a model, authenticate a source, or establish a provenance PASS.
"""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "handoff_contract_builder", SKILL / "scripts" / "build_feature_media.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class HandoffModelSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="handoff-schema-fixture-")
        self.root = Path(self.temp.name)
        self.original_run = "original-model-run-schema-fixture"
        self.edit_run = "current-edit-schema-fixture"
        self.source_hash = hashlib.sha256(b"isolated schema fixture; not media").hexdigest()
        self.original_evidence = {
            "schema": "feature-model-execution/v1",
            "mode": "live",
            "run_id": self.original_run,
            "current_live_e2e": "pass",
            "source_live_e2e": None,
            "raw": {"sha256": self.source_hash},
            "disclosure": {"label": "Live model"},
        }
        self.evidence_path = self.root / "original-schema-fixture.json"
        self.evidence_bytes = (json.dumps(self.original_evidence, sort_keys=True) + "\n").encode()
        self.evidence_path.write_bytes(self.evidence_bytes)
        self.handoff = json.loads((SKILL / "assets" / "handoff.template.json").read_text())
        self.handoff["workflow"].update(
            lane="verified-reuse", source_run_id=self.original_run,
            change_summary="Isolated schema test; not a recording or provenance receipt."
        )
        self.handoff["model_execution"] = {
            "mode": "live",
            "operation": "reuse",
            "run_id": self.original_run,
            "edit_run_id": self.edit_run,
            "evidence": self.evidence_path.name,
            "current_live_e2e": "not-run",
            "source_live_e2e": {
                "status": "pass",
                "run_id": self.original_run,
                "evidence": self.evidence_path.name,
                "sha256": hashlib.sha256(self.evidence_bytes).hexdigest(),
            },
            "disclosure": "Live model",
        }

    def tearDown(self):
        self.temp.cleanup()

    def read_summary(self, summary):
        # The real builder's structural check, without codec or platform tools.
        # Only the handoff model summary crosses this contract boundary.
        return builder.read_model(
            {"model_execution": summary}, self.root, self.source_hash,
            "full-recording", {"width": 160, "height": 120}
        )[0]

    def test_reuse_and_reedit_preserve_original_identity_and_current_not_run(self):
        for operation in ("reuse", "re-edit"):
            with self.subTest(operation=operation):
                summary = copy.deepcopy(self.handoff["model_execution"])
                summary["operation"] = operation
                result = self.read_summary(summary)
                self.assertEqual(result["run_id"], self.original_run)
                self.assertEqual(result["edit_run_id"], self.edit_run)
                self.assertEqual(result["current_live_e2e"], "not-run")
                self.assertEqual(result["source_live_e2e"]["run_id"], self.original_run)
                self.assertEqual(self.evidence_path.read_bytes(), self.evidence_bytes)
                self.assertEqual(self.handoff["workflow"]["source_run_id"], self.original_run)
                self.assertEqual(result["checks"],
                                 "schema-consistency-and-source-hash-only; provenance-review-required")

    def test_edit_id_cannot_replace_original_model_run(self):
        summary = copy.deepcopy(self.handoff["model_execution"])
        summary["run_id"] = self.edit_run
        with self.assertRaisesRegex(builder.Invalid, "run_id differs from its evidence"):
            self.read_summary(summary)

    def test_separate_edit_identity_is_required(self):
        summary = copy.deepcopy(self.handoff["model_execution"])
        del summary["edit_run_id"]
        with self.assertRaisesRegex(builder.Invalid, "separate edit_run_id"):
            self.read_summary(summary)

    def test_summary_label_cannot_be_translated_expanded_or_replaced_with_object(self):
        for disclosure in ("Translated fixture label", "Live model; extra commentary",
                           {"label": "Live model"}):
            with self.subTest(disclosure=disclosure):
                summary = copy.deepcopy(self.handoff["model_execution"])
                summary["disclosure"] = disclosure
                with self.assertRaisesRegex(builder.Invalid, "disclosure must match"):
                    self.read_summary(summary)

    def test_reuse_cannot_claim_a_new_live_pass(self):
        summary = copy.deepcopy(self.handoff["model_execution"])
        summary["current_live_e2e"] = "pass"
        with self.assertRaisesRegex(builder.Invalid, "current_live_e2e must remain not-run"):
            self.read_summary(summary)

    def test_unknown_original_result_stays_null_without_promoting_handoff(self):
        unknown_evidence = copy.deepcopy(self.original_evidence)
        unknown_evidence["current_live_e2e"] = "not-run"
        unknown_bytes = (json.dumps(unknown_evidence, sort_keys=True) + "\n").encode()
        self.evidence_path.write_bytes(unknown_bytes)
        summary = copy.deepcopy(self.handoff["model_execution"])
        summary["source_live_e2e"] = None
        result = self.read_summary(summary)
        self.assertIsNone(result["source_live_e2e"])
        self.assertEqual(result["current_live_e2e"], "not-run")
        self.assertEqual(result["source_evidence_current_live_e2e"], "not-run")
        self.assertEqual(self.handoff["status"], "blocked")
        self.assertEqual(self.handoff["gates"]["model_source"]["status"], "not-run")
        self.assertEqual(self.evidence_path.read_bytes(), unknown_bytes)


if __name__ == "__main__":
    unittest.main()
