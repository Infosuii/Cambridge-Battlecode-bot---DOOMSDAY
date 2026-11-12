"""Proxy opponent, step 4: does a local opponent give the ladder's verdicts?

  python tools/proxy/compare.py --ladder research/proxy/ladder_arms.json --run <name>=<local_duel out dir>,... [...]
         [--md research/proxy/VALIDATION.md] [--json out.json]

A run is one opponent (a proxy, or a control such as self-play against v65) that every arm of the ladder duel has
played locally on the duel's schedule (tools/proxy/local_duel.py, one out dir per arm, all with the same seeds).
Give each run as name=dir1,dir2,... ; each dir's games.json names its arm.

For each run:
  level     the arm's mean gem margin and win rate, locally and on the ladder
  per game  over the 120 (group, slot) games of each arm: correlation of the local margin (mean over seeds) with the
            ladder margin, i.e. whether the proxy finds the same maps and opponents hard
  teams     per opponent, the margin pooled over all arms (60 ladder games per team in the duel plan), locally and on
            the ladder, and their correlation across the 12 teams: whether the proxy knows which teams are hard
  arms      Spearman rank correlation of the arm means; and for each pair of arms, the paired local difference
            (same games) against the paired ladder difference, with standard errors; a pair "agrees" when the
            signs match, and is "decided" on the ladder when |difference| > 2 SE
The ladder itself is one game per (arm, group, slot); its paired SEs (about 50 gems) bound how well any proxy can be
shown to agree.
"""
import argparse
import collections as co
import json
import math
from pathlib import Path


def mean(x):
    return sum(x) / len(x) if x else float('nan')


def se(x):
    if len(x) < 2:
        return float('nan')
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1) / len(x))


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sxy / (sx * sy) if sx and sy else float('nan')


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def load_ladder(path):
    out = co.defaultdict(dict)
    for r in json.loads(Path(path).read_text(encoding='utf8'))['games']:
        out[r['arm']][(r['group'], r['slot'])] = (r['margin'], r['win'])
    return out


def team_of_group(path):
    plan = json.loads(Path(json.loads(Path(path).read_text(encoding='utf8'))['plan']).read_text(encoding='utf8'))
    return [g['opponent'] for g in plan['groups']]


def load_run(dirs):
    out = {}
    for d in dirs:
        g = json.loads((Path(d) / 'games.json').read_text(encoding='utf8'))
        per = co.defaultdict(list)
        for r in g['games']:
            per[(r['group'], r['slot'])].append((r['margin'], r['win'] + 0.5 * r.get('draw', False)))
        out[g['name']] = {k: (mean([m for m, _ in v]), mean([w for _, w in v])) for k, v in per.items()}
    return out


def evaluate(ladder, local, teams_of):
    arms = [a for a in ladder if a in local]
    per_team = co.defaultdict(lambda: ([], []))
    for a in arms:
        for k in set(ladder[a]) & set(local[a]):
            per_team[teams_of[k[0]]][0].append(ladder[a][k][0])
            per_team[teams_of[k[0]]][1].append(local[a][k][0])
    teams = [dict(team=t, games=len(l), ladder=mean(l), ladder_se=se(l), local=mean(p), local_se=se(p))
             for t, (l, p) in sorted(per_team.items())]
    rows = []
    for a in arms:
        keys = sorted(set(ladder[a]) & set(local[a]))
        lm = [ladder[a][k][0] for k in keys]
        pm = [local[a][k][0] for k in keys]
        rows.append(dict(arm=a, games=len(keys), ladder=mean(lm), ladder_se=se(lm), ladder_win=mean([ladder[a][k][1] for k in keys]),
                         local=mean(pm), local_se=se(pm), local_win=mean([local[a][k][1] for k in keys]),
                         per_game_r=pearson(lm, pm)))
    pairs = []
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            keys = sorted(set(ladder[a]) & set(ladder[b]) & set(local[a]) & set(local[b]))
            dl = [ladder[b][k][0] - ladder[a][k][0] for k in keys]
            dp = [local[b][k][0] - local[a][k][0] for k in keys]
            pairs.append(dict(a=a, b=b, games=len(keys), ladder=mean(dl), ladder_se=se(dl), local=mean(dp), local_se=se(dp),
                              agree=(mean(dl) > 0) == (mean(dp) > 0), decided=abs(mean(dl)) > 2 * se(dl)))
    summary = dict(arms=len(arms),
                   spearman=spearman([r['ladder'] for r in rows], [r['local'] for r in rows]) if len(rows) > 2 else float('nan'),
                   pearson=pearson([r['ladder'] for r in rows], [r['local'] for r in rows]) if len(rows) > 2 else float('nan'),
                   pairs_agree=sum(p['agree'] for p in pairs), pairs=len(pairs),
                   decided_agree=sum(p['agree'] for p in pairs if p['decided']), decided=sum(p['decided'] for p in pairs),
                   per_game_r=mean([r['per_game_r'] for r in rows]),
                   team_r=pearson([t['ladder'] for t in teams], [t['local'] for t in teams]) if len(teams) > 2 else float('nan'))
    return dict(summary=summary, arms=rows, pairs=pairs, teams=teams)


