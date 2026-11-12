"""Compare EXP-019 with the previously audited v92 production-wrapper fixture."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json

import audit_bush_wrappers as audit
import ablate_dev as bench

def main():
    out = bench.CACHE/"bush-reachable-audit"
    audit.OUT = bench.OUT = out
    root = Path(__file__).resolve().parent
    prior=json.loads((root/"DIAGNOSTIC_RECOUNT.json").read_bytes())
    base={r["map"]:r for r in prior["rows"] if r["probe"]=="bush-wrapper-audit" and r["arm"]=="v92"}
    assert prior["engine_hash"]==bench.ENGINE and len(base)==16
    reference=bench.CACHE/"bush-wrapper-audit/v92/bot.wasm"
    assert bench.digest(reference)==prior["fixture_hashes"]["bush-wrapper-audit/v92"]
    maps=sorted((bench.CACHE/"jd-sets/conf").glob("*.map26a"))
    assert len(maps)==16 and {p.name for p in maps}==set(base)
    assert bench.digest(bench.CACHE/"v92.wasm")==bench.OPPS["v92"][1]
    arm="codex-bush-reachable"
    wasm=audit.build(arm)
    (out/"games").mkdir()
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows=list(pool.map(audit.measure,[(arm,mp,wasm) for mp in maps]))
    for row in rows:
        ref=base[row["map"]]
        for key in ("map_sha256","tiles","components","labels","mask_equal"):
            assert row[key]==ref[key],(row["map"],key,row[key],ref[key])
        row["base_fuel"]=ref["fuel"]
    total=sum(r["fuel"] for r in rows)
    baseline=sum(r["base_fuel"] for r in rows)
    result={"engine":bench.ENGINE,"fixture_sha256":bench.digest(wasm),"reference_sha256":bench.digest(reference),
            "maps":len(rows),"fuel":total,"base_fuel":baseline,"pass":total*10<=baseline*9,"rows":rows}
    with (root/"BUSH_REACHABLE_AUDIT.json").open("x",encoding="utf8",newline="\n") as f:
        json.dump(result,f,indent=2)
        f.write("\n")
    print({k:v for k,v in result.items() if k!="rows"},flush=True)
    return 0 if result["pass"] else 3

if __name__=="__main__":
    raise SystemExit(main())
