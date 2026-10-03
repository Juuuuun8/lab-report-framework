from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import test_quality_gates as fixtures
from test_quality_gates import SAMPLE, ROOT
from artifact_checks import record_build, verify_build
from reproduce import reproduce, load_spec
from review_prose import record_review, review_errors, quantities
from validate_experiment import Audit, check_tex, check_professor_scores, validate
from workflow_core import approval_current
from workflow import release, build_review, packet_g1
from workflow import initial_state
from workflow_core import write_state


class ReliabilityTests(unittest.TestCase):
    clone_sample = fixtures.QualityGateTests.clone_sample
    refresh_gate = fixtures.QualityGateTests.refresh_gate
    def test_noop_cannot_pass_reproduction(self):
        _, spec = load_spec(SAMPLE)
        spec["commands"] = [{"argv": ["{python}", "-c", "pass"], "cwd": "."}]
        with self.assertRaisesRegex(FileNotFoundError, "did not create"):
            reproduce(SAMPLE, spec)

    def test_numeric_change_and_stale_pdf_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "build").mkdir()
            shutil.copy2(SAMPLE / "deliverables/report.pdf", exp / "build/final-candidate.pdf")
            path = exp / "prose/typeset/P-005.tex"
            path.write_text(path.read_text(encoding="utf-8").replace("194.74", "999.99"), encoding="utf-8")
            errors = validate(exp, 8, candidate=True).errors
            self.assertTrue(any("numbers or units changed" in error for error in errors), errors)
            self.assertTrue(any("prose review is missing or stale" in error for error in errors), errors)
            self.assertTrue(any("PDF is stale" in error for error in errors), errors)

    def test_wording_change_invalidates_prose_review(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            plan = yaml.safe_load((exp / "spec/WRITING_PLAN.yaml").read_text(encoding="utf-8"))
            path = exp / "prose/typeset/P-001.tex"
            path.write_text(path.read_text(encoding="utf-8") + "証明された。", encoding="utf-8")
            self.assertIn("prose review is missing or stale", review_errors(exp, plan["slots"][0]))

    def test_approval_substring_is_not_a_user_decision(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            with self.assertRaisesRegex(ValueError, "decision must start"):
                record_review(exp, "P-001", "未承認", "未承認 P-001")

    def test_explicit_numeric_approval_is_bound_to_versions(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "prose/typeset/P-005.tex"
            path.write_text(path.read_text(encoding="utf-8").replace("194.74", "999.99"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "numbers or units changed"):
                record_review(exp, "P-005", "組版のみ")
            record_review(exp, "P-005", "テスト上の訂正", "承認 P-005: テスト上の数値訂正")
            slot = yaml.safe_load((exp / "spec/WRITING_PLAN.yaml").read_text(encoding="utf-8"))["slots"][4]
            self.assertEqual(review_errors(exp, slot), [])
            path.write_text(path.read_text(encoding="utf-8").replace("999.99", "888.88"), encoding="utf-8")
            self.assertIn("prose review is missing or stale", review_errors(exp, slot))

    def test_percent_does_not_hide_numbers(self):
        self.assertNotEqual(quantities("5%改善し、値は10だった。"), quantities(r"5\%改善し、値は99だった。", tex=True))

    def test_reordered_measurements_are_detected(self):
        self.assertNotEqual(quantities("Aは10 ms、Bは20 ms。"), quantities(r"Aは\SI{20}{ms}、Bは\SI{10}{ms}。", tex=True))

    def test_review_cannot_reseal_modified_original(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "prose/original/P-001.md"
            path.write_text(path.read_text(encoding="utf-8") + "AIが追加した本文。", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "original user prose changed"):
                record_review(exp, "P-001", "確認したつもり")

    def test_future_confirmation_keeps_g1_and_g2_current(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "spec/ACADEMIC_INTEGRITY.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["confirmations"].update(student_can_explain=False, sources_not_fabricated=False)
            path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            self.assertTrue(approval_current(exp, "G1")[0])
            self.assertTrue(approval_current(exp, "G2")[0])

    def test_reapproved_plan_does_not_reuse_old_g2(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "spec/EXPERIMENT_PLAN.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["objective"] += " 計画変更"
            path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            self.refresh_gate(exp, "G1")
            self.assertFalse(approval_current(exp, "G2")[0])

    def test_completed_pdf_cannot_be_used_as_skeleton(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "build").mkdir()
            shutil.copy2(SAMPLE / "deliverables/report.pdf", exp / "build/skeleton.pdf")
            errors = validate(exp, 5, skeleton=True).errors
            self.assertTrue(any("skeleton PDF lacks" in error for error in errors), errors)
            self.assertTrue(any("PDF does not match" in error for error in errors), errors)

    def test_partial_draft_passes_but_candidate_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "spec/WRITING_PLAN.yaml"
            plan = yaml.safe_load(path.read_text(encoding="utf-8"))
            plan["status"] = "prose_partial"
            for slot in plan["slots"][1:]:
                slot["status"] = "awaiting_user"
                (exp / slot["typeset_file"]).unlink()
            path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            self.assertEqual(validate(exp, 6, draft=True).errors, [])
            self.assertTrue(validate(exp, 7).errors)

    def test_numeric_score_without_teacher_scale_is_rejected(self):
        requirements = yaml.safe_load((SAMPLE / "spec/ASSIGNMENT_REQUIREMENTS.yaml").read_text(encoding="utf-8"))
        professor = yaml.safe_load((SAMPLE / "quality/PROFESSOR_REVIEW.yaml").read_text(encoding="utf-8"))
        professor["overall"]["score_percent"] = 100
        for row in professor["rubric"]:
            row["score"] = 1
        audit = Audit()
        check_professor_scores(requirements, professor, audit)
        self.assertTrue(any("total score must be null" in error for error in audit.errors))

    def test_teacher_scores_are_calculated_not_asserted(self):
        requirements = {"rubric_source": {"status": "provided"}, "rubric_criteria": [
            {"rubric_id": "RUB-001", "max_score": 10, "weight": 70},
            {"rubric_id": "RUB-002", "max_score": 5, "weight": 30}]}
        professor = {"rubric": [{"rubric_id": "RUB-001", "score": 8, "report_locators": ["1節"]},
                               {"rubric_id": "RUB-002", "score": 3, "report_locators": ["2節"]}],
                     "overall": {"score_percent": 74}}
        audit = Audit()
        check_professor_scores(requirements, professor, audit)
        self.assertEqual(audit.errors, [])
        professor["overall"]["score_percent"] = 100
        audit = Audit()
        check_professor_scores(requirements, professor, audit)
        self.assertTrue(audit.errors)

    def test_tex_order_comments_and_generated_tables(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "report/main.tex"
            main = path.read_text(encoding="utf-8")
            main = main.replace(r"\input{sections/02-method.tex}", "")
            main = main.replace(r"\input{sections/01-purpose.tex}", r"\input{sections/02-method.tex}" + "\n" + r"\input{sections/01-purpose.tex}")
            path.write_text(main, encoding="utf-8")
            # Move the real reference out of the active section and leave only a comment.
            prose = exp / "prose/typeset/P-003.tex"
            prose.write_text("% " + prose.read_text(encoding="utf-8"), encoding="utf-8")
            audit = Audit()
            check_tex(exp, audit, set())
            self.assertTrue(any("lst:timer must be referenced" in e for e in audit.errors), audit.errors)
            table = exp / "report/sections/03-results.tex"
            text = table.read_text(encoding="utf-8")
            import re
            caption = re.search(r"\\caption\{[^}]*\}", text).group()
            text = text.replace(caption, "").replace(r"\end{table}", caption + "\n" + r"\end{table}")
            table.write_text(text, encoding="utf-8")
            audit = Audit()
            check_tex(exp, audit, set(), allow_planned_references=True)
            self.assertIn("PHASE 6: table caption must be above the table", audit.errors)

    def test_bottom_listing_caption_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            path = exp / "report/sections/02-method.tex"
            path.write_text(path.read_text(encoding="utf-8").replace("language=Python", "captionpos=b,language=Python"), encoding="utf-8")
            audit = Audit()
            check_tex(exp, audit, set(), allow_planned_references=True)
            self.assertIn("PHASE 6: local listing caption must be above code", audit.errors)

    def test_actual_input_order_not_filename_order(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "report/sections/01-purpose.tex").write_text(r"図\ref{fig:order}に示す。", encoding="utf-8")
            (exp / "report/sections/02-method.tex").write_text(r"\begin{figure}[tbp]\includegraphics{dummy}\caption{図}\label{fig:order}\end{figure}", encoding="utf-8")
            (exp / "report/main.tex").write_text(r"\documentclass{labreport}\begin{document}\input{sections/02-method.tex}\input{sections/01-purpose.tex}\end{document}", encoding="utf-8")
            audit = Audit()
            check_tex(exp, audit, set())
            self.assertIn("PHASE 6: figure fig:order must be referenced before placement", audit.errors)

    def test_style_in_active_preamble_input_is_checked(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "report/custom.tex").write_text(r"\geometry{margin=5mm}", encoding="utf-8")
            path = exp / "report/main.tex"
            path.write_text(path.read_text(encoding="utf-8").replace(r"\input{meta.tex}", r"\input{meta.tex}\input{custom.tex}"), encoding="utf-8")
            audit = Audit()
            check_tex(exp, audit, set())
            self.assertTrue(any("style command requires approved" in e for e in audit.errors))

    def test_changed_review_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "build").mkdir()
            shutil.copy2(SAMPLE / "deliverables/report.pdf", exp / "build/final-candidate.pdf")
            path = exp / "quality/PROFESSOR_REVIEW.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["reviewed_pdf_sha256"] = "0" * 64
            path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            self.assertTrue(any("PROFESSOR_REVIEW is not bound" in e for e in validate(exp, 8, candidate=True).errors))

    def test_failed_release_restores_previous_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            exp = self.clone_sample(Path(raw))
            (exp / "build").mkdir()
            shutil.copy2(SAMPLE / "deliverables/report.pdf", exp / "build/final-candidate.pdf")
            old = exp / "deliverables"
            old.mkdir()
            (old / "report.pdf").write_bytes(b"previous trusted report")
            (old / "notes.txt").write_bytes(b"user note")
            self.refresh_gate(exp, "G3")
            import subprocess
            with patch("workflow.run_validation"), patch("workflow.subprocess.run", side_effect=subprocess.CalledProcessError(1, "test")):
                with self.assertRaises(subprocess.CalledProcessError):
                    release(exp)
            self.assertEqual((old / "report.pdf").read_bytes(), b"previous trusted report")
            self.assertEqual((old / "notes.txt").read_bytes(), b"user note")

    def test_review_packet_contains_decision_material(self):
        text = "\n".join(packet_g1(SAMPLE))
        self.assertIn("合格条件", text)
        self.assertIn("表紙", text)
        self.assertIn("除外", text)
        packet = build_review(SAMPLE, "G1", [{"path": "a", "sha256": "new"}], [{"path": "a", "sha256": "old"}])
        self.assertIn("前回確認からの変更", packet)

    @unittest.skipUnless(shutil.which("latexmk"), "local TeX integration test; compiler is optional for CI")
    def test_new_template_partial_writing_to_release(self):
        # A fresh template, not a completed STATE, drives every real command.
        with tempfile.TemporaryDirectory(prefix="report-flow-") as raw:
            exp = Path(raw) / "experiment"
            shutil.copytree(ROOT / "templates/experiment", exp)
            write_state(exp, initial_state())
            self.assertTrue(validate(exp, 2).errors)
            for name in ("REPORT_META", "USER_DECISIONS", "ASSIGNMENT_REQUIREMENTS", "CONTEXT_INDEX", "EXPERIMENT_PLAN"):
                shutil.copy2(SAMPLE / "spec" / f"{name}.yaml", exp / "spec" / f"{name}.yaml")
            for name in ("instructions",):
                shutil.copytree(SAMPLE / name, exp / name, dirs_exist_ok=True)
            shutil.copy2(SAMPLE / "QUESTIONS.md", exp / "QUESTIONS.md")
            integrity = yaml.safe_load((SAMPLE / "spec/ACADEMIC_INTEGRITY.yaml").read_text(encoding="utf-8"))
            integrity["confirmations"].update(actual_work_status="unconfirmed", data_not_fabricated=False, sources_not_fabricated=False, student_can_explain=False)
            (exp / "spec/ACADEMIC_INTEGRITY.yaml").write_text(yaml.safe_dump(integrity, allow_unicode=True), encoding="utf-8")
            def command(*args):
                result = fixtures.run(*args)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result
            workflow = ROOT / "scripts/workflow.py"
            build = ROOT / "scripts/build_report.py"
            command(workflow, "prepare-review", exp, "--gate", "G1")
            command(workflow, "approve", exp, "--gate", "G1", "--decision", "承認 G1: test planning")
            # Deterministic raw fixture stands in for user-performed measurements.
            for name in ("data/raw", "analysis", "report"):
                shutil.copytree(SAMPLE / name, exp / name, dirs_exist_ok=True)
            for name in ("EXECUTION_MANIFEST", "REPRODUCE", "SOURCES", "CLAIMS", "WRITING_PLAN"):
                shutil.copy2(SAMPLE / "spec" / f"{name}.yaml", exp / "spec" / f"{name}.yaml")
            for name in ("RESULT_TRACEABILITY.md", "SOURCE_AUDIT.md", "WORKLOG.md"):
                shutil.copy2(SAMPLE / name, exp / name)
            plan_path = exp / "spec/WRITING_PLAN.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["status"] = "skeleton_ready"
            for slot in plan["slots"]:
                slot.update(authorship="user", status="awaiting_user", original_sha256=None, proofread_notes=None)
                slot.pop("review", None)
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            integrity["confirmations"].update(actual_work_status="confirmed", data_not_fabricated=True)
            (exp / "spec/ACADEMIC_INTEGRITY.yaml").write_text(yaml.safe_dump(integrity, allow_unicode=True), encoding="utf-8")
            command(exp / "analysis/analyze.py")
            command(build, exp, "--mode", "skeleton")
            command(workflow, "prepare-review", exp, "--gate", "G2")
            command(workflow, "approve", exp, "--gate", "G2", "--decision", "承認 G2: test skeleton")
            # One paragraph is received first, while all other slots stay empty.
            for folder in ("original", "typeset"):
                (exp / "prose" / folder).mkdir(parents=True, exist_ok=True)
                source = SAMPLE / "prose" / folder / ("P-001.md" if folder == "original" else "P-001.tex")
                shutil.copy2(source, exp / "prose" / folder / source.name)
            record_review(exp, "P-001", "test fixture reviewed")
            command(build, exp, "--mode", "draft")
            from pypdf import PdfReader
            draft_text = "".join(page.extract_text() or "" for page in PdfReader(exp / "build/draft.pdf").pages)
            self.assertIn("文章2", draft_text.replace(" ", ""))
            self.assertNotIn("文章1）", draft_text.replace(" ", ""))
            self.assertIn("本例の目的", draft_text.replace(" ", ""))
            for slot in plan["slots"][1:]:
                for folder, key in (("original", "original_file"), ("typeset", "typeset_file")):
                    shutil.copy2(SAMPLE / slot[key], exp / slot[key])
                record_review(exp, slot["slot_id"], "test fixture reviewed")
            for name in ("HANDOFF.md", "PROFESSOR_EVALUATION.md"):
                shutil.copy2(SAMPLE / name, exp / name)
            integrity["confirmations"].update(sources_not_fabricated=True, student_can_explain=True)
            (exp / "spec/ACADEMIC_INTEGRITY.yaml").write_text(yaml.safe_dump(integrity, allow_unicode=True), encoding="utf-8")
            command(build, exp, "--mode", "candidate")
            for name in ("FINAL_CHECK", "QUALITY_REVIEW", "PROFESSOR_REVIEW"):
                shutil.copy2(SAMPLE / "quality" / f"{name}.yaml", exp / "quality" / f"{name}.yaml")
            command(ROOT / "scripts/render_pdf.py", exp / "build/final-candidate.pdf", exp / "quality/rendered", "--manifest", exp / "quality/RENDER_MANIFEST.yaml")
            command(workflow, "bind-reviews", exp)
            command(workflow, "prepare-review", exp, "--gate", "G3")
            command(workflow, "approve", exp, "--gate", "G3", "--decision", "承認 G3: test final")
            command(workflow, "release", exp)
            self.assertEqual(validate(exp, 8).errors, [])
            self.assertEqual((exp / "deliverables/report.pdf").read_bytes(), (exp / "build/final-candidate.pdf").read_bytes())


if __name__ == "__main__":
    unittest.main()
