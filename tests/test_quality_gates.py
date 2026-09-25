from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sort-benchmark"
VALIDATOR = ROOT / "scripts" / "validate_experiment.py"
POLISH_GUARD = ROOT / "scripts" / "polish_guard.py"
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
        return target

    def test_completed_sample_passes_phase_7(self) -> None:
        result = run(VALIDATOR, SAMPLE, "--phase", "7")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_polish_guard_detects_numeric_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = self.clone_sample(Path(raw))
            snapshot = run(POLISH_GUARD, "snapshot", experiment)
            self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)
            section = experiment / "report" / "sections" / "03-results.tex"
            section.write_text(section.read_text(encoding="utf-8").replace("194.74", "195.74", 1), encoding="utf-8")
            verify = run(POLISH_GUARD, "verify", experiment)
            self.assertNotEqual(verify.returncode, 0)
            self.assertIn("protected technical content changed", verify.stderr)

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

    def test_released_clone_verifies_without_ignored_build_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            experiment = Path(raw) / "experiment"
            shutil.copytree(SAMPLE, experiment, ignore=shutil.ignore_patterns("build", "POLISH_BASELINE.json"))
            state_path = experiment / "workflow" / "STATE.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["example_only"] = False
            for gate in state["gates"].values():
                gate["decided_by"] = "user"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = run(VALIDATOR, experiment, "--phase", "8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
