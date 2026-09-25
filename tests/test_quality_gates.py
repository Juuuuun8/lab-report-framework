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


if __name__ == "__main__":
    unittest.main()
