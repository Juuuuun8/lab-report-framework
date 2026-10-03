import copy
import tempfile
import unittest
from pathlib import Path
import yaml

import test_quality_gates as fixtures
from task_scope import check_tasks, check_reviews
from validate_experiment import Audit, validate
from workflow import initial_state, next_actions, build_review
from workflow_core import gate_digest
from report_views import render
import scope_fixture


class TaskScopeTests(unittest.TestCase):
    clone_sample = fixtures.QualityGateTests.clone_sample
    refresh_gate = fixtures.QualityGateTests.refresh_gate

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.exp = self.clone_sample(Path(self.temp.name))
        self.req = {"task_scopes": [scope_fixture.task()], "requirements": [{"requirement_id": "REQ-001"}]}

    def check(self, phase=1):
        audit = Audit()
        check_tasks(self.exp, self.req, initial_state(), audit, phase)
        return audit.errors

    def test_new_workflow_requires_boundaries(self):
        self.assertEqual(initial_state()["version"], 2)
        self.req.pop("task_scopes")
        self.assertTrue(self.check())

    def test_legacy_is_reported_not_silently_certified(self):
        audit = Audit()
        check_tasks(self.exp, {}, {"version": 1}, audit, 1)
        self.assertEqual(audit.errors, [])
        self.assertIn("未適用", audit.notes[0])
        self.assertIn("未設定", "\n".join(next_actions(self.exp)))

    def test_ordered_tasks_accept_only_prior_dependencies(self):
        second = copy.deepcopy(self.req["task_scopes"][0])
        second.update(task_id="TASK-002", prior_task_ids=["TASK-001"])
        self.req["task_scopes"].append(second)
        self.assertEqual(self.check(5), [])
        self.req["task_scopes"][0]["prior_task_ids"] = ["TASK-002"]
        self.assertTrue(any("later" in e for e in self.check()))

    def test_unknown_requirement_and_code_role_overlap(self):
        self.req["task_scopes"][0].update(requirement_ids=["REQ-999"], submission_code=["analysis/analyze.py"])
        errors = self.check(5)
        self.assertTrue(any("unknown requirements" in e for e in errors))
        self.assertTrue(any("separate files" in e for e in errors))

    def test_unsafe_and_missing_code(self):
        task = self.req["task_scopes"][0]
        task["helper_code"] = ["../outside.py"]
        self.assertTrue(any("unsafe" in e for e in self.check()))
        task["helper_code"] = ["analysis/absent.py"]
        self.assertEqual(self.check(1), [])
        self.assertTrue(any("missing" in e for e in self.check(5)))

    def test_each_slot_and_task_need_mapping_and_reviews(self):
        record = {"task_scope_reviews": scope_fixture.reviews(), "slots": [{"slot_id": "P-001", "task_ids": ["TASK-001"]}]}
        audit = Audit()
        check_reviews(self.req, record, audit, "skeleton")
        self.assertEqual(audit.errors, [])
        record["slots"][0]["task_ids"] = ["TASK-999"]
        record["task_scope_reviews"][0]["status"] = "pending"
        audit = Audit()
        check_reviews(self.req, record, audit, "skeleton")
        self.assertGreaterEqual(len(audit.errors), 3)

    def test_final_review_needs_every_task_and_actual_notes(self):
        for rows in ([], scope_fixture.reviews() * 2, [{"task_id": "TASK-001", "status": "passed", "evidence": "TODO"}]):
            audit = Audit()
            check_reviews(self.req, {"task_scope_reviews": rows}, audit, "final")
            self.assertTrue(audit.errors)

    def test_declared_code_outside_standard_directories_is_bound_to_g2(self):
        path = self.exp / "student.py"
        path.write_text("print(1)", encoding="utf-8")
        task = scope_fixture.task()
        task["submission_code"] = ["student.py"]
        scope_fixture.set_field(self.exp, "spec/ASSIGNMENT_REQUIREMENTS.yaml", "task_scopes", [task])
        before = gate_digest(self.exp, "G2")[0]
        path.write_text("print(2)", encoding="utf-8")
        self.assertNotEqual(before, gate_digest(self.exp, "G2")[0])

    def test_boundaries_appear_in_writing_and_final_views(self):
        scope_fixture.set_field(self.exp, "spec/ASSIGNMENT_REQUIREMENTS.yaml", "task_scopes", [scope_fixture.task()])
        scope_fixture.set_field(self.exp, "quality/PROFESSOR_REVIEW.yaml", "task_scope_reviews", scope_fixture.reviews())
        self.assertIn("持ち込まない内容", render(self.exp, "writing"))
        self.assertIn("学習範囲 TASK-001", render(self.exp, "evaluation"))
        self.assertTrue(any("TASK SCOPE" in e for e in validate(self.exp, 5).errors))

    def test_g1_packet_shows_actual_boundaries_and_roles(self):
        scope_fixture.set_field(self.exp, "spec/ASSIGNMENT_REQUIREMENTS.yaml", "task_scopes", [scope_fixture.task()])
        packet = build_review(self.exp, "G1", [])
        for text in ("TASK-001", "I-001 全文", "持ち込まない内容", "提出コード", "analysis/analyze.py", "コメント"):
            self.assertIn(text, packet)


if __name__ == "__main__":
    unittest.main()
