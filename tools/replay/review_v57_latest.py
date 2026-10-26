"""Summarize native engine2 v57 games, separating losses, wins and opponent cohorts.

No replay reconstruction or causal claim: income includes kills, and drafting/duration differ.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ['earnedGold', 'monsterDamageDone', 'championDamageDone', 'deaths', 'collectedGems', 'submittedGems']


def value_at(runs, round_number):
    cursor = 0
    for run in runs:
        cursor += run['duration']
        if round_number < cursor:
            return float(run['value'])
    return float(runs[-1]['value']) if runs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', default='artifacts/claude_ops/V57_LATEST_REVIEW_MANIFEST.json')
    ap.add_argument('--out', default='artifacts/claude_ops/V57_SPRINT3_LOSS_REVIEW.json')
    args = ap.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text(encoding='utf8'))
    cohorts = defaultdict(list)
    cases = []
    for row in manifest['matches']:
        raw = (ROOT / row['summary']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        game = json.loads(raw)
        assert game['match']['engineVersion'] == '2.0.0'
        us = 'team' + row['side'].upper()
        them = 'teamB' if us == 'teamA' else 'teamA'
        one = dict(matchId=row['matchId'], map=row['map'], opponent=row['opponent'], win=row['win'], kind=row['kind'], rounds=game['match']['roundsStarted'])
        for label, team in [('us', us), ('opponent', them)]:
            champs = [c for c in game['champions'] if c['team'] == team]
            stats = {f: sum(float(c['metrics'][f]) for c in champs) for f in FIELDS}
            stats['faults'] = game['diagnostics']['botFaults'][team]
            stats['heroes'] = {c['name']: {f: float(c['metrics'][f]) for f in FIELDS} for c in champs}
            stats['at250'] = {f: sum(value_at(t['runs'], 250) for t in game['championTimelines'] if t['owner']['team'] == team and t['metric'] == f) for f in FIELDS} if one['rounds'] >= 250 else None
            stats['at500'] = {f: sum(value_at(t['runs'], 500) for t in game['championTimelines'] if t['owner']['team'] == team and t['metric'] == f) for f in FIELDS} if one['rounds'] >= 500 else None
            stats['fuel'] = 0
            stats['earlyEmblems'] = []
            stats['deathContexts'] = Counter()
            stats['repeatDeathsWithin100'] = 0
            stats['deathGems'] = 0
            for e in game['events']:
                if not isinstance(e['owner'], dict) or e['owner'].get('team') != team:
                    continue
                if e['kind'] == 'fuelExhausted':
                    stats['fuel'] += len(e['entries'])
                if e['kind'] == 'death':
                    times = sorted(x['timestamp']['round'] for x in e['entries'])
                    stats['repeatDeathsWithin100'] += sum(b - a <= 100 for a, b in zip(times, times[1:]))
                    for x in e['entries']:
                        stats['deathContexts'][x.get('context', '')] += 1
                        stats['deathGems'] += float(x.get('amount', 0))
                if e['kind'] == 'itemCombination':
                    for x in e['entries']:
                        if x['timestamp']['round'] <= 250:
                            stats['earlyEmblems'].append(dict(hero=e['owner']['name'], round=x['timestamp']['round'], item=x['target']['name']))
            one[label] = stats
        cases.append(one)
        cohorts['all'].append(one)
        cohorts['wins' if one['win'] else 'losses'].append(one)
        cohorts['ranked' if row['kind'] == 'ranked' else 'unranked'].append(one)
        if row['kind'] == 'ranked': cohorts['ranked-wins' if one['win'] else 'ranked-losses'].append(one)
        cohorts['opponent:' + row['opponent']].append(one)
    aggregate = {}
    for key, games in cohorts.items():
        summary = dict(games=len(games), wins=sum(g['win'] for g in games), us={}, opponent={})
        for side in ['us', 'opponent']:
            s = summary[side]
            for f in FIELDS + ['fuel', 'faults', 'repeatDeathsWithin100', 'deathGems']:
                s[f] = statistics.mean(g[side][f] for g in games)
            for cutoff in ['at250', 'at500']:
                eligible = [g[side][cutoff] for g in games if g[side][cutoff] is not None]
                s[cutoff] = dict(games=len(eligible), **{f: statistics.mean(g[f] for g in eligible) for f in FIELDS}) if eligible else None
            s['earlyEmblemFamilies'] = dict(Counter(e['item'].split(' Emblem')[0] for g in games for e in g[side]['earlyEmblems']))
            s['deathContexts'] = dict(sum((g[side]['deathContexts'] for g in games), Counter()))
        aggregate[key] = summary
    # Explicit cases with the largest round250 income gaps, independent of map name.
    losses = [g for g in cases if g['kind'] == 'ranked' and not g['win'] and g['us']['at250'] is not None]
    losses.sort(key=lambda g: g['opponent']['at250']['earnedGold'] - g['us']['at250']['earnedGold'], reverse=True)
    output = dict(engine='2.0.0', live_submission=56, selected=manifest['selected'], downloaded=len(cases), failed_downloads=len(manifest['errors']),
                  limits='Native cumulative earned gold includes kills and bonuses. No inferred capture counts. Ranked games follow the v57 activation; individual match metadata does not expose submission versions. Extra20 unranked games have unverified bot identity and are not attributed to v57. Cohorts differ in opponent, map, draft and duration. These are associations, not patch causality. Death amount is recorded as provided by the engine; interpretation requires replay verification.',
                  cohorts=aggregate, largest_early_economy_loss_cases=losses[:12])
    target = ROOT / args.out
    target.write_text(json.dumps(output, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
    for name in ['all', 'losses', 'wins', 'opponent:Claudus Maximus']:
        if name in aggregate:
            g = aggregate[name]
            print(name, g['games'], 'wins', g['wins'], 'R250', g['us']['at250'], 'enemy R250', g['opponent']['at250'])


if __name__ == '__main__':
    main()
