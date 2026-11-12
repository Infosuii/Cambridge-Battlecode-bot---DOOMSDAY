"""An offline arm fixture exercises old-version activation during a duel."""
import json
from pathlib import Path
from subprocess import CompletedProcess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/replay"))
import ladder_duel


def snapshot(old_status_at):
    return {"active": {"version": 102}, "selected": {"version": 102}, "pinned": True,
            "submissions": [{"version": 105, "createdAt": "2026-11-03T09:00:00Z",
                             "status": "inactive", "statusAt": old_status_at}]}


class OlderActivationTest(unittest.TestCase):
    def run_arm(self, after, during=None):
        before = snapshot("2026-11-04T09:00:00Z")
        state = before

        def list_submissions(*_):
            nonlocal state
            previous = state
            if during is not None and state is before:
                state = during
            return previous

        def read_groups(*_):
            nonlocal state
            state = after
            return {"g": [{"status": "finished"}] * 5}

        if during is None:
            during = before.copy()
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "plan.json"
            plan.write_text(json.dumps({"groups": [{"opponent": "fixture", "opponentId": "team",
                                                    "maps": ["m"] * 5, "sides": ["a"] * 5}],
                                        "arms": {"v92": {"groups": ["pinned-group"]}}}), encoding="utf8")
            args = ["ladder_duel.py", "run", "--plan", str(plan), "--arm", "challenger", "--version", "102"]
            with patch.object(sys, "argv", args), patch.object(ladder_duel, "activate"), \
                    patch.object(ladder_duel, "wait_for_quota"), \
                    patch.object(ladder_duel, "cli_json", side_effect=list_submissions), \
                    patch.object(ladder_duel, "cli", return_value=CompletedProcess([], 0, '{"groupId":"g"}', "")), \
                    patch.object(ladder_duel, "finished_groups", side_effect=read_groups):
                error = None
                try:
                    ladder_duel.main()
                except SystemExit as exc:
                    error = str(exc)
            return json.loads(plan.read_text(encoding="utf8"))["arms"]["challenger"], error

    def test_old_version_changed_and_returned_to_inactive(self):
        arm, error = self.run_arm(snapshot("2026-11-04T10:01:00Z"))
        self.assertEqual(arm.get("contaminated"), [105])
        self.assertIn("contaminated", error or "")

    def test_unchanged_old_version_allows_result(self):
        arm, error = self.run_arm(snapshot("2026-11-04T09:00:00Z"))
        self.assertEqual(arm["groups"], ["g"])
        self.assertIsNone(error)
        self.assertNotIn("contaminated", arm)

    def test_pin_disagreement_during_arm_is_discarded(self):
        unchanged = snapshot("2026-11-04T09:00:00Z")
        during = {**unchanged, "pinned": False}
        arm, error = self.run_arm(unchanged, during)
        self.assertEqual(arm.get("contaminated"), [102])
        self.assertIn("contaminated", error or "")


if __name__ == "__main__":
    unittest.main()
