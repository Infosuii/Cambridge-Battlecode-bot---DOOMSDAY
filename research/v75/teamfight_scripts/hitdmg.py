# Damage per lone basic attack on a champion (one attacker, no cast on the victim that round): victim health drop,
# by attacker champion and phase, ours vs theirs. Also max health by type and phase.
import json, collections, statistics as st, sys
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
D = collections.defaultdict(list); H = collections.defaultdict(list); SH = collections.defaultdict(list)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}; typ = {c['id']: c['type'] for c in tl['champs']}
    fr = tl['frames']
    for i, f in enumerate(fr[:-1]):
        ph = 'r<300' if f[0] < 300 else 'r300-700' if f[0] < 700 else 'r700+'
        P = {x[0]: x for x in f[1]}; N = {x[0]: x for x in fr[i + 1][1]}
        hits = collections.defaultdict(list)
        for x in f[1]:
            if not x[5] or len(x) < 10: continue
            for a in x[9]:
                if a[0] not in (5, 6): continue
                for o in f[1]:
                    if team[o[0]] != team[x[0]] and o[5] and ((o[1], o[2]) == (a[1], a[2]) or (N.get(o[0]) and (N[o[0]][1], N[o[0]][2]) == (a[1], a[2]))):
                        hits[o[0]].append((x[0], a[0])); break
        for v, lst in hits.items():
            if len(lst) != 1 or lst[0][1] != 5: continue
            a = lst[0][0]
            if v not in N or not N[v][5]: continue
            drop = P[v][3] - N[v][3]
            if drop <= 0: continue
            side = 'us' if team[a] == us else 'them'
            D[(r['result'], side, NAMES[typ[a]], ph)].append(drop)
        if i % 50 == 0:
            for x in f[1]:
                side = 'us' if team[x[0]] == us else 'them'
                H[(r['result'], side, NAMES[typ[x[0]]], ph)].append(x[4]); SH[(r['result'], side, ph)].append(x[8])
print('median health drop from a lone basic attack (loss games):   us | them   (n)')
for t in NAMES:
    cells = []
    for ph in ('r<300', 'r300-700', 'r700+'):
        a = D.get(('loss', 'us', t, ph), []); b = D.get(('loss', 'them', t, ph), [])
        cells.append(f'{ph}: {st.median(a) if len(a) > 20 else float("nan"):5.0f} | {st.median(b) if len(b) > 20 else float("nan"):5.0f} ({len(a)},{len(b)})')
    print(f'  {t:9s} ' + '   '.join(cells))
print('median max health (loss games): us | them')
for t in NAMES:
    cells = []
    for ph in ('r<300', 'r300-700', 'r700+'):
        a = H.get(('loss', 'us', t, ph), []); b = H.get(('loss', 'them', t, ph), [])
        cells.append(f'{ph}: {st.median(a) if a else float("nan"):5.0f} | {st.median(b) if b else float("nan"):5.0f}')
    print(f'  {t:9s} ' + '   '.join(cells))
for res in ('loss', 'win'):
    print(res, 'mean item count per champion: ', {ph: (round(st.mean(SH[(res, 'us', ph)]), 1), round(st.mean(SH[(res, 'them', ph)]), 1)) for ph in ('r<300', 'r300-700', 'r700+')})
