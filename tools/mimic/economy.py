"""Opening economy from replay actor ledgers, aggregated by the same classes as the fight-style report."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/proxy'))
from style_report import sides


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--index', required=True)
    ap.add_argument('--replays', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--source', default='local')
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    out.mkdir(parents=True)
    index = json.loads(Path(a.index).read_text(encoding='utf8'))
    files = [Path(a.replays).resolve() / (m + '.repl26a') for m, info in index.items() if info['source'] == a.source]
    if not files or not all(p.is_file() for p in files):
        raise SystemExit('missing replays')
    env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0', NFS_LEDGER_UNTIL='250')

    def batch(pair):
        i, paths = pair
        target = out / f'ledger-{i}.json'
        subprocess.run(['node', '--no-warnings', str(ROOT / 'tools/replay/actor_ledger.mjs'), str(target), *map(str, paths)],
                       check=True, env=env, capture_output=True, text=True)
        return json.loads(target.read_text(encoding='utf8'))

    totals = defaultdict(Counter)
    batches = enumerate([files[i:i + 12] for i in range(0, len(files), 12)])
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for games in ex.map(batch, batches):
            for game in games:
                for team, classes in sides(index[game['id']]).items():
                    for name in classes:
                        if name.startswith('proxy:'):
                            name = 'mimic'
                        for window in (100, 250):
                            if game['rounds'] < window:
                                continue
                            total = totals[f'{name}@{window}']
                            total['games'] += 1
                            for actor in game['actors']:
                                if actor['team'] == team:
                                    total.update(actor['w'].get(str(window), {}))
    report = {}
    for name, t in sorted(totals.items()):
        alive, games = max(1, t['alive']), max(1, t['games'])
        report[name] = dict(games=t['games'], capture_gold=t['cap_gold'] / games,
                            capture_gems=t['cap_gems'] / games, gold_per_alive_100=100 * t['cap_gold'] / alive,
                            clear=t['clear'] / alive, still=t['still'] / alive, travel=t['travel'] / alive,
                            spawn=t['spawn'] / alive, bank=t['bank'] / alive,
                            shared_capture=t['shared_caps'] / max(1, t['caps']))
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
