"""Localize and optimize the exact Heart striking-dash camp scoring scan."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from pg_budget import prepare as prepare_pg
from profile_pg_budget_broad import augment
import profile_pg_runtime as trace
from qualify_local import partition

HERE = Path(__file__).resolve().parent
BASE = "e_prefight -> enemies"
DASH = "dash_aim_enter -> dash_aim_done"


def read(path):
    return json.loads(path.read_bytes())


def prepare(src, enabled, optimized, diagnostic):
    prepare_pg(src, "combined", enabled)
    if diagnostic:
        trace.instrument(src)
        augment(src)
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    common.write_bytes(nl.join([f"#define CODEX_DASH_LOCAL_CAMPS {int(enabled and optimized)}".encode(), data]))
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::cast_on_enemy(")
    end = data.index(b"    if (dash_slot >= 0)", start)
    body = data[start:end]
    edits = (
        ("        int best_hits = -1000;",
         """        PROF_CHECK("dash_aim_enter");
#if CODEX_DASH_LOCAL_CAMPS
        std::vector<vec2> nearby_camps;
        for (const auto& camp : w.camps)
            if (!camp.dead && cheb(camp.pos, e.pos) <= 2 * rad)
                nearby_camps.push_back(camp.pos);
#endif
        int best_hits = -1000;"""),
        ("                for (const auto& c : w.camps)\n                    if (!c.dead && cheb(c.pos, t) <= rad) hits -= 3;",
         """#if CODEX_DASH_LOCAL_CAMPS
                for (vec2 camp : nearby_camps)
                    if (cheb(camp, t) <= rad) hits -= 3;
#else
                for (const auto& c : w.camps)
                    if (!c.dead && cheb(c.pos, t) <= rad) hits -= 3;
#endif"""),
        ("        if (best_hits > -1000) {", """        PROF_CHECK("dash_aim_done");
        if (best_hits > -1000) {"""),
    )
    for before, after in edits:
        a, b = (s.encode().replace(b"\n", nl) for s in (before, after))
        assert body.count(a) == 1, a
        body = body.replace(a, b, 1)
    bot.write_bytes(data[:start] + body + data[end:])


def cases(broad):
    affected = [r for r in broad["rows"] if r["crossings"].get(BASE)]
    assert len(affected) == 6
    ordered = sorted(broad["rows"], key=lambda r: sha256(
        f"exp038:{r['map']}:{r['side']}:{r['opponent']}".encode()).digest())
    maps = {r["map"] for r in affected}
    controls = []
    for r in ordered:
        if r["map"] in maps or r["fuel_outs"]:
            continue
        maps.add(r["map"])
        controls.append(r)
        if len(controls) == 6:
            break
    assert len(controls) == 6
    return affected + controls


def probe():
    broad = read(HERE / "PG_BUDGET_BROAD_TRACE.json")
    frozen = cases(broad)
    maps = {p.stem: p for p in partition("dev")}
    for name in sorted({r["opponent"] for r in frozen}):
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    result = {}
    for arm in ("base", "local"):
        trace.OUT = bench.CACHE / f"pg-dash-trace-{arm}"
        project = trace.OUT / "diagnostic"
        prepare(project / "src", True, arm == "local", True)
        wasm = project / "bot.wasm"
        with (trace.OUT / "build.log").open("wb") as log:
            subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                           cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        bench.OUT = trace.OUT
        (trace.OUT / "games").mkdir()
        jobs = [("profile", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in frozen]
        with ThreadPoolExecutor(max_workers=6) as pool:
            rows = list(pool.map(trace.play, jobs))
        counts = Counter()
        for b, r in zip(frozen, rows, strict=True):
            assert all(r[k] == b[k] for k in ("map_hash", "engine_seed"))
            counts.update(r["crossings"])
        result[arm] = {
            "wasm": bench.digest(wasm), "n": len(rows), "fuel": sum(r["fuel_outs"] for r in rows),
            "fault_or_code_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
            "dash_crossings": counts[DASH], "dash_maps": sorted({r["map"] for r in rows if r["crossings"].get(DASH)}),
            "crossings": dict(counts), "rows": rows,
        }
        print(arm, {k: v for k, v in result[arm].items() if k != "rows"}, flush=True)
    b, c = result["base"], result["local"]
    result["pass"] = (len(b["dash_maps"]) >= 2 and c["dash_crossings"] < b["dash_crossings"]
                      and c["fuel"] < b["fuel"] and not c["fault_or_code_cells"])
    with (HERE / "PG_DASH_TRACE.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")


def verify_release():
    frozen = cases(read(HERE / "PG_BUDGET_BROAD_TRACE.json"))
    maps = {p.stem: p for p in partition("dev")}
    for name in sorted({r["opponent"] for r in frozen}):
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    base = bench.ROOT / "bots/codex-pg-budget/bot.wasm"
    candidate = bench.ROOT / "bots/codex-pg-dash/bot.wasm"
    assert bench.digest(base) == "36854b76366f762f65853b3b66819e9c2d4742982ef7fcd69294931daf977e75"
    assert bench.digest(candidate) == read(HERE / "PG_DASH_BUILDS.json")["primary"]
    bench.OUT = bench.CACHE / "pg-dash-exact-dev"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = [(arm, 0, r["opponent"], maps[r["map"]], r["side"], wasm)
            for r in frozen for arm, wasm in (("base", base), ("candidate", candidate))]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(bench.one, jobs))
    for r, (b, c) in zip(frozen, zip(rows[::2], rows[1::2], strict=True), strict=True):
        assert all(r[k] == b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    report = {"engine": bench.ENGINE, "base": bench.digest(base), "candidate": bench.digest(candidate), "rows": rows}
    with (HERE / "PG_DASH_EXACT_DEV.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    for arm in ("base", "candidate"):
        arm_rows = [r for r in rows if r["arm"] == arm]
        print(arm, len(arm_rows), "fuel", sum(r["fuel_outs"] for r in arm_rows),
              "fault or code cells", sum(bool(r["faults"] or r["diagnostic_codes"]) for r in arm_rows))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path)
    p.add_argument("--off", action="store_true")
    p.add_argument("--verify-release", action="store_true")
    a = p.parse_args()
    if a.src:
        prepare(a.src, not a.off, True, False)
    elif a.verify_release:
        verify_release()
    else:
        probe()
