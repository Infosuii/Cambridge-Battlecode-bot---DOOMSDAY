"""Original86-map safety gate, with unchanged current-source ablation and both baselines."""
from concurrent.futures import ThreadPoolExecutor
import json

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write


if __name__ == "__main__":
    builds=read(HERE/"LIVE111_RUNTIME_ABLATION_BUILDS.json")
    screen=read(HERE/"LIVE111_RUNTIME_ABLATION_DEV.json")
    assert screen["safety_pass"] and screen["win_filter_pass"] and screen["releases"]==builds["releases"]
    wasm=SDK_ROOT/"bots/live111-runtime-ablation/bot.wasm"
    reference=SDK_ROOT/"bots/v92-e3/bot.wasm"
    assert bench.digest(CLI)==CLI_HASH and bench.digest(wasm)==builds["releases"]["ablation"]
    assert bench.digest(reference)==bench.OPPS["v92"][1]
    original=read(HERE/"ENGINE3_REBASELINE_POOL.json")
    current=read(HERE/"LIVE111_POOL_SAFETY.json")
    assert original["engine"]==current["engine"]==ENGINE
    assert current["candidate_release"]==builds["releases"]["base"]
    bases={"v92":{(r["map"],r["side"]):r for r in original["rows"] if r["arm"]=="base"},
           "live111":{(r["map"],r["side"]):r for r in current["rows"]}}
    maps=sorted((bench.ROOT/"maps/ladder-pool").glob("*.map26a"))
    assert len(maps)==86 and all(len(b)==172 for b in bases.values())
    assert all(bench.digest(p)==bases["v92"][p.stem,"A"]["map_hash"]==bases["live111"][p.stem,"A"]["map_hash"] for p in maps)
    output=bench.CACHE/"live111-ablation-pool"
    output.mkdir()
    write(HERE/"LIVE111_ABLATION_POOL_PLAN.json",{"engine":ENGINE,"candidate_release":bench.digest(wasm),"reference_release":bench.digest(reference),
          "stock111_release":builds["releases"]["base"],"maps":{p.name:bench.digest(p) for p in maps},"normal_fuel":100000,"logging":False})
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(lambda job:one(job,output=output),[("ablation",p,s,wasm,reference) for p in maps for s in "AB"]):
            rows.append(row)
            if len(rows)%40==0: print(f"{len(rows)}/172",flush=True)
    errors=sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    reports={}
    for label,indexed in bases.items():
        pairs=[(indexed[r["map"],r["side"]],r) for r in rows]
        assert all(all(b[k]==c[k] for k in ("map_hash","engine_seed","side","opponent")) for b,c in pairs)
        reports[label]=bench.summary(pairs)
    result={"engine":ENGINE,"candidate_release":bench.digest(wasm),"baselines":reports,"error_cells":errors,
            "pass":not errors and all(not r["per_cell_fuel_regressions"] for r in reports.values()),"rows":rows}
    write(HERE/"LIVE111_ABLATION_POOL_SAFETY.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)
