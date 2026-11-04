import unittest
from lease_rules import lease_state, accept_control, revoke_tasks, eligible, can_publish

BASE = "2026-11-04T01:00:00Z"


class LeaseTests(unittest.TestCase):
    def test_strict_thirty_minutes(self):
        self.assertEqual(lease_state(BASE, "2026-11-04T01:30:00Z"), "CHALLENGE")
        self.assertEqual(lease_state(BASE, "2026-11-04T01:30:01Z"), "UNAVAILABLE_30M")

    def test_outage_is_not_expiry(self):
        self.assertEqual(lease_state(BASE, "2026-11-04T03:00:00Z", reads_complete=False), "MONITOR_UNKNOWN")

    def test_adoption_grace(self):
        self.assertEqual(lease_state(None, "2026-11-04T01:30:00Z", adoption_until="2026-11-04T01:30:00Z"), "AWAITING_ADOPTION")
        self.assertEqual(lease_state(None, "2026-11-04T01:30:01Z", adoption_until="2026-11-04T01:30:00Z"), "UNAVAILABLE_30M")

    def agent(self):
        return dict(accounts=["Infosuii"], session="s1", seq=2, state="ACTIVE", last_control_at=BASE)

    def event(self, **kw):
        e = dict(verified=True, kind="CONTROL", account="Infosuii", session="s1", seq=3,
                 created_at="2026-11-04T01:10:00Z")
        e.update(kw)
        return e

    def test_short_gap_is_not_return(self):
        a = accept_control(self.agent(), self.event(), "2026-11-04T01:11:00Z")
        self.assertEqual(a["state"], "ACTIVE")
        self.assertFalse(a["requires_new_assignment"])

    def test_late_heartbeat_does_not_reclaim(self):
        a = accept_control(self.agent(), self.event(created_at="2026-11-04T01:31:00Z"), "2026-11-04T01:32:00Z")
        self.assertEqual(a["state"], "RETURNING")
        self.assertTrue(a["requires_new_assignment"])

    def test_replay_runner_foreign_and_future_rejected(self):
        for patch in [dict(seq=2), dict(kind="RUNNER"), dict(account="other"),
                      dict(session="old"), dict(created_at="2026-11-05T01:00:00Z")]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                accept_control(self.agent(), self.event(**patch), "2026-11-04T01:11:00Z")

    def test_revoke_fences_old_owner_and_quarantines_platform(self):
        t = dict(id="t", owner="builder", owner_session="s1", epoch=1, state="ACTIVE", platform_sensitive=True)
        new = revoke_tasks([t], "builder", transition_id="t-e2")[0]
        self.assertEqual(new["epoch"], 2)
        self.assertEqual(new["platform_state"], "QUARANTINED")
        self.assertFalse(can_publish(new, "builder", "s1", 1, now="2026-11-04T01:31:00Z", owner_last_control_at=BASE))
        self.assertEqual(revoke_tasks([new], "builder", transition_id="retry")[0], new)

    def test_publish_checks_expiry_even_before_dispatcher_revokes(self):
        t = dict(owner="builder", owner_session="s1", epoch=1, state="ACTIVE")
        self.assertTrue(can_publish(t, "builder", "s1", 1, now="2026-11-04T01:30:00Z", owner_last_control_at=BASE))
        self.assertFalse(can_publish(t, "builder", "s1", 1, now="2026-11-04T01:30:01Z", owner_last_control_at=BASE))
        self.assertFalse(can_publish(t, "builder", "s1", 1, now="2026-11-04T01:01:00Z", owner_last_control_at=BASE, reads_complete=False))

    def test_heavy_work_requires_live_capable_worker(self):
        w = dict(protocol_ack=True, state="ACTIVE", last_control_at=BASE, capabilities=["review"], free_capacity=1)
        self.assertFalse(eligible(w, dict(requires=["heavy-build"]), "2026-11-04T01:05:00Z"))
        self.assertTrue(eligible(w, dict(requires=["review"]), "2026-11-04T01:05:00Z"))
        w["state"] = "RETURNING"
        self.assertFalse(eligible(w, dict(requires=["review"]), "2026-11-04T01:05:00Z"))


if __name__ == "__main__":
    unittest.main()
