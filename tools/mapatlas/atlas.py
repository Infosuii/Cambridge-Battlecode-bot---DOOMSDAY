"""Map atlas: a wide feature vector for every map, computed only from what the bot itself can see at game start
(the whole map: walls, bushes, holes, altars, camps, groups, spawns), so the same features exist for unseen maps.

Map files hold the authored half; everything is mirrored by the map's symmetry first (a group that maps onto itself
counts once), which gives the map the bot plays on. Distances are 8-neighbour walking steps (Chebyshev moves) over
non-wall, non-hole tiles, from the spawn areas.

  python tools/mapatlas/atlas.py [--maps maps/ladder-pool] [--out research/x3/atlas]
writes atlas.json (per map: features + group table) and atlas.csv (features only).
"""
import argparse, csv, json, math, sys
from collections import deque
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/mapgen'))
import mapio  # noqa: E402

KIND = mapio.CAMP_NAMES  # wolf, elk, gem, gold, monolith, golem
DANGER = {'wolf', 'elk', 'monolith', 'golem'}


def mirror_fn(m):
    w, h, sym = m['w'], m['h'], m['symmetry']
    if sym == 'horizontal': return lambda x, y: (w - 1 - x, y)
    if sym == 'vertical': return lambda x, y: (x, h - 1 - y)
    return lambda x, y: (w - 1 - x, h - 1 - y)


