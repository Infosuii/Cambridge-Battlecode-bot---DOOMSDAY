"""Collect the bot's own atlas lines (X1_ATLAS, bots/x3/src/x1_atlas.h) from a dz run into a feature table, so the
categories are defined on exactly the numbers the bot computes at game start.
  python tools/mapatlas/collect.py [--run atlas-collect-01] [--out research/x3/atlas/bot_atlas.csv]
One row per map (side A's line; side B is the mirror and is checked for agreement).
"""
import argparse, csv, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def parse(line):
    d = dict(kv.split('=', 1) for kv in line.split()[1:])
    w, h, g, gems, team = d.pop('fp').split(',')
    out = dict(w=int(w), h=int(h), groups=int(g), gems=int(gems), side_team=int(team))
    for k, v in d.items():
        out[k] = float(v) if re.match(r'^-?[0-9.]+$', v) else v
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', default='atlas-collect-01'); ap.add_argument('--out', default='research/x3/atlas/bot_atlas.csv')
    a = ap.parse_args()
    games = ROOT / 'artifacts/tmp/dz' / a.run / 'games'
    rows, diffs = {}, 0
    for g in sorted(games.iterdir()):
        f = g / 'candidate.stdout'
        if not f.exists(): continue
        line = next((l for l in f.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('ATLAS ')), None)
        if not line: continue
        mp, side = g.name.rsplit('-', 1)
        r = parse(line)
        if side == 'A': rows[mp] = dict(map=mp, **r)
        elif mp in rows and (rows[mp]['groups'], rows[mp]['gems']) != (r['groups'], r['gems']): diffs += 1
    keys = list(next(iter(rows.values())))
    with open(ROOT / a.out, 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, fieldnames=keys); wr.writeheader(); [wr.writerow(rows[m]) for m in sorted(rows)]
    print(len(rows), 'maps ->', a.out, '| A/B group-count disagreements:', diffs)


if __name__ == '__main__':
    main()
