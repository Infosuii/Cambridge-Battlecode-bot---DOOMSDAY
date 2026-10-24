"""Agent A: build a bot dir with the official CLI and compare its Wasm sections with a reference.

    python tools/audit_build_compare.py --bot artifacts/tmp/A/x/bot --out artifacts/tmp/A/x/x.wasm [--ref references/builds/original.wasm]
Prints JSON: section-by-section equality, code-section sha, export list differences.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

SECTION_NAMES = {1: 'type', 2: 'import', 3: 'function', 4: 'table', 5: 'memory', 6: 'global', 7: 'export', 8: 'start',
                 9: 'element', 10: 'code', 11: 'data', 12: 'datacount', 13: 'tag'}


def _leb(raw: bytes, off: int) -> tuple[int, int]:
    v = s = 0
    while True:
        b = raw[off]
        off += 1
        v |= (b & 127) << s
        if not b & 128:
            return v, off
        s += 7


def exports(path) -> list[str]:
    raw = Path(path).read_bytes()
    off = 8
    while off < len(raw):
        kind = raw[off]
        size, off = _leb(raw, off + 1)
        if kind == 7:
            n, p = _leb(raw, off)
            names = []
            for _ in range(n):
                ln, p = _leb(raw, p)
                names.append(raw[p:p + ln].decode())
                p += ln + 1  # kind byte
                _, p = _leb(raw, p)
            return names
        off += size
    return []


def code_size(path) -> int:
    raw = Path(path).read_bytes()
    off = 8
    while off < len(raw):
        kind = raw[off]
        size, off = _leb(raw, off + 1)
        if kind == 10:
            return size
        off += size
    return 0


def compare(wasm, ref) -> dict:
    a, b = dict(engine.wasm_sections(wasm)), dict(engine.wasm_sections(ref))
    sections = {SECTION_NAMES.get(k, str(k)): (a.get(k) == b.get(k)) for k in sorted(set(a) | set(b))}
    ea, eb = exports(wasm), exports(ref)
    return {
        'wasm': str(wasm), 'ref': str(ref),
        'wasm_sha256': engine.sha256(wasm), 'ref_sha256': engine.sha256(ref),
        'code_sha': engine.code_section_sha(wasm), 'ref_code_sha': engine.code_section_sha(ref),
        'code_identical': engine.code_section_sha(wasm) == engine.code_section_sha(ref),
        'all_non_custom_sections_identical': all(sections.values()),
        'sections_equal': sections,
        'code_bytes': code_size(wasm), 'ref_code_bytes': code_size(ref),
        'exports_removed': sorted(set(eb) - set(ea)), 'exports_added': sorted(set(ea) - set(eb)),
        'n_exports': len(ea), 'ref_n_exports': len(eb),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bot', help='bot dir containing src/ (built with the official CLI)')
    ap.add_argument('--out', required=True, help='output wasm (or existing wasm when --bot is omitted)')
    ap.add_argument('--ref', default=str(ROOT / 'references/builds/original.wasm'))
    ap.add_argument('--json', help='write the comparison here')
    a = ap.parse_args(argv)
    if a.bot:
        engine.official_build(ROOT / a.bot, ROOT / a.out)
    res = compare(ROOT / a.out, Path(a.ref))
    text = json.dumps(res, indent=1)
    print(text)
    if a.json:
        engine.write_json(ROOT / a.json, res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
