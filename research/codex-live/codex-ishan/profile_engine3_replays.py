"""Profile a frozen engine-3 replay partition and cross-check native death counts."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import OUT, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("partition", choices=("discovery", "confirm", "control"))
    parser.add_argument("--recount", action="store_true")
    parser.add_argument("--prefix", default="LIVE109")
    parser.add_argument("--data-dir", type=Path, default=OUT)
    args = parser.parse_args()
    prefix, data_dir = args.prefix, args.data_dir
    if args.partition == "confirm":
        assert (HERE / f"{prefix}_REPLAY_DISCOVERY.json").exists()
    rows = [r for r in read(HERE / f"{prefix}_DISCOVERY_REPLAY_SAMPLE.json")["matches"] if r["partition"] == args.partition]
    assert rows and all((data_dir / "replays" / (r["matchId"] + ".zip")).exists() for r in rows)
    output = data_dir / f"analysis-{args.partition}"
    if output.exists() and not args.recount:
        print("Existing analysis retained; use --recount to validate completed outputs.", flush=True)
        return
    output.mkdir(exist_ok=args.recount)
    extracts = output / "replays"
    extracts.mkdir(exist_ok=args.recount)
    files = []
    archive_hashes = {}
    for row in rows:
        mid = row["matchId"]
        archive = data_dir / "replays" / (mid + ".zip")
        destination = extracts / (mid + ".repl26a")
        if args.recount:
            with ZipFile(archive) as bundle:
                assert destination.read_bytes() == bundle.read("replay.repl26a")
        else:
            with ZipFile(archive) as bundle:
                with destination.open("xb") as out:
                    out.write(bundle.read("replay.repl26a"))
        files.append(destination)
        archive_hashes[mid] = bench.digest(archive)
    env = {**os.environ, "NFS_REPLAY_ENGINE": "3.0.0", "NFS_FUNNEL_UNTIL": "300"}
    def run_tool(job):
        tool, leading = job
        print(f"Starting {tool}: {len(files)} {args.partition} replays", flush=True)
        with (output / (tool + ".log")).open("wb") as log:
            subprocess.run(["node", bench.ROOT / "tools/replay" / (tool + ".mjs"), *leading,
                            output / (tool + ".json"), *files], cwd=bench.ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    if not args.recount:
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(run_tool, (("winner_profile", []), ("death_context", ["600"]), ("capture_pressure", []))))
    assert all((data_dir / "summaries" / (r["matchId"] + ".json")).exists() for r in rows)
    deaths = {r["id"]: r["deaths"] for r in read(output / "death_context.json")}
    winners = {Path(r["id"]).stem: r for r in read(output / "winner_profile.json")}
    captures = {r["id"]: r for r in read(output / "capture_pressure.json")}
    measured = []
    for row in rows:
        mid = row["matchId"]
        native = read(data_dir / "summaries" / (mid + ".json"))
        rec = {**row}
        for name, team in (("ours", int(row["side"].upper() == "B")), ("rival", int(row["side"].upper() != "B"))):
            tag = "team" + "AB"[team]
            entries = [entry for event in native["events"] if event["kind"] == "death" and event["owner"]["team"] == tag for entry in event["entries"] if entry["timestamp"]["round"] <= 600]
            dead = [d for d in deaths[mid] if d["team"] == team]
            assert len(dead) == len(entries), (mid, team, len(dead), len(entries))
            snap = winners[mid]["teams"][team]
            cap = [c for c in captures[mid]["captures"] if c["team"] == team and c["round"] <= 300 and c["gold"] > 0]
            rec[name] = {"deaths600": len(dead), "no_pvp_basic_or_cast_deaths600": sum(d["pvp_attacks"] == 0 and d["casts"] == 0 for d in dead),
                         "deaths_by_type": dict(Counter(d["type"] for d in dead)), "grouped_early": snap["grouped"][0],
                         "workers_together": snap["workers_together"], "first_contact": snap["first_contact"], "route": snap["route"][:4],
                         "inferred_capture_gold300": sum(sum(c["gain"] for c in x["capturers"]) for x in cap),
                         "inferred_capture_count300": len(cap), "inferred_clear_to_capture_delays": [x["round"] - x["clear_end"] for x in cap if {h["team"] for h in x["hitters"]} == {team}]}
        measured.append(rec)
    report = {"partition": args.partition, "n": len(rows), "native_death_counts_match": True,
              "archive_sha256": archive_hashes, "tool_output_sha256": {tool: bench.digest(output / (tool + ".json")) for tool in ("winner_profile", "death_context", "capture_pressure")},
              "rows": measured}
    write(HERE / f"{prefix}_REPLAY_{args.partition.upper()}.json", report)
    print({"partition": args.partition, "n": len(rows), "native_death_counts_match": True}, flush=True)


if __name__ == "__main__":
    main()
