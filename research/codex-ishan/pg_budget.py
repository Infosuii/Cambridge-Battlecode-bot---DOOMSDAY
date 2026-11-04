"""Run independently budgeted PG mechanism variants and prepare their release source."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from bounded_verdict import apply
import pg_rivals
import profile_pg_runtime as trace

HERE = Path(__file__).resolve().parent


def prepare(src, variant, enabled=True):
    pg_rivals.prepare(src, enabled)
    if not enabled:
        return
    config = src / "jd_config.h"
    if variant in ("siege", "combined"):
        apply(config, (("#define JD_GOV 5", "#define JD_GOV 7"),))
    if variant in ("walk", "combined"):
        data = config.read_bytes()
        nl = b"\r\n" if b"\r\n" in data else b"\n"
        config.write_bytes(b"#define X1_WALKRES 12" + nl + data)


def run(variant):
    trace.OUT = bench.CACHE / ("pg-budget-walk-r1" if variant == "walk" else f"pg-budget-{variant}")
    project = trace.OUT / "diagnostic"
    prepare(project / "src", variant)
    trace.instrument(project / "src")
    wasm = project / "bot.wasm"
    with (trace.OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    for name in trace.OPPONENTS:
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    md = bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert len(maps) == 16 and md == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    bench.OUT = trace.OUT
    (trace.OUT / "games").mkdir()
    jobs = [("profile", 0, opp, mp, side, wasm) for mp in maps for opp in trace.OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(trace.play, jobs))
    count = Counter()
    for row in rows:
        count.update(row["crossings"])
    base = json.loads((HERE / "PG_RUNTIME_LOW_TRACE.json").read_bytes())
    baseline = {(r["map"], r["opponent"], r["side"]): r for r in base["rows"]}
    for r in rows:
        b = baseline[r["map"], r["opponent"], r["side"]]
        assert all(r[k] == b[k] for k in ("map_hash", "engine_seed"))
    phases = {
        "siege": ("sg_ring -> sg_init", "sg_los -> sg_seeing"),
        "walk": ("tail -> field", "d_farm -> d_opp", "d_opp -> decide", "decide -> tail"),
    }
    phases_changed = {
        name: [sum(base["crossings"].get(k, 0) for k in keys), sum(count.get(k, 0) for k in keys)]
        for name, keys in phases.items()
    }
    result = {"variant": variant, "engine": bench.ENGINE, "map_digest": md, "wasm": bench.digest(wasm),
              "n": len(rows), "fuel": sum(r["fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows),
              "base_fuel": base["fuel"], "phases": phases_changed, "crossings": dict(count.most_common()), "rows": rows}
    with (HERE / f"PG_BUDGET_{variant.upper()}.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("variant", choices=("siege", "walk", "combined"))
    p.add_argument("--src", type=Path)
    p.add_argument("--off", action="store_true")
    a = p.parse_args()
    if a.src:
        prepare(a.src, a.variant, not a.off)
    else:
        run(a.variant)


if __name__ == "__main__":
    main()
