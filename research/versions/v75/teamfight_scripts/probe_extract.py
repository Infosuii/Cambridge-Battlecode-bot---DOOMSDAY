"""Extract one existing ladder replay for decoded-field inspection."""
from pathlib import Path
import zipfile

p = next(Path('artifacts/local-only/duel-v74').glob('*/replay.repl26a'))
with zipfile.ZipFile(p) as z:
    n = next(n for n in z.namelist() if n.endswith('.repl26a'))
    out = Path('artifacts/tmp/v67/v80-audit')
    out.mkdir(exist_ok=True)
    (out / 'probe.repl26a').write_bytes(z.read(n))
print(p)
