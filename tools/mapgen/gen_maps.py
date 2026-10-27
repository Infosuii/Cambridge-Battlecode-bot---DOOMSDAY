"""Generate new maps by structured resampling of the official maps (engine 2.0.0 MapBuilder).

Usage: python tools/mapgen/gen_maps.py --out <dir> --count N --seed S [--official research/maps/official_maps.json]
       [--exclude name ...]

Method (a structured, smoothed bootstrap of map components; see tools/mapgen/README.md):
  1. Style: draw an official template map T. Width/height are T's scaled by a factor in [0.85, 1.15]; team size and
     symmetry are T's (symmetry is swapped for another of T's compatible kinds with probability 0.25); group count,
     altar count and spawn-rectangle size/position follow T, scaled to the new area with small jitter.
  2. Terrain: T and its two nearest official maps by (wall, bush, hole) density donate square patches (side 6-14,
     random flip/rotation) that tile the authored half. The builder mirrors every placement, so terrain is symmetric.
  3. Camps: as many groups as T has per unit area (x0.85-1.15); 70% of groups are T's own, 30% come from the pool
     of all real official groups (exact member types and relative offsets, so Golem
     and monolith groups appear as they do officially), placed at free spots away from spawn and other camps.
  4. Altars are placed on free tiles away from spawn. The engine verifies integrity, the game must load the map, and
     every altar and camp must be reachable from the spawn area on foot (walls and holes block).
Rejected attempts are retried; the output names are gen<seed>_<index>.map26a, with a JSON sidecar per batch that
records each map's template and parameters.
"""
import argparse
import json
import math
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapbuilder import MapBuilder, loads_in_game  # noqa: E402
from mapio import new_engine  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CAMP_KIND = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']


def mirror(sym, w, h, x, y):
    if sym == 'horizontal':
        return w - 1 - x, y
    if sym == 'vertical':
        return x, h - 1 - y
    return w - 1 - x, h - 1 - y


def in_half(sym, w, h, x, y):
    """The authored half: a cell whose mirror is not lexicographically smaller (the mirror line is excluded)."""
    mx, my = mirror(sym, w, h, x, y)
    return (x, y) < (mx, my)


def densities(m):
    a = m['w'] * m['h']
    return (len(m['walls']) / a, len(m['bushes']) / a, len(m['holes']) / a)


def group_templates(official):
    """Real official camp groups as (types, offsets) relative to their first member."""
    out = []
    for name, m in official.items():
        for g in m['groups']:
            if not g['camps']:
                continue
            x0, y0 = g['camps'][0]['x'], g['camps'][0]['y']
            out.append({'from': name, 'members': [(c['type'], c['x'] - x0, c['y'] - y0) for c in g['camps']]})
    return out


def patch_from(donor, rng, size):
    """A square terrain patch from a donor map: dict cell->kind ('W','B','H') with random flip/rotation."""
    w, h = donor['w'], donor['h']
    x0, y0 = rng.randrange(max(1, w - size)), rng.randrange(max(1, h - size))
    cells = {}
    for kind, key in (('W', 'walls'), ('B', 'bushes'), ('H', 'holes')):
        for (x, y) in donor[key]:
            if x0 <= x < x0 + size and y0 <= y < y0 + size:
                cells[(x - x0, y - y0)] = kind
    rot, flip = rng.randrange(4), rng.random() < 0.5
    out = {}
    for (x, y), k in cells.items():
        if flip:
            x = size - 1 - x
        for _ in range(rot):
            x, y = size - 1 - y, x
        out[(x, y)] = k
    return out


def reachable(w, h, blocked, starts):
    seen = set(starts)
    q = deque(starts)
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and (nx, ny) not in blocked:
                    seen.add((nx, ny))
                    q.append((nx, ny))
    return seen


