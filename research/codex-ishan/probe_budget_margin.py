"""Find native late crossings under two fixed diagnostic fuel allowances."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json

from large_roster_stress import DENSE_OUT, HERE, bench, native_fuel, read
from qualify_local import DEV

OUT = bench.CACHE / "cpg-budget-margin"
FUELS = (80000, 100000)


def play(job):
    row = bench.one(job, fuel=int(job[0]))
    events = native_fuel(row, OUT)
    assert len(events) == row["fuel_outs"]
    return {**row, "events": events}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    ref = bench.ROOT / "bots/codex-cpg-runtime-packed/bot.wasm"
    digest = bench.digest(ref)
    assert digest == read(HERE / "CPG_RUNTIME_PACKED_BUILDS.json")["primary"]
    manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    maps = sorted((DENSE_OUT / "maps").glob("*.map26a"), key=lambda p: sha256(f"exp103:{p.name}".encode()).digest())
    maps = sorted(maps[16:], key=lambda p: sha256(f"exp105:{p.name}".encode()).digest())[:20]
    assert len(maps) == 20 and all(bench.digest(p) == manifest[p.name] for p in maps)
    for o in DEV:
        file, checksum = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == checksum
    jobs = [(str(fuel), 0, o, mp, s, ref) for mp in maps for o in DEV for s in "AB" for fuel in FUELS]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 80 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side")) for b, c in pairs)
    report = {"engine": bench.ENGINE, "sha256": digest, "maps": {mp.name: manifest[mp.name] for mp in maps}, "n": len(pairs),
              "fuel_suspensions": {f: sum(r["fuel_outs"] for r in rows if r["arm"] == str(f)) for f in FUELS},
              "errors": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)}
    with (HERE / "CPG_BUDGET_MARGIN.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print({k: v for k, v in report.items() if k != "maps"}, flush=True)


if __name__ == "__main__":
    main()
