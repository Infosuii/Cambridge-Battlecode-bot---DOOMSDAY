"""Ladder test of the counter table: x3ctr differs from v92 only on the (map, side) cells its table switched
(bots/x3ctr/src/x1_counter.h). Compare those cells' win rate in the x3ctr era against the v92 era, with the other
cells as the control (difference in differences).
  python data/ladder/x3ctr/table_test.py"""
import json, re, math
from pathlib import Path
D = Path(__file__).resolve().parent; ROOT = D.parents[2]
rows = set()
for line in (ROOT / 'bots/x3ctr/src/x1_counter.h').read_text(encoding='utf-8').splitlines():
    m = re.search(r'//\s*(\S+)\s+([AB])\s*$', line)
    if m and re.match(r'\s*\d', line): rows.add((m.group(1).replace('-', '_'), m.group(2).lower()))
print('table cells', len(rows))
def cells(era):
    out = []
    for kind in ('ranked', 'unranked'):
        for m in json.load(open(D / f'{era}_{kind}/matches_era.json', encoding='utf-8')):
            us = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
            out.append(((m['map'], us['side']) in rows, us['result'] == 'win', kind))
    return out
res = {}
for era in ('v92', 'x3ctr'):
    c = cells(era)
    for sw in (True, False):
        g = [w for s, w, _ in c if s == sw]
        res[era, sw] = (sum(g), len(g))
        print(f"{era:6s} {'table cells' if sw else 'other cells'}: {sum(g)}/{len(g)} = {sum(g) / max(1, len(g)):.1%}")
def p(e, s): w, n = res[e, s]; return w / n, n
(a, na), (b, nb), (c_, nc), (d, nd) = p('x3ctr', True), p('v92', True), p('x3ctr', False), p('v92', False)
did = (a - b) - (c_ - d)
se = math.sqrt(sum(x * (1 - x) / n for x, n in ((a, na), (b, nb), (c_, nc), (d, nd))))
print(f'table effect (diff in diff): {did:+.1%} +- {se:.1%} (z {did / se:+.2f})')
