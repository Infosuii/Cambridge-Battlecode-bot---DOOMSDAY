"""Read a .map26a file into plain Python through the engine's own MapBuilder (engine 2.0.0 map editor wasm).

Usage: python tools/mapgen/mapio.py <map.map26a> [...]   (prints a summary per map)

The builder stores the authored half of a symmetric map: camps/groups are the authored copies, and the game mirrors
them (`full_*` helpers apply the symmetry). Struct layouts were read off known maps (see tools/mapgen/README.md):
  metadata {u32 width, u32 height, ...}; camp {u32 type, u32 x, u32 y}; group {u32 gems, u32 gold, u32 respawn,
  u32 members}; spawn area {i32 x0, y0, x1, y1} for team A. Camp types: 0 wolf, 1 elk, 2 gem cluster,
  3 gold cluster, 4 monolith, 5 golem. Symmetry: 0 horizontal, 1 vertical, 2 rotational.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapbuilder import Engine, MapBuilder  # noqa: E402

CAMP_NAMES = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']
SYM_NAMES = ['horizontal', 'vertical', 'rotational']


def engine_wasm():
    pat = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'cambc', 'assets', '*', 'mapeditor', 'assets', 'v2_0_0-*.wasm')
    hits = glob.glob(pat)
    if not hits:
        raise FileNotFoundError('engine 2.0.0 map editor wasm not found (run any cambc 4.0.0 build or `cambc mapeditor` once)')
    return hits[0]


def new_engine():
    os.environ.setdefault('BC_ENGINE_WASM', engine_wasm())
    return Engine()


def _u32s(e, addr, n):
    raw = e.mem.read(e.store, addr, addr + 4 * n)
    return [int.from_bytes(raw[4 * i:4 * i + 4], 'little', signed=True) for i in range(n)]


def read_map(e, data):
    mb = MapBuilder(e, file_bytes=data)
    h, o = mb.h, e.out

    def get(name, *args, n=1):
        e.check(e.call(name, h, *args, o))
        return _u32s(e, o, n)

    w, hh = get('MapBuilder_GetBitboardMetadata', n=2)
    sym = get('MapBuilder_GetSymmetry')[0]
    team = get('MapBuilder_GetNumChampsPerTeam')[0]
    spawn = get('MapBuilder_GetTeamASpawnArea', n=4)

    def cells(kind):
        out = []
        for x in range(w):
            for y in range(hh):
                e.check(e.call(f'MapBuilder_Get{kind}', h, x, y, o))
                if e.mem.read(e.store, o, o + 1)[0]:
                    out.append((x, y))
        return out

    walls, bushes, holes, altars = cells('Wall'), cells('Bush'), cells('Hole'), cells('Altar')
    camps = []
    for i in range(get('MapBuilder_GetNumCamps')[0]):
        e.check(e.call('MapBuilder_GetCampHandle', h, i, o))
        ch = e.u64(o)
        e.check(e.call('MapBuilder_GetCamp', h, ch, o))
        t, x, y = _u32s(e, o, 3)
        camps.append({'handle': ch, 'type': t, 'x': x, 'y': y})
    by_handle = {c['handle']: c for c in camps}
    groups = []
    for g in range(get('MapBuilder_GetNumCampGroups')[0]):
        e.check(e.call('MapBuilder_GetCampGroupHandle', h, g, o))
        gh = e.u64(o)
        e.check(e.call('MapBuilder_GetCampGroup', h, gh, o))
        gems, gold, respawn, members = _u32s(e, o, 4)
        mem = []
        for k in range(members):
            e.check(e.call('MapBuilder_GetCampGroupCamp', h, gh, k, o))
            c = by_handle.get(e.u64(o))
            if c is not None:
                mem.append({'type': c['type'], 'x': c['x'], 'y': c['y']})
        groups.append({'gems': gems, 'gold': gold, 'respawn': respawn, 'camps': mem})
    mb.destroy()
    for c in camps:
        del c['handle']
    return {'w': w, 'h': hh, 'symmetry': SYM_NAMES[sym] if 0 <= sym < 3 else sym, 'team': team, 'spawn': spawn,
            'walls': walls, 'bushes': bushes, 'holes': holes, 'altars': altars, 'camps': camps, 'groups': groups}


def summary(m):
    kinds = {}
    for c in m['camps']:
        n = CAMP_NAMES[c['type']] if 0 <= c['type'] < len(CAMP_NAMES) else str(c['type'])
        kinds[n] = kinds.get(n, 0) + 1
    return (f"{m['w']}x{m['h']} {m['symmetry']} team{m['team']} walls{len(m['walls'])} bush{len(m['bushes'])} "
            f"holes{len(m['holes'])} altars{len(m['altars'])} groups{len(m['groups'])} camps{kinds} "
            f"gems{sum(g['gems'] for g in m['groups'])} gold{sum(g['gold'] for g in m['groups'])}")


if __name__ == '__main__':
    e = new_engine()
    for f in sys.argv[1:]:
        print(os.path.basename(f), summary(read_map(e, open(f, 'rb').read())))
