"""Our deaths vs the opponents' in a duel arm's replays (tools/replay/death_context.mjs output).
  python research/x3/duel/death_compare.py PLAN ARM REPLAY_DIR DEATHS_JSON"""
import json, glob, sys
plan_f, arm, rdir, deaths_f = sys.argv[1:5]
files = sorted(p.replace(chr(92), '/') for p in glob.glob(f'{rdir}/**/*.repl26a', recursive=True))
plan = json.load(open(plan_f, encoding='utf-8'))
d = json.load(open(deaths_f))
assert len(d) == len(files), (len(d), len(files))
agg = {'us': [], 'them': []}
for f, rep in zip(files, d):
    gi, pos = (int(x[:2]) for x in f.split(rdir.rstrip('/') + '/')[1].split('/')[:2])
    our = 0 if plan['groups'][gi]['sides'][pos - 1] == 'a' else 1
    for x in rep['deaths']: agg['us' if x['team'] == our else 'them'].append(x)
G = len(files)
for tag in ('us', 'them'):
    xs = agg[tag]; n = len(xs)
    pr = lambda c: f"{100 * sum(1 for x in xs if c(x)) / max(1, n):.0f}%"
    print(f"{tag:4s} {n/G:.1f} deaths/game | healthy 5 rounds before {pr(lambda x: x['hp5'] >= 0.6 * x['max_hp'])} | "
          f"outnumbered by 2+ {pr(lambda x: x['enemies4'] >= x['allies4'] + 2)} | no ally within 4 {pr(lambda x: x['allies4'] == 0)} | "
          f"hitting camps {pr(lambda x: x['camp_attacks'] > 0)} | never hit back {pr(lambda x: x['pvp_attacks'] == 0)} | "
          f"gems lost {sum(x['gems'] for x in xs) / G:.0f}/game")
    print('      deaths/game by round: ' + '  '.join(f"{lo}-{hi} {sum(lo <= x['round'] < hi for x in xs) / G:.2f}" for lo, hi in ((0, 150), (150, 400), (400, 800), (800, 2001))))
