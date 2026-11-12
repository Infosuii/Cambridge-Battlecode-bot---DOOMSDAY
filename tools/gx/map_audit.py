"""Extract terrain, altar and camp features from engine 2.0.0 maps."""
import argparse
from collections import deque
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/mapgen"))
from mapio import Engine, read_map

NEIGHBOURS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def mirror(p, width, height, symmetry):
    x, y = p
    return (width-1-x if symmetry != "vertical" else x,
            height-1-y if symmetry != "horizontal" else y)


def bfs(terrain, sources):
    queue = deque(set(sources) & terrain)
    distances = dict.fromkeys(queue, 0)
    while queue:
        x, y = queue.popleft()
        distance = distances[x, y] + 1
        for dx, dy in NEIGHBOURS:
            p = x+dx, y+dy
            if p in terrain and p not in distances:
                distances[p] = distance
                queue.append(p)
    return distances


def group_distance(tiles, field):
    return min((field[p] for p in tiles if p in field), default=None)


def cheb(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))


def features(m, runtime=None):
    w, h = m["w"], m["h"]
    s = m["symmetry"]
    if s not in ("horizontal", "vertical", "rotational"):
        raise ValueError(f"Unexpected symmetry: {s}")
    x0, y0, x1, y1 = m["spawn"]
    a = {(x, y) for x in range(x0, x1+1) for y in range(y0, y1+1)}
    b = {mirror(p, w, h, s) for p in a}
    blocked = set(m["walls"]) | set(m["holes"]) | set(m["altars"])
    terrain = {(x, y) for x in range(w) for y in range(h)} - blocked
    ring = {(x+dx, y+dy) for x, y in m["altars"] for dx, dy in NEIGHBOURS} & terrain
    groups = []
    for g in m["groups"]:
        tiles = {(c["x"], c["y"]) for c in g["camps"]}
        groups.append((tiles, g["gems"], g["gold"]))
        other = {mirror(p, w, h, s) for p in tiles}
        if tiles != other:
            groups.append((other, g["gems"], g["gold"]))
    estimated = len(groups), sum(v for _, v, _ in groups)
    if runtime is not None:
        if (runtime["width"], runtime["height"]) != (w, h):
            raise ValueError("Runtime and authored map dimensions differ")
        groups = [({tuple(p) for p in g["tiles"]}, g["gems"], g["gold"]) for g in runtime["groups"]]
    camp_tiles = set().union(*(t for t, _, _ in groups))
    d_a = bfs(terrain - b, a)
    d_b = bfs(terrain - a, b)
    d_alt = bfs(terrain - b, ring - camp_tiles - b)
    d_gate = bfs(terrain - b, ring - b)
    reachable = [v for p, v in d_alt.items() if p in a]
    reachable_groups, bank_distance, detour = [], [], []
    cut = central = sum_gems = 0
    for tiles, gems, _ in groups:
        sa, sb, ba = group_distance(tiles, d_a), group_distance(tiles, d_b), group_distance(tiles, d_alt)
        sum_gems += gems
        if gems and sa is None:
            cut += gems
        if gems and sa is not None:
            reachable_groups.append(sa)
        if gems and ba is not None:
            bank_distance.append(ba)
        if gems and sa is not None and sb is not None and abs(sa-sb) <= max(3, (sa+sb)*0.18):
            central += gems
        if gems and sa is not None:
            straight = min((cheb(p,q) for p in tiles for q in a), default=0)
            if straight >= 3:
                detour.append(sa/straight)
    narrow = sum(sum((x+dx, y+dy) in terrain for dx,dy in NEIGHBOURS) <= 3 for x,y in terrain)
    def med(xs):
        return statistics.median(xs) if xs else None
    return dict(width=w, height=h, symmetry=s, team=m["team"], authored_groups=len(m["groups"]),
        groups=len(groups), gems=sum_gems, runtime_groups=(runtime is not None),
        mirrored_group_estimate=estimated[0], mirrored_gem_estimate=estimated[1], altars=len(m["altars"]),
        altar_open_spawn_steps=min(reachable, default=None),
        altar_open_tiles=len(ring - camp_tiles), altar_gated_tiles=len(ring & camp_tiles),
        altar_without_camps_spawn_steps=group_distance(a, d_gate),
        gem_group_altar_steps_med=med(bank_distance), gem_group_spawn_steps_med=med(reachable_groups),
        spawn_detour_med=med(detour), narrow_fraction=round(narrow / max(1,len(terrain)), 5),
        bush_fraction=round(len(m["bushes"])/(w*h), 5),
        cut_gem_fraction=round(cut/max(1,sum_gems), 5),
        centre_gem_fraction=round(central/max(1,sum_gems), 5),
        jackpot_fraction=round(max((v for _,v,_ in groups), default=0)/max(1,sum_gems), 5))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("engine", type=Path)
    cli.add_argument("map_dir", type=Path)
    cli.add_argument("--runtime-keys", type=Path)
    cli.add_argument("--runtime-groups", type=Path)
    args = cli.parse_args()
    os.environ["BC_ENGINE_WASM"] = str(args.engine.resolve())
    engine = Engine()
    keys = json.loads(args.runtime_keys.read_text()) if args.runtime_keys else {}
    groups = json.loads(args.runtime_groups.read_text()) if args.runtime_groups else {}
    data = {}
    for p in sorted(args.map_dir.glob("*.map26a")):
        blob = p.read_bytes()
        runtime_groups = groups.get(p.stem)
        sha = sha256(blob).hexdigest()
        if args.runtime_groups and (not runtime_groups or runtime_groups["map_sha256"] != sha):
            raise ValueError(f"Missing or mismatched runtime map: {p.stem}")
        row = features(read_map(engine, blob), runtime_groups)
        row["sha256"] = sha
        runtime = keys.get(p.stem+"-A")
        if runtime:
            row["runtime_key"] = runtime[:4]
            row["geometry_key_equal"] = runtime[:4] == [
                row["width"], row["height"], row["groups"], row["gems"]]
        data[p.stem] = row
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
