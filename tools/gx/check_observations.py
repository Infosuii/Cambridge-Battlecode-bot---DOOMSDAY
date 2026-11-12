"""Conformance checks on camp catalogue records and visibility reads."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('catalogue', 'visibility', 'capture'))
    p.add_argument('wasm', type=Path)
    p.add_argument('maps', type=Path)
    p.add_argument('scratch', type=Path)
    p.add_argument('layouts', nargs='+')
    p.add_argument('--rounds', type=int, default=0)
    p.add_argument('--workers', type=int, default=8)
    a = p.parse_args()
    a.scratch.mkdir(parents=True)
    tool = os.environ.get('DZ_CAMBC', 'cambc')

    def run(name):
        path = a.maps / (name + '.map26a')
        out = a.scratch / name
        out.mkdir()
        cmd = [tool, 'run', str(a.wasm.resolve()), str(a.wasm.resolve()), '--map', str(path.resolve()),
               '--out-dir', str(out.resolve()), '--statistics', str((out / 'summary.json').resolve()),
               '--json', '--release']
        if a.rounds > 0:
            cmd += ['--rounds', str(a.rounds)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(name + '\n' + result.stdout + result.stderr)
        with zipfile.ZipFile(next(out.glob('*.repl26a'))) as replay:
            logs = [replay.read('team-' + side + '.stdout').decode(errors='replace') for side in 'ab']
        native = out / 'summary.json'
        faults = json.loads(native.read_text())['diagnostics']['botFaults'] if native.exists() else None
        if (not a.rounds and faults is None) or (faults is not None and any(faults.values())):
            raise ValueError((name, faults, [s[-4000:] for s in logs]))
        hits = [re.findall(r'GXCATALOG ([01]) groups=(\d+) camps=(\d+)', s) for s in logs]
        if a.mode == 'catalogue' and (not all(hits) or any(len(set(rows)) != 1 for rows in hits)):
            raise ValueError((name, hits))
        checked = [s.count('GXSEEN checked') for s in logs]
        if a.mode == 'visibility' and any('GXSEEN mismatch' in s for s in logs):
            raise ValueError((name, logs))
        progress = []
        if a.mode == 'capture':
            for log in logs:
                rows = [tuple(map(int, x)) for x in re.findall(r'GXPROG r=(\d+) group=(\d+) type=(\d+) timer=(-?\d+) on=([01])', log)]
                if not rows or any(not 0 <= kind <= 4 or timer < 0 for _, _, kind, timer, _ in rows):
                    raise ValueError((name, rows[:30]))
                progress.append(dict(count=len(rows), states=Counter(kind for _, _, kind, _, _ in rows),
                    timers={k: sorted({timer for _, _, kind, timer, _ in rows if kind == k}) for k in range(5)},
                    ally_on=sum(k == 1 and on for _, _, k, _, on in rows)))
        return dict(map=name, map_sha256=sha256(path.read_bytes()).hexdigest(), faults=faults,
                    catalogue_markers=hits, hidden_checks_marked=checked, progress=progress, mismatch_count=0)

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows = list(pool.map(run, a.layouts))
    print(json.dumps(dict(mode=a.mode, wasm_sha256=sha256(a.wasm.read_bytes()).hexdigest(),
                          rounds=a.rounds, rows=rows), indent=2))


if __name__ == '__main__':
    main()
