#!/usr/bin/env python3
"""Generate bot/src/nn_schema.h and python/nfs/schema_gen.py from schemas/observation.json (agent C).

Usage:
    python tools/gen_schema.py           # write both files
    python tools/gen_schema.py --check   # exit 1 if the checked-in files differ from the generator output

Output is deterministic: it depends only on the schema file's parsed content. kObsSchemaHash is FNV-1a-32 of
json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=True).
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'schemas' / 'observation.json'
OUT_H = ROOT / 'bot' / 'src' / 'nn_schema.h'
OUT_PY = ROOT / 'python' / 'nfs' / 'schema_gen.py'

RAW_TYPES = {'i': 'std::int32_t', 'I': 'std::uint32_t', 'f': 'float'}


def fnv1a32(data: bytes) -> int:
    h = 0x811C9DC5
    for b in data:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def canonical_bytes(schema: dict) -> bytes:
    return json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def f32(v: float) -> float:
    return struct.unpack('<f', struct.pack('<f', float(v)))[0]


def f32_literal(v: float) -> str:
    """A decimal that parses to exactly this float32 in both C++ (with suffix f) and numpy.float32."""
    v = f32(v)
    s = '%.9g' % v
    assert f32(float(s)) == v
    if 'e' not in s and '.' not in s and 'inf' not in s and 'nan' not in s:
        s += '.0'
    return s


def ident(name: str) -> str:
    out = re.sub(r'[^0-9A-Za-z_]', '_', name)
    if out[0].isdigit():
        out = '_' + out
    return out


def expand(features: list[dict], prefix: str = '') -> list[dict]:
    """Flatten a feature list: 'expand' -> one feature per label, 'repeat' -> N copies of 'fields'."""
    out = []
    for f in features:
        if 'repeat' in f:
            for k in range(int(f['repeat'])):
                out += expand(f['fields'], f"{prefix}{f['name']}{k}.")
            continue
        base = prefix + f['name']
        scale, lo, hi = float(f['scale']), float(f['clip'][0]), float(f['clip'][1])
        if not (scale > 0 and lo <= hi):
            raise ValueError(f'bad scale/clip for {base}')
        if not (lo <= 0.0 <= hi):
            raise ValueError(f'clip of {base} must contain 0 (absent/padded values encode as 0)')
        labels = f.get('expand')
        names = [f'{base}.{lab}' for lab in labels] if labels else [base]
        for i, n in enumerate(names):
            out.append({'name': n, 'base': base, 'index_in_group': i, 'group_size': len(names), 'scale': scale,
                        'lo': lo, 'hi': hi, 'visibility': f['visibility'], 'units': f['units']})
    return out


def raw_layout(schema: dict) -> dict:
    """Byte layout of RawTurn and its row structs: {struct: [(name, code, count, offset)]}, sizes."""
    rt = schema['raw_turn']
    sizes = {}
    layouts = {}
    for sname in ('objective', 'ally', 'enemy'):
        off, rows = 0, []
        for item in rt[sname]:
            name, code = item[0], item[1]
            count = item[2] if len(item) > 2 else 1
            assert code in RAW_TYPES, (sname, name)
            rows.append((name, code, count, off))
            off += 4 * count
        layouts[sname], sizes[sname] = rows, off
    off, rows = 0, []
    for item in rt['turn']:
        name, code = item[0], item[1]
        count = item[2] if len(item) > 2 else 1
        width = sizes[code] if code in sizes else 4
        rows.append((name, code, count, off))
        off += width * count
    layouts['turn'], sizes['turn'] = rows, off
    return {'layouts': layouts, 'sizes': sizes}


def build(schema: dict) -> dict:
    sg = expand(schema['self_global'])
    ally = expand(schema['ally_row'])
    enemy = expand(schema['enemy_row'])
    for block in (sg, ally, enemy):
        names = [f['name'] for f in block]
        if len(set(names)) != len(names):
            raise ValueError('duplicate feature names')
    obj_rep = [f for f in schema['self_global'] if 'repeat' in f]
    assert len(obj_rep) == 1 and obj_rep[0]['name'] == 'obj'
    obj_fields = expand(obj_rep[0]['fields'])
    K_a, K_e = int(schema['rows']['ally']['K']), int(schema['rows']['enemy']['K'])
    d = {
        'hash': fnv1a32(canonical_bytes(schema)),
        'version': int(schema['version']), 'raw_version': int(schema['raw_version']), 'raw_magic': int(schema['raw_magic']),
        'sg': sg, 'ally': ally, 'enemy': enemy, 'obj_fields': obj_fields, 'obj_slots': int(obj_rep[0]['repeat']),
        'obj_base': next(i for i, f in enumerate(sg) if f['name'].startswith('obj0.')),
        'K_a': K_a, 'K_e': K_e,
        'raw': raw_layout(schema),
        'max_age': int(schema['memory']['max_age_rounds']),
        'small_max_area': int(schema['size_classes']['small_max_area']),
        'medium_max_area': int(schema['size_classes']['medium_max_area']),
        'n_sectors': int(schema['belief']['n_sectors']),
    }
    sgd, ad, ed = len(sg), len(ally), len(enemy)
    d.update(sgd=sgd, ad=ad, ed=ed, ally_off=sgd, ally_mask_off=sgd + K_a * ad, enemy_off=sgd + K_a * ad + K_a,
             enemy_mask_off=sgd + K_a * ad + K_a + K_e * ed, obs_dim=sgd + K_a * ad + K_a + K_e * ed + K_e)
    # Raw rows must match the schema K values.
    turn = {n: (c, cnt) for n, c, cnt, _ in d['raw']['layouts']['turn']}
    assert turn['ally'] == ('ally', K_a) and turn['enemy'] == ('enemy', K_e) and turn['obj'][1] == d['obj_slots']
    return d


def _arr(name: str, vals: list[float]) -> str:
    body = ', '.join(f32_literal(v) + 'f' for v in vals)
    return f'inline constexpr float {name}[{len(vals)}] = {{{body}}};'


def _consts(block: list[dict], strip: str = '') -> list[str]:
    lines, seen = [], set()
    for i, f in enumerate(block):
        n = f['name'][len(strip):] if strip and f['name'].startswith(strip) else f['name']
        lines.append(f'inline constexpr int {ident(n)} = {i};')
        if f['group_size'] > 1 and f['index_in_group'] == 0:
            b = f['base'][len(strip):] if strip and f['base'].startswith(strip) else f['base']
            if b not in seen:
                seen.add(b)
                lines.append(f'inline constexpr int {ident(b)}__base = {i}, {ident(b)}__n = {f["group_size"]};')
    return lines


def render_header(d: dict) -> str:
    L = []
    L.append('// GENERATED by tools/gen_schema.py from schemas/observation.json - do not edit (agent C).')
    L.append('// Observation layout: [self_global | ally rows | ally mask | enemy rows | enemy mask] (CONTRACTS 3.3).')
    L.append('// Pure constants: no cambc.h, no code, no dynamic initialisation.')
    L.append('#pragma once')
    L.append('#include <cstddef>')
    L.append('#include <cstdint>')
    L.append('')
    L.append('namespace nnobs {')
    L.append(f'inline constexpr std::uint32_t kObsSchemaHash = 0x{d["hash"]:08X}u;')
    L.append(f'inline constexpr int kObsVersion = {d["version"]};')
    L.append(f'inline constexpr std::uint32_t kRawVersion = {d["raw_version"]}u;')
    L.append(f'inline constexpr std::uint32_t kRawMagic = 0x{d["raw_magic"]:08X}u;')
    L.append(f'inline constexpr int kSelfGlobalDim = {d["sgd"]};')
    L.append(f'inline constexpr int kAllyRows = {d["K_a"]}, kAllyDim = {d["ad"]};')
    L.append(f'inline constexpr int kEnemyRows = {d["K_e"]}, kEnemyDim = {d["ed"]};')
    L.append('inline constexpr int kObsDim = kSelfGlobalDim + kAllyRows * kAllyDim + kAllyRows + kEnemyRows * kEnemyDim + kEnemyRows;')
    L.append(f'static_assert(kObsDim == {d["obs_dim"]});')
    L.append('inline constexpr int kAllyRowsOff = kSelfGlobalDim, kAllyMaskOff = kAllyRowsOff + kAllyRows * kAllyDim;')
    L.append('inline constexpr int kEnemyRowsOff = kAllyMaskOff + kAllyRows, kEnemyMaskOff = kEnemyRowsOff + kEnemyRows * kEnemyDim;')
    L.append(f'inline constexpr int kObjSlots = {d["obj_slots"]}, kObjDim = {len(d["obj_fields"])}, kObjBase = {d["obj_base"]};')
    L.append(f'inline constexpr int kMemoryMaxAge = {d["max_age"]};')
    L.append(f'inline constexpr int kSmallMaxArea = {d["small_max_area"]}, kMediumMaxArea = {d["medium_max_area"]};')
    L.append(f'inline constexpr int kBeliefSectors = {d["n_sectors"]};')
    L.append('')
    L.append('// Feature indices into the self_global block.')
    L.append('namespace fsg {')
    L += _consts(d['sg'])
    L.append('} // namespace fsg')
    L.append('// Offsets inside one objective slot (slot k starts at kObjBase + k * kObjDim).')
    L.append('namespace fobj {')
    L += _consts(d['obj_fields'])
    L.append('} // namespace fobj')
    L.append('// Offsets inside one ally row.')
    L.append('namespace fa {')
    L += _consts(d['ally'])
    L.append('} // namespace fa')
    L.append('// Offsets inside one enemy row.')
    L.append('namespace fe {')
    L += _consts(d['enemy'])
    L.append('} // namespace fe')
    L.append('')
    L.append('// Normalisation: x = clip(raw * inv_scale, lo, hi); non-finite -> 0.')
    L.append(_arr('kSGInvScale', [1.0 / f['scale'] for f in d['sg']]))
    L.append(_arr('kSGLo', [f['lo'] for f in d['sg']]))
    L.append(_arr('kSGHi', [f['hi'] for f in d['sg']]))
    L.append(_arr('kAllyInvScale', [1.0 / f['scale'] for f in d['ally']]))
    L.append(_arr('kAllyLo', [f['lo'] for f in d['ally']]))
    L.append(_arr('kAllyHi', [f['hi'] for f in d['ally']]))
    L.append(_arr('kEnemyInvScale', [1.0 / f['scale'] for f in d['enemy']]))
    L.append(_arr('kEnemyLo', [f['lo'] for f in d['enemy']]))
    L.append(_arr('kEnemyHi', [f['hi'] for f in d['enemy']]))
    L.append('')
    sz = d['raw']['sizes']
    L.append('// RawTurn byte layout (little-endian, 4-byte fields); nn_obs.h static_asserts its structs against it.')
    L.append(f'inline constexpr std::size_t kRawTurnSize = {sz["turn"]}, kRawObjSize = {sz["objective"]}, '
             f'kRawAllySize = {sz["ally"]}, kRawEnemySize = {sz["enemy"]};')
    checks = []
    for sname, macro_arg in (('turn', 'T'), ('objective', 'O'), ('ally', 'A'), ('enemy', 'E')):
        for name, code, count, off in d['raw']['layouts'][sname]:
            checks.append(f'static_assert(offsetof({macro_arg}, {name}) == {off}, "RawTurn layout: {sname}.{name}");')
    L.append('#define NNOBS_RAW_LAYOUT_CHECK(T, O, A, E) \\')
    L.append('    static_assert(sizeof(T) == kRawTurnSize && sizeof(O) == kRawObjSize && sizeof(A) == kRawAllySize && '
             'sizeof(E) == kRawEnemySize, "RawTurn sizes"); \\')
    for i, c in enumerate(checks):
        L.append('    ' + c + (' \\' if i + 1 < len(checks) else ''))
    L.append('} // namespace nnobs')
    L.append('')
    return '\n'.join(L)


def _pylist(vals: list, fmt=repr, per_line: int = 8) -> str:
    items = [fmt(v) for v in vals]
    lines = []
    for i in range(0, len(items), per_line):
        lines.append('    ' + ', '.join(items[i:i + per_line]) + ',')
    return '[\n' + '\n'.join(lines) + '\n]' if items else '[]'


def render_python(d: dict) -> str:
    L = []
    L.append('"""GENERATED by tools/gen_schema.py from schemas/observation.json - do not edit (agent C).')
    L.append('')
    L.append('Same constants as bot/src/nn_schema.h. Float arrays are exact float32 decimals."""')
    L.append('# flake8: noqa')
    L.append('')
    L.append(f'OBS_SCHEMA_HASH = 0x{d["hash"]:08X}')
    L.append(f'OBS_VERSION = {d["version"]}')
    L.append(f'RAW_VERSION = {d["raw_version"]}')
    L.append(f'RAW_MAGIC = 0x{d["raw_magic"]:08X}')
    L.append(f'SELF_GLOBAL_DIM = {d["sgd"]}')
    L.append(f'ALLY_ROWS = {d["K_a"]}')
    L.append(f'ALLY_DIM = {d["ad"]}')
    L.append(f'ENEMY_ROWS = {d["K_e"]}')
    L.append(f'ENEMY_DIM = {d["ed"]}')
    L.append('OBS_DIM = SELF_GLOBAL_DIM + ALLY_ROWS * ALLY_DIM + ALLY_ROWS + ENEMY_ROWS * ENEMY_DIM + ENEMY_ROWS')
    L.append(f'assert OBS_DIM == {d["obs_dim"]}')
    L.append('ALLY_ROWS_OFF = SELF_GLOBAL_DIM')
    L.append('ALLY_MASK_OFF = ALLY_ROWS_OFF + ALLY_ROWS * ALLY_DIM')
    L.append('ENEMY_ROWS_OFF = ALLY_MASK_OFF + ALLY_ROWS')
    L.append('ENEMY_MASK_OFF = ENEMY_ROWS_OFF + ENEMY_ROWS * ENEMY_DIM')
    L.append(f'OBJ_SLOTS = {d["obj_slots"]}')
    L.append(f'OBJ_DIM = {len(d["obj_fields"])}')
    L.append(f'OBJ_BASE = {d["obj_base"]}')
    L.append(f'MEMORY_MAX_AGE = {d["max_age"]}')
    L.append(f'SMALL_MAX_AREA = {d["small_max_area"]}')
    L.append(f'MEDIUM_MAX_AREA = {d["medium_max_area"]}')
    L.append(f'BELIEF_SECTORS = {d["n_sectors"]}')
    L.append('')
    L.append('SG_NAMES = ' + _pylist([f['name'] for f in d['sg']], per_line=4))
    L.append('OBJ_NAMES = ' + _pylist([f['name'] for f in d['obj_fields']], per_line=4))
    L.append('ALLY_NAMES = ' + _pylist([f['name'] for f in d['ally']], per_line=4))
    L.append('ENEMY_NAMES = ' + _pylist([f['name'] for f in d['enemy']], per_line=4))
    L.append('SG_VISIBILITY = ' + _pylist([f['visibility'] for f in d['sg']], per_line=4))
    L.append('ALLY_VISIBILITY = ' + _pylist([f['visibility'] for f in d['ally']], per_line=4))
    L.append('ENEMY_VISIBILITY = ' + _pylist([f['visibility'] for f in d['enemy']], per_line=4))
    lit = lambda v: f32_literal(v)  # noqa: E731
    L.append('SG_INV_SCALE = ' + _pylist([1.0 / f['scale'] for f in d['sg']], fmt=lit))
    L.append('SG_LO = ' + _pylist([f['lo'] for f in d['sg']], fmt=lit))
    L.append('SG_HI = ' + _pylist([f['hi'] for f in d['sg']], fmt=lit))
    L.append('ALLY_INV_SCALE = ' + _pylist([1.0 / f['scale'] for f in d['ally']], fmt=lit))
    L.append('ALLY_LO = ' + _pylist([f['lo'] for f in d['ally']], fmt=lit))
    L.append('ALLY_HI = ' + _pylist([f['hi'] for f in d['ally']], fmt=lit))
    L.append('ENEMY_INV_SCALE = ' + _pylist([1.0 / f['scale'] for f in d['enemy']], fmt=lit))
    L.append('ENEMY_LO = ' + _pylist([f['lo'] for f in d['enemy']], fmt=lit))
    L.append('ENEMY_HI = ' + _pylist([f['hi'] for f in d['enemy']], fmt=lit))
    L.append('')
    L.append('# RawTurn layout: (name, code, count, byte offset); code is a struct code or a row-struct name.')
    sz = d['raw']['sizes']
    L.append(f'RAW_TURN_SIZE = {sz["turn"]}')
    L.append(f'RAW_OBJ_SIZE = {sz["objective"]}')
    L.append(f'RAW_ALLY_SIZE = {sz["ally"]}')
    L.append(f'RAW_ENEMY_SIZE = {sz["enemy"]}')
    for sname, var in (('objective', 'RAW_OBJ_FIELDS'), ('ally', 'RAW_ALLY_FIELDS'), ('enemy', 'RAW_ENEMY_FIELDS'),
                       ('turn', 'RAW_TURN_FIELDS')):
        L.append(f'{var} = ' + _pylist([tuple(x) for x in d['raw']['layouts'][sname]], per_line=3))
    L.append('')
    return '\n'.join(L)


def load_schema(path: Path = SCHEMA) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def generate(schema: dict | None = None) -> tuple[str, str]:
    d = build(schema if schema is not None else load_schema())
    return render_header(d), render_python(d)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='fail if checked-in outputs differ')
    args = ap.parse_args(argv)
    h, py = generate()
    if args.check:
        bad = [p for p, text in ((OUT_H, h), (OUT_PY, py))
               if not p.exists() or p.read_text(encoding='utf-8') != text]
        for p in bad:
            print(f'out of date: {p.relative_to(ROOT)}')
        return 1 if bad else 0
    for p, text in ((OUT_H, h), (OUT_PY, py)):
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    d = build(load_schema())
    print(f'nn_schema.h / schema_gen.py: hash 0x{d["hash"]:08X} dims sg={d["sgd"]} ally={d["K_a"]}x{d["ad"]} '
          f'enemy={d["K_e"]}x{d["ed"]} obs={d["obs_dim"]} raw={d["raw"]["sizes"]["turn"]} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
