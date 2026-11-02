"""Read every official map through the engine and write their structure to research/maps/official_maps.json.

Usage: python tools/mapgen/extract_official.py [map dir] [out json]
Also reports whether terrain cells are stored for the whole map or only the authored half (mirror closure).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapio import new_engine, read_map  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def mirror(sym, w, h, x, y):
    if sym == 'horizontal':
        return w - 1 - x, y
    if sym == 'vertical':
        return x, h - 1 - y
    return w - 1 - x, h - 1 - y


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'maps', 'local-benchmarks')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'research', 'maps', 'official_maps.json')
    e = new_engine()
    maps = {}
    closure = {}
    for f in sorted(os.listdir(src)):
        if not f.endswith('.map26a'):
            continue
        m = read_map(e, open(os.path.join(src, f), 'rb').read())
        name = f[:-len('.map26a')]
        maps[name] = m
        for kind in ('walls', 'bushes', 'holes', 'altars'):
            s = set(map(tuple, m[kind]))
            if s:
                closed = sum(1 for (x, y) in s if mirror(m['symmetry'], m['w'], m['h'], x, y) in s) / len(s)
                closure.setdefault(kind, []).append(closed)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(maps, open(out, 'w'), separators=(',', ':'))
    print(f'{len(maps)} maps -> {out}')
    for k, v in closure.items():
        print(f'{k}: mirror-closed share mean {sum(v) / len(v):.3f} min {min(v):.3f} over {len(v)} maps')


if __name__ == '__main__':
    main()
