"""Re-use the captured v92 mirror arm for a frozen candidate's pool safety check."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "docs/codex"))
import pool_safety as harness

def pick_rate(raw_dir, row):
    path = raw_dir / f'{row["map"]}-{row["side"]}-{row["arm"]}' / "native.json"
    doc = json.loads(path.read_bytes())
    return any(p["champion"] == "Vesper Vale" and p["team"] == "team" + row["side"]
               for p in doc["roster"]["draft"])

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", required=True)
    p.add_argument("--wasm", required=True)
    p.add_argument("--sha256", required=True)
    a = p.parse_args()
    wasm = Path(a.wasm).resolve()
    assert sha256(wasm.read_bytes()).hexdigest() == a.sha256
    harness.WASM[a.name] = (wasm, a.sha256)
    prior = json.loads((ROOT / "docs/codex/CPG_POOL_SAFETY.json").read_bytes())
    assert prior["engine_hash"] == harness.ENGINE
    maps = {m.stem:m for m in (ROOT/"maps/ladder-pool").glob("*.map26a")}
    baseline = [r for r in prior["rows"] if r["arm"]=="v92"]
    assert len(baseline) == 2 * len(maps) == 172
    harness.OUTPUT = harness.CACHE / f"{a.name}-pool-safety"
    harness.OUTPUT.mkdir()
    jobs = [(a.name,maps[r["map"]],r["side"]) for r in baseline]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = []
        for row in pool.map(harness.one,jobs):
            rows.append(row)
            if len(rows) % 40 == 0:
                print(f"{len(rows)}/{len(jobs)}",flush=True)
    baseline_dir = harness.CACHE / "pool-safety-v1"
    pairs = list(zip(baseline,rows,strict=True))
    for base,cand in pairs:
        assert all(base[k]==cand[k] for k in ("map_hash","seed","map","side"))
        base["vesper_pick"] = pick_rate(baseline_dir,base)
        cand["vesper_pick"] = pick_rate(harness.OUTPUT,cand)
    fields=("win","fuel_outs","round1_fuel_outs","faults","opponent_faults","vesper_pick")
    totals={arm:{k:sum(r[k] for r in arm_rows) for k in fields}
            for arm,arm_rows in (("v92",baseline),(a.name,rows))}
    regression=[{"map":b["map"],"side":b["side"],"base":b["fuel_outs"],"candidate":c["fuel_outs"],
                 "base_round1":b["round1_fuel_outs"],"candidate_round1":c["round1_fuel_outs"]}
                for b,c in pairs if c["fuel_outs"]>b["fuel_outs"] or c["round1_fuel_outs"]>b["round1_fuel_outs"]]
    compact={"sha256":a.sha256,"n":len(rows),"total":totals,"fuel_regressions":regression,
             "newly_suspended":sum(x["base"]==0 and x["candidate"]>0 for x in regression),
             "round1_regressions":sum(x["candidate_round1"]>x["base_round1"] for x in regression),
             "diagnostic_cells":[{"arm":r["arm"],"map":r["map"],"side":r["side"],"codes":r["diagnostic_codes"]}
                                 for r in [*baseline,*rows] if r["diagnostic_codes"]],
             "b":sum(c["win"] and not b["win"] for b,c in pairs),
             "c":sum(b["win"] and not c["win"] for b,c in pairs)}
    out=Path(__file__).resolve().parent/f"{a.name.upper()}_POOL_SAFETY.json"
    out.write_text(json.dumps({**compact,"candidate_rows":rows},indent=2)+"\n",encoding="utf8",newline="\n")
    print(json.dumps({**compact,"fuel_regressions":len(regression)},indent=2))

if __name__=="__main__":
    main()
