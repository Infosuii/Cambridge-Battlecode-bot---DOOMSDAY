"""Verify that a selected data payload reproduces each previously measured cell."""
import argparse
from collections import Counter
import json
from pathlib import Path
from palette import OPPONENTS, read

FIELDS = ('map_sha256', 'opponent_sha256', 'engine_hash', 'outcome', 'rounds', 'banked', 'opponent_banked',
          'collected', 'gold', 'deaths', 'fuel_outs', 'faults')


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('runs', type=Path)
    cli.add_argument('selection', type=Path)
    cli.add_argument('uniform_tag')
    cli.add_argument('candidate_tag')
    args = cli.parse_args()
    fit = json.loads(args.selection.read_text())
    rows = read(args.runs, args.uniform_tag, fit['arms'], 'base')
    report = Counter()
    mismatches = []
    for opp in OPPONENTS:
        p = args.runs/f'gx-{args.candidate_tag}-pool-{opp}'/'results.json'
        result = json.loads(p.read_text())
        assert result['games'] == 172, p
        for r in result['per_game']:
            key = r['map'],r['side'],opp
            arm = fit['selected'].get(r['map'],0)
            expected = rows[arm][key]
            diff = [f for f in FIELDS if r[f] != expected[f]]
            if diff:
                mismatches.append((key,arm,diff))
            else:
                report['selected' if arm else 'unchanged'] += 1
    print(json.dumps(dict(equal=dict(report),mismatches=mismatches),indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
