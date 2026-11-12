# Isolation: share of champion-rounds with the nearest living teammate > 8 tiles, and deaths per 1000 such rounds
# (death attributed to the state 6 rounds earlier), per side, per phase, in duel losses and wins.
import json, collections, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
S = collections.defaultdict(collections.Counter)
T = collections.defaultdict(collections.Counter)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}; typ = {c['id']: c['type'] for c in tl['champs']}
    fr = tl['frames']
    P = [{x[0]: ((x[1], x[2]), x[5]) for x in f[1]} for f in fr]
    # enemy within 10 = "contested" round for that champion
    state = []
    for i, p in enumerate(P):
        st = {}
        for c, (q, al) in p.items():
            if not al: continue
            mates = [cheb(q, p[o][0]) for o in p if o != c and team[o] == team[c] and p[o][1]]
            foes = [cheb(q, p[o][0]) for o in p if team[o] != team[c] and p[o][1]]
            nm = min(mates) if mates else 99; nf = min(foes) if foes else 99
            st[c] = ('alone' if nm > 8 else 'pair' if nm > 3 else 'tight', nf <= 10)
        state.append(st)
    for i in range(len(P)):
        ph = 'early' if fr[i][0] < 400 else 'mid' if fr[i][0] < 1000 else 'late'
        for c, (iso, contested) in state[i].items():
            side = 'us' if team[c] == us else 'them'
            key = (r['result'], side, ph)
            S[key][iso] += 1
            if contested: S[key][iso + '_c'] += 1
            if iso == 'alone' and side == 'us': T[(r['result'], 'alone')][NAMES[typ[c]]] += 1
        if i >= 6:
            for c, (q, al) in P[i].items():
                if not al and P[i - 1][c][1] and c in state[i - 6]:
                    side = 'us' if team[c] == us else 'them'
                    iso, contested = state[i - 6][c]
                    S[(r['result'], side, 'all')]['death_' + iso] += 1
for k in sorted(S):
    if k[2] == 'all': continue
    c = S[k]; n = c['alone'] + c['pair'] + c['tight']
    print(f'{k[0]:4s} {k[1]:4s} {k[2]:5s}  alone {100*c["alone"]/n:4.1f}%  pair(4-8) {100*c["pair"]/n:4.1f}%  tight(<=3) {100*c["tight"]/n:4.1f}%   '
          f'with enemy <=10: alone {100*c["alone_c"]/max(1,c["alone"]):4.1f}% pair {100*c["pair_c"]/max(1,c["pair"]):4.1f}% tight {100*c["tight_c"]/max(1,c["tight"]):4.1f}%')
for res in ('loss', 'win'):
    for side in ('us', 'them'):
        tot = collections.Counter()
        for ph in ('early', 'mid', 'late'): tot.update(S[(res, side, ph)])
        d = S[(res, side, 'all')]
        print(f'{res} {side}: deaths per 1000 champion-rounds by state 6 rounds earlier: ' + ', '.join(
            f'{s} {1000*d["death_"+s]/max(1,tot[s]):.1f} ({d["death_"+s]})' for s in ('alone', 'pair', 'tight')))
