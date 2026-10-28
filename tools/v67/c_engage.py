"""How each team fights: engagements, numbers, focus fire and kill anatomy from timeline.json files.

Usage: c_engage.py INDEX.json --folder artifacts/local-only/duel-v74 [--only loss] [--out OUT.json]
INDEX rows: {matchId, side, opponent, map, result}. Every measure is computed for both teams of the same games, so
each line reads "us vs them".

A hit is an attack (kind 5) whose target tile holds a living enemy champion at the start of the round or the next, or a
cast (kind 6) on such a tile. Hits cluster into fights: a hit within 12 tiles of an open fight's centre and at most 8
rounds after its last hit joins it, otherwise it opens a new fight centred on the victim. At the first hit of a fight
the local numbers are the living champions of each side within 7 tiles of the centre.
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]
R_LOCAL, R_JOIN, GAP = 7, 12, 8


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def analyse(tl, us):
    team = {c['id']: c['team'] for c in tl['champs']}
    frames = tl['frames']
    pos_at = []  # per frame: id -> (x, y, hp, alive)
    for _, rows, _ in frames:
        pos_at.append({r[0]: ((r[1], r[2]), r[3], r[4], r[5]) for r in rows})
    hits = []  # (frame index, attacker team, attacker, victim)
    for i, (rnd, rows, _) in enumerate(frames):
        nxt = pos_at[i + 1] if i + 1 < len(frames) else pos_at[i]
        for r in rows:
            if not r[5] or len(r) < 10:
                continue
            t = team[r[0]]
            for kind, tx, ty, _slot in r[9]:
                if kind not in (5, 6):
                    continue
                victim = None
                for vid, (p, hp, mhp, alive) in pos_at[i].items():
                    if team[vid] == t or not alive:
                        continue
                    if p == (tx, ty) or nxt.get(vid, (None,))[0] == (tx, ty):
                        victim = vid
                        break
                if victim is not None:
                    hits.append((i, t, r[0], victim))
    # deaths: alive -> dead transitions
    deaths = []  # (frame, team, id, pos)
    for i in range(1, len(frames)):
        for cid, (p, hp, mhp, alive) in pos_at[i].items():
            prev = pos_at[i - 1].get(cid)
            if prev and prev[3] and not alive:
                deaths.append((i, team[cid], cid, prev[0]))
    # focus fire: rounds where >= 2 champions of a team hit champions
    focus = {t: collections.Counter() for t in (0, 1)}
    by_round = collections.defaultdict(list)
    for i, t, a, v in hits:
        by_round[(i, t)].append((a, v))
    for (i, t), lst in by_round.items():
        attackers = {a for a, _ in lst}
        if len(attackers) < 2:
            continue
        per_att = {}
        for a, v in lst:
            per_att.setdefault(a, v)
        top = collections.Counter(per_att.values()).most_common(1)[0][1]
        focus[t]['rounds'] += 1
        focus[t]['att'] += len(per_att)
        focus[t]['on_top'] += top
        focus[t]['all_same'] += top == len(per_att)
    # kill anatomy: distinct attackers on the victim in the 5 rounds before death, rounds from first hit of the streak
    anatomy = {t: [] for t in (0, 1)}
    hits_on = collections.defaultdict(list)
    for i, t, a, v in hits:
        hits_on[v].append((i, a))
    for i, t, cid, p in deaths:
        hs = [(j, a) for j, a in hits_on[cid] if i - 6 <= j < i]
        if not hs:
            continue
        streak = [j for j, _ in hits_on[cid] if j < i]
        first = i
        for j in sorted(streak, reverse=True):
            if first - j > 3:
                break
            first = j
        anatomy[t].append((len({a for _, a in hs}), i - first))
    # fights
    fights = []
    for i, t, a, v in hits:
        vp = pos_at[i][v][0]
        f = None
        for g in fights:
            if g['open'] and i - g['last'] <= GAP and cheb(vp, g['c']) <= R_JOIN:
                f = g
                break
        for g in fights:
            if g['open'] and i - g['last'] > GAP:
                g['open'] = False
        if f is None:
            f = dict(open=True, start=i, last=i, c=vp, init=t, att={0: set(), 1: set()})
            fights.append(f)
        f['last'] = i
        f['att'][t].add(a)
    rows = []
    for f in fights:
        s, c = f['start'], f['c']
        local = {0: 0, 1: 0}
        hp = {0: 0.0, 1: 0.0}
        near = {0: 0, 1: 0}
        spread = {0: [], 1: []}
        for cid, (p, h, mhp, alive) in pos_at[s].items():
            if not alive:
                continue
            d = cheb(p, c)
            if d <= R_LOCAL:
                local[team[cid]] += 1
                hp[team[cid]] += h
            elif d <= 2 * R_LOCAL:
                near[team[cid]] += 1
        # spacing of each side's local champions 5 rounds before the first hit: distance to the nearest teammate
        pre = pos_at[max(0, s - 5)]
        for cid, (p, h, mhp, alive) in pos_at[s].items():
            if not alive or cheb(p, c) > R_LOCAL or cid not in pre or not pre[cid][3]:
                continue
            q = pre[cid][0]
            mates = [cheb(q, pre[o][0]) for o in pre if o != cid and team[o] == team[cid] and pre[o][3]]
            if mates:
                spread[team[cid]].append(min(mates))
        peak = {0: 0, 1: 0}
        for j in range(s, min(len(frames), f['last'] + 1)):
            cnt = {0: 0, 1: 0}
            for cid, (p, h, mhp, alive) in pos_at[j].items():
                if alive and cheb(p, c) <= R_LOCAL:
                    cnt[team[cid]] += 1
            for t in (0, 1):
                peak[t] = max(peak[t], cnt[t])
        dead = {0: 0, 1: 0}
        for i, t, cid, p in deaths:
            if s <= i <= f['last'] + 3 and cheb(p, c) <= R_JOIN:
                dead[t] += 1
        me, op = us, 1 - us
        rows.append(dict(init='us' if f['init'] == me else 'them', round=frames[s][0], dur=f['last'] - s + 1,
                         local=(local[me], local[op]), hp=(hp[me], hp[op]), near=(near[me], near[op]),
                         peak=(peak[me], peak[op]), part=(len(f['att'][me]), len(f['att'][op])),
                         dead=(dead[me], dead[op]), spread=(spread[me], spread[op])))
    return dict(focus={'us': focus[us], 'them': focus[1 - us]},
                anatomy={'us': anatomy[us], 'them': anatomy[1 - us]}, fights=rows,
                deaths=sum(1 for d in deaths if d[1] == us), kills=sum(1 for d in deaths if d[1] != us))


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def report(results, label):
    print(f'== {label}: {len(results)} games')
    for side in ('us', 'them'):
        fc = collections.Counter()
        for r in results:
            fc.update(r['focus'][side])
        an = [x for r in results for x in r['anatomy'][side]]
        print(f'  {side:4s} focus: rounds with 2+ champions hitting champions {fc["rounds"] / len(results):.1f}/game, '
              f'hits on the round\'s main target {pct(fc["on_top"], fc["att"])}, all on one target {pct(fc["all_same"], fc["rounds"])}')
        if an:
            print(f'       kills OF {side}: {len(an) / len(results):.1f}/game with hits, distinct attackers on victim (last 5 rounds) '
                  f'mean {st.mean(a for a, _ in an):.2f}, 1 attacker {pct(sum(a == 1 for a, _ in an), len(an))}, '
                  f'3+ {pct(sum(a >= 3 for a, _ in an), len(an))}; streak length median {st.median(b for _, b in an)}')
    fights = [f for r in results for f in r['fights']]
    big = [f for f in fights if f['part'][0] + f['part'][1] >= 2]
    print(f'  fights {len(fights) / len(results):.1f}/game ({len(big) / len(results):.1f} with 2+ hitters); initiated by us '
          f'{pct(sum(f["init"] == "us" for f in big), len(big))}')
    for who in ('us', 'them'):
        sub = [f for f in big if f['init'] == who]
        if not sub:
            continue
        a = 0 if who == 'us' else 1  # index of the initiator in (us, them) tuples
        print(f'  -- fights {who} start ({len(sub) / len(results):.1f}/game): initiator local numbers minus defender at first hit')
        buckets = collections.defaultdict(list)
        for f in sub:
            d = f['local'][a] - f['local'][1 - a]
            buckets[max(-2, min(2, d))].append(f)
        for d in sorted(buckets):
            fs = buckets[d]
            di = sum(f['dead'][a] for f in fs)
            dd = sum(f['dead'][1 - a] for f in fs)
            print(f'     diff {d:+d}{"+" if abs(d) == 2 else " "} {len(fs) / len(results):5.2f}/game  share {pct(len(fs), len(sub)):>4s}  '
                  f'initiator deaths {di / len(fs):.2f}  defender deaths {dd / len(fs):.2f}  '
                  f'peak present {st.mean(f["peak"][a] for f in fs):.1f} v {st.mean(f["peak"][1 - a] for f in fs):.1f}')
        sp = [x for f in sub for x in f['spread'][a]]
        if sp:
            print(f'     initiator spacing 5 rounds before (nearest teammate): median {st.median(sp)}, <=3 {pct(sum(x <= 3 for x in sp), len(sp))}')
        sp = [x for f in sub for x in f['spread'][1 - a]]
        if sp:
            print(f'     defender spacing: median {st.median(sp)}, <=3 {pct(sum(x <= 3 for x in sp), len(sp))}')
    # outcome by numbers present at peak
    print('  outcome by peak numbers (us - them):')
    buckets = collections.defaultdict(list)
    for f in big:
        buckets[max(-2, min(2, f['peak'][0] - f['peak'][1]))].append(f)
    for d in sorted(buckets):
        fs = buckets[d]
        print(f'     {d:+d}{"+" if abs(d) == 2 else " "} {len(fs) / len(results):5.2f}/game  our deaths {sum(f["dead"][0] for f in fs) / len(fs):.2f}  '
              f'their deaths {sum(f["dead"][1] for f in fs) / len(fs):.2f}')
    print('  where the deaths are (per game): ', end='')
    for side, k in (('us', 0), ('them', 1)):
        tot = sum(f['dead'][k] for f in big)
        out = sum(f['dead'][k] for f in big if f['peak'][k] < f['peak'][1 - k])
        print(f'{side} {tot / len(results):.1f} in fights, {pct(out, tot)} while outnumbered at peak; ', end='')
    print()
    print(f'  totals per game: our deaths {st.mean(r["deaths"] for r in results):.1f}, kills {st.mean(r["kills"] for r in results):.1f}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index')
    ap.add_argument('--folder', required=True)
    ap.add_argument('--only', choices=['loss', 'win'])
    ap.add_argument('--out')
    a = ap.parse_args()
    rows = json.load(open(ROOT / a.index))
    res = {'loss': [], 'win': []}
    for r in rows:
        if a.only and r['result'] != a.only:
            continue
        f = ROOT / a.folder / r['matchId'] / 'timeline.json'
        if not f.exists():
            continue
        out = analyse(json.load(open(f)), 0 if r['side'] == 'a' else 1)
        out['opponent'] = r.get('opponent')
        res[r['result']].append(out)
    for k in ('loss', 'win'):
        if res[k]:
            report(res[k], f'{a.index} {k}')
    if a.out:
        json.dump(res, open(ROOT / a.out, 'w'), default=list)


if __name__ == '__main__':
    main()
