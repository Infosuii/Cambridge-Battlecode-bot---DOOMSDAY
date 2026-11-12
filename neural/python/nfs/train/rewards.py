"""Objective-aligned reward with separate, configurable and ablatable components.

The game objective (engine 1.0.3, SDK constants): a team wins by submitting `winning_gems` gems at an altar, or at
`max_rounds` the engine resolves the winner with its own tiebreakers. The summary's `match.outcome` is authoritative;
we never re-implement tiebreakers. Carried gems are worth nothing at the end and are dropped on death.

Return of an agent stream (per champion, per match), rounds t = 0..T, discount gamma per round:

    G = sum_t gamma^t r_t,   r_t = terminal_t + deposit_t + carry_shaping_t + economy_t + death_t + damage_t + objective_t

- terminal (t = T-1 only): +win / -win / tie, plus margin * clip((own team gems - opponent gems) / margin_scale, -1, 1).
  This is the objective; every other term is a small, documented helper.
- deposit: w_submitted * (own submitted gems delta) [+ w_team_submitted * team delta]. Banking is the only way
  carried gems become score, so it is rewarded directly.
- carry_shaping: potential-based shaping F_t = gamma * Phi(s_{t+1}) - Phi(s_t), Phi = carry_potential * carried gems,
  and Phi(terminal) = 0. It telescopes: sum_t gamma^t F_t = -Phi(s_0) (= 0 at spawn), so it cannot change which
  policy is optimal (Ng et al. 1999); picking up a bag and then losing it (death, or the game ending) nets exactly
  zero in discounted return, while depositing converts the potential into the larger deposit reward.
- economy: w_gold * earned gold (small explicit weight; gold only matters through items).
- death: -w_death per death (the bag loss is already priced by the shaping term).
- damage: w_damage * champion damage done (small; ablatable).
- objective: w_objective * objective-control events (camp clears) (small; ablatable).

Default scale (fixtures in tests/python/test_train_rewards.py): a typical full match gives dense terms well below the
terminal win term, so the win/margin dominates and dense terms only break ties between otherwise similar
trajectories. `scale_report` checks this for any configuration.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields

import numpy as np

COMPONENTS = ('terminal', 'deposit', 'carry_shaping', 'economy', 'death', 'damage', 'objective')


@dataclass
class RewardConfig:
    gamma: float = 0.9997                # per round; 0.9997^2000 = 0.55, so the terminal objective reaches early decisions
    win: float = 1.0
    tie: float = 0.0
    margin: float = 0.5
    margin_scale: float = 1000.0
    w_submitted: float = 5e-4            # per own submitted gem
    w_team_submitted: float = 0.0        # optional team-share of deposits
    carry_potential: float = 3e-4        # Phi = carry_potential * carried gems; must be <= w_submitted
    w_gold: float = 1e-5                 # per earned gold (small)
    w_death: float = 0.03                # per death
    w_damage: float = 2e-6               # per champion damage point dealt
    w_objective: float = 0.005           # per camp clear
    ablate: tuple = ()                   # component names forced to zero

    def validate(self) -> 'RewardConfig':
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError(f'reward weight {f.name} is not finite')
        if not 0.0 < self.gamma <= 1.0:
            raise ValueError('gamma must be in (0, 1]')
        if self.carry_potential > self.w_submitted:
            raise ValueError('carry_potential must not exceed w_submitted (carrying must be worth less than banking)')
        if self.carry_potential < 0 or self.w_death < 0 or self.w_submitted < 0:
            raise ValueError('carry_potential, w_death and w_submitted must be non-negative')
        bad = set(self.ablate) - set(COMPONENTS)
        if bad:
            raise ValueError(f'unknown ablated components {sorted(bad)}')
        return self

    def on(self, comp: str) -> float:
        return 0.0 if comp in self.ablate else 1.0

    @classmethod
    def from_dict(cls, d: dict) -> 'RewardConfig':
        d = dict(d or {})
        if 'ablate' in d:
            d['ablate'] = tuple(d['ablate'])
        return cls(**{k: v for k, v in d.items() if not k.startswith('_')}).validate()

    def to_dict(self) -> dict:
        d = asdict(self)
        d['ablate'] = list(self.ablate)
        return d


@dataclass
class AgentSeries:
    """Cumulative per-round values for one agent, index 0..T (length T+1, value at the START of round index)."""
    submitted: np.ndarray
    carried: np.ndarray
    gold: np.ndarray
    deaths: np.ndarray
    damage: np.ndarray
    objective: np.ndarray
    team_submitted: np.ndarray | None = None
    outcome: str = 'tie'                 # 'win' | 'loss' | 'tie' for this agent's team
    final_team_gems: float = 0.0
    final_opponent_gems: float = 0.0

    @property
    def T(self) -> int:
        return len(self.submitted) - 1


def terminal_reward(outcome: str, own_gems: float, opp_gems: float, cfg: RewardConfig) -> float:
    base = cfg.win if outcome == 'win' else -cfg.win if outcome == 'loss' else cfg.tie
    m = float(np.clip((own_gems - opp_gems) / cfg.margin_scale, -1.0, 1.0))
    return (base + cfg.margin * m) * cfg.on('terminal')


def per_round_components(s: AgentSeries, cfg: RewardConfig) -> dict[str, np.ndarray]:
    """Reward components for each transition t -> t+1 (arrays of length T)."""
    cfg.validate()
    T = s.T
    if T < 1:
        raise ValueError('series needs at least one transition')
    g = cfg.gamma
    d = lambda a: np.diff(np.asarray(a, dtype=np.float64))
    out = {c: np.zeros(T) for c in COMPONENTS}
    out['deposit'] = cfg.w_submitted * d(s.submitted)
    if s.team_submitted is not None and cfg.w_team_submitted:
        out['deposit'] = out['deposit'] + cfg.w_team_submitted * d(s.team_submitted)
    phi = cfg.carry_potential * np.asarray(s.carried, dtype=np.float64).copy()
    phi[-1] = 0.0                                                    # terminal potential is zero
    out['carry_shaping'] = g * phi[1:] - phi[:-1]
    out['economy'] = cfg.w_gold * d(s.gold)
    out['death'] = -cfg.w_death * d(s.deaths)
    out['damage'] = cfg.w_damage * d(s.damage)
    out['objective'] = cfg.w_objective * d(s.objective)
    out['terminal'][-1] = terminal_reward(s.outcome, s.final_team_gems, s.final_opponent_gems, cfg)
    for c in COMPONENTS:
        if c != 'terminal':
            out[c] = out[c] * cfg.on(c)
    return out


def total(components: dict[str, np.ndarray]) -> np.ndarray:
    return sum(components[c] for c in COMPONENTS)


def discounted_return(r: np.ndarray, gamma: float, start: int = 0) -> float:
    r = np.asarray(r[start:], dtype=np.float64)
    return float(np.sum(r * gamma ** np.arange(len(r))))


def interval_rewards(components: dict[str, np.ndarray], boundaries: list[int], gamma: float) -> list[dict]:
    """SMDP interval rewards between decision rounds b_0 < b_1 < ... (the last interval ends at T).
    R_i = sum_{t=b_i}^{b_{i+1}-1} gamma^(t-b_i) r_t, per component, plus the gap tau_i = b_{i+1} - b_i used for
    gamma^tau bootstrapping. Equal consecutive boundaries give an empty interval (tau = 0)."""
    T = len(next(iter(components.values())))
    ends = list(boundaries[1:]) + [T]
    out = []
    for b, e in zip(boundaries, ends):
        b, e = max(0, min(b, T)), max(0, min(e, T))
        w = gamma ** np.arange(max(0, e - b))
        comp = {c: float(np.sum(components[c][b:e] * w)) for c in COMPONENTS}
        out.append(dict(components=comp, reward=sum(comp.values()), tau=e - b, start=b, end=e,
                        terminal=e >= T))
    return out


def episode_breakdown(s: AgentSeries, cfg: RewardConfig) -> dict:
    comps = per_round_components(s, cfg)
    per = {c: discounted_return(comps[c], cfg.gamma) for c in COMPONENTS}
    return dict(components=per, total=sum(per.values()))


def scale_report(s: AgentSeries, cfg: RewardConfig) -> dict:
    """Dense (non-terminal) discounted magnitude versus the win term as seen from the start of the episode
    (win * gamma^T). `ok` requires the dense terms to stay below that, so the objective dominates."""
    b = episode_breakdown(s, cfg)['components']
    dense = sum(abs(v) for k, v in b.items() if k != 'terminal')
    win_at_start = cfg.win * cfg.gamma ** max(0, s.T - 1)
    return dict(components=b, dense_abs=dense, win_term=cfg.win, win_term_at_start=win_at_start,
                dense_to_win=dense / max(win_at_start, 1e-12), ok=dense < win_at_start)


# --------------------------------------------------------------------------------------------- from summaries
def _expand(runs, length: int) -> np.ndarray:
    vals = np.concatenate([np.full(int(r['duration']), float(r['value'])) for r in runs]) if runs else np.zeros(0)
    if len(vals) < length:
        vals = np.concatenate([vals, np.full(length - len(vals), vals[-1] if len(vals) else 0.0)])
    return vals[:length]


def series_from_summary(d: dict, team: str, champion_id: int, rounds: int | None = None) -> AgentSeries:
    """Build an agent's cumulative series from an engine summary (championTimelines, teamTimelines, events).
    Timeline index i is the value after i samples (sampleCount = rounds + 1)."""
    team = team if team.startswith('team') else 'team' + team.upper()
    other = 'teamB' if team == 'teamA' else 'teamA'
    n = (rounds if rounds is not None else int(d['match']['roundsStarted'])) + 1
    tl = {t['metric']: t['runs'] for t in d.get('championTimelines', [])
          if t['owner'].get('team') == team and int(t['owner'].get('id', -1)) == champion_id}
    team_tl = {t['owner']: t['runs'] for t in d.get('teamTimelines', []) if t['metric'] == 'submittedGems'}
    get = lambda m: _expand(tl.get(m, []), n)
    obj = np.zeros(n)
    for e in d.get('events', []):
        if e.get('kind') == 'campClear' and e['owner'].get('team') == team and int(e['owner'].get('id', -1)) == champion_id:
            for entry in e.get('entries', []):
                r = int(entry['timestamp']['round'])
                if 0 <= r + 1 < n:
                    obj[r + 1:] += 1
    scores = {t['team']: float(t['submittedGems']) for t in d.get('teams', [])}
    o = d['match'].get('outcome')
    outcome = 'win' if o == team else 'loss' if o == other else 'tie'
    return AgentSeries(submitted=get('submittedGems'), carried=get('gems'), gold=get('earnedGold'),
                       deaths=get('deaths'), damage=get('championDamageDone'), objective=obj,
                       team_submitted=_expand(team_tl.get(team, []), n), outcome=outcome,
                       final_team_gems=scores.get(team, 0.0), final_opponent_gems=scores.get(other, 0.0))
