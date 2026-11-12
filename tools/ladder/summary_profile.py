"""How each team played, from match summaries alone (fast; replays add detail later): for every recent loss to a
strong team (data/ladder/losses48/matches.json) and both teams, where and when they cleared camps, picked up gems,
killed and died (own half / contested / enemy half, from the map's spawns), their banking rhythm, item order,
emblems, consumables (teleport crystals, altar locks) and wards.
  python tools/ladder/summary_profile.py [--data data/ladder/losses48] [--out research/x3/losses48/summary_rows.json]
A position is "own" when it is more than 3 tiles nearer the team's spawn centre than the enemy's (Chebyshev),
"enemy" when more than 3 tiles nearer the enemy's, else "contested".
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/mapgen'))
CHAR = json.loads((ROOT / 'data/ladder/char_ids.json').read_text())
PHASES = [(0, 150), (150, 300), (300, 600), (600, 1000), (1000, 5000)]


def spawns(eng, cache, name):
    if name in cache: return cache[name]
    import mapio
    p = ROOT / 'maps/ladder-pool' / f"{name.replace('_', '-')}.map26a"
    if not p.exists(): cache[name] = None; return None
    m = mapio.read_map(eng, p.read_bytes()); w, h = m['w'], m['h']; x0, y0, x1, y1 = m['spawn']
    a = ((x0 + x1) / 2, (y0 + y1) / 2)
    b = {'horizontal': (w - 1 - a[0], a[1]), 'vertical': (a[0], h - 1 - a[1])}.get(m['symmetry'], (w - 1 - a[0], h - 1 - a[1]))
    cache[name] = (a, b, w, h); return cache[name]


def side_of(p, own, opp):
    d1 = max(abs(p[0] - own[0]), abs(p[1] - own[1])); d2 = max(abs(p[0] - opp[0]), abs(p[1] - opp[1]))
    return 'own' if d1 + 3 < d2 else 'enemy' if d2 + 3 < d1 else 'contested'


def phase(r): return next(i for i, (a, b) in enumerate(PHASES) if a <= r < b)


def team_profile(s, team, own, opp):
    ev = [(e['kind'], e['owner'], x) for e in s['events'] if e['owner'].get('team') == team for x in e['entries']]
    R = lambda x: x['timestamp']['round']; P = lambda x: (x.get('x', 0), x.get('y', 0))
    out = {}
    for kind, key in (('campClear', 'clears'), ('gemCollection', 'pickups'), ('kill', 'kills'), ('death', 'deaths'), ('wardPlacement', 'wards')):
        grid = [[0, 0, 0] for _ in PHASES]  # own, contested, enemy
        first = []
        for k, o, x in sorted(((k, o, x) for k, o, x in ev if k == kind), key=lambda t: R(t[2])):
            sd = side_of(P(x), own, opp); grid[phase(R(x))][('own', 'contested', 'enemy').index(sd)] += int(x.get('value', 1) or 1) if kind == 'gemCollection' else 1
            if len(first) < 10: first.append((R(x), sd))
        out[key] = grid; out[key + '_first'] = first
    deps = sorted((R(x), int(x['value'])) for k, o, x in ev if k == 'gemSubmission')
    out['deposits'] = [[sum(1 for r, v in deps if phase(r) == i), sum(v for r, v in deps if phase(r) == i)] for i in range(len(PHASES))]
    out['first_deposit'] = deps[0][0] if deps else None
    lost = [(R(x), int(x['value'])) for k, o, x in ev if k == 'gemLoss']
    out['gems_lost'] = [sum(v for r, v in lost if phase(r) == i) for i in range(len(PHASES))]
    buys = sorted((R(x), x['target']['name'], int(x['value'])) for k, o, x in ev if k == 'buyItem')
    fam = lambda n: n.split(' ')[0]
    out['shards_by_phase'] = [{} for _ in PHASES]
    for r, n, q in buys:
        d = out['shards_by_phase'][phase(r)]; d[fam(n)] = d.get(fam(n), 0) + q
    order, seen = [], set()
    for r, n, q in buys:
        f = fam(n) + ' ' + n.split(' of ')[-1] if ' of ' in n else fam(n)
        if f not in seen: seen.add(f); order.append([r, f])
    out['item_order'] = order[:8]
    emb = sorted((R(x), x['target']['name']) for k, o, x in ev if k == 'itemCombination')
    out['emblems'] = [[r, n] for r, n in emb[:8]]
    cons = {}
    for k, o, x in ev:
        if k == 'buyConsumable':
            c = cons.setdefault(x['target']['name'], [0, None]); c[0] += int(x['value']); c[1] = c[1] if c[1] is not None else R(x)
    out['consumables'] = cons
    out['champions'] = sorted({c['name'] for c in s['champions'] if c['team'] == team})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='data/ladder/losses48'); ap.add_argument('--out', default='research/x3/losses48/summary_rows.json')
    a = ap.parse_args()
    import mapio
    eng = mapio.new_engine(); cache = {}
    data = ROOT / a.data; matches = json.loads((data / 'matches.json').read_text(encoding='utf-8'))
    rows, miss = [], 0
    for m in matches:
        f = data / 'summaries' / f"{m['matchId']}.json"
        if not f.exists(): miss += 1; continue
        try: s = json.loads(f.read_text(encoding='utf-8'))
        except ValueError: miss += 1; continue
        sp = spawns(eng, cache, m['map'])
        if not sp: continue
        a_, b_, w, h = sp
        us, them = ('teamA', 'teamB') if m['side'] == 'a' else ('teamB', 'teamA')
        own_us, own_them = (a_, b_) if us == 'teamA' else (b_, a_)
        rows.append(dict(m, their_names=[CHAR.get(str(c), str(c)) for c in (m.get('their_draft') or [])], our_names=[CHAR.get(str(c), str(c)) for c in (m.get('our_draft') or [])],
                         rounds=s['match']['roundsCompleted'], w=w, h=h,
                         us=team_profile(s, us, own_us, own_them), them=team_profile(s, them, own_them, own_us),
                         banked=[int(t['submittedGems']) for t in s['teams'] if t['team'] == us][0], their_banked=[int(t['submittedGems']) for t in s['teams'] if t['team'] == them][0]))
    out = ROOT / a.out; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    print(len(rows), 'rows;', miss, 'summaries missing ->', out)


if __name__ == '__main__':
    main()
