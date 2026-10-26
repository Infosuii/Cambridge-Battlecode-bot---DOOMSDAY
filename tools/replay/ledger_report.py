"""Actor-level opening ledger report for v54 (offline analysis; no bot inputs).

Reads the per-actor ledger written by actor_ledger.mjs and the committed ladder snapshots, and reports how each
team spent its champion-rounds and where capture income came from, by cohort and round window.
Usage: python tools/replay/ledger_report.py [ledger.json] [out.md]
"""
from collections import defaultdict
import json
from pathlib import Path
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[2]
TYPES = ['Ryth', 'Vesper', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart']
ACTS = ['clear', 'pvp', 'cast', 'bank', 'spawn', 'travel', 'still']


def load_meta():
    data = ROOT / 'data/ladder'
    v52 = json.loads((data / 'v52_since_live_20261025.json').read_text())
    control = json.loads((data / 'v54_control_wins_20261025.json').read_text())
    targeted = []
    for name in ['hidden', 'meow']:
        targeted += json.loads((data / f'v53_group_{name}_status_20261025.json').read_text(encoding='utf-8-sig'))['matches']
    latest = [m for m in json.loads((data / 'v53_since_live_analysis_20261025.json').read_text()) if m['status'] == 'finished']
    extra = []
    for f in sorted(data.glob('*.json')):
        try:
            d = json.loads(f.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        if isinstance(d, dict):
            d = d.get('matches', [])
        if isinstance(d, list):
            extra += [m for m in d if isinstance(m, dict) and 'matchId' in m and 'teams' in m]
    meta = {m['matchId']: m for m in extra}
    meta.update({m['matchId']: m for m in v52 + control + latest + targeted})
    tids = {m['matchId'] for m in targeted}
    return meta, latest, tids


def team_stats(g, team, W):
    acts = [a for a in g['actors'] if a['team'] == team]
    tot = defaultdict(float)
    for a in acts:
        for k, v in a['w'].get(str(W), {}).items():
            tot[k] += v
    alive = max(1.0, tot['alive'])
    n = max(1, len(acts))
    out = {'actors': len(acts), 'dead_share': tot['dead'] / max(1.0, tot['alive'] + tot['dead'])}
    for k in ACTS:
        out[k] = tot[k] / alive
    out['cap_gold_per_actor'] = tot['cap_gold'] / n
    out['cap_gold_per_alive_100'] = 100 * tot['cap_gold'] / alive
    out['clear_gold_per_clear_round'] = tot['cap_gold'] / max(1.0, tot['clear'] + tot['cast'])
    out['caps_per_actor'] = tot['caps'] / n
    out['shared_cap_frac'] = tot['shared_caps'] / max(1.0, tot['caps'])
    out['kill_gold'] = tot['kill_gold']
    out['spend_per_actor'] = tot['spend'] / n
    out['zero_capture_actors'] = sum(1 for a in acts if a['w'].get(str(W), {}).get('caps', 0) == 0)
    fb = [a['first_buy'] for a in acts if a['first_buy'] is not None]
    out['median_first_buy'] = st.median(fb) if fb else None
    out['treasure_by_W'] = sum(1 for a in acts if a['emblems'].get('treasure', 10 ** 9) <= W)
    out['emblems_by_W'] = sum(sum(1 for r in a['emblems'].values() if r <= W) for a in acts) / n
    return out


def med(rows, key, i):
    xs = [r[i][key] for r in rows if r[i][key] is not None]
    return round(st.median(xs), 3) if xs else None


def main():
    ledger = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'artifacts/local-only/v53-review/ledger-all.json').read_text())
    outp = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'research/v54/V54_ACTOR_LEDGER.md')
    meta, latest, tids = load_meta()
    latest_ids = {m['matchId'] for m in latest}
    games = []
    for g in ledger:
        m = meta.get(g['id'])
        if not m:
            continue
        names = [t['name'] for t in m['teams']]
        sides = {t['name']: t['side'] for t in m['teams']}
        res = {t['name']: t['result'] for t in m['teams']}
        if 'DOOMSDAY' in names:
            us = 'ab'.index(sides['DOOMSDAY'])
            kind = 'v53' if g['id'] in latest_ids or g['id'] in tids else 'v52'
            win = res['DOOMSDAY'] == 'win'
            opp = next(n for n in names if n != 'DOOMSDAY')
        else:
            winner = next(t for t in m['teams'] if t['result'] == 'win')
            us = 'ab'.index(winner['side'])  # reference: "us" = the top-team winner
            kind = 'reference'
            win = True
            opp = next(n for n in names if n != winner['name'])
        g2 = dict(g, us=us, kind=kind, win=win, map=m['map'], opp=opp, targeted=g['id'] in tids)
        games.append(g2)
    cohorts = {
        'v53 losses': [g for g in games if g['kind'] == 'v53' and not g['win']],
        'v53 wins': [g for g in games if g['kind'] == 'v53' and g['win']],
        'v53 targeted (meow, HAK)': [g for g in games if g['targeted']],
        'v53 losses, no deaths either side by R250 (pure economy)': [],
        'v52 losses': [g for g in games if g['kind'] == 'v52' and not g['win']],
        'top-team reference wins (us = winner)': [g for g in games if g['kind'] == 'reference'],
    }
    pure = []
    for g in cohorts['v53 losses']:
        deaths = [sum(1 for a in g['actors'] if a['team'] == t for d in a['deaths'] if d['round'] <= 250) for t in [0, 1]]
        if deaths == [0, 0]:
            pure.append(g)
    cohorts['v53 losses, no deaths either side by R250 (pure economy)'] = pure
    lines = ['# Actor-level opening ledger (v54 phase 1)', '',
             'Offline omniscient replay analysis with the pinned engine (`tools/replay/actor_ledger.mjs`, this report: '
             '`tools/replay/ledger_report.py`). Never a bot input. Each alive champion-round is assigned one activity in priority '
             'order bank > PvP attack > camp attack > cast > on own spawn > travel/other. Capture income is the positive gold change '
             'between round states not explained by a kill or purchase (Marcella tribute gold is excluded when the bag drops). '
             '"Shared" captures are reward events received in the same round by allies within 3 tiles (a split reward). '
             'Values are cohort medians of per-game team values, us / opponent. Cohorts overlap and are not random samples.', '']
    summary = {}
    for name, rows in cohorts.items():
        if not rows:
            continue
        lines.append(f'## {name} — {len(rows)} games')
        lines.append('')
        lines.append('| Window | Metric | Us | Opponent |')
        lines.append('|---|---|---:|---:|')
        summary[name] = {}
        for W in [100, 250, 500]:
            pairs = [(team_stats(g, g['us'], W), team_stats(g, 1 - g['us'], W)) for g in rows]
            summary[name][W] = {}
            for key, label in [('dead_share', 'dead share of champion-rounds'), ('clear', 'camp-attack share of alive rounds'),
                               ('cast', 'cast-only share'), ('pvp', 'PvP-attack share'), ('travel', 'moving, no attack share'), ('still', 'stationary off-spawn, no attack share'),
                               ('spawn', 'on-spawn share'), ('bank', 'banking share'),
                               ('cap_gold_per_actor', 'capture gold per actor'),
                               ('cap_gold_per_alive_100', 'capture gold per 100 alive champion-rounds'),
                               ('clear_gold_per_clear_round', 'capture gold per attack/cast round'),
                               ('caps_per_actor', 'capture events per actor'), ('shared_cap_frac', 'shared-capture fraction'),
                               ('zero_capture_actors', 'actors with no capture yet'), ('median_first_buy', 'median first purchase round'),
                               ('treasure_by_W', 'actors with Treasure emblem'), ('emblems_by_W', 'emblems per actor'),
                               ('kill_gold', 'kill gold (team)')]:
                a, b = med(pairs, key, 0), med(pairs, key, 1)
                summary[name][W][key] = [a, b]
                if key == 'median_first_buy' and W != 500:
                    continue
                fmt = (lambda x: '-' if x is None else (f'{x:.2f}' if isinstance(x, float) and abs(x) < 10 else f'{x:.0f}'))
                lines.append(f'| R{W} | {label} | {fmt(a)} | {fmt(b)} |')
        lines.append('')
    # Per champion-type productivity in the first 250 rounds: ours in v53 losses vs everyone else.
    lines.append('## Capture gold by R250 per champion type (v53 games)')
    lines.append('')
    lines.append('| Type | Our actors | Our median gold | Our zero-capture share | Opp actors | Opp median gold |')
    lines.append('|---|---:|---:|---:|---:|---:|')
    by = defaultdict(lambda: [[], []])
    for g in games:
        if g['kind'] != 'v53':
            continue
        for a in g['actors']:
            side = 0 if a['team'] == g['us'] else 1
            by[a['type']][side].append(a['w'].get('250', {}).get('cap_gold', 0))
    for t in sorted(by, key=lambda t: -len(by[t][0])):
        u, o = by[t]
        if not u and not o:
            continue
        lines.append(f'| {TYPES[t]} | {len(u)} | {st.median(u) if u else "-"} | {sum(1 for x in u if x == 0) / max(1, len(u)):.2f} | '
                     f'{len(o)} | {st.median(o) if o else "-"} |')
    lines.append('')
    outp.write_text('\n'.join(lines) + '\n', encoding='utf8')
    (outp.with_suffix('.json')).write_text(json.dumps(summary, indent=1) + '\n', encoding='utf8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
