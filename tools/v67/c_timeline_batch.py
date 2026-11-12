"""Write timeline.json (tools/v67/c_timeline.mjs) next to every downloaded platform replay bundle in a folder.

Usage: c_timeline_batch.py artifacts/local-only/v67-ranked [--workers 6] [--glob 'games/*/*.repl26a']
Platform downloads are zip bundles; the inner replay.repl26a is extracted to a temporary folder first.
"""
import argparse
import concurrent.futures as cf
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def one(bundle):
    out = bundle.parent / 'timeline.json'
    if out.exists():
        return 'cached'
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(bundle) as z:
            inner = next(n for n in z.namelist() if n.endswith('.repl26a'))
            z.extract(inner, tmp)
        p = subprocess.run(['node', str(ROOT / 'tools/v67/c_timeline.mjs'), str(Path(tmp) / inner), str(out)],
                           capture_output=True, text=True, env={**os.environ, 'NFS_REPLAY_ENGINE': '2.0.0'}, timeout=600)
        if p.returncode:
            return 'error ' + p.stderr[-300:]
    return 'ok'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--glob', default='*/replay.repl26a', help="local benchmark runs: 'games/*/*.repl26a'")
    a = ap.parse_args()
    bundles = sorted((ROOT / a.folder).glob(a.glob))
    with cf.ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(one, bundles))
    errs = [r for r in res if r.startswith('error')]
    print(len(bundles), 'bundles;', res.count('ok'), 'new,', res.count('cached'), 'cached,', len(errs), 'errors', errs[:2])


if __name__ == '__main__':
    main()
