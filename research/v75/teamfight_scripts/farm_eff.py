# Farming efficiency in the first N rounds (default 500), per side: share of living champion-rounds hitting a camp,
# moving without hitting, idle, dead; camp kills credited (camp health to 0 in a round where a side hit it, last
# hitter's side), and farm gold (gold rises not near an enemy death) per camp-hitting round.
import json, collections, statistics as st, sys
idx, folder = sys.argv[1], sys.argv[2]
UNTIL = int(sys.argv[3]) if len(sys.argv) > 3 else 500
rows = json.load(open(idx))
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
S = collections.defaultdict(collections.Counter)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    camps = {(c['x'], c['y']): k for k, c in enumerate(tl['camps'])}
    fr = tl['frames']
    for i in range(1, len(fr)):
        if fr[i - 1][0] >= UNTIL: break
        P = {x[0]: x for x in fr[i - 1][1]}; N = {x[0]: x for x in fr[i][1]}
        died = [(P[c][1], P[c][2], team[c]) for c in N if P.get(c) and P[c][5] and not N[c][5]]
        for c, x in P.items():
            side = ('us' if team[c] == us else 'them') + '-' + r['result']
            k = S[side]
            if not x[5]:
                k['dead'] += 1; continue
            k['alive'] += 1
            acts = x[9] if len(x) > 9 else []
            kinds = {a[0] for a in acts}
            camp_hit = any(a[0] in (5, 6) and (a[1], a[2]) in camps for a in acts)
            k['camp'] += camp_hit
            k['move_only'] += kinds == {4} or kinds == {4, 23}
            k['idle'] += not kinds
            nx = N.get(c)
            if nx and nx[5]:
                rise = nx[6] - x[6]
                if rise > 0 and not any(t != team[c] and cheb((dx, dy), (x[1], x[2])) <= 6 for dx, dy, t in died):
                    k['farm_gold'] += rise
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    k = S[side]; a = k['alive']; t = a + k['dead']
    print(f'{side:9s} first {UNTIL} rounds: dead {100*k["dead"]/t:4.1f}%  of living rounds: camp hits {100*k["camp"]/a:4.1f}%  '
          f'move only {100*k["move_only"]/a:4.1f}%  idle {100*k["idle"]/a:4.1f}%   farm gold per camp-hit round {k["farm_gold"]/max(1,k["camp"]):.2f}  per living round {k["farm_gold"]/a:.2f}')
