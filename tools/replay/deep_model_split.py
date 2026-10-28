"""Freeze internal game-separated model partitions from the examined set only."""
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from deep_preflight import ROOT


def main():
    study = ROOT / 'research/deep-2026-10-28'
    target = study / 'MODEL_SPLIT.json'
    catalog = json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/restored-catalog.json').read_text(encoding='utf-8'))
    groups = defaultdict(list)
    for row in catalog:
        if row['partition'] != 'examined':
            continue
        a_won = next(side['result'] == 'win' for side in row['sides'] if side['side'] == 'a')
        groups[(row['cohort'], a_won)].append(row['match_id'])
    rng = random.Random(20261028)
    for key in sorted(groups):
        groups[key].sort()
        rng.shuffle(groups[key])

    def allocate(proportion, total, caps):
        counts = {key: min(math.floor(proportion * len(values)), caps[key]) for key, values in groups.items()}
        ranked = sorted(groups, key=lambda key: (-(proportion * len(groups[key]) - math.floor(proportion * len(groups[key]))),
                        hashlib.sha256(str(key).encode()).hexdigest()))
        remaining = total - sum(counts.values())
        for key in ranked:
            if remaining and counts[key] < caps[key]:
                counts[key] += 1
                remaining -= 1
        assert remaining == 0
        return counts

    train = allocate(.6, 231, {key: len(values) for key, values in groups.items()})
    calibration = allocate(.2, 77, {key: len(values) - train[key] for key, values in groups.items()})
    rows = []
    for (cohort, outcome), values in sorted(groups.items()):
        key = (cohort, outcome)
        for i, mid in enumerate(values):
            split = 'train' if i < train[key] else 'calibration' if i < train[key] + calibration[key] else 'test'
            rows.append({'match_id': mid, 'cohort': cohort, 'team_a_won': outcome, 'split': split})
    result = {'seed': 20261028, 'unit': 'game', 'eligible': 'examined only',
              'strata': ['primary cohort', 'Team A outcome'], 'hands_off_used': 0,
              'method': 'seeded within-stratum shuffle; Hamilton 231/77/77 allocation before model features/results',
              'counts': dict(Counter(r['split'] for r in rows)), 'rows': sorted(rows, key=lambda r: r['match_id'])}
    assert result['counts'] == {'train': 231, 'calibration': 77, 'test': 77}
    for split in result['counts']:
        assert {r['team_a_won'] for r in rows if r['split'] == split} == {False, True}
    raw = (json.dumps(result, indent=2) + '\n').encode()
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('Internal model partition is immutable; do not resplit after inspecting results')
    target.write_bytes(raw)
    print(json.dumps({'games': len(rows), 'counts': result['counts'], 'hands_off_used': 0}))


if __name__ == '__main__':
    main()
