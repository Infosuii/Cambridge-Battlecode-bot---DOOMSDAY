"""Mode shares from an APEX_MODESTATS run (cumulative "MODES R<round> <type> slot<k>: mode=count ..." lines in our
team's stdout): per mode, the share of all champion turns up to round R, plus the DIAG stuck/abandon counters.

Usage: c_modes.py RUN [--round 500]
"""
import argparse
import collections
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MODES = re.compile(r'^MODES R(\d+) (\S+) slot(\d+): (.*)$')
DIAG = re.compile(r'^DIAG R(\d+) (\S+) slot(\d+) stuck=(\d+) abandons=(\d+) idlemax=(\d+)$')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--round', type=int, default=500)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    total, by_hero, diag = collections.Counter(), collections.defaultdict(collections.Counter), collections.Counter()
    seen, n = set(), 0
    for g in games:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        bundle = next((ROOT / g['folder']).glob('*.repl26a'))
        with zipfile.ZipFile(bundle) as z:
            text = z.read(f"team-{g['side']}.stdout").replace(b'\0', b'').decode('utf8', 'replace')
        last = {}
        for line in text.splitlines():
            m = MODES.match(line)
            if m and int(m[1]) <= a.round:
                last[(m[2], m[3])] = m[4]
            d = DIAG.match(line)
            if d and int(d[1]) == a.round:
                diag['stuck'] += int(d[4])
                diag['abandons'] += int(d[5])
                diag['idlemax'] += int(d[6])
                diag['n'] += 1
        n += 1
        for (hero, _), counts in last.items():
            for kv in counts.split():
                k, v = kv.rsplit('=', 1)
                total[k] += int(v)
                by_hero[hero][k] += int(v)
    s = sum(total.values())
    print(f'{n} games, {s} champion turns up to round {a.round}')
    for k, v in total.most_common(30):
        print(f'  {k:16s} {v / s:6.3f}')
    if diag['n']:
        print(f"per champion at R{a.round}: stuck {diag['stuck'] / diag['n']:.1f}, abandons {diag['abandons'] / diag['n']:.1f}, "
              f"longest idle streak {diag['idlemax'] / diag['n']:.1f}")


if __name__ == '__main__':
    main()
