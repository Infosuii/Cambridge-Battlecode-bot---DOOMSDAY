"""Pure availability rules. GitHub I/O/CAS is performed by the dispatcher, not this module.

All times are timezone-aware UTC. Controller activity is validated by the caller
against immutable GitHub comment metadata and a registered account/session/seq.
"""
from datetime import datetime, timedelta

TIMEOUT = timedelta(minutes=30)
CHALLENGE = timedelta(minutes=20)


def _utc(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() != timedelta(0):
        raise ValueError("UTC time required")
    return dt


def lease_state(last_activity, now, *, adoption_until=None, reads_complete=True):
    """A failed/partial read never establishes expiry. Exactly 30m is valid."""
    if not reads_complete:
        return "MONITOR_UNKNOWN"
    current = _utc(now)
    adoption = _utc(adoption_until) if adoption_until else None
    if adoption and current <= adoption:
        return "AWAITING_ADOPTION" if last_activity is None else "ACTIVE"
    if last_activity is None:
        if adoption is None:
            return "UNKNOWN"
        return "UNAVAILABLE_30M"
    last = _utc(last_activity)
    if last > current:
        return "MONITOR_UNKNOWN"
    age = current - last
    if age > TIMEOUT:
        return "UNAVAILABLE_30M"
    if age >= CHALLENGE:
        return "CHALLENGE"
    return "ACTIVE"


def accept_control(agent, event, now):
    """Return a new agent record or reject invalid/replayed control input.

    event.created_at must come from GitHub, event.verified=True only after the
    caller validates comment metadata/format and account/session identity.
    Late activity after a real >30m gap requires recovery, never silent renewal.
    """
    if not event.get("verified") or event.get("kind") != "CONTROL":
        raise ValueError("not verified controller activity")
    if event.get("account") not in agent["accounts"]:
        raise ValueError("unregistered account")
    if event.get("session") != agent.get("session"):
        raise ValueError("new session needs registration")
    if event.get("seq", -1) <= agent.get("seq", -1):
        raise ValueError("duplicate or old sequence")
    at = _utc(event["created_at"])
    if at > _utc(now):
        raise ValueError("future server timestamp")
    previous = agent.get("last_control_at")
    if previous and at <= _utc(previous):
        raise ValueError("old event timestamp")
    was_unavailable = agent.get("state") in {"UNAVAILABLE_30M", "RETURNING"}
    gap = previous and at - _utc(previous) > TIMEOUT
    grace = agent.get("adoption_until")
    gap_after_grace = gap and (not grace or at > _utc(grace))
    recovered = bool(was_unavailable or gap_after_grace)
    result = dict(agent, seq=event["seq"], last_control_at=event["created_at"])
    result["state"] = "RETURNING" if recovered else "ACTIVE"
    result["requires_new_assignment"] = recovered
    return result


def revoke_tasks(tasks, owner, *, transition_id):
    """Revocation result is committed with the agent transition in ONE CAS write."""
    updated = []
    for task in tasks:
        t = dict(task)
        if t.get("owner") == owner and t.get("state") not in {"DONE", "RELEASED"}:
            t.update(owner=None, owner_session=None, epoch=t["epoch"] + 1,
                     state="READY_UNASSIGNED", transition_id=transition_id)
            if t.get("platform_sensitive"):
                t["platform_state"] = "QUARANTINED"
        updated.append(t)
    return updated


def eligible(worker, task, now):
    return (worker.get("protocol_ack") is True
            and worker.get("state") == "ACTIVE"
            and lease_state(worker.get("last_control_at"), now) == "ACTIVE"
            and not worker.get("requires_new_assignment", False)
            and set(task.get("requires", [])).issubset(worker.get("capabilities", []))
            and worker.get("free_capacity", 0) > 0)


def can_publish(task, agent_id, session, epoch):
    return (task.get("owner") == agent_id
            and task.get("owner_session") == session
            and task.get("epoch") == epoch
            and task.get("state") == "ACTIVE")
