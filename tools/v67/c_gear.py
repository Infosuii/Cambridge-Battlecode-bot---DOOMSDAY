"""Gear comparison from items.json exports (tools/v67/c_items_batch.py): us vs the other team, per champion type.

Usage: c_gear.py INDEX.json --folder artifacts/local-only/duel-v74 [--only loss] [--types vesper,varg]
Per type and round: max health, gold earned so far, items held by stat (strength/focus/health) and family, and the most
common purchase orders (first 10 shard/emblem purchases, sells and combines folded in).
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
FAM = ['monster', 'power', 'durability', 'treasure', 'jungle', 'home', 'bruiser', 'tribute', 'capture', 'prospector',
       'hunter', 'skirmish', 'greed', 'collectors']
STAT = ['str', 'foc', 'hp']


def item_name(i):
    return f'{FAM[i // 6]}-{STAT[(i % 6) // 2]}{"-E" if i % 2 else ""}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index')
    ap.add_argument('--folder', required=True)
    ap.add_argument('--only', choices=['loss', 'win'])
    ap.add_argument('--types', default='')
    ap.add_argument('--rounds', default='300,500,700')
    a = ap.parse_args()
    rows = json.load(open(ROOT / a.index))
    want = set(a.types.split(',')) if a.types else None
    rounds = [r for r in a.rounds.split(',')]
    snap = collections.defaultdict(list)   # (side, type, round) -> [(maxhp, earned, items)]
    orders = collections.defaultdict(list)  # (side, type) -> [first purchases]
    for r in rows:
        if a.only and r['result'] != a.only:
            continue
        f = ROOT / a.folder / r['matchId'] / 'items.json'
        if not f.exists():
            continue
        d = json.load(open(f))
        us = 0 if r['side'] == 'a' else 1
        team = {c['id']: c['team'] for c in d['champs']}
        typ = {c['id']: NAMES[c['type']] for c in d['champs']}
        for rnd in rounds:
            for row in d['snaps'].get(rnd, []):
                cid = row[0]
                snap[('us' if team[cid] == us else 'them', typ[cid], rnd)].append((row[1], row[2], row[3:]))
        seq = collections.defaultdict(list)
        for rnd, cid, item, delta, gold in d['buys']:
            if delta > 0:
                seq[cid].extend([item_name(item)] * delta)
        for cid, s in seq.items():
            orders[('us' if team[cid] == us else 'them', typ[cid])].append(s)
    types = sorted({k[1] for k in snap}, key=NAMES.index)
    for t in types:
        if want and t not in want:
            continue
        print(f'== {t}')
        for rnd in rounds:
            line = []
            for side in ('us', 'them'):
                L = snap.get((side, t, rnd), [])
                if len(L) < 3:
                    line.append(f'{side}: -')
                    continue
                stats = collections.Counter()
                fams = collections.Counter()
                for _, _, items in L:
                    for i, n in enumerate(items):
                        if n:
                            w = n * (5 if i % 2 else 1)  # an emblem stands for its five shards
                            stats[STAT[(i % 6) // 2]] += w
                            fams[FAM[i // 6]] += w
                tot = sum(stats.values()) or 1
                line.append(f'{side}: hp {st.median(x[0] for x in L):5.0f} earned {st.median(x[1] for x in L):5.0f} '
                            f'shards {tot / len(L):4.1f} (str {100 * stats["str"] / tot:3.0f}% foc {100 * stats["foc"] / tot:3.0f}% hp {100 * stats["hp"] / tot:3.0f}%) '
                            f'fam {", ".join(f"{k} {100 * v / tot:.0f}%" for k, v in fams.most_common(4))} [n={len(L)}]')
            print(f'  R{rnd}  ' + '\n        '.join(line))
        for side in ('us', 'them'):
            O = orders.get((side, t), [])
            if not O:
                continue
            first = collections.Counter(tuple(o[:3]) for o in O)
            print(f'  {side} first three buys: ' + '; '.join(f'{" > ".join(k)} x{v}' for k, v in first.most_common(4)))


if __name__ == '__main__':
    main()
