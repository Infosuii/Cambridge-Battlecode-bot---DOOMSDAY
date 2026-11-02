"""Maze-style maps for x1's gates (engine 2.0.0 MapBuilder), set A (PC). Agent 2's unseen maze maps never arrived;
these stand in for the map kind where x1 lost most to v88: long corridors, chokes, dead ends, camps in rooms.

Usage: python tools/maze/gen_maze.py --out maps/x1-maze --count 30 --seed 7 [--prefix pc_maze]

Per map:
  1. Style from an official template T (research/maps/official_maps.json): team size, symmetry, spawn rectangle
     (scaled), camp-group and altar counts per area. Size 40-80 per side.
  2. Maze: a coarse grid of cells with pitch p = corridor width (1-3) + 1 wall, carved by a recursive backtracker
     (a perfect maze), then 10-30% of the remaining inner walls between cells reopened (loops), and 0-2 open rooms.
     Built on the whole map, then the authored half is kept (the builder mirrors it).
  3. Camps: official groups (exact member types and offsets; 70% from T, 30% from the pool) each get a room carved
     around them (bounding box + 1); altars get a 3x3 clearing. Spawn area + 2 is cleared.
  4. Bushes: 2-6% of corridor tiles; holes: 0-8% of wall tiles become holes (block walking, not sight).
  5. Repair: on the mirrored full map, walls between the spawn's region and any unreached open tile are knocked
     through (with their mirror) until every open tile, camp and altar is reachable from both spawns.
  6. The engine verifies integrity and the game must load the map.
Writes <prefix>_NN.map26a and <prefix>_meta.json (per-map parameters, seed).
"""
import argparse
import json
import math
import os
import random
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mapgen'))
from gen_maps import group_templates, in_half, mirror  # noqa: E402
from mapbuilder import MapBuilder, loads_in_game  # noqa: E402
from mapio import new_engine  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CAMP_KIND = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def maze_walls(w, h, rng, cw, loops, rooms):
    """Set of wall tiles of a maze over the whole w x h map."""
    p = cw + 1
    nx, ny = max(2, (w - 1) // p), max(2, (h - 1) // p)
    walls = {(x, y) for x in range(w) for y in range(h)}

    def carve_cell(i, j):
        x0, y0 = 1 + i * p, 1 + j * p
        for x in range(x0, min(w, x0 + cw)):
            for y in range(y0, min(h, y0 + cw)):
                walls.discard((x, y))

    def carve_link(i, j, i2, j2):
        x0, y0 = 1 + min(i, i2) * p, 1 + min(j, j2) * p
        if i != i2:  # horizontal neighbours: open the wall column between them
            for y in range(y0, min(h, y0 + cw)):
                walls.discard((x0 + cw, y))
        else:
            for x in range(x0, min(w, x0 + cw)):
                walls.discard((x, y0 + cw))

    seen = {(0, 0)}
    stack = [(0, 0)]
    carve_cell(0, 0)
    links = set()
    while stack:
        i, j = stack[-1]
        nbrs = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= i + di < nx and 0 <= j + dj < ny and (i + di, j + dj) not in seen]
        if not nbrs:
            stack.pop()
            continue
        i2, j2 = rng.choice(nbrs)
        seen.add((i2, j2))
        carve_cell(i2, j2)
        carve_link(i, j, i2, j2)
        links.add(frozenset(((i, j), (i2, j2))))
        stack.append((i2, j2))
    # Loops: reopen a share of the walls the perfect maze kept.
    closed = [((i, j), (i + di, j + dj)) for i in range(nx) for j in range(ny) for di, dj in ((1, 0), (0, 1))
              if i + di < nx and j + dj < ny and frozenset(((i, j), (i + di, j + dj))) not in links]
    rng.shuffle(closed)
    for a, b in closed[:round(len(closed) * loops)]:
        carve_link(*a, *b)
    # Open rooms.
    for _ in range(rooms):
        rw, rh = rng.randint(1, 3) * p + cw, rng.randint(1, 3) * p + cw
        x0, y0 = rng.randrange(1, max(2, w - rw - 1)), rng.randrange(1, max(2, h - rh - 1))
        for x in range(x0, min(w - 1, x0 + rw)):
            for y in range(y0, min(h - 1, y0 + rh)):
                walls.discard((x, y))
    return walls


