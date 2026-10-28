# Contact episodes: a champion's consecutive rounds with an enemy champion within 6. Per episode: rounds, hits dealt,
# health lost, toward/away reversals, whether it ended in death; per side.
import json, collections, sys, statistics as st
idx, folder = sys.argv[1], sys.argv[2]
rows = json.load(open(idx))
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
E = collections.defaultdict(list)
for r in rows:
    tl = json.load(open(f'{folder}/{r["matchId"]}/timeline.json'))
    us = 0 if r['side'] == 'a' else 1
    team = {c['id']: c['team'] for c in tl['champs']}
    fr = tl['frames']
    open_ep = {}
    for i, f in enumerate(fr[:-1]):
        N = {x[0]: x for x in fr[i + 1][1]}
        for x in f[1]:
            cid = x[0]; t = team[cid]
            foes = [o for o in f[1] if team[o[0]] != t and o[5]]
            nd = min((cheb((x[1], x[2]), (o[1], o[2])) for o in foes), default=99)
            ep = open_ep.get(cid)
            if x[5] and nd <= 6:
                if ep is None:
                    ep = open_ep[cid] = dict(side=('us' if t == us else 'them') + '-' + r['result'], n=0, hits=0, lost=0, dirs=[], hp0=x[3] / max(1, x[4]), died=False)
                ep['n'] += 1
                kinds = {a[0] for a in (x[9] if len(x) > 9 else [])}
                ep['hits'] += bool(kinds & {5, 6})
                nx = N.get(cid)
                if nx and nx[5]:
                    ep['lost'] += max(0, x[3] - nx[3])
                    nd2 = min((cheb((nx[1], nx[2]), (o[1], o[2])) for o in foes), default=99)
                    if 4 in kinds and not (kinds & {5, 6}):
                        ep['dirs'].append(1 if nd2 < nd else -1 if nd2 > nd else 0)
                elif nx and not nx[5]:
                    ep['died'] = True
            elif ep is not None:
                E[ep['side']].append(ep); del open_ep[cid]
for side in ('us-loss', 'them-loss', 'us-win', 'them-win'):
    L = [e for e in E[side] if e['n'] >= 3]
    def rev(e):
        d = [x for x in e['dirs'] if x]
        return sum(1 for a, b in zip(d, d[1:]) if a != b)
    died = [e for e in L if e['died']]
    print(f'{side:9s} episodes(3+ rounds) {len(L):5d}: rounds median {st.median(e["n"] for e in L):.0f}  acting share {100*sum(e["hits"] for e in L)/sum(e["n"] for e in L):.0f}%  '
          f'reversals/episode {st.mean(rev(e) for e in L):.2f}  episodes with 2+ reversals {100*sum(rev(e) >= 2 for e in L)/len(L):.0f}%  died {100*len(died)/len(L):.0f}%  '
          f'| fatal episodes: acting {100*sum(e["hits"] for e in died)/max(1,sum(e["n"] for e in died)):.0f}%, start hp {100*st.mean(e["hp0"] for e in died) if died else 0:.0f}%, reversals {st.mean(rev(e) for e in died) if died else 0:.2f}')
