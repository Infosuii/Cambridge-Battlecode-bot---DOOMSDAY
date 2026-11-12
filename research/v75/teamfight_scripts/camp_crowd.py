# Champions per camp in the first N rounds: for each round and side, the camps hit and how many of the side's champions
# hit each; distinct camps hit per round; and camp kills (camp health to zero while hit by the side).
import json, collections, statistics as st, sys
idx, folder = sys.argv[1], sys.argv[2]
UNTIL = int(sys.argv[3]) if len(sys.argv) > 3 else 500
rows = json.load(open(idx))
S = collections.defaultdict(collections.Counter)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    camps = {(c['x'], c['y']): k for k, c in enumerate(tl['camps'])}
    for f in tl['frames']:
        if f[0] >= UNTIL: break
        per = {0: collections.Counter(), 1: collections.Counter()}
        for x in f[1]:
            if not x[5] or len(x) < 10: continue
            hit = {camps[(a[1], a[2])] for a in x[9] if a[0] in (5, 6) and (a[1], a[2]) in camps}
            for k in hit: per[team[x[0]]][k] += 1
        for t in (0, 1):
            if not per[t]: continue
            side = ('us' if t == us else 'them') + '-' + r['result']
            S[side]['rounds'] += 1
            S[side]['camps'] += len(per[t])
            S[side]['hitters'] += sum(per[t].values())
            S[side]['crowd3'] += sum(1 for v in per[t].values() if v >= 3)
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    k = S[side]
    print(f'{side:9s} rounds with camp hits {k["rounds"]:6d}: distinct camps hit per such round {k["camps"]/k["rounds"]:.2f}  '
          f'champions per hit camp {k["hitters"]/k["camps"]:.2f}  camps with 3+ of ours {100*k["crowd3"]/k["camps"]:.0f}%')
