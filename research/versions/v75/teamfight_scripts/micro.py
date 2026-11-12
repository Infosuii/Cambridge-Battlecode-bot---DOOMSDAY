# Action economy in champion fights: for every living champion with an enemy champion within 4 tiles, what it did that
# round (attack on a champion, attack on something else, cast, move, dash, nothing), per side and champion type.
import json, collections, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
C = collections.defaultdict(collections.Counter)
dmg = collections.defaultdict(list)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}; typ = {c['id']: c['type'] for c in tl['champs']}
    fr = tl['frames']
    for i, f in enumerate(fr[:-1]):
        P = {x[0]: x for x in f[1]}
        N = {x[0]: x for x in fr[i + 1][1]}
        for x in f[1]:
            if not x[5]: continue
            me = (x[1], x[2]); t = team[x[0]]
            foes = [o for o in f[1] if team[o[0]] != t and o[5] and cheb(me, (o[1], o[2])) <= 4]
            if not foes: continue
            side = ('us' if t == us else 'them') + '-' + r['result']
            acts = x[9] if len(x) > 9 else []
            kinds = {a[0] for a in acts}
            on_champ = any(a[0] == 5 and any((o[1], o[2]) == (a[1], a[2]) or (N.get(o[0]) and (N[o[0]][1], N[o[0]][2]) == (a[1], a[2])) for o in foes) for a in acts)
            k = C[side]; k['n'] += 1
            k['att_champ'] += on_champ
            k['att_other'] += (5 in kinds) and not on_champ
            k['cast'] += 6 in kinds
            k['move'] += 4 in kinds
            k['dash'] += 23 in kinds
            k['idle'] += not kinds
            # Bookkeeping (recall/cancel/ward) must not hide non-combat moves.
            k['strict_move_only'] += kinds == {4}
            k['move_only'] += 4 in kinds and not bool(kinds & {5, 6})
            # health lost this round, a proxy for damage taken while in contact
            if x[0] in N and N[x[0]][5]: k['hp_lost'] += max(0, x[3] - N[x[0]][3])
            k2 = C[side + ':' + NAMES[typ[x[0]]]]; k2['n'] += 1; k2['att_champ'] += on_champ; k2['cast'] += 6 in kinds; k2['move_only'] += 4 in kinds and not bool(kinds & {5, 6}); k2['idle'] += not kinds
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    k = C[side]; n = k['n']
    print(f'{side:10s} contact rounds {n:6d}: attack champ {100*k["att_champ"]/n:4.1f}%  attack other {100*k["att_other"]/n:4.1f}%  cast {100*k["cast"]/n:4.1f}%  '
          f'move {100*k["move"]/n:4.1f}%  move-only {100*k["move_only"]/n:4.1f}%  dash {100*k["dash"]/n:4.1f}%  nothing {100*k["idle"]/n:4.1f}%  hp lost/round {k["hp_lost"]/n:.0f}')
print('by type (loss games): attack champ / cast / move-only / nothing')
types = sorted({s.split(':')[1] for s in C if ':' in s})
for t in types:
    a = C.get('us-loss:' + t); b = C.get('them-loss:' + t)
    f = lambda k: f'{k["n"]:5d} {100*k["att_champ"]/k["n"]:4.0f}% {100*k["cast"]/k["n"]:4.0f}% {100*k["move_only"]/k["n"]:4.0f}% {100*k["idle"]/k["n"]:4.0f}%' if k and k['n'] > 50 else '      -'
    print(f'  {t:9s} us {f(a)}   them {f(b)}')
