"""Exercise independently selected large development layouts at the ordinary budget."""
from concurrent.futures import ThreadPoolExecutor
import json

import ablate_dev as bench
from engine3_pool import HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from qualify_local import partition


def main():
    metadata = read(bench.CACHE / "engine3-retry-l1/rows.json")
    wanted = {r["map"] for r in metadata if r["size"] == "large"}
    maps = [p for p in partition("dev") if p.stem in wanted]
    assert maps and len(maps) == len(wanted)
    wasm = SDK_ROOT / "bots/live111/bot.wasm"
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    assert bench.digest(wasm) == identity["wasm_sha256"]
    output = bench.CACHE / "live111-large-development"
    output.mkdir()
    write(HERE / "LIVE111_LARGE_DEV_PLAN.json", {"selection": "All large frozen dev map metadata only; no outcomes inspected", "maps": {p.name: bench.digest(p) for p in maps}, "wasm": bench.digest(wasm)})
    for opponent in ("x3inv", "public-khiri"):
        assert bench.digest(bench.CACHE / bench.OPPS[opponent][0]) == bench.OPPS[opponent][1]
        (output / opponent).mkdir()
    def run(job):
        mp, side, opponent = job
        row = one(("stock111", mp, side, wasm, bench.CACHE / bench.OPPS[opponent][0]), output=output / opponent, opponent=opponent)
        doc = read(output / opponent / f"{mp.stem}-{side}-stock111/native.json")
        row["early_events"] = [{"actor": e["owner"]["id"], "name": e["owner"]["name"], "round": x["timestamp"]["round"]} for e in doc["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + side for x in e["entries"] if x["timestamp"]["round"] <= 100]
        return row
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, [(mp, side, opponent) for mp in maps for side in "AB" for opponent in ("x3inv", "public-khiri")]))
    report = {"source111": identity["wasm_sha256"], "n_games": len(rows), "fuel": sum(r["fuel_outs"] for r in rows), "round1": sum(r["round1_fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows), "rows": rows}
    write(HERE / "LIVE111_LARGE_DEV_CENSUS.json", report)
    print({k: v for k, v in report.items() if k != "rows"}, flush=True)


if __name__ == "__main__": main()
