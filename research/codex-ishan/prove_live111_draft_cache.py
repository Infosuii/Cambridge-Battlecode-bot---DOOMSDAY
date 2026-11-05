"""Charged SDK cache-mechanics smoke before any gameplay candidate test."""
from concurrent.futures import ThreadPoolExecutor
import re
from zipfile import ZipFile
import subprocess

import ablate_dev as bench
from engine3_pool import CLI,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_draft_cache import prepare
from profile_live111_first import exact_build
from qualify_local import partition

MAIN=r'''#include "bot.h"
#include "draft.h"
#include "codex_field_cache.h"
#include <cstdio>
int main(){
    while(true){
        if(bc::is_draft()){
            const bool first=bc::draft::current_draft(team::ally).empty();
            codex_field_cache::store();
            if(first) std::printf("CACHE_DRAFT %llu %llu\n",(unsigned long long)codex_field_cache::draft_before,(unsigned long long)codex_field_cache::draft_after);
            play_draft();
        }else{
            World w;w.init();
            codex_field_cache::bypass=true;
            auto start=bc::fuel_remaining();w.prepare_field_order();auto middle=bc::fuel_remaining();
            auto expected=std::move(w.field_order);
            codex_field_cache::bypass=false;
            bool loaded=codex_field_cache::load(w);auto finish=bc::fuel_remaining();
            bool equal=loaded&&expected==w.field_order;
            w.field_order.clear();w.bridges_on=true;
            bool bridge_rejected=!codex_field_cache::load(w);
            std::printf("CACHE_PROOF %d %d %d %zu %llu %llu %zu\n",loaded,equal,bridge_rejected,expected.size(),(unsigned long long)(start-middle),(unsigned long long)(middle-finish),bc::draft_memory.size());
            bc::resign();
        }
        bc::end_turn();
    }
}'''

if __name__ == "__main__":
    output=bench.CACHE/"live111-draft-cache-proof"
    output.mkdir()
    off=output/"off-source";prepare(off,False)
    control=exact_build(off,SDK_ROOT/"bots/live111-draft-cache-off",1)
    assert bench.digest(control)==read(HERE/"LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"]
    source=output/"proof-source";prepare(source,True,True)
    (source/"main.cpp").write_text(MAIN,encoding="utf8",newline="\n")
    wasm=exact_build(source,SDK_ROOT/"bots/live111-draft-cache-proof",1)
    maps=sorted(partition("dev"),key=bench.digest)[:3]
    write(HERE/"LIVE111_DRAFT_CACHE_PROOF_PLAN.json",{"maps":{p.name:bench.digest(p) for p in maps},"off":bench.digest(control),"probe":bench.digest(wasm),"scope":"3stable-SHAdev maps,both sides;ordinary100k,normaldraftbudget,no strength claim"})
    ref=SDK_ROOT/"bots/v92-e3/bot.wasm";assert bench.digest(ref)==bench.OPPS["v92"][1]
    def run(job):
        mp,side=job;directory=output/f"{mp.stem}-{side}";directory.mkdir()
        bots=(wasm,ref) if side=="A" else (ref,wasm)
        with (directory/"run.log").open("wb") as log:
            subprocess.run([CLI,"run",*bots,"--map",mp,"--release","--fuel","100000","--rounds","3","--log-limit","1048576","--statistics",directory/"native.json","--out-dir",directory,"--json"],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/"native.json");assert doc["match"]["engineBuildHash"]==ENGINE and doc["match"]["mapHash"]==bench.digest(mp) and doc["diagnostics"]["detailedCaptureComplete"]
        (bundle,)=directory.glob("*.repl26a")
        with ZipFile(bundle) as z: stdout=z.read(f"team-{side.lower()}.stdout").replace(b"\0",b"")
        proofs=[list(map(int,m)) for m in re.findall(rb"CACHE_PROOF (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)",stdout)]
        draft=[list(map(int,m)) for m in re.findall(rb"CACHE_DRAFT (\d+) (\d+)",stdout)]
        errors=bool(doc["diagnostics"]["codes"]) or any(doc["diagnostics"]["botFaults"].values())
        return {"map":mp.stem,"side":side,"map_hash":bench.digest(mp),"proofs":proofs,"draft":draft,"errors":errors,"stdout":stdout.decode(errors="replace")[-1200:]}
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(run,[(p,s) for p in maps for s in "AB"]))
    passed=all(not r["errors"] and r["proofs"] and all(all(p[:3]) for p in r["proofs"]) and r["draft"] and r["draft"][0][0]>=1000000 and r["draft"][0][1]>0 for r in rows)
    write(HERE/"LIVE111_DRAFT_CACHE_PROOF.json",{"engine":ENGINE,"off":bench.digest(control),"probe":bench.digest(wasm),"pass":passed,"rows":rows})
    print({"pass":passed,"rows":rows},flush=True)
