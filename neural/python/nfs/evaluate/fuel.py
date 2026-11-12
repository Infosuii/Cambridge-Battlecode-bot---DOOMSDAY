"""Fuel and telemetry parsing.

Three sources, in decreasing authority:
1. `fuelExhausted` events in the official match summary (engine-reported; one entry per exhausted turn).
2. The replay bundle members `team-a.fuel` / `team-b.fuel`. FORMAT IS INFERRED (not documented by the CLI), verified
   by Agent H on engine 1.0.3 (archive/agents/H/TELEMETRY_FORMAT.md): 8-byte tag b'a62leuf\\0', 5 opaque header bytes, then
   little-endian int64 values: 8 budget constants (per team pair: draft, turn, first turn, turn) followed by the fuel
   USED by every turn of that team in engine order (draft picks first, then champion turns round by round).
   Exhausted turns read exactly the turn budget (100000). Cross-checked against (1) by `check_against_events`.
3. Team stdout lines starting with 'NFT1 ' (Agent B dev telemetry, only when kTelemetry). Parsed tolerantly.
"""
from __future__ import annotations

import base64
import json
import re
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

FUEL_TAG = b'a62leuf\0'
FUEL_HEADER_BYTES = 13
N_BUDGET_CONSTANTS = 8


def summary_fuel_events(summary: dict) -> dict[str, dict]:
    """team -> {'entries': n, 'by_champion': {id: n}, 'rounds': [...]} from fuelExhausted events."""
    out: dict[str, dict] = {t: dict(entries=0, by_champion={}, rounds=[]) for t in ('teamA', 'teamB')}
    for e in summary.get('events', []):
        if e.get('kind') != 'fuelExhausted':
            continue
        team = e['owner']['team']
        rec = out.setdefault(team, dict(entries=0, by_champion={}, rounds=[]))
        n = len(e['entries'])
        rec['entries'] += n
        if n:
            cid = str(e['owner'].get('id'))
            rec['by_champion'][cid] = rec['by_champion'].get(cid, 0) + n
            rec['rounds'] += [int(x['timestamp']['round']) for x in e['entries'] if 'timestamp' in x]
    for rec in out.values():
        rec['rounds'].sort()
    return out


def parse_fuel_member(raw: bytes) -> dict:
    """Decode a team-?.fuel member. Returns {'budgets': [...], 'used': np.ndarray[int64], 'header': hex}."""
    if not raw.startswith(FUEL_TAG):
        raise ValueError('not a fuel member (tag mismatch)')
    body = raw[FUEL_HEADER_BYTES:]
    if len(body) % 8:
        raise ValueError(f'fuel member body length {len(body)} is not a multiple of 8')
    vals = np.frombuffer(body, dtype='<i8')
    if len(vals) < N_BUDGET_CONSTANTS:
        raise ValueError('fuel member too short')
    return dict(header=raw[len(FUEL_TAG):FUEL_HEADER_BYTES].hex(), budgets=[int(v) for v in vals[:N_BUDGET_CONSTANTS]],
                used=vals[N_BUDGET_CONSTANTS:].astype(np.int64))


