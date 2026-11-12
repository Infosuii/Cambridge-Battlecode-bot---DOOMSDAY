"""Strategy profiles over the bot's 48 runtime lab knobs (src/lab.h; A2_KNOBS in common.h), as deltas on the baked
vector. Each profile is built as a whole-bot variant for league testing; the chosen per-map profile set is compiled
into a runtime table by tools/v67/c_v71_knobs.py.

Usage: c_profiles.py --base bots/v70 --out-prefix artifacts/tmp/v67/v71p   (writes one folder per profile)
       c_profiles.py --list
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

# knob index -> delta (see lab.h: 0 aggression, 1 retreat hp, 2 danger ttd, 3 danger hp, 4 tribute carry, 5 hunt range,
# 6 hunt hp, 7 chase, 8 gold weight, 11 cohesion, 13 hunt gems, 22/23 melee/ranged aggression, 24-31 fight verdict,
# 32 caster risk, 36/37 banking, 38 cohesion distance, 40 middle camps, 41 team-fight engage, 43/44 early aggression, hunt)
PROFILES = {
    'aggr': {0: 1.0, 22: 1.0, 23: 1.0, 43: 1.0},
    'caut': {0: -1.0, 22: -1.0, 23: -1.0, 43: -1.0, 3: 2.0, 1: 1.0},
    'bank': {4: -1.5, 36: 1.5, 37: -1.0},
    'hoard': {4: 1.5, 36: -1.0},
    'hunt': {5: 1.0, 7: 1.0, 13: -1.0, 44: 1.0, 6: -1.0},
    'group': {11: 3.0, 38: -1.0, 41: 1.0},
    'gems': {8: -1.5},
    'gold': {8: 1.5},
    'mid': {40: 2.0},
    'nomid': {40: -2.0},
    'search': {24: -1.0, 25: 1.0, 31: 1.0},
    'ranged': {32: -1.5, 23: 1.0},
    # Round 3 (stronger or combined versions of the profiles closest to v70 overall)
    'hunt2': {5: 2.0, 7: 2.0, 13: -2.0, 44: 2.0, 6: -2.0},
    'ranged2': {32: -3.0, 23: 2.0},
    'search2': {24: -2.0, 25: 2.0, 31: 2.0},
    'huntranged': {5: 1.0, 7: 1.0, 13: -1.0, 44: 1.0, 6: -1.0, 32: -1.5, 23: 1.0},
    'bankhunt': {4: -1.5, 36: 1.5, 37: -1.0, 5: 1.0, 7: 1.0, 13: -1.0, 44: 1.0, 6: -1.0},
    'softcaut': {0: -0.5, 22: -0.5, 23: -0.5, 3: 1.0},
    'softaggr': {0: 0.5, 22: 0.5, 23: 0.5},
    'decisive': {30: -0.5},
    'patient': {30: 1.0},
    'teamfight': {41: 2.0},
    # Round 5 (2026-10-28, from the v67 ladder-loss review: blob farming, idling at camps, leaving camps near enemies):
    # 9 wait weight, 10 need pool (champions a group needs), 12 shop gold, 14 stage timeout, 15 hunt switch, 2 danger ttd
    'spread': {10: -2.0, 11: -3.0},
    'solo': {10: -3.0, 11: -3.0, 14: -2.0},
    'needplus': {10: 2.0},
    'nohunt': {15: -2.0},
    'calm': {2: -1.0},
    'wait': {9: 2.0},
    'nowait': {9: -2.0},
    'shopmore': {12: 2.0},
    'shopless': {12: -2.0},
}


def deltas(name):
    """Knob deltas of a profile; 'old+new' combines two, and on a shared knob the first (the map's existing profile)
    wins, as it does at runtime when the table sets that knob over a variant's baked value."""
    out = {}
    for part in reversed(name.split('+')):
        out.update(PROFILES[part])
    return out


def baked(base):
    code = (ROOT / base / 'src/common.h').read_text(encoding='utf8')
    return [float(x) for x in re.search(r'^#define A2_KNOBS ([^\r\n]*)', code, re.M)[1].split(',')]


def vector(base, name):
    v = baked(base)
    for i, d in deltas(name).items():
        v[i] = round(v[i] + d, 4)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='bots/v70')
    ap.add_argument('--out-prefix')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--only', nargs='*', help='build only these profiles')
    a = ap.parse_args()
    if a.list:
        print(json.dumps(PROFILES, indent=1))
        return
    for name in a.only or PROFILES:
        v = vector(a.base, name)
        knobs = [f'{i}={v[i]}' for i in deltas(name)]
        args = [sys.executable, 'tools/v67/c_variant.py', '--base', a.base, '--out', f'{a.out_prefix}-{name}']
        for k in knobs:
            args += ['--knob', k]
        subprocess.run(args, cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
