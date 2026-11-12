"""Maze-style maps for x1's gates, set B (5060, comms/x1 J015), engine 2.0.0 MapBuilder. Independent of set A
(tools/maze/gen_maze.py on build/z-plan, recursive backtracker): a different maze algorithm, room-first layout and an
optional cave pass, so the two sets do not share one generator's bias.

Usage: python tools/maze/gen_maze_g5060.py --out DIR --count 40 --seed 5060 [--prefix g5060_maze]

Per map:
  1. Style: an official template T (research/maps/official_maps.json, adgato maps excluded) gives the team size and
     spawn rectangle (scaled). Size 40-80 per side; symmetry rotational, or reflective (horizontal / vertical) on
     square maps.
  2. Rooms first: 2-5 rectangles of 2-4 x 2-4 maze cells, fully open, each pre-joined as one node.
  3. Maze: randomized Kruskal over the cell grid (pitch = corridor width 1-3 + 1 wall) with the rooms as nodes, which
     gives many short dead ends (a backtracker gives long winding corridors); then 10-30% of the remaining closed
     cell walls are reopened (loops).
  4. Caves (about one map in three, corridors 2-3 wide only): corridor tiles touching a wall become wall with
     probability 0.2 outside rooms, giving ragged corridors with 1-wide chokes.
  5. Camps: official groups (exact member types and offsets) placed in rooms (70%) or at maze junctions (cells with
     3+ open links); their bounding box + 1 is cleared. Count per authored half = area / 2 x the official median
     group density x U(0.7, 1.5), capped at the official maximum density (pc/msgs/0009). Altars: 1-3 per half in
     rooms or junctions, 3x3 clearing. Spawn area + 2 cleared.
  6. Repair on the mirrored full map: walls between the spawn's region and unreached open tiles are knocked through
     (with their mirror) until every open tile, camp and altar is reachable from both spawns (8-neighbour moves).
  7. Bushes 1-4% of corridor tiles, holes 0-5% of wall tiles; the engine verifies integrity and the game must load.
Writes PREFIX_NN.map26a and PREFIX_meta.json (per-map parameters, seed). Screening by self-play is a separate step
(tools/maze/screen_g5060.py).
"""
import argparse
import json
import math
import os
import random
import statistics
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


class DSU:
    def __init__(self, n): self.p = list(range(n))
    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]; a = self.p[a]
        return a
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b: return False
        self.p[a] = b; return True


