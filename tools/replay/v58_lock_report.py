"""Report lock use and completed tribute timing from a completed bench; raw replays remain local-only.

Usage: python tools/replay/v58_lock_report.py <bench prefix> <report.json>
Completed tribute latency excludes time before a start and cannot prove how much delay an altar lock caused.
"""
from pathlib import Path
import glob
import json
import statistics as st
import sys
import zipfile
from ledger_bench import run_batches

ROOT = Path(__file__).resolve().parents[2]


def main():
    prefix, output = sys.argv[1:3]
    work = ROOT / 'artifacts/local-only/v58' / Path(prefix).name
    work.mkdir(parents=True, exist_ok=True)
    files, sides = [], {}
    for summary in sorted(glob.glob(prefix + '-seed*-s*/summary.json')):
        seed = Path(summary).parent.name.split('-seed')[-1].split('-')[0]
        for g in json.loads(Path(summary).read_text(encoding='utf8'))['per_game']:
            name = f"{g['map']}-{g['side']}-seed{seed}"
            p = work / (name + '.repl26a')
            if not p.exists():
                matches = list(Path(g['folder']).glob('*.repl26a'))
                assert len(matches) == 1
                with zipfile.ZipFile(matches[0]) as z:
                    p.write_bytes(z.read('replay.repl26a'))
            files.append(str(p))
            sides[name] = 0 if g['side'] == 'A' else 1
    assert files, 'no completed games'
    cache = work / 'lock-audit.json'
    if not cache.exists():
        run_batches('v58_lock_audit.mjs', [], files, cache)
    rows = json.loads(cache.read_text(encoding='utf8'))
    assert len(rows) == len(files)
    report = {'games': len(rows), 'note': __doc__.splitlines()[-1]}
    for label in ('candidate', 'opponent'):
        records = [r['teams'][sides[r['id']] if label == 'candidate' else 1 - sides[r['id']]] for r in rows]
        totals = {key: sum(r[key] for r in records) for key in ('locks', 'starts', 'banks', 'restarts')}
        latency = [v for r in records for v in r['latency_rounds']]
        report[label] = dict(totals, locks_per_game=totals['locks'] / len(rows),
                             completion_ratio=totals['banks'] / max(1, totals['starts']),
                             completed_latency_mean=st.mean(latency) if latency else None)
    Path(output).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
