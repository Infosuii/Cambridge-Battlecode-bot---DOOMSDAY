"""Build a still.mjs list for one candidate of a run_eval run: every --step-th cell, replays extracted to --out.

report.json games are in cell order, so games[i] is work/g<i>/*.repl26a (a bundle zip holding replay.repl26a).
usage: python -I tools/replay3/still_pick.py runs/rl_env_1104/eval/<run> <candidate> <out_dir> [--step 10]
Writes <out_dir>/list.json for: node tools/replay3/still.mjs <out_dir>/list.json <out_dir>/still.json
"""
import argparse
import glob
import json
import os
import zipfile


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("candidate")
    ap.add_argument("out")
    ap.add_argument("--step", type=int, default=10)
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    items = []
    for i, g in enumerate(rep["games"]):
        if g["candidate"] != a.candidate or g.get("status") != "ok":
            continue
        cells = sorted(rep["cells"])
        if cells.index(g["cell"]) % a.step:
            continue
        src = glob.glob(os.path.join(a.run, "work", f"g{i}", "*.repl26a"))
        if not src:
            continue
        dst = os.path.join(a.out, f"g{i}.repl26a")
        if not os.path.exists(dst):
            with zipfile.ZipFile(src[0]) as z, open(dst, "wb") as f:
                f.write(z.read("replay.repl26a"))
        items.append(dict(id=g["cell"], replay=dst.replace("\\", "/"), us=0 if g["side"] == "A" else 1, tag=a.candidate,
                          opponent=g["opponent"], map=g["map"], score=g["score"]))
    json.dump(items, open(os.path.join(a.out, "list.json"), "w"), indent=1)
    print(len(items), "games listed")


if __name__ == "__main__":
    main()
