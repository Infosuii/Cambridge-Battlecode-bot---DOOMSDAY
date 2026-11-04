"""Test the measured effect of pricing the SDK Vesper bonus in her route."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from shutil import copytree
import subprocess
import sys

import ablate_dev as bench
from bounded_verdict import apply

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "vesper-passive-dev"
sys.path.insert(0, str(HERE / "discovery4"))
from metrics import timeline


def prepare(src, enabled):
    copytree(bench.ROOT / "bots/v92/src", src)
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    common.write_bytes(f"#define CODEX_VESPER_PASSIVE {int(enabled)}".encode() + nl + data)
    h = src / "bot.h"
    data = h.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    anchor = b"        if (tune::kGoldTaper <= 0) return weight;"
    assert data.count(anchor) == 1
    data = data.replace(anchor, nl.join([
        b"#if CODEX_VESPER_PASSIVE",
        b"        const float adjusted = type == bc::champion_type::vesper_vale && round <= 150",
        b"            ? weight * (1.0f + static_cast<float>(bc::constants::vesper_vale_bonus_gold_percent) / 100.0f)",
        b"            : weight;",
        b"        if (tune::kGoldTaper <= 0) return adjusted;",
        b"#else",
        anchor,
        b"#endif",
    ]), 1)
    anchor = b"        return weight * (1.0f - 0.8f * t);"
    assert data.count(anchor) == 1
    h.write_bytes(data.replace(anchor, nl.join([
        b"#if CODEX_VESPER_PASSIVE",
        b"        return adjusted * (1.0f - 0.8f * t);",
        b"#else",
        anchor,
        b"#endif",
    ]), 1))
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    for first, last in ((b"int Bot::score_groups(", b"// Follow-up table"),
                        (b"void Bot::refresh_follow_ups()", b"int Bot::route_search(")):
        start = data.index(first)
        end = data.index(last, start)
        body = data[start:end]
        anchor = b"gold_weight() * static_cast<float>(g.gold)"
        assert body.count(anchor) in (1, 2)
        body = body.replace(anchor, b"CODEX_FARM_GOLD_WEIGHT * static_cast<float>(g.gold)")
        header = nl.join([
            b"#if CODEX_VESPER_PASSIVE",
            b"    const float adjusted_gold_weight = gold_weight();",
            b"#define CODEX_FARM_GOLD_WEIGHT adjusted_gold_weight",
            b"#else",
            b"#define CODEX_FARM_GOLD_WEIGHT gold_weight()",
            b"#endif",
        ]) + nl
        opening = body.index(nl)
        data = data[:start] + body[:opening + len(nl)] + header + body[opening + len(nl):] + b"#undef CODEX_FARM_GOLD_WEIGHT" + nl + data[end:]
    bot.write_bytes(data)


def metrics(native, team):
    roster = [r for r in native["roster"]["champions"] if r["team"] == team and r["name"] == "Vesper Vale"]
    if not roster:
        return None
    assert len(roster) == 1
    mid = roster[0]["id"]
    own = {"championTimelines": [r for r in native["championTimelines"] if r["owner"]["id"] == mid]}
    gems = sum(int(e["value"]) for g in native["events"] if g["kind"] == "gemCollection" and g["owner"]["team"] == team
               for e in g["entries"] if e["timestamp"]["round"] <= 150 and e.get("target", {}).get("kind") == "campGroup")
    return {"vesper_gold": timeline(own, team, "earnedGold", 150), "team_camp_gems": gems}


def run(job):
    row = bench.one(job)
    _, _, opp, mp, side, _ = job
    tag = f"passive-0-{opp}-{mp.stem}-{side}"
    cand = json.loads((OUT / "games" / tag / "native.json").read_bytes())
    old = bench.CACHE / "opening-window-behavior/games" / tag.replace("passive-", "base-", 1) / "native.json"
    base = json.loads(old.read_bytes())
    assert all(cand["match"][k] == base["match"][k] for k in ("engineBuildHash", "mapHash", "seed"))
    assert cand["roster"]["draft"] == base["roster"]["draft"]
    return {**row, "base": metrics(base, "team"+side), "candidate": metrics(cand, "team"+side)}


def probe():
    project = OUT / "release"
    prepare(project / "src", True)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    exact = json.loads((HERE / "OPENING_WINDOW_BEHAVIOR.json").read_bytes())
    assert exact["binaries"]["off"] == bench.OPPS["v92"][1]
    maps = {p.stem: p for p in (bench.CACHE / "jd-sets/conf").glob("*.map26a")}
    for opp in ("x3inv", "public-khiri"):
        file, sha = bench.OPPS[opp]
        assert bench.digest(bench.CACHE / file) == sha
    bench.OUT = OUT
    (OUT / "games").mkdir()
    jobs = [("passive", 0, r["opponent"], maps[r["map"]], r["side"], wasm)
            for r in exact["rows"] if r["arm"] == "base"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    selected = [r for r in rows if r["base"] is not None]
    fields = ("vesper_gold", "team_camp_gems")
    by_map = defaultdict(float)
    for r in selected:
        by_map[r["map"]] += r["candidate"]["vesper_gold"] - r["base"]["vesper_gold"]
    delta = {f: sum(r["candidate"][f]-r["base"][f] for r in selected) for f in fields}
    bad = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"n": len(rows), "vesper_cells": len(selected), "delta": delta, "by_map_vesper_gold": by_map,
              "fault_or_code_cells": bad, "wasm": bench.digest(wasm), "engine": bench.ENGINE,
              "pass": delta["vesper_gold"] > 0 and delta["team_camp_gems"] >= 0 and
                      sum(v > 0 for v in by_map.values()) >= 2 and not bad, "rows": rows}
    with (HERE / "VESPER_PASSIVE_DEV.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        probe()
