"""Verify activation and restoration require the requested pinned version."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/replay"))
import ladder_duel


def submission_state(active, selected, pinned):
    return {"active": {"version": active}, "selected": {"version": selected}, "pinned": pinned}


class PinnedActivationTest(unittest.TestCase):
    def test_latest_mode_with_same_version_must_be_pinned(self):
        latest = submission_state(80, 80, False)
        pinned = submission_state(80, 80, True)
        with patch.object(ladder_duel, "cli_json", side_effect=[latest, pinned]), \
                patch.object(ladder_duel, "cli") as activate:
            ladder_duel.activate(80)
        activate.assert_called_once_with(["submissions", "activate", "80"])

    def test_stays_pending_until_active_and_selected_agree(self):
        stale = submission_state(80, 81, True)
        pinned = submission_state(80, 80, True)
        with patch.object(ladder_duel, "cli_json", side_effect=[stale, stale, pinned]) as read, \
                patch.object(ladder_duel, "cli") as activate, patch("time.sleep") as sleep:
            ladder_duel.activate(80)
        activate.assert_called_once_with(["submissions", "activate", "80"])
        sleep.assert_called_once_with(10)
        self.assertEqual(read.call_count, 3)

    def test_verified_pin_does_not_mutate(self):
        pinned = submission_state(80, 80, True)
        with patch.object(ladder_duel, "cli_json", return_value=pinned), \
                patch.object(ladder_duel, "cli") as activate:
            ladder_duel.activate(80)
        activate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
