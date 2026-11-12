"""Enrich existing ladder/local replays without playing games. audit_batch.py INDEX FOLDER [--workers N]."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

p = argparse.ArgumentParser()
p.add_argument('index')
p.add_argument('folder')
p.add_argument('--workers', type=int, default=3)
a = p.parse_args()
rows = json.loads(Path(a.index).read_text())

def one(r):
    folder = Path(a.folder) / r['matchId']
    out = folder / 'policy500.json'
    if out.exists():
        return 'cached'
    bundle = next(folder.glob('*.repl26a'))
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(bundle) as z:
            inner = next(n for n in z.namelist() if n.endswith('.repl26a'))
            replay = Path(tmp) / 'inner.repl26a'
            replay.write_bytes(z.read(inner))
        result = subprocess.run(['node', '--no-warnings', 'research/v81/policy_extract.mjs',
                                 str(replay), str(out)], capture_output=True, text=True,
                                env={**os.environ, 'NFS_REPLAY_ENGINE': '2.0.0'}, timeout=600)
        if result.returncode:
            raise RuntimeError(f'{bundle}: {result.stderr[-1500:]}')
    return 'ok'

with ThreadPoolExecutor(a.workers) as ex:
    for n, result in enumerate(ex.map(one, rows), 1):
        if n % 20 == 0 or n == len(rows):
            print(n, '/', len(rows), result, flush=True)
