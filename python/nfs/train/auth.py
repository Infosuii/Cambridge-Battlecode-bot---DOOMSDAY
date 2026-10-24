"""Explicit training authorization and wall-clock limits for every parameter-updating entry point."""
from __future__ import annotations


class TrainingNotAuthorized(PermissionError):
    pass


def require_authorization(authorized: bool, time_limit_minutes: float | None, what: str) -> float:
    """Refuse unless the caller explicitly authorized training AND gave a positive finite time limit."""
    if not authorized:
        raise TrainingNotAuthorized(f'{what} updates model parameters; pass --i-authorize-training to run it')
    if time_limit_minutes is None:
        raise TrainingNotAuthorized(f'{what} requires an explicit --time-limit-minutes')
    t = float(time_limit_minutes)
    if not (0.0 < t < 24 * 60):
        raise TrainingNotAuthorized(f'{what}: time limit must be in (0, 1440) minutes, got {t}')
    return t
