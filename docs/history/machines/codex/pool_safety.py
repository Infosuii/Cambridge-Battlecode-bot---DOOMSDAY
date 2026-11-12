"""Official-pool release safety comparison, both sides against frozen v92."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
CLI = ROOT / "tools/vendor/cambc.exe"
ENGINE = "85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21"
WASM = {
    "v92": ("v92.wasm", "5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47"),
    "cpg": ("cpg-archive-1.wasm", "a06ae0655dc5a473db4c783e4b436487ac39959e04eb02573090b938625657a4"),
}
OUTPUT = CACHE / "pool-safety-v1"

def one(job):
    arm, mp, side = job
    home = OUTPUT / f"{mp.stem}-{side}-{arm}"
    home.mkdir()
    names = (arm, "v92") if side == "A" else ("v92", arm)
    cmd = [CLI, "run", *(CACHE / WASM[n][0] for n in names), "--map", mp, "--release", "--json",
           "--log-limit", "0", "--statistics", home / "native.json", "--out-dir", home]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=120)
    (home / "run.log").write_bytes(proc.stdout + proc.stderr)
    proc.check_returncode()
    summary = json.loads((home / "native.json").read_bytes())
    match = summary["match"]
    assert match["engineVersion"] == "2.0.0" and match["engineBuildHash"] == ENGINE
    owner = "team" + side
    fuel = [e["timestamp"]["round"] for event in summary["events"]
            if event["kind"] == "fuelExhausted" and event["owner"]["team"] == owner for e in event["entries"]]
    diag = summary["diagnostics"]
    assert diag["detailedCaptureComplete"]
    return {"arm": arm, "opponent": "v92", "map": mp.stem, "side": side,
            "map_hash": match["mapHash"], "seed": match["seed"], "win": match["outcome"] == owner,
            "fuel_outs": len(fuel), "round1_fuel_outs": fuel.count(1),
            "faults": diag["botFaults"][owner], "opponent_faults": sum(diag["botFaults"].values()) - diag["botFaults"][owner],
            "diagnostic_codes": diag["codes"]}

def main():
    for file, digest in WASM.values():
        assert sha256((CACHE / file).read_bytes()).hexdigest() == digest
    maps = sorted((ROOT / "maps/ladder-pool").glob("*.map26a"))
    assert len(maps) == 86
    OUTPUT.mkdir()
    jobs = [(arm, mp, side) for mp in maps for side in "AB" for arm in WASM]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = []
        for row in pool.map(one, jobs):
            rows.append(row)
            if len(rows) % 40 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(a["map_hash"] == b["map_hash"] and a["seed"] == b["seed"] for a,b in pairs)
    total = {arm: {k:sum(r[k] for r in rows if r["arm"]==arm)
                  for k in ("win","faults","opponent_faults","fuel_outs","round1_fuel_outs")} for arm in WASM}
    regressions = [{"map": a["map"], "side": a["side"], "baseline": a["fuel_outs"], "candidate": b["fuel_outs"],
                    "baseline_round1": a["round1_fuel_outs"], "candidate_round1": b["round1_fuel_outs"]}
                   for a,b in pairs if b["fuel_outs"] > a["fuel_outs"] or b["round1_fuel_outs"] > a["round1_fuel_outs"]]
    result = {"total": total, "fuel_regressions": regressions, "n_pairs": len(pairs),
              "b": sum(b["win"] and not a["win"] for a,b in pairs), "c": sum(a["win"] and not b["win"] for a,b in pairs),
              "engine_hash": ENGINE, "wasm": WASM, "rows": rows}
    (Path(__file__).resolve().parent / "CPG_POOL_SAFETY.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf8", newline="\n")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"}, indent=2))

if __name__ == "__main__":
    main()