def build_one(eng, rng, official, names, templates):
    tname = rng.choice(names)
    T = official[tname]
    w = h = rng.randint(40, 80)
    if rng.random() < 0.4:
        h = max(40, min(80, round(w * rng.uniform(0.75, 1.25))))
    sym = T['symmetry'] if (T['symmetry'] == 'rotational' or w == h) else 'rotational'
    if w != h and sym != 'rotational':
        sym = 'rotational'
    team = T['team']
    area_ratio = (w * h) / (T['w'] * T['h'])
    cw = rng.choice([1, 1, 2, 2, 3])
    loops = rng.uniform(0.10, 0.30)
    walls = maze_walls(w, h, rng, cw, loops, rng.randint(0, 2))
    walls = {c for c in walls if in_half(sym, w, h, *c)}

    def full(cells):
        out = set(cells)
        out |= {mirror(sym, w, h, *c) for c in cells}
        return out

    # Spawn: T's rectangle, scaled, moved into the authored half if needed (as tools/mapgen/gen_maps.py).
    scale = w / T['w']
    sx0, sy0, sx1, sy1 = T['spawn']
    sw, sh = max(1, round((sx1 - sx0 + 1) * scale)), max(1, round((sy1 - sy0 + 1) * scale))
    while sw * sh < team:
        sw += 1
    sw, sh = min(sw, 6), min(sh, 6)
    px = min(w - sw, max(0, round(sx0 / T['w'] * w)))
    py = min(h - sh, max(0, round(sy0 / T['h'] * h)))

    def rect(qx, qy):
        return [(x, y) for x in range(qx, qx + sw) for y in range(qy, qy + sh)]

    if any(not in_half(sym, w, h, *c) for c in rect(px, py)):
        opts = [(abs(qx - px) + abs(qy - py), qx, qy) for qx in range(0, w - sw + 1) for qy in range(0, h - sh + 1)
                if all(in_half(sym, w, h, *c) for c in rect(qx, qy))]
        if not opts:
            return None, 'spawn does not fit'
        _, px, py = min(opts)
    spawn = rect(px, py)
    occupied = set()
    for (x, y) in spawn:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                walls.discard((x + dx, y + dy))
                occupied.add((x + dx, y + dy))

    def free(x, y):
        return 0 <= x < w and 0 <= y < h and in_half(sym, w, h, x, y) and (x, y) not in occupied

    # Camp groups in carved rooms.
    n_groups = max(2, round(len(T['groups']) * area_ratio * rng.uniform(0.85, 1.15)))
    own = [t for t in templates if t['from'] == tname]
    placed = []
    for _ in range(n_groups):
        g = rng.choice(own) if own and rng.random() < 0.7 else rng.choice(templates)
        for _try in range(300):
            ax, ay = rng.randrange(w), rng.randrange(h)
            cells = [(t, ax + dx, ay + dy) for (t, dx, dy) in g['members']]
            xs, ys = [c[1] for c in cells], [c[2] for c in cells]
            box = [(x, y) for x in range(min(xs) - 1, max(xs) + 2) for y in range(min(ys) - 1, max(ys) + 2)]
            if not all(free(x, y) for (x, y) in box):
                continue
            if min(math.hypot(x - px, y - py) for (_, x, y) in cells) < 8:
                continue
            for c in box:
                walls.discard(c)
                occupied.add(c)
            placed.append({'from': g['from'], 'cells': cells})
            break
    if len(placed) < 0.8 * n_groups:
        return None, 'too few camp groups fitted'
    n_alt = max(1, round(len(T['altars']) * rng.uniform(0.8, 1.25) / 2))
    altars = []
    for _ in range(n_alt):
        for _try in range(200):
            x, y = rng.randrange(1, w - 1), rng.randrange(1, h - 1)
            box = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            if all(free(*c) for c in box) and math.hypot(x - px, y - py) >= 6:
                for c in box:
                    walls.discard(c)
                    occupied.add(c)
                altars.append((x, y))
                break

    # Repair connectivity on the full mirrored map: knock through walls until every open tile is reachable.
    spawn_full = full(spawn)
    knocked = 0
    while True:
        blocked = full(walls)
        seen = set(spawn_full)
        q = deque(spawn_full)
        while q:
            x, y = q.popleft()
            for dx, dy in N8:
                c = (x + dx, y + dy)
                if 0 <= c[0] < w and 0 <= c[1] < h and c not in seen and c not in blocked:
                    seen.add(c)
                    q.append(c)
        open_all = {(x, y) for x in range(w) for y in range(h)} - blocked
        lost = open_all - seen
        if not lost:
            break
        # A wall with a reached neighbour and an unreached open neighbour; else the wall nearest an unreached tile.
        cand = [c for c in blocked if any((c[0] + dx, c[1] + dy) in seen for dx, dy in N8)
                and any((c[0] + dx, c[1] + dy) in lost for dx, dy in N8)]
        if not cand:
            t = rng.choice(sorted(lost))
            cand = [min((c for c in blocked if any((c[0] + dx, c[1] + dy) in seen for dx, dy in N8)),
                        key=lambda c: abs(c[0] - t[0]) + abs(c[1] - t[1]))]
        c = rng.choice(cand)
        a = c if in_half(sym, w, h, *c) else mirror(sym, w, h, *c)
        walls.discard(a)
        knocked += 1
        if knocked > 4000:
            return None, 'repair did not converge'
    # Bushes in corridors, holes from walls (kept off the spawn clearing and camp rooms).
    corridor = [c for c in open_all if in_half(sym, w, h, *c) and c not in occupied]
    bush = set(rng.sample(corridor, round(len(corridor) * rng.uniform(0.02, 0.06))))
    hole_share = rng.uniform(0.0, 0.08)
    holes = {c for c in walls if rng.random() < hole_share and 0 < c[0] < w - 1 and 0 < c[1] < h - 1}
    walls -= holes

    mb = MapBuilder(eng, w, h, sym)
    try:
        mb.team_size(team)
        mb.spawn(px, py, px + sw - 1, py + sh - 1)
        for (x, y) in walls:
            mb.wall(x, y)
        for (x, y) in holes:
            mb.hole(x, y)
        for (x, y) in bush:
            mb.bush(x, y)
        for (x, y) in altars:
            mb.altar(x, y)
        for g in placed:
            for (t, x, y) in g['cells']:
                mb.camp(CAMP_KIND[t], x, y)
        mb.verify()
        data = mb.encode()
    except RuntimeError as e:
        return None, f'builder: {e}'
    finally:
        mb.destroy()
    if not loads_in_game(eng, data):
        return None, 'game does not load'
    meta = {'template': tname, 'w': w, 'h': h, 'symmetry': sym, 'team': team, 'corridor': cw, 'loops': round(loops, 3),
            'groups': len(placed), 'altars_half': len(altars), 'knocked': knocked, 'bushes_half': len(bush),
            'holes_half': len(holes), 'walls_half': len(walls)}
    return data, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--count', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--prefix', default='pc_maze')
    ap.add_argument('--official', default=os.path.join(ROOT, 'research', 'maps', 'official_maps.json'))
    a = ap.parse_args()
    official = {k: v for k, v in json.load(open(a.official)).items() if not k.startswith('adgato-gemcombat')}
    names = sorted(official)
    templates = group_templates(official)
    rng = random.Random(a.seed)
    eng = new_engine()
    os.makedirs(a.out, exist_ok=True)
    made, tries, reasons, metas = 0, 0, {}, {}
    while made < a.count and tries < a.count * 40:
        tries += 1
        data, meta = build_one(eng, rng, official, names, templates)
        if data is None:
            reasons[meta] = reasons.get(meta, 0) + 1
            continue
        name = f'{a.prefix}_{made:02d}'
        open(os.path.join(a.out, name + '.map26a'), 'wb').write(data)
        metas[name] = meta
        made += 1
    json.dump({'seed': a.seed, 'made': made, 'tries': tries, 'rejections': reasons, 'maps': metas},
              open(os.path.join(a.out, f'{a.prefix}_meta.json'), 'w'), indent=1)
    print(f'made {made} in {tries} tries; rejections {reasons}')


if __name__ == '__main__':
    main()
