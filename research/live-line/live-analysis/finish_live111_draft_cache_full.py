"""Resume the exact frozen proof with completed controls and preserved partial artifacts."""
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition


if __name__ == "__main__":
    bug=read(HERE/"CACHE_PROOF_COMPLETION_BUG.json");assert bug["native_missing"] and not bug["result_written"]
    plan=read(HERE/"LIVE111_DRAFT_CACHE_FULL_PLAN.json")
    output=bench.CACHE/"live111-draft-cache-proof-full"
    maps=partition("dev")
    assert plan["maps"]=={p.name:bench.digest(p) for p in maps}
    control=SDK_ROOT/"bots/live111-draft-cache-full-off/bot.wasm"
    probe=SDK_ROOT/"bots/live111-draft-cache-full-proof/bot.wasm"
    ref=SDK_ROOT/"bots/v92-e3/bot.wasm"
    assert bench.digest(CLI)==CLI_HASH and bench.digest(control)==plan["off"]==read(HERE/"LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"]
    assert bench.digest(probe)==plan["probe"] and bench.digest(ref)==bench.OPPS["v92"][1]
    def run(job):
        mp,side,arm=job
        old=output/f"{mp.stem}-{side}-{arm}"
        reused=arm=="probe" and (old/"native.json").exists()
        directory=old if reused else output/f"{mp.stem}-{side}-resume-{arm}"
        if not reused:
            directory.mkdir()
            own=probe if arm=="probe" else control
            bots=(own,ref) if side=="A" else (ref,own)
            with (directory/"run.log").open("wb") as log:
                subprocess.run([CLI,"run",*bots,"--map",mp,"--release","--fuel","100000",*(["--rounds","3"] if arm=="probe" else []),"--log-limit","1048576" if arm=="probe" else "0","--statistics",directory/"native.json","--out-dir",directory,"--json"],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/"native.json")
        assert doc["match"]["engineVersion"]=="3.0.0" and doc["match"]["engineBuildHash"]==ENGINE and doc["match"]["mapHash"]==bench.digest(mp) and doc["diagnostics"]["detailedCaptureComplete"]
        row={"arm":arm,"map":mp.stem,"side":side,"map_hash":bench.digest(mp),"engine_seed":doc["match"]["seed"],"draft":doc["roster"]["draft"],"errors":bool(doc["diagnostics"]["codes"]) or any(doc["diagnostics"]["botFaults"].values()),
             "directory":directory.relative_to(bench.ROOT).as_posix(),"reused_completed_probe":reused,"native_sha256":bench.digest(directory/"native.json")}
        if arm=="probe":
            (bundle,)=directory.glob("*.repl26a")
            with ZipFile(bundle) as z:stdout=z.read(f"team-{side.lower()}.stdout").replace(b"\0",b"")
            row["proofs"]=[list(map(int,m)) for m in re.findall(rb"CACHE_PROOF (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)",stdout)]
            row["draft_fuel"]=[list(map(int,m)) for m in re.findall(rb"CACHE_DRAFT (\d+) (\d+)",stdout)]
            row["corrupt_rejected"]=[int(m) for m in re.findall(rb"CACHE_REJECT (\d+)",stdout)]
            row["memory_preserved"]=[int(m) for m in re.findall(rb"CACHE_PRESERVED (\d+)",stdout)]
            row["draft_fuel_events"]=[x for e in doc["events"] if e["kind"]=="fuelExhausted" and e["owner"].get("team")=="team"+side for x in e["entries"] if x["timestamp"].get("phase")=="draft"]
        return row
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run,[(p,s,a) for p in maps for s in "AB" for a in ("base","probe")]):
            rows.append(row)
            if len(rows)%60==0:print(f"{len(rows)}/360",flush=True)
    pairs=list(zip(rows[::2],rows[1::2],strict=True))
    def passed(pair):
        a,b=pair
        return not(a["errors"] or b["errors"]) and all(a[k]==b[k] for k in ("map_hash","side","engine_seed","draft")) and b["proofs"] and all(all(p[:3]) for p in b["proofs"]) and b["corrupt_rejected"] and all(b["corrupt_rejected"]) and b["memory_preserved"] and all(b["memory_preserved"]) and b["draft_fuel"] and all(x[0]>=1000000 and x[1]>0 for x in b["draft_fuel"]) and not b["draft_fuel_events"]
    result={"engine":ENGINE,"n_games":len(rows),"n_pairs":len(pairs),"off":bench.digest(control),"probe":bench.digest(probe),"pass":all(passed(p) for p in pairs),"failed":sum(not passed(p) for p in pairs),"rows":rows}
    write(HERE/"LIVE111_DRAFT_CACHE_FULL_PROOF.json",result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
