# Fight outcome vs local power at the first hit: HP ratio and shard difference, us vs them.
import json, collections, sys
sys.path.insert(0, 'tools/v67')
from pathlib import Path
from c_engage import cheb, R_LOCAL, R_JOIN, GAP
rows = json.load(open('research/v75/duel_v74.json'))
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
tab_hp = collections.defaultdict(lambda: [0, 0, 0]); tab_sh = collections.defaultdict(lambda: [0, 0, 0])
tab_eq = collections.defaultdict(lambda: [0, 0, 0])
duel = collections.defaultdict(lambda: [0, 0])  # 1v1 fights: (our type) -> [we die, they die]
shard_gap = collections.defaultdict(list)
for r in rows:
    tl = json.load(open(f'artifacts/local-only/duel-v74/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    typ = {c['id']: c['type'] for c in tl['champs']}
    frames = tl['frames']
    P = [{x[0]: ((x[1], x[2]), x[3], x[4], x[5], x[8]) for x in fr[1]} for fr in frames]
    for i in (200, 400, 600, 800, 1000):
        if i < len(frames):
            sh = {0: 0, 1: 0}
            for cid, v in P[i].items(): sh[team[cid]] += v[4]
            shard_gap[(r['result'], i)].append(sh[us] - sh[1 - us])
    hits = []
    for i, fr in enumerate(frames):
        nxt = P[i + 1] if i + 1 < len(frames) else P[i]
        for x in fr[1]:
            if not x[5] or len(x) < 10: continue
            t = team[x[0]]
            for kind, tx, ty, _ in x[9]:
                if kind not in (5, 6): continue
                for vid, v in P[i].items():
                    if team[vid] != t and v[3] and (v[0] == (tx, ty) or nxt.get(vid, (None,))[0] == (tx, ty)):
                        hits.append((i, t, x[0], vid)); break
    deaths = [(i, team[c], c, P[i - 1][c][0]) for i in range(1, len(frames)) for c, v in P[i].items() if P[i - 1].get(c, (0, 0, 0, 0))[3] and not v[3]]
    fights = []
    for i, t, a, v in hits:
        vp = P[i][v][0]; f = None
        for g in fights:
            if g['open'] and i - g['last'] <= GAP and cheb(vp, g['c']) <= R_JOIN: f = g; break
        for g in fights:
            if g['open'] and i - g['last'] > GAP: g['open'] = False
        if f is None:
            f = dict(open=True, start=i, last=i, c=vp, att={0: set(), 1: set()}); fights.append(f)
        f['last'] = i; f['att'][t].add(a)
    for f in fights:
        if len(f['att'][0]) + len(f['att'][1]) < 2: continue
        s, c = f['start'], f['c']
        hp = {0: 0, 1: 0}; sh = {0: 0, 1: 0}; n = {0: 0, 1: 0}; who = {0: [], 1: []}
        for cid, v in P[s].items():
            if v[3] and cheb(v[0], c) <= R_LOCAL:
                t = team[cid]; hp[t] += v[1]; sh[t] += v[4]; n[t] += 1; who[t].append(cid)
        if not n[0] or not n[1]: continue
        dead = {0: 0, 1: 0}
        for i, t, cid, p in deaths:
            if s <= i <= f['last'] + 3 and cheb(p, c) <= R_JOIN: dead[t] += 1
        me, op = us, 1 - us
        ratio = hp[me] / max(1, hp[op])
        b = '<0.5' if ratio < 0.5 else '0.5-0.8' if ratio < 0.8 else '0.8-1.25' if ratio < 1.25 else '1.25-2' if ratio < 2 else '>2'
        for tab, key in ((tab_hp, b), (tab_sh, max(-6, min(6, (sh[me] - sh[op]) // 2 * 2)))):
            tab[key][0] += 1; tab[key][1] += dead[me]; tab[key][2] += dead[op]
        if 0.8 <= ratio < 1.25 and n[me] == n[op]:
            k = max(-4, min(4, sh[me] - sh[op]))
            tab_eq[k][0] += 1; tab_eq[k][1] += dead[me]; tab_eq[k][2] += dead[op]
        if n[me] == 1 and n[op] == 1 and len(f['att'][me]) <= 1 and len(f['att'][op]) <= 1:
            duel[NAMES[typ[who[me][0]]]][0] += dead[me]; duel[NAMES[typ[who[me][0]]]][1] += dead[op]
def show(name, tab, order=None):
    print(name)
    for k in (order or sorted(tab)):
        if k in tab:
            n, a, b = tab[k]; print(f'   {str(k):>9s}  fights {n:5d}  our deaths/fight {a / n:.2f}  theirs {b / n:.2f}')
show('by local HP ratio us/them at first hit', tab_hp, ['<0.5', '0.5-0.8', '0.8-1.25', '1.25-2', '>2'])
show('by local shard difference (us - them, bucket of 2)', tab_sh)
show('even HP (0.8-1.25) and even numbers, by shard difference', tab_eq)
print('1v1 fights by our champion: our deaths / their deaths')
for k, (a, b) in sorted(duel.items(), key=lambda kv: -sum(kv[1])): print(f'   {k:9s} {a:4d} {b:4d}')
import statistics as st
for res in ('loss', 'win'):
    print(res, 'team shard difference us-them at round', {i: round(st.mean(shard_gap[(res, i)]), 1) for i in (200, 400, 600, 800, 1000) if shard_gap[(res, i)]})
