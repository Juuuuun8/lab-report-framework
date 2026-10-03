from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from workflow_core import gate_digest  # noqa: E402
from workflow import packet_g1  # noqa: E402
from artifact_checks import record_build  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sort-benchmark"
VALIDATOR = ROOT / "scripts" / "validate_experiment.py"
REPRODUCE = ROOT / "scripts" / "reproduce.py"
WORKFLOW = ROOT / "scripts" / "workflow.py"


def run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class QualityGateTests(unittest.TestCase):
    def refresh_gate(self, experiment: Path, gate: str) -> None:
        state_path = experiment / "workflow" / "STATE.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        digest, manifest = gate_digest(experiment, gate)
        state["gates"][gate]["artifact_digest"] = digest
        state["gates"][gate]["artifact_count"] = len(manifest)
        state["gates"][gate]["artifacts"] = manifest
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def clone_sample(self, parent: Path) -> Path:
        target = parent / "experiment"
        shutil.copytree(SAMPLE, target, ignore=shutil.ignore_patterns("build", "deliverables", "POLISH_BASELINE.json"))
        # A copied fixture is outside examples/, so convert only its already
        # approved migration gates to ordinary user approvals.
        state_path = target / "workflow" / "STATE.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["example_only"] = False
        for gate in state["gates"].values():
            if gate["status"] == "approved":
                gate["decided_by"] = "user"
                gate["decision_text"] = "承認 test fixture"
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        writing_path = target / "spec" / "WRITING_PLAN.yaml"
        writing = yaml.safe_load(writing_path.read_text(encoding="utf-8"))
        for slot in writing["slots"]:
            slot["authorship"] = "user"
        writing_path.write_text(yaml.safe_dump(writing, allow_unicode=True, sort_keys=False), encoding="utf-8")
        # These tests relabel an already typeset fictional fixture, not an actual
        # experiment. Rebind its fixture records to that deliberately changed label.
        for mode in ("skeleton", "candidate"):
            source = SAMPLE / "build" / ("skeleton.pdf" if mode == "skeleton" else "final-candidate.pdf")
            if not source.is_file() and mode == "candidate":
                source = SAMPLE / "deliverables/report.pdf"
            if not source.is_file() and mode == "skeleton":
                source = SAMPLE / "preview/skeleton.pdf"
            record = record_build(target, mode, source)
            if mode == "candidate":
                for name in ("FINAL_CHECK", "QUALITY_REVIEW", "PROFESSOR_REVIEW"):
                    path = target / "quality" / f"{name}.yaml"
                    data = yaml.safe_load(path.read_text(encoding="utf-8"))
                    data.update(reviewed_pdf_sha256=record["pdf_sha256"], reviewed_inputs_digest=record["inputs_digest"])
                    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.refresh_gate(target, "G1")
        self.refresh_gate(target, "G2")
        return target

    def test_completed_sample_passes_phase_7(self) -> None:
        result = run(VALIDATOR, SAMPLE, "--phase", "7")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_g1_summary_has_at_most_five_items(self) -> None:
        self.assertLessEqual(len(packet_g1(SAMPLE)), 5)

    def test_default_template_omits_optional_audit_documents(self) -> None:
        template = ROOT / "templates" / "experiment"
        self.assertFalse((template / "RUBRIC_TRACEABILITY.md").exists())
        self.assertFalse((template / "ORAL_DEFENSE.md").exists())
        self.assertFalse((template / "IMPROVEMENT_BACKLOG.yaml").exists())

    def test_external_claim_without_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "spec" / "CLAIMS.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["claims"][0]["source_ids"] = []
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "5")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external claim C-001 has no source", result.stdout)

    def test_unknown_ai_policy_is_rejected_before_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "spec" / "ACADEMIC_INTEGRITY.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["ai_use"]["status"] = "unknown"
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "1")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AI-use policy must be resolved", result.stdout)

    def test_unapproved_local_style_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            section = experiment / "report" / "sections" / "01-purpose.tex"
            section.write_text(section.read_text(encoding="utf-8") + "\n\\geometry{margin=10mm}\n", encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "6")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("style command requires approved", result.stdout)

    def test_final_validation_rejects_missing_user_prose(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            (experiment / "prose" / "typeset" / "P-005.tex").unlink()
            result = run(VALIDATOR, experiment, "--phase", "6")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("typeset prose is missing for P-005", result.stdout)

    def test_nonexample_cannot_claim_example_fixture_authorship(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "spec" / "WRITING_PLAN.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["slots"][0]["authorship"] = "example_fixture"
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.refresh_gate(experiment, "G2")
            result = run(VALIDATOR, experiment, "--phase", "6")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("authorship must be user", result.stdout)

    def test_prose_files_do_not_invalidate_g2_structure_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            before, _ = gate_digest(experiment, "G2")
            prose = experiment / "prose" / "original" / "P-001.md"
            prose.write_text(prose.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            plan_path = experiment / "spec" / "WRITING_PLAN.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["status"] = "prose_complete"
            plan["slots"][0]["original_sha256"] = "0" * 64
            plan["slots"][0]["status"] = "typeset"
            plan["slots"][0]["proofread_notes"] = "受領済み"
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
            after, _ = gate_digest(experiment, "G2")
            self.assertEqual(before, after)

    def test_skeleton_validation_uses_planned_references_before_user_prose(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            shutil.rmtree(experiment / "prose" / "typeset")
            (experiment / "prose" / "typeset").mkdir()
            plan_path = experiment / "spec" / "WRITING_PLAN.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["status"] = "skeleton_ready"
            for slot in plan["slots"]:
                slot["status"] = "awaiting_user"
                slot["original_sha256"] = None
                slot["proofread_notes"] = None
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "5")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_g1_approval_becomes_stale_after_reviewed_input_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "spec" / "REPORT_META.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["cover"]["title"] += "（変更）"
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "3")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("G1 approval is stale", result.stdout)

    def test_raw_data_change_after_seal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "data" / "raw" / "timings.csv"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "3")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("raw data hash mismatch", result.stdout)

    def test_reproduction_rejects_changed_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "data" / "processed" / "summary.csv"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = run(REPRODUCE, "verify", experiment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("differs from sealed output", result.stderr)

    def test_text_output_line_endings_do_not_invalidate_seal_or_g2(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            path = experiment / "data" / "processed" / "summary.csv"
            text = path.read_text(encoding="utf-8")
            path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            result = run(VALIDATOR, experiment, "--phase", "6")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_python_cache_does_not_change_gate_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            before, _ = gate_digest(experiment, "G2")
            cache = experiment / "analysis" / "__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "analyze.cpython-test.pyc").write_bytes(b"machine-specific")
            after, manifest = gate_digest(experiment, "G2")
            self.assertEqual(before, after)
            self.assertFalse(any("__pycache__" in str(item["path"]) for item in manifest))

    def test_release_is_blocked_when_g3_is_not_approved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            state_path = experiment / "workflow" / "STATE.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["gates"]["G3"]["status"] = "pending"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(WORKFLOW, "release", experiment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("G3 has not been approved", result.stderr)

    def test_release_contains_only_required_deliverables_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            build = experiment / "build"
            build.mkdir()
            shutil.copy2(SAMPLE / "deliverables" / "report.pdf", build / "final-candidate.pdf")
            deliverables = experiment / "deliverables"
            deliverables.mkdir()
            for legacy in ("QUALITY_REVIEW.yaml", "RUBRIC_TRACEABILITY.md", "ORAL_DEFENSE.md"):
                (deliverables / legacy).write_text("legacy\n", encoding="utf-8")

            self.refresh_gate(experiment, "G3")

            result = run(WORKFLOW, "release", experiment)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                {path.name for path in deliverables.iterdir() if path.is_file()},
                {"report.pdf", "HANDOFF.md", "PROFESSOR_EVALUATION.md", "SOURCE_AUDIT.md", "RESULT_TRACEABILITY.md", "WORKLOG.md"},
            )

    def test_professor_review_is_required_for_final_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            (experiment / "quality" / "PROFESSOR_REVIEW.yaml").unlink()
            result = run(VALIDATOR, experiment, "--phase", "8", "--candidate")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing professor review", result.stdout)

    def test_released_clone_verifies_without_ignored_build_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            shutil.copytree(SAMPLE / "deliverables", experiment / "deliverables")
            self.refresh_gate(experiment, "G3")
            result = run(VALIDATOR, experiment, "--phase", "8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
