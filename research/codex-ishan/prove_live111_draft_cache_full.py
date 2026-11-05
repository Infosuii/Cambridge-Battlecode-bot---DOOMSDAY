"""Full development equivalence/draft parity and corrupted-cache rejection controls."""
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_draft_cache import prepare
from profile_live111_first import exact_build
from prove_live111_draft_cache import MAIN
from qualify_local import partition

CONTROLS=r'''
            w.bridges_on=false;
            std::array<std::byte,codex_field_cache::end> bytes{};
            std::memcpy(bytes.data(),bc::draft_memory.data(),bytes.size());
            const auto good=bytes;
            auto rejected=[&](){w.field_order.clear();return !codex_field_cache::decode(w,bytes.data(),bytes.size())&&w.field_order.empty();};
            bool corrupt=true;
            bytes[codex_field_cache::offset]^=std::byte{1};corrupt&=rejected();bytes=good;
            bytes[codex_field_cache::offset+4]^=std::byte{1};corrupt&=rejected();bytes=good;
            codex_field_cache::Header header{};
            std::memcpy(&header,bytes.data()+codex_field_cache::offset,sizeof(header));
            std::array<std::uint16_t,240> order{};
            std::memcpy(order.data(),bytes.data()+codex_field_cache::offset+sizeof(header),2*header.count);
            if(header.count>=2){
                order[1]=order[0];header.checksum=codex_field_cache::checksum(order.data(),header.count);
                std::memcpy(bytes.data()+codex_field_cache::offset,&header,sizeof(header));
                std::memcpy(bytes.data()+codex_field_cache::offset+sizeof(header),order.data(),2*header.count);
                corrupt&=rejected();bytes=good;
            }
            std::memcpy(&header,bytes.data()+codex_field_cache::offset,sizeof(header));
            std::memcpy(order.data(),bytes.data()+codex_field_cache::offset+sizeof(header),2*header.count);
            order[0]=header.count;header.checksum=codex_field_cache::checksum(order.data(),header.count);
            std::memcpy(bytes.data()+codex_field_cache::offset,&header,sizeof(header));
            std::memcpy(bytes.data()+codex_field_cache::offset+sizeof(header),order.data(),2*header.count);
            corrupt&=rejected();bytes=good;
            std::memcpy(&header,bytes.data()+codex_field_cache::offset,sizeof(header));++header.width;
            std::memcpy(bytes.data()+codex_field_cache::offset,&header,sizeof(header));corrupt&=rejected();bytes=good;
            w.field_order.clear();corrupt&=!codex_field_cache::decode(w,bytes.data(),bytes.size()-1)&&w.field_order.empty();
            std::memcpy(&header,bytes.data()+codex_field_cache::offset,sizeof(header));header.count=241;
            std::memcpy(bytes.data()+codex_field_cache::offset,&header,sizeof(header));corrupt&=rejected();
            std::printf("CACHE_REJECT %d\n",corrupt);
'''

if __name__ == "__main__":
    first=read(HERE/"LIVE111_DRAFT_CACHE_PROOF.json");assert first["pass"]
    output=bench.CACHE/"live111-draft-cache-proof-full"
    output.mkdir()
    off=output/"off-source";prepare(off,False)
    control=exact_build(off,SDK_ROOT/"bots/live111-draft-cache-full-off",1)
    assert bench.digest(control)==first["off"]==read(HERE/"LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"]
    source=output/"proof-source";prepare(source,True,True)
    cpp=MAIN.replace('play_draft();','play_draft();\n            if(first) std::printf("CACHE_PRESERVED %d\\n",codex_field_cache::memory_preserved);')
    cpp=cpp.replace('            std::printf("CACHE_PROOF',CONTROLS+'\n            std::printf("CACHE_PROOF')
    (source/"main.cpp").write_text(cpp,encoding="utf8",newline="\n")
    wasm=exact_build(source,SDK_ROOT/"bots/live111-draft-cache-full-proof",1)
    maps=partition("dev")
    write(HERE/"LIVE111_DRAFT_CACHE_FULL_PLAN.json",{"maps":{p.name:bench.digest(p) for p in maps},"off":bench.digest(control),"probe":bench.digest(wasm),"schema":"512..1007v1","scope":"All90devmaps/both sides,normal100k/naturaldraft;exact draft parity against unchanged111"})
    reference=SDK_ROOT/"bots/v92-e3/bot.wasm";assert bench.digest(reference)==bench.OPPS["v92"][1]
    def run(job):
        mp,side,arm=job;directory=output/f"{mp.stem}-{side}-{arm}";directory.mkdir()
        own=wasm if arm=="probe" else control
        bots=(own,reference) if side=="A" else (reference,own)
        with (directory/"run.log").open("wb") as log:
            subprocess.run([CLI,"run",*bots,"--map",mp,"--release","--fuel","100000","--rounds","3","--log-limit","1048576" if arm=="probe" else "0","--statistics",directory/"native.json","--out-dir",directory,"--json"],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/"native.json");assert doc["match"]["engineBuildHash"]==ENGINE and doc["match"]["mapHash"]==bench.digest(mp) and doc["diagnostics"]["detailedCaptureComplete"]
        row={"arm":arm,"map":mp.stem,"side":side,"map_hash":bench.digest(mp),"engine_seed":doc["match"]["seed"],"draft":doc["roster"]["draft"],"errors":bool(doc["diagnostics"]["codes"]) or any(doc["diagnostics"]["botFaults"].values())}
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
    result={"engine":ENGINE,"n_games":len(rows),"n_pairs":len(pairs),"off":bench.digest(control),"probe":bench.digest(wasm),"pass":all(passed(p) for p in pairs),"failed":sum(not passed(p) for p in pairs),"rows":rows}
    write(HERE/"LIVE111_DRAFT_CACHE_FULL_PROOF.json",result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
