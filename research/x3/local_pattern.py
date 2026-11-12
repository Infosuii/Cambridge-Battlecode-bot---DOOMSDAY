"""Ladder loss pattern on local dz runs (research/x3/ECONOMY_GAP.md): for each run, the candidate's win rate, the
opponent's camp clears on the candidate's side and the candidate's on theirs, gold earned by round 600 and late camp
clears, Bruiser shards bought. Reads games/*/summary.json from artifacts/tmp/dz/<run> or <run>/evidence.zip.
  python research/x3/local_pattern.py RUN [RUN ...]"""
import json, sys, zipfile, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def summaries(run):
    tmp = ROOT / 'artifacts/tmp/dz' / run / 'games'
    if tmp.is_dir():
        for g in sorted(tmp.iterdir()):
            f = g / 'summary.json'
            if f.exists(): yield g.name, json.loads(f.read_text(encoding='utf-8'))
        return
    z = zipfile.ZipFile(ROOT / 'research/dz/runs' / run / 'evidence.zip')
    for n in sorted(z.namelist()):
        if n.endswith('summary.json'): yield n.split('/')[-2], json.loads(z.read(n))

def at(runs, t):
    v, s = 0.0, 0
    for r in runs:
        if s > t: break
        v = float(r['value']); s += r['duration']
    return v

for run in sys.argv[1:]:
    res = {(g['map'] + '-' + g['side']): g for g in json.load(open(ROOT / 'research/dz/runs' / run / 'results.json'))['per_game']}
    rows = []
    for name, s in summaries(run):
        g = res.get(name)
        if not g: continue
        us = 'team' + g['side']; them = 'teamB' if us == 'teamA' else 'teamA'
        win = g['outcome'] == us
        cl = {us: [], them: []}
        for e in s['events']:
            if e['kind'] == 'campClear' and e['owner']['team'] in cl:
                cl[e['owner']['team']] += [(x['timestamp']['round'], x['x'], x['y']) for x in e['entries']]
        cen = {k: (st.mean(x for _, x, _ in v), st.mean(y for _, _, y in v)) if v else None for k, v in cl.items()}
        d2 = lambda p, q: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
        inv = lambda a, b: sum(d2((x, y), cen[b]) < d2((x, y), cen[a]) for _, x, y in cl[a]) if cen[a] and cen[b] else 0
        gold = {k: sum(at(tl['runs'], 600) for tl in s['championTimelines'] if tl['owner']['team'] == k and tl['metric'] == 'earnedGold') for k in cl}
        bru = {k: sum(int(i['quantity']) for c in s['champions'] if c['team'] == k for i in c['itemsBought'] if i['item'].startswith('Bruiser Shard')) for k in cl}
        late = {k: sum(t >= 600 for t, _, _ in v) for k, v in cl.items()}
        rows.append(dict(win=win, inv_them=inv(them, us), inv_us=inv(us, them), g_us=gold[us], g_them=gold[them],
                         late_us=late[us], late_them=late[them], bru_us=bru[us], bru_them=bru[them]))
    if not rows:
        print(run, 'no summaries'); continue
    m = lambda k, r=rows: st.mean(x[k] for x in r)
    print(f"{run}: {sum(r['win'] for r in rows)}/{len(rows)} won | opp clears on our side {m('inv_them'):.1f}, ours on "
          f"theirs {m('inv_us'):.1f} | gold r600 {m('g_us'):.0f} / {m('g_them'):.0f} | clears r600+ {m('late_us'):.1f} / "
          f"{m('late_them'):.1f} | bruiser shards {m('bru_us'):.0f} / {m('bru_them'):.0f}")
    lost = [r for r in rows if not r['win']]
    if lost:
        print(f"   in its {len(lost)} losses: opp clears on our side {m('inv_them', lost):.1f}, gold r600 {m('g_us', lost):.0f} / {m('g_them', lost):.0f}")
