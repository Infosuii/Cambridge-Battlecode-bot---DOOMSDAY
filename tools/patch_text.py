"""Apply literal (old -> new) replacements to a CRLF/LF source file, preserving its line endings.

Usage (from Python): from patch_text import patch; patch(path, [(old, new), ...]); each old must occur exactly once.
"""
from pathlib import Path


def patch(path, pairs, count=1):
    p = Path(path)
    raw = p.read_bytes().decode('utf-8', errors='surrogateescape')
    crlf = '\r\n' in raw
    s = raw.replace('\r\n', '\n')
    for old, new in pairs:
        n = s.count(old)
        if n != count:
            raise SystemExit(f'{path}: expected {count} occurrence(s), found {n}: {old[:80]!r}')
        s = s.replace(old, new)
    if crlf:
        s = s.replace('\n', '\r\n')
    p.write_bytes(s.encode('utf-8', errors='surrogateescape'))
