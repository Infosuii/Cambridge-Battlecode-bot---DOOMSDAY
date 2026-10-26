"""Compare v58 ladder losses with wins from native summaries: gem flow, economy curve, deaths and fights.

Usage: python tools/replay/v59_loss_review.py --manifest research/v59/V59_LADDER_MANIFEST.json --out research/v59/V59_LOSS_REVIEW.json
Reads every summary in the manifest (or, with --scan, every <dir>/summary.json under artifacts/local-only/v58-ladder).
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
CURVE = ['earnedGold', 'collectedGems', 'submittedGems', 'deaths', 'kills', 'gems', 'monsterDamageDone', 'championDamageDone']
MARKS = [100, 200, 300, 500, 800]


def value_at(runs, round_number, scale):
    # Timelines are sampled per input step; scale converts rounds to samples.
    cursor, target = 0, round_number * scale
    for run in runs:
        cursor += run['duration']
        if target < cursor:
            return float(run['value'])
    return float(runs[-1]['value']) if runs else 0.0


def team_stats(game, team, rounds):
    samples = game['championTimelines'][0]['sampleCount'] if game['championTimelines'] else 1
    scale = samples / max(1, rounds + 1)
    champs = [c for c in game['champions'] if c['team'] == team]
    out = dict(final={f: sum(float(c['metrics'][f]) for c in champs) for f in CURVE + ['championDamageTaken', 'monsterDamageTaken', 'healingDone', 'spentGold']})
    out['heroes'] = sorted(c['name'] for c in champs)
    out['curve'] = {}
    for r in MARKS:
        if r <= rounds:
            out['curve'][r] = {f: sum(value_at(t['runs'], r, scale) for t in game['championTimelines']
                                      if t['owner'].get('team') == team and t['metric'] == f) for f in CURVE}
    deaths, lost_to_champ, lost_to_camp, stolen_by_us = Counter(), 0.0, 0.0, 0.0
    first_death, death_rounds = None, []
    for e in game['events']:
        own = e['owner'].get('team')
        for x in e['entries']:
            r = x['timestamp']['round']
            if e['kind'] == 'death' and own == team:
                deaths[x['context']] += 1
                death_rounds.append(r)
            if e['kind'] == 'gemLoss' and own == team:
                if x['context'] == 'champion':
                    lost_to_champ += float(x['value'])
                else:
                    lost_to_camp += float(x['value'])
    out['deathContext'] = dict(deaths)
    out['deathRounds'] = sorted(death_rounds)
    out['gemsLostToChampions'] = lost_to_champ
    out['gemsLostToCamps'] = lost_to_camp
    out['fuelOuts'] = sum(len(e['entries']) for e in game['events'] if e['kind'] == 'fuelExhausted' and e['owner'].get('team') == team)
    items = Counter()
    for c in champs:
        for it in c.get('itemsBought', []):
            items[it['item'].split(' ')[0]] += int(it['quantity'])
    out['itemFamilies'] = dict(items)
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.fmean(xs), 1) if xs else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest')
    ap.add_argument('--listing', default='data/ladder/v58_since_live.json')
    ap.add_argument('--root', default='artifacts/local-only/v58-ladder')
    ap.add_argument('--out', default='research/v59/V59_LOSS_REVIEW.json')
    args = ap.parse_args()
    listing = {g['matchId']: g for g in json.loads((ROOT / args.listing).read_text(encoding='utf8'))}
    rows = []
    for path in sorted((ROOT / args.root).glob('*/summary.json')):
        key = path.parent.name
        if key not in listing:
            continue
        try:
            game = json.loads(path.read_text(encoding='utf8'))
        except ValueError:
            continue
        meta = listing[key]
        us_t = next(t for t in meta['teams'] if t['name'] == 'DOOMSDAY')
        them_t = next(t for t in meta['teams'] if t['name'] != 'DOOMSDAY')
        us, them = 'team' + us_t['side'].upper(), 'team' + them_t['side'].upper()
        rounds = game['match']['roundsStarted']
        sub = {t['team']: float(t['submittedGems']) for t in game['teams']}
        rows.append(dict(matchId=key, map=meta['map'], kind=meta['kind'], opponent=them_t['name'], win=us_t['result'] == 'win',
                         endReason=meta['endReason'], rounds=rounds, ourSubmitted=sub[us], theirSubmitted=sub[them],
                         us=team_stats(game, us, rounds), them=team_stats(game, them, rounds)))
    (ROOT / args.out).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf8')
    report(rows)


def report(rows):
    print(f'{len(rows)} games, {sum(r["win"] for r in rows)} wins')
    for label, sel in [('LOSSES', [r for r in rows if not r['win']]), ('WINS', [r for r in rows if r['win']])]:
        print(f'\n== {label} ({len(sel)}) rounds {mean([r["rounds"] for r in sel])}; ended by 1000 gems {sum(r["rounds"] < 2000 for r in sel)}')
        for side in ['us', 'them']:
            print(f'  {side:4} final: ' + ' '.join(f'{f}={mean([r[side]["final"][f] for r in sel])}' for f in
                                                ['collectedGems', 'submittedGems', 'earnedGold', 'deaths', 'kills', 'championDamageDone', 'monsterDamageDone']),
                  f'lostToChamp={mean([r[side]["gemsLostToChampions"] for r in sel])} lostToCamp={mean([r[side]["gemsLostToCamps"] for r in sel])} fuelOuts={mean([r[side]["fuelOuts"] for r in sel])}')
            for m in MARKS[:4]:
                c = [r[side]['curve'].get(m) for r in sel]
                c = [x for x in c if x]
                print(f'    R{m:<4} ' + ' '.join(f'{f}={mean([x[f] for x in c])}' for f in ['earnedGold', 'collectedGems', 'submittedGems', 'deaths', 'kills', 'gems']))
    losses = [r for r in rows if not r['win']]
    print('\nDeath contexts in losses (us):', sum((Counter(r['us']['deathContext']) for r in losses), Counter()))
    print('Death contexts in wins (us):', sum((Counter(r['us']['deathContext']) for r in rows if r['win']), Counter()))
    # Where does the loss margin come from? Collected deficit vs conversion deficit.
    print('\nLoss decomposition (submitted margin = collected margin - (our unbanked/lost) + (their unbanked/lost))')
    buckets = Counter()
    for r in losses:
        u, t = r['us']['final'], r['them']['final']
        collect_gap = u['collectedGems'] - t['collectedGems']
        if collect_gap < -100:
            kind = 'outfarmed'
        elif u['collectedGems'] - u['submittedGems'] > (t['collectedGems'] - t['submittedGems']) + 100:
            kind = 'failed-to-bank'
        else:
            kind = 'close'
        steal = r['them']['final']['kills'] >= r['us']['final']['kills'] + 3
        buckets[(kind, 'outkilled' if steal else '-')] += 1
        r['lossKind'] = kind
    for k, v in buckets.most_common():
        print(' ', k, v)
    print('\nLosses by map:')
    by_map = defaultdict(lambda: [0, 0])
    for r in rows:
        by_map[r['map']][0] += r['win']
        by_map[r['map']][1] += 1
    for m, (w, n) in sorted(by_map.items(), key=lambda kv: kv[1][0] / kv[1][1]):
        if n - w >= 2:
            print(f'  {m:24} {w}/{n}')
    print('\nOpponent drafts in losses:', Counter(h for r in losses for h in r['them']['heroes']).most_common())
    print('Our drafts in losses:', Counter(h for r in losses for h in r['us']['heroes']).most_common())
    print('Opponent drafts in wins:', Counter(h for r in rows if r['win'] for h in r['them']['heroes']).most_common())
    print('Opponent item families in losses:', sum((Counter(r['them']['itemFamilies']) for r in losses), Counter()).most_common(12))
    print('Our item families in losses:', sum((Counter(r['us']['itemFamilies']) for r in losses), Counter()).most_common(12))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
