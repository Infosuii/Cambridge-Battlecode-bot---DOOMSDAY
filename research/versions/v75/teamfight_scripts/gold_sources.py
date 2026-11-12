# Gold rises per champion-round split into kill gold (an enemy champion died within 6 tiles this round or last) and
# other (camp rewards, captures), cumulative to rounds 300/500/700, per side; plus the size of kill payouts.
import json, collections, statistics as st, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
G = collections.defaultdict(list); pay = []
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    fr = tl['frames']
    acc = {0: collections.Counter(), 1: collections.Counter()}
    for i in range(1, len(fr)):
        P = {x[0]: x for x in fr[i - 1][1]}; N = {x[0]: x for x in fr[i][1]}
        died = [(P[c][1], P[c][2], team[c]) for c in N if P.get(c) and P[c][5] and not N[c][5]]
        if i >= 2:
            Q = {x[0]: x for x in fr[i - 2][1]}
            died += [(Q[c][1], Q[c][2], team[c]) for c in P if Q.get(c) and Q[c][5] and not P[c][5]]
        for c, x in N.items():
            if c not in P: continue
            rise = x[6] - P[c][6]
            if rise <= 0: continue
            # buys lower gold in the same round; rises are net, which is fine for income
            kill = any(t != team[c] and cheb((dx, dy), (x[1], x[2])) <= 6 for dx, dy, t in died)
            acc[team[c]]['kill' if kill else 'other'] += rise
            if kill: pay.append(rise)
        rnd = fr[i][0]
        if rnd in (300, 500, 700):
            for t in (0, 1):
                G[(r['result'], 'us' if t == us else 'them', rnd)].append((acc[t]['kill'], acc[t]['other']))
for res in ('loss', 'win'):
    for rnd in (300, 500, 700):
        cells = []
        for side in ('us', 'them'):
            L = G[(res, side, rnd)]
            cells.append(f'{side}: kill gold {st.mean(k for k, _ in L):5.0f}  other {st.mean(o for _, o in L):5.0f}')
        print(f'{res} R{rnd}  ' + '   '.join(cells))
print('kill-round gold rises: median', st.median(pay), 'p75', sorted(pay)[3 * len(pay) // 4])