def kruskal_maze(w, h, rng, cw, loops, n_rooms):
    """Wall tiles of the whole w x h map, plus room tiles and junction-cell tiles (for camp placement)."""
    p = cw + 1
    nx, ny = max(3, (w - 1) // p), max(3, (h - 1) // p)
    walls = {(x, y) for x in range(w) for y in range(h)}
    cell_tiles = lambda i, j: [(x, y) for x in range(1 + i * p, min(w - 1, 1 + i * p + cw))
                               for y in range(1 + j * p, min(h - 1, 1 + j * p + cw))]

    def link_tiles(a, b):
        (i, j), (i2, j2) = a, b
        x0, y0 = 1 + min(i, i2) * p, 1 + min(j, j2) * p
        if i != i2: return [(x0 + cw, y) for y in range(y0, min(h - 1, y0 + cw))]
        return [(x, y0 + cw) for x in range(x0, min(w - 1, x0 + cw))]

    for i in range(nx):
        for j in range(ny):
            walls.difference_update(cell_tiles(i, j))
    idx = lambda c: c[0] * ny + c[1]
    dsu, links, room_tiles = DSU(nx * ny), set(), set()
    rooms = []
    for _ in range(n_rooms):
        for _try in range(30):
            rw, rh = rng.randint(2, 4), rng.randint(2, 4)
            if rw >= nx or rh >= ny: break
            i0, j0 = rng.randrange(0, nx - rw + 1), rng.randrange(0, ny - rh + 1)
            box = {(i, j) for i in range(i0, i0 + rw) for j in range(j0, j0 + rh)}
            if any(c in r or any(abs(c[0] - d[0]) + abs(c[1] - d[1]) <= 1 for d in r) for r in rooms for c in box):
                continue
            rooms.append(box)
            for c in box:
                for d in ((c[0] + 1, c[1]), (c[0], c[1] + 1)):
                    if d in box:
                        dsu.union(idx(c), idx(d)); links.add(frozenset((c, d)))
                        walls.difference_update(link_tiles(c, d))
            x0, y0 = 1 + i0 * p, 1 + j0 * p
            for x in range(x0, min(w - 1, x0 + rw * p - 1)):  # also the wall crossings inside the room
                for y in range(y0, min(h - 1, y0 + rh * p - 1)):
                    walls.discard((x, y)); room_tiles.add((x, y))
            break
    edges = [((i, j), (i + di, j + dj)) for i in range(nx) for j in range(ny) for di, dj in ((1, 0), (0, 1))
             if i + di < nx and j + dj < ny]
    rng.shuffle(edges)
    closed = []
    for a, b in edges:
        if frozenset((a, b)) in links: continue
        if dsu.union(idx(a), idx(b)):
            links.add(frozenset((a, b))); walls.difference_update(link_tiles(a, b))
        else:
            closed.append((a, b))
    for a, b in closed[:round(len(closed) * loops)]:
        links.add(frozenset((a, b))); walls.difference_update(link_tiles(a, b))
    degree = {}
    for l in links:
        for c in l: degree[c] = degree.get(c, 0) + 1
    in_room = set().union(*rooms) if rooms else set()
    junction_tiles = {t for c, d in degree.items() if d >= 3 and c not in in_room for t in cell_tiles(*c)}
    return walls, room_tiles, junction_tiles, len(rooms)


def cave_pass(walls, w, h, rng, keep):
    """Ragged, uneven corridors: corridor tiles that touch a wall (4-neighbour) become wall with probability 0.2,
    except in rooms (keep). Narrows 2-3 wide corridors to chokes in places; the repair step restores reachability."""
    added = set()
    for x in range(1, w - 1):
        for y in range(1, h - 1):
            if (x, y) in walls or (x, y) in keep: continue
            if any((x + dx, y + dy) in walls for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) and rng.random() < 0.2:
                added.add((x, y))
    return walls | added


def build_one(eng, rng, official, names, templates, dens_med, dens_max):
    tname = rng.choice(names)
    T = official[tname]
    w = rng.randint(40, 80)
    h = w if rng.random() < 0.6 else max(40, min(80, round(w * rng.uniform(0.75, 1.25))))
    sym = rng.choice(['rotational', 'rotational', 'horizontal', 'vertical']) if w == h else 'rotational'
    team = T['team']
    cw = rng.choice([1, 2, 2, 3])
    loops = rng.uniform(0.10, 0.30)
    walls, room_tiles, junction_tiles, n_rooms = kruskal_maze(w, h, rng, cw, loops, rng.randint(2, 5))
    caves = cw >= 2 and rng.random() < 0.45  # about one map in three overall
    if caves:
        walls = cave_pass(walls, w, h, rng, room_tiles)
    walls = {c for c in walls if in_half(sym, w, h, *c)}
    full = lambda cells: set(cells) | {mirror(sym, w, h, *c) for c in cells}

    scale = w / T['w']
    sx0, sy0, sx1, sy1 = T['spawn']
    sw, sh = max(1, round((sx1 - sx0 + 1) * scale)), max(1, round((sy1 - sy0 + 1) * scale))
    while sw * sh < team: sw += 1
    sw, sh = min(sw, 6), min(sh, 6)
    px = min(w - sw, max(0, round(sx0 / T['w'] * w)))
    py = min(h - sh, max(0, round(sy0 / T['h'] * h)))
    rect = lambda qx, qy: [(x, y) for x in range(qx, qx + sw) for y in range(qy, qy + sh)]
    if any(not in_half(sym, w, h, *c) for c in rect(px, py)):
        opts = [(abs(qx - px) + abs(qy - py), qx, qy) for qx in range(0, w - sw + 1) for qy in range(0, h - sh + 1)
                if all(in_half(sym, w, h, *c) for c in rect(qx, qy))]
        if not opts: return None, 'spawn does not fit'
        _, px, py = min(opts)
    spawn = rect(px, py)
    occupied = set()
    for (x, y) in spawn:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                walls.discard((x + dx, y + dy)); occupied.add((x + dx, y + dy))
    free = lambda x, y: 0 <= x < w and 0 <= y < h and in_half(sym, w, h, x, y) and (x, y) not in occupied
    anchors_room = [c for c in room_tiles if in_half(sym, w, h, *c)]
    anchors_junc = [c for c in junction_tiles if in_half(sym, w, h, *c)]

    density = min(dens_max, dens_med * rng.uniform(0.7, 1.5))
    n_groups = max(2, round(w * h / 2 * density))
    own = [t for t in templates if t['from'] == tname]
    placed = []
    for _ in range(n_groups):
        g = rng.choice(own) if own and rng.random() < 0.5 else rng.choice(templates)
        pool = anchors_room if (anchors_room and rng.random() < 0.7) or not anchors_junc else anchors_junc
        for _try in range(300):
            ax, ay = rng.choice(pool) if pool and _try < 200 else (rng.randrange(w), rng.randrange(h))
            cells = [(t, ax + dx, ay + dy) for (t, dx, dy) in g['members']]
            xs, ys = [c[1] for c in cells], [c[2] for c in cells]
            box = [(x, y) for x in range(min(xs) - 1, max(xs) + 2) for y in range(min(ys) - 1, max(ys) + 2)]
            if not all(free(x, y) for (x, y) in box): continue
            if min(math.hypot(x - px, y - py) for (_, x, y) in cells) < 8: continue
            for c in box: walls.discard(c); occupied.add(c)
            placed.append({'from': g['from'], 'cells': cells})
            break
    if len(placed) < 0.8 * n_groups: return None, 'too few camp groups fitted'
    altars = []
    for _ in range(rng.randint(1, 3)):
        pool = anchors_room + anchors_junc
        for _try in range(200):
            x, y = rng.choice(pool) if pool and _try < 150 else (rng.randrange(1, w - 1), rng.randrange(1, h - 1))
            box = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            if all(free(*c) for c in box) and math.hypot(x - px, y - py) >= 6:
                for c in box: walls.discard(c); occupied.add(c)
                altars.append((x, y)); break
    if not altars: return None, 'no altar fitted'

    spawn_full = full(spawn)
    knocked = 0
    while True:
        blocked = full(walls)
        seen, q = set(spawn_full), deque(spawn_full)
        while q:
            x, y = q.popleft()
            for dx, dy in N8:
                c = (x + dx, y + dy)
                if 0 <= c[0] < w and 0 <= c[1] < h and c not in seen and c not in blocked:
                    seen.add(c); q.append(c)
        open_all = {(x, y) for x in range(w) for y in range(h)} - blocked
        lost = open_all - seen
        if not lost: break
        cand = [c for c in blocked if any((c[0] + dx, c[1] + dy) in seen for dx, dy in N8)
                and any((c[0] + dx, c[1] + dy) in lost for dx, dy in N8)]
        if not cand:
            t = rng.choice(sorted(lost))
            cand = [min((c for c in blocked if any((c[0] + dx, c[1] + dy) in seen for dx, dy in N8)),
                        key=lambda c: abs(c[0] - t[0]) + abs(c[1] - t[1]))]
        c = rng.choice(cand)
        walls.discard(c if in_half(sym, w, h, *c) else mirror(sym, w, h, *c))
        knocked += 1
        if knocked > 4000: return None, 'repair did not converge'
    corridor = [c for c in open_all if in_half(sym, w, h, *c) and c not in occupied]
    bush = set(rng.sample(corridor, round(len(corridor) * rng.uniform(0.01, 0.04))))
    hole_share = rng.uniform(0.0, 0.05)
    holes = {c for c in walls if rng.random() < hole_share and 0 < c[0] < w - 1 and 0 < c[1] < h - 1}
    walls -= holes

    mb = MapBuilder(eng, w, h, sym)
    try:
        mb.team_size(team)
        mb.spawn(px, py, px + sw - 1, py + sh - 1)
        for (x, y) in walls: mb.wall(x, y)
        for (x, y) in holes: mb.hole(x, y)
        for (x, y) in bush: mb.bush(x, y)
        for (x, y) in altars: mb.altar(x, y)
        for g in placed:
            for (t, x, y) in g['cells']: mb.camp(CAMP_KIND[t], x, y)
        mb.verify()
        data = mb.encode()
    except RuntimeError as e:
        return None, f'builder: {e}'
    finally:
        mb.destroy()
    if not loads_in_game(eng, data): return None, 'game does not load'
    meta = {'template': tname, 'w': w, 'h': h, 'symmetry': sym, 'team': team, 'corridor': cw, 'loops': round(loops, 3),
            'rooms': n_rooms, 'caves': caves, 'groups_half': len(placed), 'group_density_full': round(2 * len(placed) / (w * h), 5),
            'altars_half': len(altars), 'knocked': knocked, 'bushes_half': len(bush), 'holes_half': len(holes),
            'walls_half': len(walls)}
    return data, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True); ap.add_argument('--count', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True); ap.add_argument('--prefix', default='g5060_maze')
    ap.add_argument('--official', default=os.path.join(ROOT, 'research', 'maps', 'official_maps.json'))
    a = ap.parse_args()
    official = {k: v for k, v in json.load(open(a.official)).items() if not k.startswith('adgato-gemcombat')}
    dens = [len(v['groups']) / (v['w'] * v['h']) for v in official.values()]
    dens_med, dens_max = statistics.median(dens), max(dens)
    names, templates = sorted(official), group_templates(official)
    rng, eng = random.Random(a.seed), new_engine()
    os.makedirs(a.out, exist_ok=True)
    made, tries, reasons, metas = 0, 0, {}, {}
    while made < a.count and tries < a.count * 40:
        tries += 1
        data, meta = build_one(eng, rng, official, names, templates, dens_med, dens_max)
        if data is None:
            reasons[meta] = reasons.get(meta, 0) + 1; continue
        name = f'{a.prefix}_{made:02d}'
        open(os.path.join(a.out, name + '.map26a'), 'wb').write(data)
        metas[name] = meta; made += 1
    json.dump({'seed': a.seed, 'made': made, 'tries': tries, 'rejections': reasons, 'official_group_density':
               {'median': dens_med, 'max': dens_max}, 'maps': metas}, open(os.path.join(a.out, f'{a.prefix}_meta.json'), 'w'), indent=1)
    print(f'made {made} in {tries} tries; rejections {reasons}')


if __name__ == '__main__': main()
