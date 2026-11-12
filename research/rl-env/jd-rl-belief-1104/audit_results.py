"""Audit pinned E124 rows; map-cluster intervals are exploratory, not release gates."""
import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'evidence'
SEED, REPS = 1104, 10000

def rows(name):
    return list(csv.reader((EVIDENCE / name).open(), delimiter='\t'))

def interval(groups):
    rng = random.Random(SEED)
    g = list(groups.values())
    samples = []
    for _ in range(REPS):
        selected = rng.choices(g, k=len(g))
        samples.append(sum(sum(v) for v in selected) / sum(len(v) for v in selected))
    samples.sort()
    return [samples[int(.025 * REPS)], samples[int(.975 * REPS)]]

off, fresh, extra = rows('e124_off.tsv'), rows('e124_fresh.tsv'), rows('e124_c4.tsv')
report = {'source_commit': '0b0ae8e475c65c2901a0aad02842c58a0fee6c55',
          'bootstrap': {'seed': SEED, 'replicates': REPS, 'unit': 'map; both sides and opponent variants together'},
          'limitations': ['Known official maps; new opponent jitter does not make new maps.',
                         'Checkpoint comparison/selection used these results; intervals are exploratory.',
                         'No match manifests, WASM hashes or fuel telemetry independently verified.',
                         'Win rates against v92-family opponents do not compare nnc4 directly with CPG.']}
for label, selected in [('official', [r for r in off + extra if r[0] == 'nnc4' and r[2].startswith('maps~')]),
                        ('fresh', [r for r in fresh if r[0] == 'nnc4']),
                        ('unseen', [r for r in extra if r[0] == 'nnc4' and not r[2].startswith('maps~')])]:
    keys = [(r[1], r[2], r[3]) for r in selected]
    assert len(keys) == len(set(keys)), 'duplicate game cells'
    groups = defaultdict(list)
    for r in selected:
        value = float(r[4]); assert value in (0., .5, 1.)
        groups[r[2]].append(value)
    report[label] = {'cells': len(selected), 'maps': len(groups), 'wins': sum(map(sum, groups.values())),
                     'win_rate': sum(map(sum, groups.values())) / len(selected),
                     'map_cluster_percentile_95': interval(groups)}
lookup = {(r[0], r[1], r[2], r[3]): float(r[4]) for r in off}
paired = defaultdict(list)
for r in off:
    if r[0] == 'nnc4':
        key = ('nnc0', r[1], r[2], r[3]); assert key in lookup
        paired[r[2]].append(float(r[4]) - lookup[key])
report['nnc4_minus_nnc0_same_cells'] = {'cells': sum(map(len, paired.values())),
    'delta': sum(map(sum, paired.values())) / sum(map(len, paired.values())),
    'map_cluster_percentile_95': interval(paired)}
report['input_sha256'] = {name: hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest()
                          for name in ['e124_c4.tsv', 'e124_fresh.tsv', 'e124_off.tsv']}
output = ROOT / 'E124_AUDIT.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
