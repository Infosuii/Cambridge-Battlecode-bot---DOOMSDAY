"""Statistics for deterministic map benchmarks.

Design rules (docs/neural-framework/EVALUATION_PROTOCOL.md section 4):
* The engine is deterministic for (wasm A, wasm B, map). A cell (map, side, opponent) is one fixed outcome, not a
  random draw; re-running it adds nothing. The only replication unit we resample is the MAP (cluster).
* Side and opponent cells on the same map are NOT independent: they share the map's structure. All opponents are
  therefore resampled jointly with the same bootstrap map indices.
* Paired comparison: candidate cell minus baseline cell with identical (opponent, map, side). The baseline is the
  original playing the candidate's seat (original-vs-X), or an incumbent candidate.
* Wilson intervals over games are reported only as a secondary, naive view (they treat games as independent).
"""
from __future__ import annotations

import itertools
import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

QUANTILE_METHOD = 'inverted_cdf'  # exact for discrete bootstrap distributions; lower bound is conservative


def wilson(k: float, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (draws may be counted as 0.5)."""
    if n <= 0:
        return (float('nan'), float('nan'))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def cell_key(row: dict) -> tuple[str, str, str]:
    return (row['opponent'], row['map'], row['side'])


def margin(row: dict) -> float:
    return float(row['gems']) - float(row['opponent_gems'])


def paired_differences(candidate: list[dict], baseline: list[dict]) -> list[dict]:
    """Per-cell differences; raises if the cell sets differ (a paired comparison needs identical cells)."""
    base = {cell_key(r): r for r in baseline}
    cand = {cell_key(r): r for r in candidate}
    if set(base) != set(cand):
        missing = sorted(set(cand) ^ set(base))[:6]
        raise ValueError(f'candidate and baseline cells differ (e.g. {missing})')
    out = []
    for k in sorted(cand):
        c, b = cand[k], base[k]
        out.append(dict(opponent=k[0], map=k[1], side=k[2], d_win=float(c['win']) - float(b['win']),
                        d_margin=margin(c) - margin(b),
                        d_fuel=int(c.get('fuel_exhausted', 0)) - int(b.get('fuel_exhausted', 0)),
                        cand_win=float(c['win']), base_win=float(b['win'])))
    return out


def per_map_means(diffs: list[dict], metric: str) -> dict[str, dict[str, float]]:
    """opponent -> map -> mean of `metric` over that map's sides."""
    acc: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for d in diffs:
        acc[d['opponent']][d['map']].append(float(d[metric]))
    return {o: {m: float(np.mean(v)) for m, v in ms.items()} for o, ms in acc.items()}


@dataclass
class Interval:
    point: float
    lo95: float          # 2.5th percentile (two-sided 95%)
    hi95: float          # 97.5th percentile
    lb_one_sided: float  # alpha-quantile (one-sided lower bound used by the gate)
    n_clusters: int

    def as_dict(self) -> dict:
        return dict(point=self.point, ci95=[self.lo95, self.hi95], one_sided_lower=self.lb_one_sided,
                    n_map_clusters=self.n_clusters)


def joint_map_bootstrap(per_map: dict[str, dict[str, float]], n_boot: int = 20000, seed: int = 20261024,
                        alpha: float = 0.05, pooled: bool = True) -> dict[str, Interval]:
    """Resample maps with replacement ONCE per replicate and apply the same indices to every series.

    per_map: series name (opponent) -> map -> value. All series must cover the same maps.
    Returns series -> Interval of the mean over maps; with pooled=True also '__pooled__' = equal-weight mean over
    series per map (computed inside each replicate, so the cross-opponent dependence is preserved).
    """
    series = sorted(per_map)
    if not series:
        raise ValueError('no series')
    maps = sorted(per_map[series[0]])
    for s in series:
        if sorted(per_map[s]) != maps:
            raise ValueError(f'series {s} does not cover the same maps')
    mat = np.array([[per_map[s][m] for s in series] for m in maps], dtype=float)  # [n_maps, n_series]
    if pooled:
        mat = np.concatenate([mat, mat.mean(axis=1, keepdims=True)], axis=1)
        series = series + ['__pooled__']
    n = len(maps)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot = mat[idx].mean(axis=1)  # [n_boot, n_series]
    out = {}
    for j, s in enumerate(series):
        col = boot[:, j]
        out[s] = Interval(point=float(mat[:, j].mean()),
                          lo95=float(np.quantile(col, 0.025, method=QUANTILE_METHOD)),
                          hi95=float(np.quantile(col, 0.975, method=QUANTILE_METHOD)),
                          lb_one_sided=float(np.quantile(col, alpha, method=QUANTILE_METHOD)), n_clusters=n)
    return out


def exact_bootstrap_distribution(values: list[float]) -> dict[float, float]:
    """Exact distribution of the bootstrap mean for small n (enumerates multinomial compositions). Test oracle."""
    n = len(values)
    dist: dict[float, float] = defaultdict(float)
    for counts in _compositions(n, n):
        coef = math.factorial(n)
        for c in counts:
            coef //= math.factorial(c)
        p = coef / n ** n
        mean = round(sum(c * v for c, v in zip(counts, values)) / n, 12)
        dist[mean] += p
    return dict(sorted(dist.items()))


def _compositions(total: int, parts: int):
    for cuts in itertools.combinations(range(total + parts - 1), parts - 1):
        prev, out = -1, []
        for c in cuts:
            out.append(c - prev - 1)
            prev = c
        out.append(total + parts - 1 - prev - 1)
        yield out


def exact_quantile(dist: dict[float, float], q: float) -> float:
    acc = 0.0
    for v, p in dist.items():
        acc += p
        if acc >= q - 1e-12:
            return v
    return max(dist)


def opponent_table(rows: list[dict]) -> dict[str, dict]:
    """Descriptive per-opponent table for one result set (wins, naive Wilson interval, margin, fuel, faults)."""
    acc: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        acc[r['opponent']].append(r)
    out = {}
    for o, rs in sorted(acc.items()):
        n = len(rs)
        wins = sum(float(r['win']) for r in rs)
        sides = {}
        for side in ('A', 'B'):
            ss = [r for r in rs if r['side'] == side]
            if ss:
                sides[side] = dict(games=len(ss), wins=sum(float(r['win']) for r in ss),
                                   mean_margin=float(np.mean([margin(r) for r in ss])))
        out[o] = dict(games=n, wins=wins, win_rate=wins / n if n else float('nan'),
                      wilson95_naive=list(wilson(wins, n)), maps=len({r['map'] for r in rs}),
                      mean_margin=float(np.mean([margin(r) for r in rs])) if rs else float('nan'),
                      fuel_exhausted_entries=sum(int(r.get('fuel_exhausted', 0)) for r in rs),
                      games_with_fuel_exhaustion=sum(1 for r in rs if int(r.get('fuel_exhausted', 0)) > 0),
                      faults=sum(int(r.get('faults', 0)) for r in rs), by_side=sides)
    return out


def paired_table(candidate: list[dict], baseline: list[dict], n_boot: int = 20000, seed: int = 20261024,
                 alpha: float = 0.05) -> dict:
    """Per-opponent paired win/margin differences with joint map-cluster bootstrap intervals."""
    diffs = paired_differences(candidate, baseline)
    win = joint_map_bootstrap(per_map_means(diffs, 'd_win'), n_boot, seed, alpha)
    mar = joint_map_bootstrap(per_map_means(diffs, 'd_margin'), n_boot, seed + 1, alpha)
    worst = defaultdict(list)
    for o, ms in per_map_means(diffs, 'd_win').items():
        worst[o] = sorted(ms.items(), key=lambda kv: kv[1])[:3]
    return dict(win=dict((k, v.as_dict()) for k, v in win.items()),
                margin=dict((k, v.as_dict()) for k, v in mar.items()),
                worst_maps_by_d_win={o: [dict(map=m, d_win=v) for m, v in w] for o, w in worst.items()},
                cells=len(diffs), method=dict(cluster='map', joint_over_opponents=True, n_boot=n_boot, seed=seed,
                                              alpha_one_sided=alpha, quantile_method=QUANTILE_METHOD))
