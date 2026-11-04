"""Measure the exact opening-window binary's first-150-round collection behavior."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import ablate_dev as bench

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "opening-window-behavior"
sys.path.insert(0, str(HERE / "discovery4"))
from metrics import timeline

OPPONENTS = ("x3inv", "public-khiri")
ROUND_LIMIT = 150


def run(job):
    row = bench.one(job)
    arm, _, opp, mp, side, _ = job
    work = OUT / "games" / f"{arm}-0-{opp}-{mp.stem}-{side}"
    native = json.loads((work / "native.json").read_bytes())
    target = OUT / "replays" / f"{arm}-{opp}-{mp.stem}-{side}.repl26a"
    with ZipFile(next(work.glob("*.repl26a"))) as z:
        target.write_bytes(z.read("replay.repl26a"))
    team = "team" + side
    camp_gems = sum(int(e["value"]) for event in native["events"]
                    if event["kind"] == "gemCollection" and event["owner"]["team"] == team
                    for e in event["entries"] if e["timestamp"]["round"] <= ROUND_LIMIT
                    and e.get("target", {}).get("kind") == "campGroup")
    return {**row, "replay": target.name, "camp_gems": camp_gems,
            "earned_gold": timeline(native, team, "earnedGold", ROUND_LIMIT)}


def main(variant="opening-window", build_file="OPENING_WINDOW_BUILDS.json", result_file="OPENING_WINDOW_BEHAVIOR.json"):
    global OUT
    OUT = bench.CACHE / f"{variant}-behavior"
    builds = json.loads((HERE / build_file).read_bytes())
    binaries = {"base": bench.CACHE / "v92.wasm", "window": bench.ROOT / "bots" / f"codex-{variant}" / "bot.wasm"}
    assert [bench.digest(p) for p in binaries.values()] == [builds["off"], builds["release"]]
    for name in OPPONENTS:
        filename, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / filename) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    digest = bench.sha256("\n".join(f"{bench.digest(m)} {m.name}" for m in maps).encode()).hexdigest()
    assert len(maps) == 16 and digest == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    (OUT / "replays").mkdir()
    jobs = [(arm, 0, opp, mp, side, wasm) for mp in maps for opp in OPPONENTS
            for side in "AB" for arm, wasm in binaries.items()]
    with ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(run, jobs))
    env = {**os.environ, "NFS_REPLAY_ENGINE": "2.0.0", "NFS_FUNNEL_UNTIL": str(ROUND_LIMIT)}
    profile = OUT / "camp-capture.json"
    subprocess.run(["node", bench.ROOT / "tools/replay/capture_pressure.mjs", profile,
                    *(OUT / "replays" / row["replay"] for row in rows)], env=env, cwd=bench.ROOT, check=True)
    by_id = {r["id"]: r for r in json.loads(profile.read_bytes())}
    for row in rows:
        our_team = int(row["side"] == "B")
        captures = by_id[Path(row["replay"]).stem]["captures"]
        row["inferred_camp_gold"] = sum(sum(p["gain"] for p in c["capturers"])
                                      for c in captures if c["team"] == our_team
                                      and c["gold"] > 0 and c["round"] <= ROUND_LIMIT)
    fields = ("earned_gold", "inferred_camp_gold", "camp_gems")
    by_map = defaultdict(lambda: dict.fromkeys(fields, 0))
    for base, window in zip(rows[::2], rows[1::2], strict=True):
        assert all(base[k] == window[k] for k in ("map_hash", "engine_seed", "map", "side", "opponent"))
        for field in fields:
            by_map[base["map"]][field] += window[field] - base[field]
    aggregate = {field: sum(r[field] for r in by_map.values()) for field in fields}
    result = {"binaries": builds, "round_limit": ROUND_LIMIT, "map_digest": digest,
              "engine": bench.ENGINE, "pairs": len(rows) // 2,
              "faults": sum(r["faults"] for r in rows), "by_map": by_map,
              "delta": aggregate,
              "improved_maps": [m for m, d in by_map.items()
                                if d["inferred_camp_gold"] > 0 or d["camp_gems"] > 0],
              "rows": rows}
    with (HERE / result_file).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k not in ("rows", "by_map")}, flush=True)


if __name__ == "__main__":
    main()
