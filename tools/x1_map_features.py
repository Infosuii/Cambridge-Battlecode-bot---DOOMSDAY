"""Structural features of maps for per-map strategy clusters (J020 B; research/x1/CBR_IM_ARCHITECTURE.md section 6).

usage: python tools/x1_map_features.py OUT.json DIR [DIR ...]      (every *.map26a in each DIR; kind = DIR's name)
Per map (full map; camps / groups are mirrored from the authored half): size, team, wall / bush / hole shares, groups
and their gems / gold per area, gem-only (no gold anywhere), spawn-to-spawn walk and its straight-line ratio, walk to
the nearest altar, home / contested value share (group value nearer to our spawn on foot, or within 15% of equal),
gem-weighted walk / straight ratio to groups (maze-ness), corridor share (open tiles with <= 2 open 4-neighbours).
"""
import json, math, os, sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'mapgen'))
from mapio import new_engine, read_map  # noqa: E402

N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def mirror(sym, w, h, x, y):
    if sym == 'horizontal': return w - 1 - x, y
    if sym == 'vertical': return x, h - 1 - y
    return w - 1 - x, h - 1 - y


def bfs(w, h, blocked, sources):
    d = {s: 0 for s in sources if s not in blocked}
    q = deque(d)
    while q:
        x, y = q.popleft()
        for dx, dy in N8:
            c = (x + dx, y + dy)
            if 0 <= c[0] < w and 0 <= c[1] < h and c not in blocked and c not in d:
                d[c] = d[(x, y)] + 1; q.append(c)
    return d


def features(m):
    w, h, sym = m['w'], m['h'], m['symmetry']
    area = w * h
    walls, holes, bushes = set(map(tuple, m['walls'])), set(map(tuple, m['holes'])), set(map(tuple, m['bushes']))
    altars = set(map(tuple, m['altars']))
    blocked = walls | holes | altars
    x0, y0, x1, y1 = m['spawn']
    spawn_a = [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    spawn_b = [mirror(sym, w, h, x, y) for x, y in spawn_a]
    da, db = bfs(w, h, blocked, spawn_a), bfs(w, h, blocked, spawn_b)
    groups = []
    for g in m['groups']:
        cells = [(c['x'], c['y']) for c in g['camps']]
        if not cells: continue
        groups.append((g['gems'], g['gold'], cells))
        mc = [mirror(sym, w, h, x, y) for x, y in cells]
        if sorted(mc) != sorted(cells): groups.append((g['gems'], g['gold'], mc))
    def near(dist, cells):
        best = None
        for (x, y) in cells:
            for dx, dy in N8 + [(0, 0)]:
                v = dist.get((x + dx, y + dy))
                if v is not None and (best is None or v < best): best = v
        return best
    home = cont = tot = 0.0; ratio_num = ratio_den = 0.0
    for gems, gold, cells in groups:
        val = gems + 0.15 * gold
        a, b = near(da, cells), near(db, cells)
        if a is None or b is None: continue
        tot += val
        if a < 0.85 * b: home += val
        elif a <= 1.15 * b: cont += val
        straight = min(max(abs(x - sx), abs(y - sy)) for x, y in cells for sx, sy in spawn_a)
        if straight > 0: ratio_num += val * a / straight; ratio_den += val
    open_tiles = [(x, y) for x in range(w) for y in range(h) if (x, y) not in blocked]
    corr = sum(1 for (x, y) in open_tiles if sum((x + dx, y + dy) not in blocked and 0 <= x + dx < w and 0 <= y + dy < h
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 2)
    alt_ring = [(ax + dx, ay + dy) for ax, ay in altars for dx, dy in N8]
    alt_walk = min((da[c] for c in alt_ring if c in da), default=None)
    sp = near(da, spawn_b)
    sp_straight = min(max(abs(bx - ax), abs(by - ay)) for ax, ay in spawn_a for bx, by in spawn_b)
    gems_total = sum(g[0] for g in groups); gold_total = sum(g[1] for g in groups)
    return dict(w=w, h=h, area=area, team=m['team'], symmetry=sym, wall_share=len(walls) / area, bush_share=len(bushes) / area,
                hole_share=len(holes) / area, groups=len(groups), groups_per_kt=1000 * len(groups) / area,
                gems_per_kt=1000 * gems_total / area, gold_per_kt=1000 * gold_total / area, gem_only=gold_total == 0,
                spawn_walk=sp, spawn_ratio=(sp / sp_straight) if sp and sp_straight else None, altars=len(altars),
                altar_walk=alt_walk, home_share=home / tot if tot else None, contested_share=cont / tot if tot else None,
                maze_ratio=ratio_num / ratio_den if ratio_den else None, corridor_share=corr / max(1, len(open_tiles)))


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    e = new_engine(); res = {}
    for d in dirs:
        kind = os.path.basename(os.path.normpath(d))
        for f in sorted(os.listdir(d)):
            if not f.endswith('.map26a'): continue
            try:
                res[f[:-7]] = dict(kind=kind, **features(read_map(e, open(os.path.join(d, f), 'rb').read())))
            except Exception as ex:  # a map the builder cannot read: record and go on
                res[f[:-7]] = dict(kind=kind, error=repr(ex)[:200])
            print(f[:-7], flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__': main()
