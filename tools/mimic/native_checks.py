"""Audit mimic's own native match statistics (local_duel.py reports the candidate side)."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    jobs = []
    for directory in a.runs:
        data = json.loads((Path(directory) / 'games.json').read_text(encoding='utf8'))
        jobs.extend((data['name'], row) for row in data['games'])

    def read(job):
        arm, row = job
        folder = ROOT / row['folder']
        data = json.loads((folder / 'summary.json').read_text(encoding='utf8'))
        side = 'B' if row['side'] == 'a' else 'A'
        r = engine.parse_summary(data, folder, row['map'], side)
        return arm, dict(games=1, faults=r.faults, fuel_exhausted=r.fuel_exhausted, deaths=r.deaths,
                         earned_gold=r.gold, collected_gems=r.collected)

    result = defaultdict(Counter)
    with ThreadPoolExecutor(max_workers=8) as ex:
        for arm, values in ex.map(read, jobs):
            result[arm].update(values)
    Path(a.out).write_text(json.dumps(result, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(result, indent=2))
    if any(r['faults'] for r in result.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
