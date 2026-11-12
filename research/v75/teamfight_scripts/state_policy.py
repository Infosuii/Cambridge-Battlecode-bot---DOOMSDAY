# Contact behaviour by situation: own health share x local health ratio (allies vs enemies within 6). Per side:
# rounds, share hitting (attack/cast), share moving away without hitting, share moving toward without hitting,
# deaths within 5 rounds per 100 rounds.
import json, collections, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
C = collections.defaultdict(collections.Counter)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    fr = tl['frames']
    alive_at = [{x[0]: x[5] for x in f[1]} for f in fr]
    for i, f in enumerate(fr[:-6]):
        N = {x[0]: x for x in fr[i + 1][1]}
        for x in f[1]:
            if not x[5] or len(x) < 10: continue
            t = team[x[0]]; me = (x[1], x[2])
            foes = [o for o in f[1] if team[o[0]] != t and o[5]]
            nd = min((cheb(me, (o[1], o[2])) for o in foes), default=99)
            if nd > 4: continue
            mine = x[3] + sum(o[3] for o in f[1] if team[o[0]] == t and o[5] and o[0] != x[0] and cheb(me, (o[1], o[2])) <= 6)
            theirs = sum(o[3] for o in foes if cheb(me, (o[1], o[2])) <= 6)
            ratio = mine / max(1, theirs)
            hb = 'hp<35' if x[3] < 0.35 * x[4] else 'hp35-70' if x[3] < 0.7 * x[4] else 'hp70+'
            rb = 'r<0.6' if ratio < 0.6 else 'r0.6-1.2' if ratio < 1.2 else 'r1.2+'
            side = ('us' if t == us else 'them') + '-' + r['result']
            k = C[(side, hb, rb)]
            k['n'] += 1
            kinds = {a[0] for a in x[9]}
            hit = bool(kinds & {5, 6})
            k['hit'] += hit
            nx = N.get(x[0])
            if nx and 4 in kinds and not hit:
                nd2 = min((cheb((nx[1], nx[2]), (o[1], o[2])) for o in foes), default=99)
                k['away'] += nd2 > nd; k['toward'] += nd2 < nd
            k['dead5'] += any(not alive_at[j].get(x[0], 1) for j in range(i + 1, i + 6))
print(f'{"situation":20s} | {"us (loss games)":^34s} | {"them (loss games)":^34s} | {"us (win games)":^34s}')
print(f'{"":20s} | ' + ' | '.join(['  n    hit  away toward die5'] * 3))
for hb in ('hp70+', 'hp35-70', 'hp<35'):
    for rb in ('r1.2+', 'r0.6-1.2', 'r<0.6'):
        cells = []
        for side in ('us-loss', 'them-loss', 'us-win'):
            k = C[(side, hb, rb)]; n = max(1, k['n'])
            cells.append(f'{k["n"]:5d} {100*k["hit"]/n:4.0f}% {100*k["away"]/n:4.0f}% {100*k["toward"]/n:4.0f}% {100*k["dead5"]/n:4.1f}')
        print(f'{hb + " " + rb:20s} | ' + ' | '.join(cells))
