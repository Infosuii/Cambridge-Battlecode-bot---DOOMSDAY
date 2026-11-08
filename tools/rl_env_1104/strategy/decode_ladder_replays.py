"""Decode downloaded ladder replay bundles with tools/replay3/review.mjs (engine 3.0.0, pinned visualiser assets).

Extracts replay.repl26a from each bundle not yet decoded, writes a panel and runs the node reviewer, which writes
<out>/review-<match>.json per game (score/roster/bag parity is asserted inside the reviewer).

usage: python -I tools/rl_env_1104/strategy/decode_ladder_replays.py data/ladder/live_v112_20261108 artifacts/tmp/ladder_review
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile

ASSETS = r"C:/Users/info/AppData/Local/cambc/assets/cd8f45ac1d5caafb57059504159ca451af47388d35d405c81625fe18281c764d/visualiser/assets"


def main() -> None:
    src, out = sys.argv[1], os.path.abspath(sys.argv[2])
    os.makedirs(out, exist_ok=True)
    idx = {m["matchId"]: m for m in json.load(open(os.path.join(src, "match_index.json"), encoding="utf-8"))}
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    panel = []
    for mid in sorted(os.listdir(os.path.join(src, "replays"))):
        if os.path.exists(os.path.join(out, f"review-{mid}.json")):
            continue
        sm = os.path.join(src, "summaries", mid + ".json")
        if mid not in idx or not os.path.exists(sm):
            continue
        try:
            data = zipfile.ZipFile(os.path.join(src, "replays", mid)).read("replay.repl26a")
        except (zipfile.BadZipFile, KeyError):
            continue
        rp = os.path.join(out, mid + ".repl26a")
        with open(rp, "wb") as f:
            f.write(data)
        panel.append(dict(match=mid, map=idx[mid]["map"], replay=rp, sha256=sha(rp), summary=os.path.abspath(sm), summary_sha256=sha(sm)))
    if not panel:
        print("nothing new")
        return
    pf = os.path.join(out, "panel-pending.json")
    json.dump(panel, open(pf, "w"))
    env = dict(os.environ, NFS_REPLAY_ASSETS=ASSETS)
    here = os.path.dirname(os.path.abspath(__file__))
    tool = os.path.join(here, "..", "..", "replay3")
    r = subprocess.run(["node", "review.mjs", pf, os.path.join(out, "review.json")], cwd=tool, env=env, capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-1500:])
    for p in panel:
        os.remove(p["replay"])


if __name__ == "__main__":
    main()
