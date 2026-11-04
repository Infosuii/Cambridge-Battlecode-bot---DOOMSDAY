"""Discovery-only subsystem ablations on 16 frozen development maps."""
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from random import Random
import argparse
import json
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/"artifacts/codex-p0"
OUT=CACHE/"ablations-v2"
CLI=ROOT/"tools/vendor/cambc.exe"
ENGINE="85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21"
SEEDS=(301,607)
OPPS={
 "v92":("v92.wasm","5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47"),
 "x3inv":("opp-x3inv.wasm","d762af611f243ddc08714cac8b7b7cab0436d29f9f5fcb97c3b0fff372cbbcd9"),
 "p65pack":("opp-p65pack.wasm","9fdeeaebbad3eb1b083116e6224d4e33d06e79190d2dc26fde85eac3f19b4eda"),
 "public-khiri":("opp-public-khiri.wasm","76ceb2016112eb09622a906edb52700c27f1fab9b87bfe2ed0d638d506402727"),
}
ARMS={"base":{}, "lab_off":{"A2_LAB":(1,0),"A2_RTSW":(1,0),"A2_LADFIT":(1,0),"A2_HYB":(3,0),"LADDER_TABLES":(1,0)},
      "a3_off":{"A3_BACKOFF":(1,0),"A3_BACK_EQ":("0.4f","0.0f"),"A3_BIG_LINEUP":(6,-1)},
      "duo_off":{"NOVA_DUO":(5,0)}, "tsearch_off":{"APEX_TS_DECIDE":(1,0)}}

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def project_for(arm,seed):
    suffix="-v3" if arm=="lab_off" else ""
    return OUT/f"{arm}-{seed}{suffix}"

def prepare(job):
    arm,seed=job
    project=project_for(arm,seed)
    shutil.copytree(ROOT/"bots/v92/src",project/"src")
    header=project/"src/common.h"
    src=header.read_bytes()
    macros={**ARMS[arm],"NOVA_SEED":(1,seed),"NOVA_SEED_EPS":("0.04f","0.005f")}
    for name,(old,new) in macros.items():
        pat=rb"(?m)^#define "+name.encode()+rb" "+re.escape(str(old).encode())+rb"(?=\s|$)"
        src,n=re.subn(pat,f"#define {name} {new}".encode(),src,count=1)
        assert n==1,name
    header.write_bytes(src)

def one(job, *, log_limit=0):
    arm,seed,opp,mp,side,wasm=job
    match=OUT/"games"/f"{arm}-{seed}-{opp}-{mp.stem}-{side}"
    match.mkdir()
    bots=(wasm,CACHE/OPPS[opp][0]) if side=="A" else (CACHE/OPPS[opp][0],wasm)
    with (match/"run.log").open("wb") as log:
        subprocess.run([CLI,"run",*bots,"--map",mp,"--release","--json","--log-limit",str(log_limit),"--statistics",
                        match/"native.json","--out-dir",match],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    s=json.loads((match/"native.json").read_bytes())
    m=s["match"]
    assert m["engineVersion"]=="2.0.0" and m["engineBuildHash"]==ENGINE
    team="team"+side
    fuel=[x["timestamp"]["round"] for e in s["events"] if e["kind"]=="fuelExhausted" and e["owner"]["team"]==team for x in e["entries"]]
    assert s["diagnostics"]["detailedCaptureComplete"]
    outcome=m["outcome"]
    score=1 if outcome==team else 0 if outcome in ("teamA","teamB") else 0.5
    return {"arm":arm,"noise_seed":seed,"opponent":opp,"map":mp.stem,"side":side,"score":score,
            "engine_seed":m["seed"],"map_hash":m["mapHash"],"fuel_outs":len(fuel),"round1_fuel_outs":fuel.count(1),
            "faults":s["diagnostics"]["botFaults"][team],"diagnostic_codes":s["diagnostics"]["codes"]}

def summary(pairs):
    by=defaultdict(list)
    for a,b in pairs:
        assert a["map_hash"]==b["map_hash"] and a["engine_seed"]==b["engine_seed"]
        by[a["map"]].append(b["score"]-a["score"])
    maps=[by[k] for k in sorted(by)]
    rng=Random(1104)
    obs=[x for group in maps for x in group]
    sims=[]
    for _ in range(2000):
        sample=[x for group in rng.choices(maps,k=len(maps)) for x in group]
        sims.append(100*sum(sample)/len(sample))
    sims.sort()
    return {"n":len(pairs),"base_score":sum(a["score"] for a,b in pairs),"candidate_score":sum(b["score"] for a,b in pairs),
            "delta_pp":round(100*sum(obs)/len(obs),3),"map_cluster_ci_pp":[round(sims[i],3) for i in (50,1949)],
            "fuel":[sum(pair[i]["fuel_outs"] for pair in pairs) for i in (0,1)],
            "round1":[sum(pair[i]["round1_fuel_outs"] for pair in pairs) for i in (0,1)],
            "faults":[sum(pair[i]["faults"] for pair in pairs) for i in (0,1)],
            "per_cell_fuel_regressions":sum(b["fuel_outs"]>a["fuel_outs"] or b["round1_fuel_outs"]>a["round1_fuel_outs"] for a,b in pairs)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("prepare","prepare-lab","run"))
    args=parser.parse_args()
    config=[(arm,seed) for seed in SEEDS for arm in ARMS]
    if args.stage=="prepare":
        OUT.mkdir()
        for job in config:
            prepare(job)
        return
    if args.stage=="prepare-lab":
        for seed in SEEDS:
            prepare(("lab_off",seed))
        return
    (OUT/"games").mkdir()
    for name,(file,expected) in OPPS.items():
        assert digest(CACHE/file)==expected,name
    maps=sorted((CACHE/"jd-sets/conf").glob("*.map26a"))
    assert len(maps)==16
    md=sha256("\n".join(f"{digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert md=="94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    built=[]
    for arm,seed in config:
        path=project_for(arm,seed)/"bot.wasm"
        built.append(((arm,seed),path,digest(path)))
    print("Built",len(built),"independent WASMs",flush=True)
    jobs=[(arm,seed,opp,mp,side,wasm) for (arm,seed),wasm,_ in built for mp in maps for opp in OPPS for side in "AB"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows=[]
        for row in pool.map(one,jobs):
            rows.append(row)
            if len(rows)%128==0:
                print(f"{len(rows)}/{len(jobs)} games",flush=True)
    def key(r):
        return tuple(r[k] for k in ("noise_seed","opponent","map","side"))
    base={key(r):r for r in rows if r["arm"]=="base"}
    result={}
    for arm in ARMS:
        if arm=="base":
            continue
        pairs=[(base[key(r)],r) for r in rows if r["arm"]==arm]
        result[arm]={"overall":summary(pairs),
                     "per_opponent":{opp:summary([(a,b) for a,b in pairs if a["opponent"]==opp]) for opp in OPPS}}
    report={"scope":"Exploratory 16-map heavy development screen; no holdout, no ladder inference.",
            "engine":ENGINE,"seeds":SEEDS,"map_digest":md,"changes":ARMS,
            "binaries":{f"{arm}-{seed}":d for (arm,seed),_,d in built},"results":result}
    target=Path(__file__).resolve().parent/"ABLATIONS.json"
    target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8",newline="\n")
    (OUT/"rows.json").write_text(json.dumps(rows,indent=2),encoding="utf8")
    print(json.dumps({arm:d["overall"] for arm,d in result.items()},indent=2),flush=True)

if __name__=="__main__":
    main()
