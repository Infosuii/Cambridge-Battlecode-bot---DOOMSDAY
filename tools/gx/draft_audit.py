"""Measure opponent identification on deduplicated historical matches."""
from collections import Counter, defaultdict
from hashlib import sha256
import argparse
import json
from pathlib import Path

OWN = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'


def read(path):
    rows = set()
    for match in json.loads(Path(path).read_text()):
        if match.get('status') != 'finished' or len(match.get('teams', ())) != 2:
            continue
        a, b = match['teams']
        if b.get('teamId') == OWN:
            a, b = b, a
        picks = tuple(int(x) for x in b.get('draftPicks', ()))
        if a.get('teamId') != OWN or len(picks) < 2:
            continue
        rows.add((b['name'], match['map'], b['side'], picks))
    return rows


def score(train, test, mode):
    def key(side, picks):
        if mode == 'prefix':
            return (len(picks), picks[:-1])
        if mode == 'full':
            return picks
        return side, picks
    votes = defaultdict(lambda: defaultdict(set))
    for team, name, side, picks in train:
        votes[key(side, picks)][team].add(name)
    table = {k: team for k, counts in votes.items() if len(counts) == 1
             for team, maps in counts.items() if len(maps) >= 3}
    counts = Counter()
    detail = defaultdict(Counter)
    for team, _, side, picks in test:
        guess = table.get(key(side, picks))
        kind = 'unknown' if guess is None else 'correct' if guess == team else 'wrong'
        counts[kind] += 1
        detail[team][kind] += 1
    return dict(entries=len(table), totals=dict(counts), teams={t: dict(c) for t, c in sorted(detail.items())})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('older')
    parser.add_argument('newer')
    args = parser.parse_args()
    older, newer = read(args.older), read(args.newer)
    all_rows = older | newer
    folds = [{r for r in all_rows if sha256(r[1].encode()).digest()[0] % 2 == i} for i in range(2)]
    tests = {'map0_to_map1': (folds[0], folds[1]), 'map1_to_map0': (folds[1], folds[0]),
             'older_to_newer': (older, newer), 'older_to_newer_fresh_maps': (
                 older, {r for r in newer if r[1] not in {x[1] for x in older}}
             )}
    print(json.dumps(dict(rows={'older': len(older), 'newer': len(newer), 'combined': len(all_rows)},
        tests={label: {mode: score(train, test, mode) for mode in ('prefix', 'full', 'full_and_side')}
               for label, (train, test) in tests.items()}), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
