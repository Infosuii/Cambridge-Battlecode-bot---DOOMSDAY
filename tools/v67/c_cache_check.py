"""Check the game cache: replay N games of a finished run with the cache disabled and compare their summaries.

Usage: c_cache_check.py RUN [--n 3]
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
os.environ['NFS_GAME_CACHE'] = '0'
from nfs import engine  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--n', type=int, default=3)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    build = ROOT / 'artifacts/evaluations/v67' / a.run / 'build'
    ok = True
    for g in games[:: max(1, len(games) // a.n)][:a.n]:
        folder = ROOT / g['folder']
        ours, theirs = build / f"bot-s{g['seed']}.wasm", build / f"p0-s{g['seed']}.wasm"
        A, B = (ours, theirs) if g['side'] == 'a' else (theirs, ours)
        fresh = ROOT / 'artifacts/tmp/v67/cache-check' / folder.name
        if fresh.exists():
            for p in fresh.iterdir():
                p.unlink()
        engine.run_match(A, B, engine.MAPS / f"{g['map']}.map26a", fresh, candidate_side=g['side'].upper())
        old = json.loads((folder / 'summary.json').read_text())
        new = json.loads((fresh / 'summary.json').read_text())
        same = old['teams'] == new['teams'] and old['match'] == new['match'] and old['champions'] == new['champions']
        ok &= same
        print(g['map'], g['side'], 'seed', g['seed'], 'identical' if same else 'DIFFERENT')
    print('cache check', 'passed' if ok else 'FAILED')


if __name__ == '__main__':
    main()
