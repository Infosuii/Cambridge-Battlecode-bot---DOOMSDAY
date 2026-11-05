"""Trace the first remaining R1 event on the exact rejected cache candidate."""
import os
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from profile_live109_target import main
from profile_live111_first import exact_build,instrument

REFERENCE="live111-draft-cache-release-on"


def prepare(src,enabled,case): instrument(src,enabled,case,reference_name=REFERENCE)


if __name__ == "__main__":
    original=read(HERE/"LIVE111_DRAFT_CACHE_RELEASE_LARGE.json")
    root=bench.CACHE/"live111-draft-cache-release"
    source=SDK_ROOT/"bots"/REFERENCE/"src"
    release=original["builds"]["on"]["sha256"]
    assert bench.digest(source.parent/"bot.wasm")==release
    identity={"kind":"Derived rejected cache candidate;not a new platform submission","platform_basis":111,"parent_manifest":"LIVE111_SOURCE_VERIFIED.json",
              "wasm_sha256":release,"source_file_hashes":{p.relative_to(source).as_posix():bench.digest(p) for p in source.rglob('*') if p.is_file()}}
    write(HERE/f"{REFERENCE.upper()}_SOURCE_VERIFIED.json",identity)
    events=[]
    for _,r in original["pairs"]:
        native=read(root/r["opponent"]/f"{r['map']}-{r['side']}-draft-cache-release/native.json")
        for e in native["events"]:
            if e["kind"]!="fuelExhausted" or e["owner"].get("team")!="team"+r["side"]:continue
            for entry in e["entries"]:
                if entry["timestamp"]["round"]==1:events.append({**r,"actor":e["owner"]["id"],"champion":e["owner"]["name"]})
    eligible=[r for r in events if r["side"]=="A"]
    row=min(eligible,key=lambda r:(r["map_hash"],r["actor"],r["opponent"]))
    directory=bench.CACHE/"live111-cache-first-baseline";directory.mkdir()
    old=root/row["opponent"]/f"{row['map']}-A-draft-cache-release"
    (archive,)=old.glob('*.repl26a');replay=directory/"raw.repl26a"
    with ZipFile(archive) as z:
        with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
    turn=directory/"turn.json"
    subprocess.run(["node",HERE/"trace_turn.mjs",replay,"1","0",str(row["actor"]),turn],cwd=bench.ROOT,env={**os.environ,"NFS_REPLAY_ENGINE":"3.0.0"},check=True)
    view=read(turn)
    case={"stage":"cachefirst111","round":1,"type":view["observation"]["actor"]["type"],**{k:row[k] for k in ("map","map_hash","side","opponent","actor","champion")},
          "traces":{"base":{"path":turn.relative_to(bench.ROOT).as_posix(),"sha256":bench.digest(turn)}}}
    write(HERE/"LIVE111_CACHE_REMAINING_R1_PLAN.json",{"selection":"All remaining independent-development candidateR1events,first stableSHA sideA actor/opponent","events":events,"case":case,"derived_release":release})
    main(label="cachefirst111",cases=[case],prepare_fn=prepare,build_fn=exact_build,expected_hash=release,project_prefix="live111-target")