def turn_profile(parsed: dict, n_draft: int, n_champions: int, rounds: int | None = None) -> dict:
    """Split per-turn usage into draft / first champion turn / regular turns and summarise the regular tail."""
    used = parsed['used']
    draft_budget, turn_budget, first_budget = parsed['budgets'][0], parsed['budgets'][1], parsed['budgets'][2]
    draft = used[:n_draft]
    first = used[n_draft:n_draft + n_champions]
    reg = used[n_draft + n_champions:]
    prof = dict(turns=int(len(used)), draft_turns=int(len(draft)), budgets=dict(draft=draft_budget, turn=turn_budget,
                first_turn=first_budget), first_turn_max=int(first.max()) if len(first) else 0,
                draft_max=int(draft.max()) if len(draft) else 0)
    if len(reg):
        prof.update(regular_turns=int(len(reg)), mean=float(reg.mean()), p50=float(np.percentile(reg, 50)),
                    p90=float(np.percentile(reg, 90)), p99=float(np.percentile(reg, 99)),
                    p999=float(np.percentile(reg, 99.9)), max=int(reg.max()),
                    at_cap=int((reg >= turn_budget).sum()), over_90pct=int((reg >= 0.9 * turn_budget).sum()),
                    over_95pct=int((reg >= 0.95 * turn_budget).sum()))
        tail_n = max(1, len(reg) // 4)
        late = reg[-tail_n:]
        prof['late_quarter'] = dict(turns=int(len(late)), mean=float(late.mean()), p99=float(np.percentile(late, 99)),
                                    at_cap=int((late >= turn_budget).sum()))
    else:
        prof.update(regular_turns=0)
    # Consistency of the inferred layout: draft picks + one turn per champion per started round. The final round(s)
    # may be partial (observed: up to one round short when the match ends mid-round), hence the 2-round window.
    if rounds is not None and n_champions:
        expected_max = n_draft + n_champions * rounds
        prof['layout_consistent'] = bool(n_draft + n_champions * (rounds - 2) < len(used) <= expected_max)
    return prof


def cell_fuel(folder) -> dict:
    """Fuel picture of one match folder: summary events + per-team per-turn profile (+ cross-check)."""
    folder = Path(folder)
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    events = summary_fuel_events(summary)
    roster = summary.get('roster', {}).get('champions', [])
    per_team = Counter(c['team'] for c in roster)
    rounds = int(summary['match']['roundsStarted'])
    out = dict(events=events, teams={})
    bundles = sorted(folder.glob('*.repl26a'))
    if not bundles:
        return out
    with zipfile.ZipFile(bundles[0]) as z:
        names = set(z.namelist())
        for side in ('a', 'b'):
            member = f'team-{side}.fuel'
            team = 'team' + side.upper()
            if member not in names:
                continue
            try:
                parsed = parse_fuel_member(z.read(member))
            except ValueError as exc:
                out['teams'][team] = dict(error=str(exc))
                continue
            n = per_team.get(team, 0)
            prof = turn_profile(parsed, n_draft=n, n_champions=n, rounds=rounds)
            prof['cap_turns_match_events'] = prof.get('at_cap', 0) == events.get(team, {}).get('entries', 0)
            out['teams'][team] = prof
    return out


def check_against_events(cell: dict) -> bool:
    """True when every team's cap-hit regular turns equal its fuelExhausted entries (validates the inferred format)."""
    return all(t.get('cap_turns_match_events', False) for t in cell.get('teams', {}).values()) and bool(cell.get('teams'))


def used_series(folder, team: str) -> np.ndarray:
    folder = Path(folder)
    with zipfile.ZipFile(sorted(folder.glob('*.repl26a'))[0]) as z:
        return parse_fuel_member(z.read(f'team-{team[-1].lower()}.fuel'))['used']


def overhead(cand_folder, ref_folder, team: str) -> dict:
    """Per-turn fuel overhead of the same team between two replays with identical actions (aligned by turn index)."""
    a, b = used_series(cand_folder, team), used_series(ref_folder, team)
    n = min(len(a), len(b))
    d = a[:n] - b[:n]
    return dict(turns=int(n), aligned=len(a) == len(b), mean=float(d.mean()) if n else 0.0,
                p50=float(np.percentile(d, 50)) if n else 0.0, p99=float(np.percentile(d, 99)) if n else 0.0,
                max=int(d.max()) if n else 0, min=int(d.min()) if n else 0)


# ---------------------------------------------------------------- NFT1 telemetry (dev builds, Agent B format)

_KV = re.compile(r'([A-Za-z_][\w.\-/]*)=("(?:[^"\\]|\\.)*"|[^\s]+)')


_NUM = re.compile(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$')
_KIND = re.compile(r'^[A-Za-z_][\w.\-]*$')


def _value(v: str):
    if v.startswith('"') and v.endswith('"'):
        return bytes(v[1:-1], 'utf-8').decode('unicode_escape')
    if _NUM.match(v):
        return int(v) if re.match(r'^[+-]?\d+$', v) else float(v)
    if v.lower() in ('true', 'false'):
        return v.lower() == 'true'
    return v  # includes 'nan'/'inf' tokens: kept as strings (never silently turned into numbers)


def parse_nft1_line(line: str) -> dict | None:
    """One 'NFT1 ...' line -> dict, or None if not telemetry. Accepted payloads (tolerant, in order):
    JSON object; 'b64:<base64 JSON>'; '<kind> k=v k=v ...'; 'k=v ...'. Unknown shapes -> {'_raw': payload}."""
    line = line.strip().lstrip('\0')
    if not line.startswith('NFT1'):
        return None
    payload = line[4:].strip()
    if not payload:
        return {'_raw': ''}
    if payload.startswith('{'):
        try:
            obj = json.loads(payload)
            return obj if isinstance(obj, dict) else {'_raw': payload}
        except json.JSONDecodeError:
            return {'_raw': payload, '_error': 'json'}
    if payload.startswith('b64:'):
        try:
            return json.loads(base64.b64decode(payload[4:]).decode('utf-8'))
        except Exception:  # noqa: BLE001 - tolerant parser
            return {'_raw': payload, '_error': 'b64'}
    rec: dict = {}
    head, _, rest = payload.partition(' ')
    if '=' not in head:
        if not _KIND.match(head):
            return {'_raw': payload}
        rec['kind'] = head
        payload = rest
    for k, v in _KV.findall(payload):
        rec[k] = _value(v)
    if not rec:
        rec['_raw'] = payload
    return rec


def parse_telemetry(stdout: str) -> dict:
    """Aggregate NFT1 records of one team's stdout (NUL padding already removed by engine.team_stdout)."""
    recs = [r for r in (parse_nft1_line(x) for x in stdout.splitlines()) if r is not None]
    per_head: dict[str, Counter] = defaultdict(Counter)
    reasons: dict[str, Counter] = defaultdict(Counter)
    fuel: dict[str, list[float]] = defaultdict(list)
    totals: Counter = Counter()
    malformed = 0
    for r in recs:
        if '_raw' in r:
            malformed += 1
            continue
        head = str(r.get('head', r.get('h', '_turn')))
        for key in ('calls', 'admitted', 'neural', 'fallback', 'refused', 'budget_refused', 'invalid', 'nan',
                    'skipped', 'errors'):
            if isinstance(r.get(key), (int, float)):
                per_head[head][key] += r[key]
                totals[key] += r[key]
        if isinstance(r.get('reason'), (str, int)):
            reasons[head][str(r['reason'])] += int(r.get('count', 1))
        for key in ('fuel', 'spent', 'fuel_spent'):
            if isinstance(r.get(key), (int, float)):
                fuel[head].append(float(r[key]))
    return dict(records=len(recs), malformed=malformed, totals=dict(totals),
                per_head={h: dict(c) for h, c in per_head.items()}, reasons={h: dict(c) for h, c in reasons.items()},
                fuel={h: dict(n=len(v), mean=float(np.mean(v)), max=float(np.max(v))) for h, v in fuel.items() if v})
