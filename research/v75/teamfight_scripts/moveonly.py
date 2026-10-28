# Our move-only rounds in contact (enemy champion within 4): direction vs the nearest enemy, whether an enemy stood in
# attack range at the start of the round, and health. Same for the top teams.
import json, collections, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
# attack range per type: the largest distance seen between an attacker and its target tile
rng = collections.Counter()
for r in rows[:20]:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    typ = {c['id']: c['type'] for c in tl['champs']}
    for f in tl['frames']:
        for x in f[1]:
            for a in (x[9] if len(x) > 9 else []):
                if a[0] == 5 and not any(b[0] in (4, 23) for b in x[9]):
                    rng[typ[x[0]]] = max(rng[typ[x[0]]], cheb((x[1], x[2]), (a[1], a[2])))
print('attack range by type:', {NAMES[k]: v for k, v in sorted(rng.items())})
C = collections.defaultdict(collections.Counter)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}; typ = {c['id']: c['type'] for c in tl['champs']}
    fr = tl['frames']
    for i, f in enumerate(fr[:-1]):
        N = {x[0]: x for x in fr[i + 1][1]}
        for x in f[1]:
            if not x[5] or len(x) < 10: continue
            t = team[x[0]]; me = (x[1], x[2])
            foes = [o for o in f[1] if team[o[0]] != t and o[5]]
            if not foes: continue
            nd = min(cheb(me, (o[1], o[2])) for o in foes)
            if nd > 4: continue
            side = ('us' if t == us else 'them') + '-' + r['result']
            kinds = {a[0] for a in x[9]}
            k = C[side]; k['n'] += 1
            if kinds != {4}: continue
            nx = N.get(x[0])
            if not nx: continue
            nme = (nx[1], nx[2])
            nd2 = min(cheb(nme, (o[1], o[2])) for o in foes)
            R = rng.get(typ[x[0]], 1)
            k['mo'] += 1
            k['toward' if nd2 < nd else 'away' if nd2 > nd else 'same'] += 1
            k['inrange_start'] += nd <= R
            k['inrange_end'] += nd2 <= R
            hpf = x[3] / max(1, x[4])
            k['hp<50'] += hpf < 0.5
            # carrying gems toward home / near camp? record whether a camp is being fought within 2
            k['adj_enemy'] += nd <= 1
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    k = C[side]; n = k['n']; m = k['mo']
    print(f'{side:9s} move-only {100*m/n:4.1f}% of contact rounds; of those: toward {100*k["toward"]/m:3.0f}% away {100*k["away"]/m:3.0f}% same-dist {100*k["same"]/m:3.0f}%  '
          f'enemy in our range at start {100*k["inrange_start"]/m:3.0f}%  in range after the move {100*k["inrange_end"]/m:3.0f}%  below half hp {100*k["hp<50"]/m:3.0f}%  adjacent {100*k["adj_enemy"]/m:3.0f}%')
    print(f'{"":9s} per contact round: move-only with enemy in range at start {100*k["inrange_start"]/n:4.1f}%, ending in range {100*k["inrange_end"]/n:4.1f}%, toward {100*k["toward"]/n:4.1f}%, away {100*k["away"]/n:4.1f}%')
