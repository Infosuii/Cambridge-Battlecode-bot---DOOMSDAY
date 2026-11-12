"""Map clusters for the specialist plans (E61): size (draft feature 2, area / 10000 >= 0.4) x maze (gem-weighted walk /
straight-line distance from our spawn to the camp groups >= 1.2, path_feats.js). Writes clusters/c<k>_{train,test}.txt
(map paths relative to the project root). Train: maps_new4, official maps, maps_maze; test: maps_test4, maps_mazetest.
Cluster k = 2 * large + maze: 0 small-open, 1 small-maze, 2 large-open, 3 large-maze."""
import json

AREA, RATIO = 0.4, 1.2
d = {**json.load(open("mld_feats_v4.json")), **json.load(open("mld_feats_maze.json"))}
p = {**json.load(open("path_feats_v4.json")), **json.load(open("path_feats_maze.json"))}
TRAIN, TEST = ("maps_new4", "maps", "maps_maze"), ("maps_test4", "maps_mazetest")
out = {}
for k in sorted(d):
    g = k.split("/")[0]
    cl = 2 * (d[k][0][2] >= AREA) + (p[k][0][0] >= RATIO)
    part = "train" if g in TRAIN else "test" if g in TEST else None
    if part:
        out.setdefault((cl, part), []).append("v4/" + k)
for (cl, part), maps in sorted(out.items()):
    open(f"clusters/c{cl}_{part}.txt", "w", newline="\n").write("\n".join(maps) + "\n")
    print(cl, part, len(maps))