def markdown(results):
    L = ['| Run | Arms | Team r | Rank corr. | Pairs agreeing | Decided pairs agreeing | Per-game r |',
         '|---|---:|---:|---:|---:|---:|---:|']
    for name, r in results.items():
        s = r['summary']
        L.append(f"| {name} | {s['arms']} | {s['team_r']:+.2f} | {s['spearman']:+.2f} | {s['pairs_agree']}/{s['pairs']} | "
                 f"{s['decided_agree']}/{s['decided']} | {s['per_game_r']:+.2f} |")
    for name, r in results.items():
        L += ['', f'### {name}', '', '| Arm | Ladder margin | Local margin | Ladder wins | Local wins | Per-game r |',
              '|---|---:|---:|---:|---:|---:|']
        for a in r['arms']:
            L.append(f"| {a['arm']} | {a['ladder']:+.0f} +/- {a['ladder_se']:.0f} | {a['local']:+.0f} +/- {a['local_se']:.0f} | "
                     f"{a['ladder_win']:.2f} | {a['local_win']:.2f} | {a['per_game_r']:+.2f} |")
        L += ['', '| Opponent (all arms pooled) | Games | Ladder margin | Local margin |', '|---|---:|---:|---:|']
        for t in r['teams']:
            L.append(f"| {t['team']} | {t['games']} | {t['ladder']:+.0f} +/- {t['ladder_se']:.0f} | {t['local']:+.0f} +/- {t['local_se']:.0f} |")
        L += ['', '| Pair (b - a) | Ladder | Local | Agree |', '|---|---:|---:|---|']
        for p in r['pairs']:
            L.append(f"| {p['b']} - {p['a']} | {p['ladder']:+.0f} +/- {p['ladder_se']:.0f}{' *' if p['decided'] else ''} | "
                     f"{p['local']:+.0f} +/- {p['local_se']:.0f} | {'yes' if p['agree'] else 'no'} |")
    L += ['', '`*`: decided on the ladder (|difference| > 2 SE).']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ladder', required=True)
    ap.add_argument('--run', action='append', required=True, help='name=dir1,dir2,...')
    ap.add_argument('--md')
    ap.add_argument('--json')
    a = ap.parse_args()
    ladder = load_ladder(a.ladder)
    teams_of = team_of_group(a.ladder)
    results = {}
    for spec in a.run:
        name, dirs = spec.split('=', 1)
        results[name] = evaluate(ladder, load_run(dirs.split(',')), teams_of)
    text = markdown(results)
    print(text)
    if a.md:
        Path(a.md).write_text(text + '\n', encoding='utf8', newline='\n')
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=1) + '\n', encoding='utf8', newline='\n')


if __name__ == '__main__':
    main()
