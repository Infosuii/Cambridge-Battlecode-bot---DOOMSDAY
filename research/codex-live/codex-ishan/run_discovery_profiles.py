"""Run the checked-in discovery analysis on one frozen split without writing history."""
import argparse
import json
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/"artifacts/codex-p0/discovery48"
ENGINE=ROOT/"artifacts/codex-p0/generator/research/agent2-neural/rl_workspace/tools/viz/v2_0_0.wasm"
PLAN=Path(__file__).resolve().parent/"DISCOVERY_SAMPLE.json"
sys.path.insert(0,str(ROOT/"tools/mapgen"))

def run(tool,args,summary=None):
    path=ROOT/"tools/ladder"/tool
    src=path.read_text(encoding="utf8")
    # The sparse base has no historical display-name lookup. The native roster
    # has the names; these scripts can retain the numeric draft IDs.
    if "CHAR = json.loads" in src:
        lines=src.splitlines(keepends=True)
        idx=next(i for i,line in enumerate(lines) if line.startswith("CHAR = json.loads"))
        lines[idx]="CHAR = {}\n"
        src="".join(lines)
    if summary:
        original="(ROOT / 'research/x3/losses48/summary_rows.json')"
        assert original in src
        src=src.replace(original,f"Path({str(summary)!r})",1)
    sys.argv=[str(path),*map(str,args)]
    exec(compile(src,str(path),"exec"),{"__file__":str(path),"__name__":"__main__"})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("partition",choices=("discovery","confirm"))
    p.add_argument("stage",choices=("prepare","finish"))
    a=p.parse_args()
    local=CACHE/a.partition
    rows=[m for m in json.loads(PLAN.read_bytes())["matches"] if m["partition"]==a.partition]
    for m in rows:
        for directory,suffix in (("summaries",".json"),("replays",".zip")):
            assert (local/directory/(m["matchId"]+suffix)).is_file()
    out=local/"analysis"
    out.mkdir(exist_ok=True)
    if a.stage=="prepare":
        (local/"matches.json").write_text(json.dumps(rows,ensure_ascii=False),encoding="utf8")
        import mapio
        mapio.engine_wasm=lambda:str(ENGINE)
        profile=out/"summary_rows.json"
        run("summary_profile.py",["--data",local,"--out",profile])
        # Clustering is fit only on discovery.
        if a.partition=="discovery":
            run("archetypes.py",["--out",out,"--k","2-3"],summary=profile)
        rep=local/"replays/rep"
        rep.mkdir(exist_ok=True)
        for m in rows:
            mid=m["matchId"]
            with ZipFile(local/"replays"/(mid+".zip")) as z:
                (rep/(mid+".repl26a")).write_bytes(z.read("replay.repl26a"))
        return

    profiles=local/"replays/profiles"
    profiles.mkdir(exist_ok=True)
    observed=set()
    for data in json.loads((out/"winner_profile.json").read_bytes()):
        assert "teams" in data,data
        mid=Path(data["id"]).stem
        observed.add(mid)
        (profiles/(mid+".json")).write_text(json.dumps(data),encoding="utf8")
    assert observed=={m["matchId"] for m in rows}
    run("loss_study.py",["--data",local,"--replays",local/"replays","--out",out,"--jobs",4])
    assert len(json.loads((out/"rows.json").read_bytes()))==len(rows)

if __name__=="__main__":
    main()
