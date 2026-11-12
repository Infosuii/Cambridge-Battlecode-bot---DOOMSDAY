"""Freeze all four inference/admission combinations on independent large-dev cases."""
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI,ENGINE,HERE,SDK_ROOT,one,read
from freeze_engine3_discovery import write
from live111_runtime_ablation import prepare
from profile_live111_first import exact_build
from qualify_local import partition
from turn_prefix import action_prefix


if __name__ == "__main__":
    identity=read(HERE/"LIVE111_SOURCE_VERIFIED.json")
    known=read(HERE/"LIVE111_RUNTIME_ABLATION_BUILDS.json")["releases"]
    output=bench.CACHE/"live111-runtime-field-factorial"
    output.mkdir()
    builds={"stock":identity["wasm_sha256"],"guard":read(HERE/"LIVE111_FIELD_PREPARE_BUILDS.json")["builds"]["on"]["sha256"],"off":known["ablation"]}
    for suffix in ("","-rebuild"):
        source=output/("combination"+suffix+"-source")
        prepare(source,True)
        apply(source/"bot.cpp",(("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();",
                                "        if (!w.fields_ready() && quota > 0 && room()) w.prepare_field_order();"),))
        wasm=exact_build(source,SDK_ROOT/"bots"/("live111-runtime-field"+suffix),1)
        builds["combination"+suffix]=bench.digest(wasm)
    assert builds["combination"]==builds["combination-rebuild"]
    assert bench.digest(SDK_ROOT/"bots/live111-runtime-ablation/bot.wasm")==builds["off"]
    write(HERE/"LIVE111_RUNTIME_FIELD_BUILDS.json",{"source_archive":identity["archive_sha256"],"builds":builds})
    maps={p.stem:p for p in partition("dev")}
    stock=read(HERE/"LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    guard=read(HERE/"LIVE111_FIELD_PREPARE_LARGE.json")["pairs"]
    key=lambda r:tuple(r[k] for k in ("map_hash","side","opponent","engine_seed","noise_seed"))
    originals={key(r):r for r in stock}
    assert all(originals[key(a)]==a for a,b in guard)
    rows={"stock":stock,"guard":[b for a,b in guard],"off":[],"combination":[]}
    for arm in ("off","combination"):
        for opp in {r["opponent"] for r in stock}: (output/(arm+"-"+opp)).mkdir()
    def run(job):
        arm,base=job
        mp=maps[base["map"]]
        ref=bench.CACHE/bench.OPPS[base["opponent"]][0]
        assert bench.digest(mp)==base["map_hash"] and bench.digest(ref)==bench.OPPS[base["opponent"]][1]
        wasm=SDK_ROOT/"bots"/("live111-runtime-ablation/bot.wasm" if arm=="off" else "live111-runtime-field/bot.wasm")
        assert bench.digest(wasm)==builds[arm]
        row=one((arm,mp,base["side"],wasm,ref),output=output/(arm+"-"+base["opponent"]),opponent=base["opponent"])
        assert key(row)==key(base)
        return arm,row
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i,(arm,row) in enumerate(pool.map(run,[(arm,r) for r in stock for arm in ("off","combination")]),1):
            rows[arm].append(row)
            if i%30==0: print(f"{i}/120",flush=True)
    indexed={arm:{key(r):r for r in records} for arm,records in rows.items()}
    summaries={f"{a}->{b}":bench.summary([(indexed[a][k],indexed[b][k]) for k in originals])
               for a,b in (("stock","guard"),("stock","off"),("stock","combination"),("off","combination"))}
    errors=sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for records in rows.values() for r in records)
    case=read(HERE/"LIVE111_FIRST_TURN_PLAN.json")["case"]
    directory=output/("combination-"+case["opponent"])/f"{case['map']}-{case['side']}-combination"
    native=read(directory/"native.json")
    rounds=[x["timestamp"]["round"] for e in native["events"] if e["kind"]=="fuelExhausted" and e["owner"]["team"]=="teamA" and e["owner"]["id"]==case["actor"] for x in e["entries"]]
    (archive,)=directory.glob("*.repl26a")
    replay=directory/"raw.repl26a"
    with ZipFile(archive) as z:
        with replay.open("xb") as f:f.write(z.read("replay.repl26a"))
    turn=directory/"turn.json"
    subprocess.run(["node",HERE/"trace_turn.mjs",replay,"1","0",str(case["actor"]),turn],cwd=bench.ROOT,env={**os.environ,"NFS_REPLAY_ENGINE":"3.0.0"},check=True)
    before,after=read(bench.ROOT/case["traces"]["base"]["path"]),read(turn)
    for data in (before,after):data["observation"].pop("input")
    mechanism={"same_own_view":before["observation"]==after["observation"],"same_action_prefix":action_prefix(before)==action_prefix(after),"actor_round1_removed":1 not in rounds,"actor_fuel_rounds":rounds,"turn_sha256":bench.digest(turn)}
    passed=not errors and all(mechanism[k] for k in ("same_own_view","same_action_prefix","actor_round1_removed")) and all(not summaries[k]["per_cell_fuel_regressions"] for k in ("stock->combination","off->combination"))
    result={"engine":ENGINE,"builds":builds,"n_total_cells":240,"new_games":120,"summaries":summaries,"mechanism":mechanism,"error_cells":errors,"pass":passed,"rows":rows}
    write(HERE/"LIVE111_RUNTIME_FIELD_FACTORIAL.json",result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
