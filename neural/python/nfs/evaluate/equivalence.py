"""Independent per-cell equivalence comparator (Agent H). Deliberately does not share code with Agent A's
tools/audit_equivalence.py, so the two can cross-check each other.

Verified on engine 1.0.3 (archive/agents/H/REPORT.md): `replay.repl26a` and `summary.json` do not depend on bot file names
and do not change when a bot burns extra fuel without changing actions; only the team's `.fuel` member changes.
Therefore:
* actions identical  <=> replay.repl26a member bytes identical (summary.json identical as a second witness);
* fuel identical     <=> both `.fuel` members identical;
* outputs identical  <=> stdout/debug members identical.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from . import fuel as fuel_mod

MEMBERS = ('replay.repl26a', 'team-a.fuel', 'team-b.fuel', 'team-a.stdout', 'team-b.stdout', 'team-a.debug',
           'team-b.debug')


def _bundle(folder: Path) -> Path | None:
    b = sorted(Path(folder).glob('*.repl26a'))
    return b[0] if b else None


def fingerprint(folder) -> dict:
    """sha256 of every replay-bundle member and of summary.json, plus outcome fields."""
    folder = Path(folder)
    out: dict = {'folder': str(folder), 'members': {}}
    b = _bundle(folder)
    if b is not None:
        with zipfile.ZipFile(b) as z:
            for name in z.namelist():
                out['members'][name] = hashlib.sha256(z.read(name)).hexdigest()
    sp = folder / 'summary.json'
    if sp.exists():
        raw = sp.read_bytes()
        out['summary_sha256'] = hashlib.sha256(raw).hexdigest()
        s = json.loads(raw)
        out['outcome'] = s['match']['outcome']
        out['rounds'] = int(s['match']['roundsStarted'])
        out['gems'] = {t['team']: int(t['submittedGems']) for t in s['teams']}
        out['engine'] = s['match']['engineVersion']
        out['map_hash'] = s['match'].get('mapHash')
    return out


def _event_stream(summary: dict) -> list[tuple]:
    rows = []
    for e in summary.get('events', []):
        o = e.get('owner', {})
        for x in e.get('entries', []):
            ts = x.get('timestamp', {})
            rows.append((int(ts.get('ordinal', 0)), int(ts.get('round', -1)), e.get('kind'), o.get('team'), o.get('id'),
                         json.dumps(x.get('target'), sort_keys=True), x.get('value'), x.get('x'), x.get('y')))
    rows.sort()
    return rows


def first_divergent_round(summary_a: dict, summary_b: dict) -> int | None:
    """Earliest round at which the ordered event streams differ (None if identical). Fuel-insensitive."""
    a, b = _event_stream(summary_a), _event_stream(summary_b)
    for x, y in zip(a, b):
        if x[1:] != y[1:]:
            return min(x[1], y[1])
    if len(a) != len(b):
        longer = a if len(a) > len(b) else b
        return longer[min(len(a), len(b))][1]
    if summary_a.get('teams') != summary_b.get('teams') or summary_a['match'].get('outcome') != summary_b['match'].get('outcome'):
        return int(min(summary_a['match']['roundsStarted'], summary_b['match']['roundsStarted']))
    return None


def compare(cand_folder, ref_folder, cand_team: str | None = None) -> dict:
    """Compare one candidate cell to the reference cell with the same (map, side, opponent).

    cand_team: 'teamA'/'teamB' seat of the candidate (for the fuel-overhead series); None skips overhead.
    """
    fa, fb = fingerprint(cand_folder), fingerprint(ref_folder)
    ma, mb = fa['members'], fb['members']
    same = {m: (ma.get(m) is not None and ma.get(m) == mb.get(m)) for m in MEMBERS if m in ma or m in mb}
    res = dict(actions_identical=same.get('replay.repl26a', False),
               summary_identical=fa.get('summary_sha256') == fb.get('summary_sha256') and 'summary_sha256' in fa,
               fuel_identical=same.get('team-a.fuel', False) and same.get('team-b.fuel', False),
               stdout_identical=same.get('team-a.stdout', False) and same.get('team-b.stdout', False),
               members=same, outcome_same=fa.get('outcome') == fb.get('outcome'),
               cand=dict(outcome=fa.get('outcome'), gems=fa.get('gems'), rounds=fa.get('rounds')),
               ref=dict(outcome=fb.get('outcome'), gems=fb.get('gems'), rounds=fb.get('rounds')),
               engine=[fa.get('engine'), fb.get('engine')])
    if not res['summary_identical'] and 'summary_sha256' in fa and 'summary_sha256' in fb:
        sa = json.loads((Path(cand_folder) / 'summary.json').read_text(encoding='utf-8'))
        sb = json.loads((Path(ref_folder) / 'summary.json').read_text(encoding='utf-8'))
        res['first_divergent_round'] = first_divergent_round(sa, sb)
    else:
        res['first_divergent_round'] = None
    if cand_team and not res['fuel_identical'] and res['actions_identical']:
        # per-turn overhead is only meaningful when both trajectories are the same (turn i == turn i)
        try:
            res['candidate_fuel_overhead'] = fuel_mod.overhead(cand_folder, ref_folder, cand_team)
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            res['candidate_fuel_overhead'] = dict(error=str(exc))
    return res


def summarize(comparisons: list[dict]) -> dict:
    n = len(comparisons)
    div = [c for c in comparisons if not c['actions_identical']]
    rounds = [c['first_divergent_round'] for c in div if c.get('first_divergent_round') is not None]
    return dict(cells=n, actions_identical=n - len(div), summary_identical=sum(c['summary_identical'] for c in comparisons),
                fuel_identical=sum(c['fuel_identical'] for c in comparisons),
                outcome_flips=sum(not c['outcome_same'] for c in comparisons), divergent_cells=len(div),
                first_divergent_round_min=min(rounds) if rounds else None,
                first_divergent_round_median=sorted(rounds)[len(rounds) // 2] if rounds else None,
                all_actions_identical=n > 0 and not div)
