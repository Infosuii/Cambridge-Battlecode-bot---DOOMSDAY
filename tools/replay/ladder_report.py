"""Win/loss breakdown of our recent ranked matches (cambc matches list --json output) by opponent rank, map, end
reason and draft.

    python tools/replay/ladder_report.py --matches <recent_ranked.json> --ladder <ladder_all.json> [--team DOOMSDAY]
"""
import argparse
from collections import defaultdict
import json


def rate(rows):
    return f"{sum(rows)}/{len(rows)} ({sum(rows) / len(rows):.0%})" if rows else '-'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--matches', required=True); p.add_argument('--ladder', required=True); p.add_argument('--team', default='DOOMSDAY')
    a = p.parse_args()
    ladder = {t['teamId']: t for t in json.load(open(a.ladder, encoding='utf-8'))}
    games = []
    for m in json.load(open(a.matches, encoding='utf-8')):
        if m['status'] != 'finished' or len(m['teams']) != 2:
            continue
        me, them = sorted(m['teams'], key=lambda t: t['name'].lower() != a.team.lower())
        rank = ladder.get(them['teamId'], {}).get('rank', 999)
        games.append(dict(win=me['result'] == 'win', map=m['map'], end=m.get('endReason'), side=me['side'], rank=rank,
                          opp=them['name'], mine=me['characters'], theirs=them['characters']))
    print('games', len(games), 'overall', rate([g['win'] for g in games]))
    brackets = [(1, 10), (11, 25), (26, 50), (51, 86), (87, 150), (151, 999)]
    print('by opponent ladder rank: ' + '  '.join(f"{lo}-{hi}: {rate([g['win'] for g in games if lo <= g['rank'] <= hi])}" for lo, hi in brackets))
    print('by side: ' + '  '.join(f"{s}: {rate([g['win'] for g in games if g['side'] == s])}" for s in ('a', 'b')))
    print('by end reason (wins/games): ' + '  '.join(f"{e}: {rate([g['win'] for g in games if g['end'] == e])}" for e in sorted({g['end'] for g in games}, key=str)))
    by_map = defaultdict(list)
    for g in games:
        by_map[g['map']].append(g)
    print('by map, all opponents | top-50 opponents:')
    for name, rows in sorted(by_map.items(), key=lambda kv: sum(g['win'] for g in kv[1]) / len(kv[1])):
        print(f"  {name:24} {rate([g['win'] for g in rows]):16} | {rate([g['win'] for g in rows if g['rank'] <= 50])}")
    for label, key in (('our pick', 'mine'), ('their pick', 'theirs')):
        by_char = defaultdict(list)
        for g in games:
            for c in set(g[key]):
                by_char[c].append(g['win'])
        print(f'win rate when {label} includes character (games >= 20): ' + '  '.join(
            f'{c}:{rate(v)}' for c, v in sorted(by_char.items(), key=lambda kv: sum(kv[1]) / len(kv[1])) if len(v) >= 20))
    worst = defaultdict(list)
    for g in games:
        worst[(g['opp'], g['rank'])].append(g['win'])
    print('opponents played >= 8 times, worst first: ' + '  '.join(
        f'{n}(#{r}):{rate(v)}' for (n, r), v in sorted(worst.items(), key=lambda kv: sum(kv[1]) / len(kv[1])) if len(v) >= 8))


if __name__ == '__main__':
    main()
