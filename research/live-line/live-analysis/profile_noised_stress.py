"""Trace only the exact native rounds found under the two fresh stress seeds."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import re

from large_roster_noised import OUT as RAW, SEEDS
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_siege_resume import prepare
from profile_roster_stress import play_scoped, prepare_coarse
from qualify_local import build

OUT = bench.CACHE / "large-roster-noise-profile"
STAGES = ("world", "support", "wardrev", "ambush", "e_td", "e_prefight", "enemies", "route0", "route1",
          "farmsel", "sg_ring", "sg_init", "sg_los", "sg_seeing", "c_safe", "c_walked", "c_cast", "d_farm", "decide", "tail")


def main():
    source = read(HERE / "LARGE_ROSTER_NOISE.json")
    affected = source["affected"]
    exact = read(RAW / "rows.json")
    maps_seen = {r["map"] for r in affected}
    controls = []
    for r in sorted(exact, key=lambda r: sha256(f"exp061:{r['map']}:{r['opponent']}:{r['side']}:{r['noise_seed']}".encode()).digest()):
        if r["map"] in maps_seen or r["fuel_outs"]:
            continue
        maps_seen.add(r["map"])
        controls.append(r)
        if len(controls) == 6:
            break
    assert len(affected) == len(controls) == 6
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True)
    prepare_coarse(src, {e["timestamp"]["round"] for row in affected for e in row["events"]}, STAGES)
    with ThreadPoolExecutor(max_workers=2) as pool:
        bins = dict(zip(SEEDS, pool.map(lambda s: build(src, OUT / f"seed-{s}", s), SEEDS), strict=True))
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    maps = {p.stem: p for p in (STRESS / "maps").glob("*.map26a")}
    for row in affected + controls:
        mp = maps[row["map"]]
        assert bench.digest(mp) == manifest[mp.name]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    jobs = [("profile", r["noise_seed"], r["opponent"], maps[r["map"]], r["side"], bins[r["noise_seed"]])
            for r in affected + controls]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play_scoped, jobs))
    joined = []
    for base, row in zip(affected + controls, rows, strict=True):
        assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "side", "opponent", "noise_seed"))
        exact_events = {(e["owner"]["name"], e["timestamp"]["round"]) for e in base.get("events", [])}
        current = {(e["owner"]["name"], e["timestamp"]["round"]) for e in native_fuel(row, OUT)}
        matches = exact_events & current
        if matches:
            rounds = {r for _, r in matches}
            phases = [p for p, line in row["examples"].items() if int(re.search(r" R(\d+)", line).group(1)) in rounds]
            joined.append({"map": row["map"], "opponent": row["opponent"], "side": row["side"], "seed": row["noise_seed"],
                           "matched_native": sorted(matches), "phases": phases})
    result = {"wasm": {s: bench.digest(b) for s, b in bins.items()}, "n": len(rows), "matches": joined,
              "fuel": sum(r["fuel_outs"] for r in rows), "errors": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
              "phases": dict(Counter(p for j in joined for p in j["phases"]))}
    with (HERE / "LARGE_ROSTER_NOISE_PROFILE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
