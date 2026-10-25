"""Give each file in a bot copy the same line endings as its counterpart in a reference bot (keeps diffs reviewable).

Usage: python tools/eol_like.py <reference src dir> <target src dir>
"""
from pathlib import Path
import sys

ref, tgt = Path(sys.argv[1]), Path(sys.argv[2])
for f in sorted(tgt.iterdir()):
    r = ref / f.name
    if not f.is_file() or not r.exists():
        continue
    want_crlf = b'\r\n' in r.read_bytes()
    data = f.read_bytes().replace(b'\r\n', b'\n')
    if want_crlf:
        data = data.replace(b'\n', b'\r\n')
    if data != f.read_bytes():
        f.write_bytes(data)
        print('fixed', f.name, 'crlf' if want_crlf else 'lf')
