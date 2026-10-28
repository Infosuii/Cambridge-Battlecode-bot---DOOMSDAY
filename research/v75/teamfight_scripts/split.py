# Team splits in contact: rounds where 2+ champions of a side are within 3 of each other and an enemy champion is within
# 4 of them; "split" when one moves toward the nearest enemy and another moves away (neither hitting).
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
    for i, f in enumerate(fr[:-1]):
        N = {x[0]: x for x in fr[i + 1][1]}
        for t in (0, 1):
            mine = [x for x in f[1] if team[x[0]] == t and x[5] and len(x) > 9]
            foes = [x for x in f[1] if team[x[0]] != t and x[5]]
            if len(mine) < 2 or not foes: continue
            moves = {}
            for x in mine:
                nd = min(cheb((x[1], x[2]), (o[1], o[2])) for o in foes)
                if nd > 4: continue
                nx = N.get(x[0])
                kinds = {a[0] for a in x[9]}
                if not nx or not nx[5]: continue
                nd2 = min(cheb((nx[1], nx[2]), (o[1], o[2])) for o in foes)
                moves[x[0]] = ('hit' if kinds & {5, 6} else 'in' if nd2 < nd else 'out' if nd2 > nd else 'hold', (x[1], x[2]))
            pairs = [(a, b) for a in moves for b in moves if a < b and cheb(moves[a][1], moves[b][1]) <= 3]
            if not pairs: continue
            side = ('us' if t == us else 'them') + '-' + r['result']
            C[side]['rounds'] += 1
            kinds = [{moves[a][0], moves[b][0]} for a, b in pairs]
            C[side]['split_in_out'] += any(k == {'in', 'out'} for k in kinds)
            C[side]['split_hit_out'] += any(k == {'hit', 'out'} for k in kinds)
            C[side]['all_out'] += all(moves[c][0] == 'out' for c in moves)
            C[side]['all_hit'] += all(moves[c][0] == 'hit' for c in moves)
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    k = C[side]; n = k['rounds']
    print(f'{side:9s} grouped contact rounds {n:6d}: one in/one out {100*k["split_in_out"]/n:4.1f}%  one hits/one leaves {100*k["split_hit_out"]/n:4.1f}%  '
          f'all leave {100*k["all_out"]/n:4.1f}%  all hit {100*k["all_hit"]/n:4.1f}%')
