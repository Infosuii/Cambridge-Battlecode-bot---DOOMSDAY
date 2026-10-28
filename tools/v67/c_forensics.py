"""Round-by-round loss forensics over timeline.json files (tools/v67/c_timeline_batch.py).

Usage: c_forensics.py INDEX.json [--only loss] [--examples 25] [--out OUT.json]
INDEX rows: {matchId, side, opponent, map, result} (research/v75/ranked_v67.json); timelines are read from
artifacts/local-only/v67-ranked/<matchId>/timeline.json. Every measure is computed for both teams in the same games,
so each line reads "us vs the team that beat us".

Death classes (8 rounds before each death, first match wins):
  camp      no enemy champion within 8 tiles at any point of the window
  dive      the victim walked toward enemies while they outnumbered its side within 6 tiles
  isolated  no ally within 8 tiles one round before death
  flee      no hit on an enemy champion in the window and the victim moved away from the nearest enemy
  traded    hit enemy champions in the window (fought and lost)
  other
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
RANGED = {1, 3, 5, 6, 8, 11}
W = 8


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def analyse(tl, us):
    champs = {c['id']: c for c in tl['champs']}
    frames = tl['frames']
    team = {c['id']: c['team'] for c in tl['champs']}
    spawn = {}
    for row in frames[0][1]:
        spawn.setdefault(team[row[0]], []).append((row[1], row[2]))
    out = {t: collections.Counter() for t in (0, 1)}
    deaths = []
    hist = collections.defaultdict(list)  # id -> list of (round, x, y)
    gold_rounds = {t: [] for t in (0, 1)}

    def near_spawn(t, p, r=1):
        return any(cheb(p, s) <= r for s in spawn[t])

    for i, (rnd, rows, hurt) in enumerate(frames):
        by = {r[0]: r for r in rows}
        for r in rows:
            cid, x, y, hp, mhp, alive, gold, gems, shards = r[:9]
            acts = r[9] if len(r) > 9 else []
            t = team[cid]
            o = out[t]
            if not alive:
                o['dead'] += 1
                continue
            o['alive'] += 1
            p = (x, y)
            home = near_spawn(t, p, 1)
            if home:
                o['home'] += 1
            kinds = [a[0] for a in acts]
            if not acts and not home:
                o['noact'] += 1
            if gold >= 150 and not home:
                o['gold150'] += 1
            gold_rounds[t].append(gold)
            o['recall'] += kinds.count(11)
            o['cancel'] += kinds.count(16)
            o['buy'] += kinds.count(13)
            enemies = [by[e] for e in by if team[e] != t and by[e][5]]
            near6 = [e for e in enemies if cheb(p, (e[1], e[2])) <= 6]
            if near6:
                o['contact'] += 1
                hit = any(a[0] in (5, 6) and any((e[1], e[2]) == (a[1], a[2]) for e in enemies) for a in acts)
                o['contact_hit'] += hit
                camp_hit = any(a[0] == 5 and not any((e[1], e[2]) == (a[1], a[2]) for e in enemies) for a in acts)
                o['contact_camp'] += camp_hit
            h = hist[cid]
            h.append((rnd, x, y))
            if len(h) >= 3 and h[-3][1:] == h[-1][1:] and h[-2][1:] != h[-1][1:] and h[-3][0] == rnd - 2:
                o['pingpong'] += 1
        # deaths: alive in previous frame, dead now
        if i == 0:
            continue
        prev = {r[0]: r for r in frames[i - 1][1]}
        for r in rows:
            cid = r[0]
            if r[5] or not prev[cid][5]:
                continue
            t = team[cid]
            lo = max(0, i - W)
            window = frames[lo:i]
            enemy_seen = False
            hits = camp_hits = moves_toward = moves_away = recall = 0
            dived = False
            last_d = None
            for rnd2, rows2, _ in window:
                b2 = {q[0]: q for q in rows2}
                me = b2[cid]
                if not me[5]:
                    continue
                mp = (me[1], me[2])
                ens = [q for q in rows2 if team[q[0]] != t and q[5]]
                als = [q for q in rows2 if team[q[0]] == t and q[5] and q[0] != cid]
                d = min((cheb(mp, (q[1], q[2])) for q in ens), default=99)
                if d <= 8:
                    enemy_seen = True
                if last_d is not None and d < 99:
                    if d < last_d:
                        moves_toward += 1
                        e6 = sum(cheb(mp, (q[1], q[2])) <= 6 for q in ens)
                        a6 = sum(cheb(mp, (q[1], q[2])) <= 6 for q in als) + 1
                        if e6 >= a6 + 1:
                            dived = True
                    elif d > last_d:
                        moves_away += 1
                last_d = d
                acts = me[9] if len(me) > 9 else []
                for a in acts:
                    if a[0] in (5, 6) and any((q[1], q[2]) == (a[1], a[2]) for q in ens):
                        hits += 1
                    elif a[0] == 5:
                        camp_hits += 1
                    elif a[0] == 11:
                        recall += 1
            pr = prev[cid]
            pp = (pr[1], pr[2])
            ens = [q for q in prev.values() if team[q[0]] != t and q[5]]
            als = [q for q in prev.values() if team[q[0]] == t and q[5] and q[0] != cid]
            a8 = [q for q in als if cheb(pp, (q[1], q[2])) <= 8]
            e6 = [q for q in ens if cheb(pp, (q[1], q[2])) <= 6]
            hp_w = window[0][1]
            start = next(q for q in hp_w if q[0] == cid)
            hp0 = start[3] / max(1, start[4]) if start[5] else None
            if not enemy_seen:
                cls = 'camp'
            elif dived:
                cls = 'dive'
            elif not a8:
                cls = 'isolated'
            elif hits == 0 and moves_away > 0:
                cls = 'flee'
            elif hits > 0:
                cls = 'traded'
            else:
                cls = 'other'
            # allies within 8 that never hit an enemy champion in the window: bystanders
            idle_allies = 0
            for q in a8:
                hit = False
                for rnd2, rows2, _ in window:
                    me2 = next(z for z in rows2 if z[0] == q[0])
                    ens2 = [z for z in rows2 if team[z[0]] != t and z[5]]
                    for a in (me2[9] if len(me2) > 9 else []):
                        if a[0] in (5, 6) and any((z[1], z[2]) == (a[1], a[2]) for z in ens2):
                            hit = True
                idle_allies += not hit
            deaths.append(dict(round=rnd, team=t, ours=t == us, id=cid, type=NAMES[champs[cid]['type']], cls=cls,
                               gems=pr[7], gold=pr[6], shards=pr[8], hp0=hp0, hits=hits, camp_hits=camp_hits,
                               recall=recall, enemies6=len(e6), allies8=len(a8), idle_allies=idle_allies,
                               enemy_shards=sum(q[8] for q in e6), ally_shards=sum(q[8] for q in a8) + pr[8],
                               x=pp[0], y=pp[1], home=min(cheb(pp, s) for s in spawn[t])))
    for t in (0, 1):
        out[t]['gold_mean'] = round(st.fmean(gold_rounds[t]), 1) if gold_rounds[t] else 0
    shards_at = {}
    for mark in (100, 200, 300, 500, 800):
        if mark < len(frames):
            rows = frames[mark][1]
            shards_at[mark] = {t: sum(r[8] for r in rows if team[r[0]] == t) for t in (0, 1)}
    return out, deaths, shards_at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index', help='index JSON, or local:RUN for a benchmark run (our side of every game)')
    ap.add_argument('--only', default='loss')
    ap.add_argument('--examples', type=int, default=20)
    ap.add_argument('--out')
    ap.add_argument('--folder', default='artifacts/local-only/v67-ranked', help='where downloaded timelines live')
    a = ap.parse_args()
    if a.index.startswith('local:'):
        run = a.index[6:]
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        rows, seen = [], set()
        for g in games:
            if (g['map'], g['side'], g['seed']) in seen:
                continue
            seen.add((g['map'], g['side'], g['seed']))
            rows.append(dict(matchId=g['folder'], map=g['map'], side=g['side'], opponent=g.get('proxy', 'pool'),
                             result='win' if g['win'] else 'loss'))
        rows = [r for r in rows if a.only == 'all' or r['result'] == a.only]
    else:
        rows = [r for r in json.loads((ROOT / a.index).read_text(encoding='utf-8')) if a.only == 'all' or r['result'] == a.only]
    agg = {'us': collections.Counter(), 'them': collections.Counter()}
    cls = {'us': collections.Counter(), 'them': collections.Counter()}
    bytype = {'us': collections.Counter(), 'them': collections.Counter()}
    shards = collections.defaultdict(lambda: [[], []])
    alld, games = [], 0
    for r in rows:
        f = (ROOT / r['matchId'] / 'timeline.json') if r['matchId'].startswith('artifacts/') else             ROOT / a.folder / r['matchId'] / 'timeline.json'
        if not f.exists():
            continue
        tl = json.loads(f.read_text())
        us = 0 if r['side'] == 'a' else 1
        out, deaths, sh = analyse(tl, us)
        games += 1
        for t in (0, 1):
            k = 'us' if t == us else 'them'
            for key, v in out[t].items():
                agg[k][key] += v
        for mark, v in sh.items():
            shards[mark][0].append(v[us])
            shards[mark][1].append(v[1 - us])
        for d in deaths:
            k = 'us' if d['ours'] else 'them'
            cls[k][d['cls']] += 1
            bytype[k][d['type']] += 1
            d.update(match=r['matchId'], map=r['map'], opponent=r['opponent'])
            alld.append(d)
    print(f'{games} games ({a.only})')
    for k in ('us', 'them'):
        g = agg[k]
        n = sum(cls[k].values())
        print(f"\n[{k}] deaths/game {n / games:.1f}; dead share {g['dead'] / (g['dead'] + g['alive']):.3f}; "
              f"rounds per game alive {g['alive'] / games:.0f}")
        print('  death classes: ' + ', '.join(f'{c} {v / games:.2f}' for c, v in cls[k].most_common()))
        print('  deaths by hero/game: ' + ', '.join(f'{c} {v / games:.2f}' for c, v in bytype[k].most_common()))
        al = g['alive']
        print(f"  of alive rounds: at home {g['home'] / al:.3f}, no action away from home {g['noact'] / al:.3f}, "
              f"gold>=150 away from home {g['gold150'] / al:.3f}, ping-pong steps {g['pingpong'] / al:.3f}; mean gold held {g['gold_mean'] / games:.0f}")
        print(f"  per game: recalls {g['recall'] / games:.1f}, recall cancels {g['cancel'] / games:.1f}, buys {g['buy'] / games:.1f}")
        print(f"  contact rounds/game {g['contact'] / games:.0f}; hit a champion in {g['contact_hit'] / max(1, g['contact']):.3f} of them, "
              f"hit a camp in {g['contact_camp'] / max(1, g['contact']):.3f}")
    print('\nshards (team total) ours / theirs: ' + ', '.join(
        f'R{m} {st.fmean(v[0]):.1f}/{st.fmean(v[1]):.1f}' for m, v in sorted(shards.items())))
    ours = [d for d in alld if d['ours']]
    theirs = [d for d in alld if not d['ours']]
    for name, ds in (('us', ours), ('them', theirs)):
        if not ds:
            continue
        hi = [d for d in ds if d['hp0'] is not None and d['hp0'] >= 0.6]
        print(f"\n[{name} deaths] n={len(ds)}: from >=60% hp within {W} rounds {len(hi) / len(ds):.2f}; mean gems lost "
              f"{st.fmean(d['gems'] for d in ds):.1f}; mean unspent gold {st.fmean(d['gold'] for d in ds):.0f}; "
              f"bystander allies within 8 {st.fmean(d['idle_allies'] for d in ds):.2f} of {st.fmean(d['allies8'] for d in ds):.2f}; "
              f"enemies within 6 {st.fmean(d['enemies6'] for d in ds):.2f}; shard ratio enemy/ours "
              f"{st.fmean(d['enemy_shards'] / max(1, d['ally_shards']) for d in ds if d['enemies6']):.2f}; "
              f"within 6 of own spawn {sum(d['home'] <= 6 for d in ds) / len(ds):.2f}")
    if a.examples:
        print('\nlargest gem losses (ours):')
        for d in sorted(ours, key=lambda d: -d['gems'])[:a.examples]:
            print(f"  {d['match'][:8]} {d['map']:<22} R{d['round']:<5} {d['type']:<8} {d['cls']:<9} gems {d['gems']:<4} "
                  f"gold {d['gold']:<4} hp0 {d['hp0'] if d['hp0'] is None else round(d['hp0'], 2)} hits {d['hits']} "
                  f"enemies6 {d['enemies6']} allies8 {d['allies8']} (idle {d['idle_allies']}) vs {d['opponent']}")
    if a.out:
        Path(a.out).write_text(json.dumps(alld) + '\n', encoding='utf-8')


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
