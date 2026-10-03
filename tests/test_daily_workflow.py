from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
import test_quality_gates as fixtures
from test_quality_gates import SAMPLE, ROOT
from receive_prose import receive
from report_views import generate, sync_rubric, freshness_errors, rubric_projection
from review_prose import record_review
from workflow import next_actions
from workflow_core import approval_current, gate_digest
from artifact_checks import build_inputs, verify_build
from layout_tuning import settings, tex
from validate_experiment import validate


class DailyWorkflowTests(unittest.TestCase):
    clone_sample = fixtures.QualityGateTests.clone_sample
    refresh_gate = fixtures.QualityGateTests.refresh_gate

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.exp = self.clone_sample(Path(self.temp.name))

    def test_batch_replacement_preserves_history_and_g2(self):
        original = self.exp / "prose/original/P-001.md"
        old = original.read_bytes()
        changed = receive(self.exp, [{"slot_id": "P-001", "text": "本人からの訂正文。\n"},
                                     {"slot_id": "P-002", "text": "実施内容の訂正。"}], "test user message 1")
        self.assertEqual(changed, ["P-001", "P-002"])
        self.assertEqual(original.read_text(encoding="utf-8"), "本人からの訂正文。\n")
        self.assertEqual(next((self.exp / "prose/history").glob("*/P-001.md")).read_bytes(), old)
        self.assertFalse((self.exp / "prose/typeset/P-001.tex").exists())
        self.assertIn("受領済み・校正待ち", (self.exp / "quality/PROSE_CHANGES.md").read_text(encoding="utf-8"))
        self.assertTrue(approval_current(self.exp, "G2")[0])
        self.assertIn("P-001", "\n".join(next_actions(self.exp)))
        self.assertEqual(validate(self.exp, 6, draft=True).errors, [])

    def test_duplicate_or_invalid_batch_is_not_partially_written(self):
        before = (self.exp / "spec/WRITING_PLAN.yaml").read_bytes()
        for second in ("P-001", "../../outside", "P-999"):
            with self.assertRaises(ValueError):
                receive(self.exp, [{"slot_id": "P-001", "text": "改訂"}, {"slot_id": second, "text": "不正"}], "user message")
        self.assertEqual((self.exp / "spec/WRITING_PLAN.yaml").read_bytes(), before)
        self.assertFalse((self.exp / "prose/history").exists())

    def test_repeat_receipt_does_not_erase_review(self):
        text = (self.exp / "prose/original/P-001.md").read_text(encoding="utf-8")
        before = (self.exp / "spec/WRITING_PLAN.yaml").read_bytes()
        self.assertEqual(receive(self.exp, [{"slot_id": "P-001", "text": text}], "same user message"), [])
        self.assertEqual((self.exp / "spec/WRITING_PLAN.yaml").read_bytes(), before)

    def test_tampered_original_is_not_resealed(self):
        (self.exp / "prose/original/P-001.md").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stored original"):
            receive(self.exp, [{"slot_id": "P-001", "text": "new"}], "user message")

    def test_receipt_cannot_skip_gates(self):
        path = self.exp / "workflow/STATE.yaml"
        state = yaml.safe_load(path.read_text(encoding="utf-8"))
        state["gates"]["G1"]["status"] = "pending"
        path.write_text(yaml.safe_dump(state), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "G1 has not been approved"):
            receive(self.exp, [{"slot_id": "P-001", "text": "new"}], "user message")

    def test_stale_generated_source_is_rejected_by_validator(self):
        path = generate(self.exp, "sources", replace_legacy=True)
        path.write_text(path.read_text(encoding="utf-8") + "old", encoding="utf-8")
        self.assertTrue(any("generated sources view is stale" in e for e in validate(self.exp, 5).errors))

    def test_stale_synced_rubric_is_rejected_by_validator(self):
        sync_rubric(self.exp)
        path = self.exp / "quality/PROFESSOR_REVIEW.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["rubric"][0]["criticism"] = "new finding"
        path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        (self.exp / "build").mkdir(exist_ok=True)
        shutil.copy2(SAMPLE / "deliverables/report.pdf", self.exp / "build/final-candidate.pdf")
        self.assertTrue(any("generated rubric is stale" in e for e in validate(self.exp, 8, candidate=True).errors))

    def test_failed_batch_restores_original_typeset_and_plan(self):
        targets = [self.exp / p for p in ("prose/original/P-001.md", "prose/typeset/P-001.tex", "spec/WRITING_PLAN.yaml")]
        before = {p: p.read_bytes() for p in targets}
        normal = Path.write_text
        def failing(path, *args, **kwargs):
            if path.name == "WRITING_PLAN.yaml":
                raise OSError("simulated write failure")
            return normal(path, *args, **kwargs)
        with patch.object(Path, "write_text", failing), self.assertRaises(OSError):
            receive(self.exp, [{"slot_id": "P-001", "text": "改訂"}], "user message")
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)

    def test_generated_views_are_idempotent_and_detect_staleness(self):
        for view in ("sources", "evaluation"):
            with self.assertRaisesRegex(ValueError, "handwritten"):
                generate(self.exp, view)
            path = generate(self.exp, view, replace_legacy=True)
            before = path.stat().st_mtime_ns
            generate(self.exp, view)
            self.assertEqual(path.stat().st_mtime_ns, before)
            self.assertEqual(freshness_errors(self.exp, view), [])
            path.write_text(path.read_text(encoding="utf-8") + "stale", encoding="utf-8")
            self.assertTrue(freshness_errors(self.exp, view))
        self.assertEqual(len(list((self.exp / "quality/view-backups").glob("*/*.md"))), 2)

    def test_rubric_sync_preserves_technical_checks_and_invalidates_binding(self):
        path = self.exp / "quality/QUALITY_REVIEW.yaml"
        before = yaml.safe_load(path.read_text(encoding="utf-8"))
        sync_rubric(self.exp)
        after = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(after["content_checks"], before["content_checks"])
        self.assertIsNone(after["reviewed_pdf_sha256"])
        professor = yaml.safe_load((self.exp / "quality/PROFESSOR_REVIEW.yaml").read_text(encoding="utf-8"))
        self.assertEqual(after["rubric"], rubric_projection(professor))
        stamp = path.stat().st_mtime_ns
        sync_rubric(self.exp)
        self.assertEqual(path.stat().st_mtime_ns, stamp)
        for verdict in ("not_met", "partially_met", "undetermined"):
            professor["rubric"][0]["verdict"] = verdict
            self.assertEqual(rubric_projection(professor)[0]["status"], "failed")

    def test_writing_brief_contains_questions_not_prose(self):
        g2 = gate_digest(self.exp, "G2")[0]
        path = generate(self.exp, "writing")
        text = path.read_text(encoding="utf-8")
        self.assertIn("本人が考えること", text)
        self.assertIn("RESULT_TRACEABILITY.md", text)
        self.assertEqual(gate_digest(self.exp, "G2")[0], g2)

    def test_optional_student_judgment_is_part_of_g2(self):
        before = gate_digest(self.exp, "G2")[0]
        path = self.exp / "spec/WRITING_PLAN.yaml"
        plan = yaml.safe_load(path.read_text(encoding="utf-8"))
        plan["slots"][0]["student_judgment"] = "観測だけで一般化できるか？"
        path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
        self.assertNotEqual(before, gate_digest(self.exp, "G2")[0])

    def test_presentation_settings_keep_g2_but_invalidate_candidate(self):
        before_g2 = gate_digest(self.exp, "G2")[0]
        before = build_inputs(self.exp, "candidate")
        (self.exp / "spec/LAYOUT_TUNING.yaml").write_text("figure_width: 0.9\ntextfloatsep_pt: 15\n", encoding="utf-8")
        self.assertEqual(before_g2, gate_digest(self.exp, "G2")[0])
        self.assertTrue(approval_current(self.exp, "G2")[0])
        self.assertNotEqual(before, build_inputs(self.exp, "candidate"))
        with self.assertRaisesRegex(ValueError, "stale"):
            verify_build(self.exp, "candidate")
        self.assertIn("0.82", tex(self.exp, "skeleton"))
        self.assertIn("0.9", tex(self.exp, "candidate"))
        for invalid in ("figure_width: 0.1", "figure_width: .nan", "figure_width: true", "font_size: 8", "null"):
            (self.exp / "spec/LAYOUT_TUNING.yaml").write_text(invalid, encoding="utf-8")
            with self.assertRaises(ValueError):
                settings(self.exp)

    def test_template_views_can_be_generated_without_overwrite_flag(self):
        with tempfile.TemporaryDirectory() as raw:
            fresh = Path(raw) / "fresh"
            shutil.copytree(ROOT / "templates/experiment", fresh)
            generate(fresh, "sources")
            generate(fresh, "evaluation")
            self.assertTrue(validate(fresh, 2).errors)  # Rendering never grants approval.

    def test_plain_language_change_summary(self):
        record_review(self.exp, "P-002", "句読点のみを統一。主張・数値は変更なし。")
        text = (self.exp / "quality/PROSE_CHANGES.md").read_text(encoding="utf-8")
        self.assertIn("句読点のみ", text)
        self.assertIn("現在の版を確認済み", text)


if __name__ == "__main__":
    unittest.main()
