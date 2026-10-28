"""Find failure patterns of our side in a run, from native summaries (distinct games only):
- banking: collected gems that were never tributed (held at the end, or lost);
- deaths to camps vs champions; gems lost to each;
- maps where we lose by more than 500 gems.
Prints per-map aggregates sorted by unbanked gems, plus the flagged games.

Usage: c_pathology.py RUN [--top 25]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--top', type=int, default=25)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    seen = set()
    per_map = collections.defaultdict(collections.Counter)
    flagged = []
    for g in games:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
        us = 'teamA' if g['side'] == 'a' else 'teamB'
        ours = [c for c in s['champions'] if c['team'] == us]
        ids = {c['id'] for c in ours}
        collected = sum(int(c['metrics']['collectedGems']) for c in ours)
        held = sum(int(c['metrics']['gems']) for c in ours)
        submitted = next(int(t['submittedGems']) for t in s['teams'] if t['team'] == us)
        lost_champ = lost_camp = camp_deaths = champ_deaths = 0
        for e in s['events']:
            if e['kind'] == 'gemLoss' and e['owner'].get('team') == us and e['owner'].get('id') in ids:
                for x in e['entries']:
                    by_camp = x.get('context') != 'champion'
                    amt = int(float(x.get('value', 0) or 0))
                    if by_camp:
                        lost_camp += amt
                    else:
                        lost_champ += amt
            if e['kind'] == 'death' and e['owner'].get('team') == us and e['owner'].get('id') in ids:
                for x in e['entries']:
                    if x.get('context') == 'champion':
                        champ_deaths += 1
                    else:
                        camp_deaths += 1
        m = per_map[(g['map'], g['side'])]
        m['n'] += 1
        m['win'] += g['win']
        m['margin'] += g['margin']
        m['collected'] += collected
        m['submitted'] += submitted
        m['held'] += held
        m['lost_champ'] += lost_champ
        m['lost_camp'] += lost_camp
        m['camp_deaths'] += camp_deaths
        m['champ_deaths'] += champ_deaths
        if collected >= 200 and submitted < 0.4 * collected:
            flagged.append((g['map'], g['side'], g['seed'], collected, submitted, held, lost_champ, lost_camp, g['margin'],
                            Path(g['folder']).name))
    tot = collections.Counter()
    for m in per_map.values():
        tot.update(m)
    n = tot['n']
    print(f"{a.run}: {n} distinct games. Per game: collected {tot['collected'] / n:.0f}, banked {tot['submitted'] / n:.0f} "
          f"({tot['submitted'] / max(1, tot['collected']):.0%}), held at end {tot['held'] / n:.0f}, lost to champions "
          f"{tot['lost_champ'] / n:.0f}, to camps {tot['lost_camp'] / n:.0f}; deaths to champions {tot['champ_deaths'] / n:.1f}, "
          f"to camps {tot['camp_deaths'] / n:.1f}")
    print(f"\n{'map side':26s} {'n':>2s} {'win':>4s} {'margin':>7s} {'collect':>7s} {'banked':>6s} {'held':>5s} {'lostCh':>6s} "
          f"{'lostCa':>6s} {'dCamp':>5s}")
    rows = sorted(per_map.items(), key=lambda kv: (kv[1]['submitted'] - kv[1]['collected']) / kv[1]['n'])
    for (mp, side), m in rows[:a.top]:
        k = m['n']
        print(f"{mp + ' ' + side:26s} {k:2d} {m['win'] / k:4.2f} {m['margin'] / k:+7.0f} {m['collected'] / k:7.0f} "
              f"{m['submitted'] / k:6.0f} {m['held'] / k:5.0f} {m['lost_champ'] / k:6.0f} {m['lost_camp'] / k:6.0f} "
              f"{m['camp_deaths'] / k:5.1f}")
    print(f'\nflagged games (collected >= 200, banked < 40%): {len(flagged)}')
    for f in sorted(flagged, key=lambda r: r[4] - r[3])[:a.top]:
        print('  ', f)


if __name__ == '__main__':
    main()