def build_one(eng, rng, official, names, templates, tname):
    T = official[tname]
    scale = rng.uniform(0.85, 1.15)
    w = max(24, min(100, round(T['w'] * scale)))
    h = max(24, min(100, round(T['h'] * scale)))
    sym = T['symmetry']
    if rng.random() < 0.25:
        sym = rng.choice(['horizontal', 'vertical', 'rotational'] if w == h else ['rotational', 'horizontal'
                                                                                    if w >= h else 'vertical'])
    team = T['team']
    area_ratio = (w * h) / (T['w'] * T['h'])

    # Terrain donors: T plus the two official maps nearest in terrain densities.
    dT = densities(T)
    near = sorted((n for n in names if n != tname),
                  key=lambda n: sum((a - b) ** 2 for a, b in zip(densities(official[n]), dT)))[:2]
    donors = [T, T] + [official[n] for n in near]
    terrain = {}
    y = 0
    while y < h:
        size = rng.randint(6, 14)
        x = 0
        while x < w:
            p = patch_from(rng.choice(donors), rng, size)
            for (px, py), k in p.items():
                cx, cy = x + px, y + py
                if cx < w and cy < h:
                    terrain[(cx, cy)] = k
            x += size
        y += size
    # Keep the authored half only; the builder mirrors.
    terrain = {c: k for c, k in terrain.items() if in_half(sym, w, h, *c)}

    # Spawn rectangle: T's size and relative position, scaled.
    sx0, sy0, sx1, sy1 = T['spawn']
    sw, sh = max(1, round((sx1 - sx0 + 1) * scale)), max(1, round((sy1 - sy0 + 1) * scale))
    while sw * sh < team:
        sw += 1
    px = min(w - sw, max(0, round(sx0 / T['w'] * w)))
    py = min(h - sh, max(0, round(sy0 / T['h'] * h)))
    def rect(px, py):
        return [(x, y) for x in range(px, px + sw) for y in range(py, py + sh)]

    spawn = rect(px, py)
    if any(not in_half(sym, w, h, *c) for c in spawn):
        # Keep T's spawn size; move it the shortest way into the authored half (its mirror image, or a nudge
        # towards the origin), instead of rejecting the template's style.
        options = []
        mx, my = mirror(sym, w, h, px + sw - 1, py + sh - 1)
        for qx, qy in [(mx, my)] + [(px - d, py) for d in range(1, w)] + [(px, py - d) for d in range(1, h)] +                 [(px - d, py - d) for d in range(1, min(w, h))]:
            if 0 <= qx <= w - sw and 0 <= qy <= h - sh and all(in_half(sym, w, h, *c) for c in rect(qx, qy)):
                options.append((abs(qx - px) + abs(qy - py), qx, qy))
        if not options:
            return None, 'spawn does not fit the authored half'
        _, px, py = min(options)
        spawn = rect(px, py)
    keep_clear = {(x + dx, y + dy) for (x, y) in spawn for dx in range(-2, 3) for dy in range(-2, 3)}
    for c in keep_clear:
        terrain.pop(c, None)

    blocked = {c for c, k in terrain.items() if k in 'WH'}
    occupied = set(keep_clear) | blocked

    def free(x, y, margin=1):
        if not (0 <= x < w and 0 <= y < h) or not in_half(sym, w, h, x, y):
            return False
        return all((x + dx, y + dy) not in occupied for dx in range(-margin, margin + 1) for dy in range(-margin, margin + 1))

    # Camp groups: count follows T (authored half), scaled by area with jitter.
    n_groups = max(1, round(len(T['groups']) * area_ratio * rng.uniform(0.85, 1.15)))
    placed = []
    own = [t for t in templates if t['from'] == tname]
    for _ in range(n_groups):
        g = rng.choice(own) if own and rng.random() < 0.7 else rng.choice(templates)
        for _try in range(400):
            ax, ay = rng.randrange(w), rng.randrange(h)
            cells = [(t, ax + dx, ay + dy) for (t, dx, dy) in g['members']]
            if all(free(x, y, 1) for (_, x, y) in cells):
                for (_, x, y) in cells:
                    occupied.update((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                    terrain.pop((x, y), None)
                placed.append({'from': g['from'], 'cells': cells})
                break
    if len(placed) < 0.85 * n_groups:
        return None, 'too few camp groups fitted'

    # Altars: T's count (whole map), authored half gets half of them.
    n_alt = max(1, round(len(T['altars']) * rng.uniform(0.8, 1.25) / 2))
    altars = []
    sxc, syc = px + sw / 2, py + sh / 2
    for _ in range(n_alt):
        for _try in range(200):
            x, y = rng.randrange(w), rng.randrange(h)
            if free(x, y, 0) and math.hypot(x - sxc, y - syc) >= 6:
                altars.append((x, y))
                occupied.add((x, y))
                terrain.pop((x, y), None)
                break

    # Reachability on the full mirrored map.
    full_blocked = set()
    for c, k in terrain.items():
        if k in 'WH':
            full_blocked.add(c)
            full_blocked.add(mirror(sym, w, h, *c))
    seen = reachable(w, h, full_blocked, spawn)
    targets = altars + [(x, y) for g in placed for (_, x, y) in g['cells']]
    for (x, y) in targets:
        if not any((x + dx, y + dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            return None, 'unreachable altar or camp'

    mb = MapBuilder(eng, w, h, sym)
    try:
        mb.team_size(team)
        mb.spawn(px, py, px + sw - 1, py + sh - 1)
        for (x, y), k in terrain.items():
            {'W': mb.wall, 'B': mb.bush, 'H': mb.hole}[k](x, y)
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
    meta = {'template': tname, 'w': w, 'h': h, 'symmetry': sym, 'team': team, 'scale': round(scale, 3),
            'donors': [tname] + near, 'groups': len(placed), 'group_sources': sorted({g['from'] for g in placed}),
            'altars_half': len(altars)}
    return data, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--count', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--official', default=os.path.join(ROOT, 'research', 'maps', 'official_maps.json'))
    ap.add_argument('--exclude', nargs='*', default=[])
    a = ap.parse_args()
    official = json.load(open(a.official))
    for n in a.exclude:
        official.pop(n, None)
    names = sorted(official)
    templates = group_templates(official)
    rng = random.Random(a.seed)
    eng = new_engine()
    os.makedirs(a.out, exist_ok=True)
    made, tries, reasons, metas = 0, 0, {}, {}
    skipped = {}
    while made < a.count and tries < a.count * 40:
        tname = rng.choice(names)  # template drawn first; failures retry the same template (no size/style bias)
        for _attempt in range(30):
            tries += 1
            data, meta = build_one(eng, rng, official, names, templates, tname)
            if data is not None:
                break
            reasons[meta] = reasons.get(meta, 0) + 1
        if data is None:
            skipped[tname] = skipped.get(tname, 0) + 1
            continue
        name = f'gen{a.seed}_{made:04d}'
        open(os.path.join(a.out, name + '.map26a'), 'wb').write(data)
        metas[name] = meta
        made += 1
    json.dump({'seed': a.seed, 'made': made, 'tries': tries, 'rejections': reasons, 'templates_skipped': skipped, 'excluded_sources': a.exclude,
               'maps': metas}, open(os.path.join(a.out, f'gen{a.seed}_meta.json'), 'w'), indent=1)
    print(f'made {made} in {tries} tries; rejections {reasons}; templates skipped {skipped}')


if __name__ == '__main__':
    main()
