"""Extract replay.repl26a from local bot_match game folders into one flat directory (offline analysis).

Usage: python tools/replay/extract_local.py <out dir> <bot_match out dir>...
Each file is named <map>-<side>.repl26a, or <prefix>__<map>-<side> when several outputs are given.
"""
from pathlib import Path
import sys
import zipfile

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
roots = [Path(p) for p in sys.argv[2:]]
for root in roots:
    for f in sorted(root.glob('games/*/*.repl26a')):
        name = f.parent.name if len(roots) == 1 else f'{root.name}__{f.parent.name}'
        with zipfile.ZipFile(f) as z:
            (out / f'{name}.repl26a').write_bytes(z.read('replay.repl26a'))
print(len(list(out.glob('*.repl26a'))), 'replays in', out)
