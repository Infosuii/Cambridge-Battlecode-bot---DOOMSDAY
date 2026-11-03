"""Render the same x3mf fit tables with a bounded set of strategy deltas."""
import argparse
import json
from pathlib import Path
import re
import shutil

IDX = (0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 22, 23, 43, 45, 46, 55, 57, 60, 61, 64, 65, 50, 49)
ARMS = {
    0: {},
    1: {4: -.8, 9: .25},                          # shorter loads, less waiting
    2: {0: -.45, 1: .40, 2: .25, 5: -.50},       # retreat before a losing hunt
    3: {8: -.60, 10: .25, 11: -.15},             # direct gem race
    4: {8: .60, 12: -.40, 10: .10},              # early shop tempo
    5: {9: .80, 10: .30, 11: .25},               # camp throughput with nearby help
    6: {12: .80, 8: -.20},                        # fewer small shopping trips
    7: {0: -.20, 2: .40, 11: .65},               # farm beside allies against packs
    8: {0: .55, 22: .20, 23: -.20, 4: -.35},     # commit melee, protect carriers
    9: {4: .75, 11: .15},                         # amortise long bank trips
}
KEY = r'(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)u'


def numbers(raw):
    tokens = [x.strip() for x in raw.split(',') if x.strip()]
    assert len(tokens) in (0, 24)
    return tokens


def deltas(tokens, arm):
    if arm == 0 or not tokens:
        return ', '.join(tokens)
    move = ARMS[arm]
    out = []
    for idx, tok in zip(IDX, tokens):
        if idx in move:
            out.append(f'{float(tok.removesuffix("f"))+move[idx]:.5f}f')
        else:
            out.append(tok)
    return ', '.join(out)


def replace_table(src, declaration, include, body_builder, eol):
    a = src.index(declaration)
    i = src.index('{', a)
    j = i
    depth = 0
    while j < len(src):
        depth += src[j] == '{'
        depth -= src[j] == '}'
        if depth == 0:
            break
        j += 1
    assert src[j:j+2] == '};'
    head, body = src[a:i+1], src[i+1:j]
    render = body_builder(src[:a], body)
    wrapper = f'#include "gx_config.h"\n#if GX_DATA_FIT\n{head}\n#include "{include}"\n}};\n#else\n{src[a:j+2]}\n#endif'
    return (src[:a]+wrapper+src[j+2:]).replace('\n', eol), render


def make(src, dest, arm_by_key):
    dest.mkdir(parents=True, exist_ok=False)
    shutil.copytree(src, dest/'src')
    out = dest/'src'
    (out/'gx_config.h').write_text('#pragma once\n#ifndef GX_DATA_FIT\n#define GX_DATA_FIT 0\n#endif\n')
    seen = set()

    def ladder(prefix, body):
        fp = [tuple(map(int, x)) for x in re.findall(r'\{'+KEY+r'\}', prefix)]
        rows = re.findall(r'\{([^{}]+)\}', body)
        assert len(fp) == len(rows) == 70
        lines = []
        for key, row in zip(fp, rows):
            assert key not in seen
            seen.add(key)
            lines.append('    {'+deltas(numbers(row), arm_by_key(key))+'},')
        return '\n'.join(lines)+'\n'

    def mapfit(prefix, body):
        lines = []
        rows = re.findall(r'\{'+KEY+r'\s*,\s*\{([^{}]*)\}\s*\}', body)
        assert len(rows) == 14
        for w,h,n,g,row in rows:
            key = tuple(map(int,(w,h,n,g)))
            assert key not in seen
            seen.add(key)
            lines.append(f'    {{{w}, {h}, {n}, {g}u, {{'+deltas(numbers(row),arm_by_key(key))+'}},')
        return '\n'.join(lines)+'\n'

    for filename, declaration, inc, renderer in (
        ('ladfit.h','inline constexpr float kFit[70][24]', 'gx_ladfit_rows.inc', ladder),
        ('x1_mapfit.h','inline constexpr Row kRows[]', 'gx_mapfit_rows.inc', mapfit)):
        p = out / filename
        raw = p.read_bytes()
        text = raw.decode().replace('\r\n','\n')
        changed, data = replace_table(text, declaration, inc, renderer, '\r\n' if b'\r\n' in raw else '\n')
        p.write_bytes(changed.encode())
        (out/inc).write_text(data)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source', type=Path, help='stock x3 src directory')
    cli.add_argument('output', type=Path, help='fresh bot directory')
    cli.add_argument('--arm', type=int, default=0, choices=sorted(ARMS))
    cli.add_argument('--table', type=Path, help='selected name-to-arm JSON')
    cli.add_argument('--keys', type=Path, help='verified map and side keys')
    args = cli.parse_args()
    if bool(args.table) != bool(args.keys):
        cli.error('Table and runtime keys must be supplied together.')
    table = {}
    if args.table:
        selected = json.loads(args.table.read_text())['selected']
        keys = json.loads(args.keys.read_text())
        for name, arm in selected.items():
            fp = tuple(keys[name+'-A'][:4])
            assert fp == tuple(keys[name+'-B'][:4]) and arm in ARMS
            assert fp not in table
            table[fp] = arm
    make(args.source, args.output, lambda key: table.get(key, args.arm))


if __name__ == '__main__':
    main()
