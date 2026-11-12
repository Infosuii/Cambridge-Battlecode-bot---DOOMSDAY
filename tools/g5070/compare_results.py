"""Compare complete deterministic gates by unique map/side identity."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def compare(reference, candidate, expected=172):
    def index(result):
        rows = result['per_game']
        by_key = {(r['map'], r['side']): r for r in rows}
        if len(rows) != expected or result['games'] != expected or len(by_key) != expected:
            raise ValueError('incomplete gate or duplicate map/side identity')
        if any(side not in ('A', 'B') for _, side in by_key):
            raise ValueError('invalid candidate side')
        wins = sum(r['outcome'] == 'team' + r['side'] for r in rows)
        if wins != result['wins']:
            raise ValueError('aggregate wins disagree with records')
        return by_key

    base, cand = index(reference), index(candidate)
    if base.keys() != cand.keys():
        raise ValueError('reference/candidate map/side sets differ')
    fields = ('outcome', 'banked', 'opponent_banked', 'rounds', 'deaths',
              'faults', 'opponent_faults', 'fuel_outs', 'map_sha256', 'engine',
              'engine_hash', 'candidate_sha256', 'opponent_sha256')
    matches = {f: sum(base[k].get(f) == cand[k].get(f) for k in base) for f in fields}
    differences = []
    gained = lost = 0
    for key in sorted(base):
        b, c = base[key], cand[key]
        bw, cw = b['outcome'] == 'team' + b['side'], c['outcome'] == 'team' + c['side']
        gained += cw and not bw
        lost += bw and not cw
        changed = {f: {'reference': b.get(f), 'candidate': c.get(f)}
                   for f in fields[:8] if b.get(f) != c.get(f)}
        if changed:
            differences.append({'map': key[0], 'side': key[1], 'changed': changed})
    required = ('outcome', 'banked', 'opponent_banked', 'map_sha256', 'engine_hash')
    exact = sum(all(base[k].get(f) == cand[k].get(f) for f in required) for k in base)
    def summary(result):
        return {**{k: result[k] for k in ('games', 'wins', 'faults', 'opponent_faults', 'fuel_outs')},
                'deaths_per_game': sum(r['deaths'] for r in result['per_game']) / expected,
                'candidate_hashes': sorted({r['candidate_sha256'] for r in result['per_game']}),
                'opponent_hashes': sorted({r['opponent_sha256'] for r in result['per_game']})}
    return {'records': expected, 'matching_required_records': exact,
            'behavioral_exact': exact == expected,
            'builds_exact': matches['candidate_sha256'] == matches['opponent_sha256'] == expected,
            'matching_fields': matches, 'reference': summary(reference), 'candidate': summary(candidate),
            'delta_wins': candidate['wins'] - reference['wins'], 'gained': gained, 'lost': lost,
            'paired_z': (gained - lost) / math.sqrt(gained + lost) if gained + lost else 0.0,
            'changed_game_records': differences}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = compare(json.loads(args.reference.read_text()), json.loads(args.candidate.read_text()))
    report['input_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                              for name, path in [('reference', args.reference), ('candidate', args.candidate)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
