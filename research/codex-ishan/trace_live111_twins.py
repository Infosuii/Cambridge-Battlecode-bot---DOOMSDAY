"""Freeze requested-rival discovery cases and inspect exact twin health steps."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import os
import subprocess

import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write


if __name__ == "__main__":
    audit=read(HERE/"LIVE111_TWIN_DEATH_AUDIT.json")["partitions"]["discovery"]["cases"]
    output=bench.CACHE/"live111-twin-traces"
    output.mkdir()
    cases=[];absent=[]
    for rival in ("QS2isLaw","0xDEADBEEF","bentheboss"):
        eligible=[r for r in audit if r["side"]=="ours" and r["opponent"]==rival and r["same_round_opposite_twin"]]
        if not eligible:absent.append(rival);continue
        chosen=min(eligible,key=lambda r:(sha256(r["matchId"].encode()).hexdigest(),r["death"]["round"],r["death"]["id"]))
        mid=chosen["matchId"]
        replay=bench.CACHE/f"live111-discovery-20261105/analysis-discovery/replays/{mid}.repl26a"
        c={"matchId":mid,"opponent":rival,"round":chosen["death"]["round"],"team":chosen["death"]["team"],
           "actors":sorted((chosen["death"]["id"],chosen["same_round_opposite_twin"]["id"])),"replay":str(replay),"replay_sha256":bench.digest(replay)}
        write(output/f"{mid}-case.json",c);cases.append(c)
    write(HERE/"LIVE111_TWIN_TRACE_PLAN.json",{"selection":"Discovery only,first stable-matchSHA then earliest linked death per requested rival","cases":cases,"absent":absent})
    def run(c):
        mid=c["matchId"]
        target=output/f"{mid}-trace.json"
        subprocess.run(["node",HERE/"trace_twin_death.mjs",output/f"{mid}-case.json",target],cwd=bench.ROOT,env={**os.environ,"NFS_REPLAY_ENGINE":"3.0.0"},check=True)
        result=read(target)
        deaths=[]
        for a,b in zip(result["transitions"],result["transitions"][1:]):
            before={x["id"]:x for x in a["twins"]}
            newly=[x for x in b["twins"] if before[x["id"]]["alive"] and not x["alive"]]
            if newly:deaths.append({"before":a,"after":b,"newly_dead":[x["id"] for x in newly]})
        return {"case":c,"trace_sha256":bench.digest(target),"death_transitions":deaths}
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
    write(HERE/"LIVE111_TWIN_DEATH_STEPS.json",{"rows":rows,"absent":absent,"limits":"Historic source interval inferred; step actor/target and health identify observed transitions,not private policy intention."})
    print({"cases":len(rows),"absent":absent,"death_transitions":[len(r["death_transitions"]) for r in rows]},flush=True)