def full_map(m):
    mir = mirror_fn(m)
    cells = {k: set(map(tuple, m[k])) | {mir(*c) for c in m[k]} for k in ('walls', 'bushes', 'holes', 'altars')}
    groups = []
    # Some files hold the authored half, others the whole map: the file is whole when most camps' mirror tiles
    # already hold a camp; then nothing is mirrored.
    tiles = {(c['x'], c['y']) for c in m['camps']}
    whole = sum(1 for t in tiles if mir(*t) in tiles) > 0.5 * max(1, len(tiles))
    if whole:
        cells = {k: set(map(tuple, m[k])) for k in ('walls', 'bushes', 'holes', 'altars')}
    in_file = {tuple(sorted((c['x'], c['y']) for c in g['camps'])) for g in m['groups']}
    for g in m['groups']:
        cs = [(c['x'], c['y'], KIND[c['type']]) for c in g['camps']]
        key = tuple(sorted((x, y) for x, y, _ in cs))
        ms = [(*mir(x, y), k) for x, y, k in cs]
        mkey = tuple(sorted((x, y) for x, y, _ in ms))
        # A group whose mirror shares a tile with it straddles the mirror line: the engine keeps one group (its
        # camps' union, gems counted once).
        straddle = bool(set(mkey) & set(key)) or whole
        camps = cs + [c for c in ms if (c[0], c[1]) not in set(key)] if straddle and not whole and mkey != key else cs
        groups.append(dict(gems=g['gems'], gold=g['gold'], respawn=g['respawn'], camps=camps, side=('mid' if set(mkey) & set(key) else 'A') if not whole else 'file'))
        if not straddle and mkey not in in_file:
            groups.append(dict(gems=g['gems'], gold=g['gold'], respawn=g['respawn'], camps=ms, side='B'))
    x0, y0, x1, y1 = m['spawn']
    sa = {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    sb = {mir(x, y) for x, y in sa}
    return cells, groups, sa, sb


def bfs(w, h, blocked, starts):
    d = [[-1] * h for _ in range(w)]
    q = deque()
    for x, y in starts:
        if 0 <= x < w and 0 <= y < h and (x, y) not in blocked:
            d[x][y] = 0; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < w and 0 <= ny < h and d[nx][ny] < 0 and (nx, ny) not in blocked:
                    d[nx][ny] = d[x][y] + 1; q.append((nx, ny))
    return d


def gini(v):
    v = sorted(v); n = len(v); s = sum(v)
    if n == 0 or s == 0: return 0.0
    return sum((2 * i - n + 1) * x for i, x in enumerate(v)) / (n * s)


def features(name, m):
    w, h = m['w'], m['h']; area = w * h
    cells, groups, sa, sb = full_map(m)
    blocked = cells['walls'] | cells['holes']
    camp_tiles = {(x, y) for g in groups for x, y, _ in g['camps']}
    walk_block = blocked | camp_tiles  # camps occupy tiles
    dA, dB = bfs(w, h, walk_block, sa), bfs(w, h, walk_block, sb)

    def reach(d, cs):  # steps to stand next to any camp of a group (-1 = unreachable on foot)
        best = -1
        for x, y, _ in cs:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and d[nx][ny] >= 0 and (best < 0 or d[nx][ny] < best): best = d[nx][ny]
        return best
    for g in groups:
        g['dA'], g['dB'] = reach(dA, g['camps']), reach(dB, g['camps'])
        g['kinds'] = sorted({k for _, _, k in g['camps']})
        g['danger'] = any(k in DANGER for k in g['kinds'])
        g['n'] = len(g['camps'])
    gems = [g['gems'] for g in groups]; tot = sum(gems) or 1
    gold = [g['gold'] for g in groups]; totg = sum(gold) or 1
    reach_g = [g for g in groups if g['dA'] >= 0]
    spawn_b = next(iter(sb)); ss = min((dA[x][y] for x, y in sb if dA[x][y] >= 0), default=-1)
    ca = (sum(x for x, _ in sa) / len(sa), sum(y for _, y in sa) / len(sa)); cb = (sum(x for x, _ in sb) / len(sb), sum(y for _, y in sb) / len(sb))
    straight = max(abs(ca[0] - cb[0]), abs(ca[1] - cb[1]))
    own = sum(g['gems'] for g in reach_g if g['dB'] < 0 or g['dA'] + 3 < g['dB'])
    contested = sum(g['gems'] for g in reach_g if g['dB'] >= 0 and abs(g['dA'] - g['dB']) <= 3)
    near = lambda r: sum(g['gems'] for g in reach_g if g['dA'] <= r)
    passable = [(x, y) for x in range(w) for y in range(h) if (x, y) not in blocked]
    reach_cells = sum(1 for x, y in passable if dA[x][y] >= 0)

    def nb(x, y):
        return sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) not in blocked and 0 <= x + dx < w and 0 <= y + dy < h)
    corridor = sum(1 for x, y in passable if nb(x, y) <= 2) / max(1, len(passable))
    alt = sorted(cells['altars'])
    altA = sorted(min((abs(ax - x) + abs(ay - y)) for x, y in sa) for ax, ay in alt)  # rough
    alt_walk = sorted(dA[ax][ay] for ax, ay in alt if dA[ax][ay] >= 0) or [-1]
    kinds = {k: sum(1 for g in groups for _, _, kk in g['camps'] if kk == k) for k in KIND}
    ncamps = sum(kinds.values()) or 1
    cx, cy = (w - 1) / 2, (h - 1) / 2; rad = 0.2 * max(w, h)
    centre = sum(g['gems'] for g in groups if math.hypot(sum(x for x, _, _ in g['camps']) / g['n'] - cx, sum(y for _, y, _ in g['camps']) / g['n'] - cy) <= rad)
    top = sorted(gems, reverse=True)
    f = dict(
        map=name, w=w, h=h, area=area, team=m['team'], symmetry=m['symmetry'],
        wall_density=round(len(cells['walls']) / area, 4), bush_density=round(len(cells['bushes']) / area, 4),
        hole_density=round(len(cells['holes']) / area, 4), n_groups=len(groups), n_camps=ncamps,
        gems_total=sum(gems), gold_total=sum(gold), gems_per_group=round(sum(gems) / max(1, len(groups)), 1),
        gem_density=round(sum(gems) / area * 100, 3), groups_per_champ=round(len(groups) / (2 * m['team']), 2),
        jackpot_share=round(top[0] / tot, 3) if top else 0, top3_share=round(sum(top[:3]) / tot, 3), gem_gini=round(gini(gems), 3),
        gold_per_gem=round(totg / tot, 2),
        **{f'share_{k}': round(v / ncamps, 3) for k, v in kinds.items()},
        harmless_gem_share=round(sum(g['gems'] for g in groups if not g['danger']) / tot, 3),
        respawn_mean=round(sum(g['respawn'] for g in groups) / max(1, len(groups)), 1),
        spawn_to_spawn=ss, spawn_straight=straight, maze_ratio=round(ss / max(1, straight), 2) if ss > 0 else -1,
        reach_cells_share=round(reach_cells / max(1, len(passable)), 3),
        unreachable_gem_share=round(sum(g['gems'] for g in groups if g['dA'] < 0) / tot, 3),
        corridor_share=round(corridor, 3),
        own_gem_share=round(own / tot, 3), contested_gem_share=round(contested / tot, 3), centre_gem_share=round(centre / tot, 3),
        gems_within_15=round(near(15) / tot, 3), gems_within_30=round(near(30) / tot, 3),
        nearest_group=min((g['dA'] for g in reach_g), default=-1),
        mean_group_dist=round(sum(g['dA'] for g in reach_g) / max(1, len(reach_g)), 1),
        n_altars=len(alt), nearest_altar=alt_walk[0], altars_own_half=sum(1 for ax, ay in alt if dA[ax][ay] >= 0 and (dB[ax][ay] < 0 or dA[ax][ay] < dB[ax][ay])),
    )
    return f, groups


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--maps', default='maps/ladder-pool'); ap.add_argument('--out', default='research/x3/atlas')
    a = ap.parse_args(); out = ROOT / a.out; out.mkdir(parents=True, exist_ok=True)
    e = mapio.new_engine(); rows, full = [], {}
    for p in sorted((ROOT / a.maps).glob('*.map26a')):
        m = mapio.read_map(e, p.read_bytes())
        f, groups = features(p.stem, m)
        rows.append(f)
        full[p.stem] = dict(features=f, groups=[{k: g[k] for k in ('gems', 'gold', 'respawn', 'side', 'dA', 'dB', 'kinds', 'n')} for g in groups])
        print(p.stem, f"{f['w']}x{f['h']} groups {f['n_groups']} gems {f['gems_total']} own {f['own_gem_share']} contested {f['contested_gem_share']} jackpot {f['jackpot_share']} maze {f['maze_ratio']}", flush=True)
    (out / 'atlas.json').write_text(json.dumps(full, indent=1), encoding='utf-8')
    with open(out / 'atlas.csv', 'w', newline='', encoding='utf-8') as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print(len(rows), 'maps ->', out)


if __name__ == '__main__':
    main()
