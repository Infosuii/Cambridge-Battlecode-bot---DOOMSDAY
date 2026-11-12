"""Freeze new-source-interval discovery independently of old-source observations."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import sys

import ablate_dev as bench
from engine3_pool import CLI, HERE, read
from freeze_engine3_discovery import write


def main():
    output = bench.CACHE / "live111-discovery-20261105"
    output.mkdir()
    raw = output / "raw"
    raw.mkdir()
    spec = importlib.util.spec_from_file_location("losses_recent", bench.ROOT / "tools/ladder/losses_recent.py")
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.CLI = str(CLI)
    original, snapshots = collector.cli_json, []
    def capture(args, *more, **kwargs):
        result = original(args, *more, **kwargs)
        name = f"{len(snapshots):03d}-{args[0]}.json"
        write(raw / name, result)
        snapshots.append({"args": args, "path": name, "sha256": bench.digest(raw / name)})
        return result
    collector.cli_json = capture
    collector.download = lambda *args: None
    sys.argv = [str(spec.origin), "--hours", "48", "--min-rating", "2000", "--out", str(output / "inventory48"), "--replays", str(output / "unused-replays")]
    collector.main()
    ladder = read(output / "inventory48/ladder.json")
    assert "DOOMSDAY" in ladder
    census = {m["matchId"]: m for item in snapshots if item["args"][0] == "matches" for m in read(raw / item["path"])["matches"]}
    selected, wins = [], []
    for m in census.values():
        if m["status"] != "finished" or m["createdAt"] < "2026-11-05T17:46:00Z": continue
        ours = next(t for t in m["teams"] if t["name"] == "DOOMSDAY")
        rival = next(t for t in m["teams"] if t["name"] != "DOOMSDAY")
        if any(t["engineVersion"] != "3.0.0" for t in m["teams"]): continue
        if rival["name"] not in {"QS2isLaw", "0xDEADBEEF", "bentheboss"} and ladder.get(rival["name"], {}).get("rating", -1) <= ladder["DOOMSDAY"]["rating"]: continue
        row = {"matchId": m["matchId"], "group": m.get("groupId") or m["matchId"], "createdAt": m["createdAt"], "map": m["map"], "side": ours["side"],
               "opponent": rival["name"], "result": ours["result"], "kind": m["kind"], "our_draft": ours["draftPicks"], "their_draft": rival["draftPicks"]}
        if ours["result"] == "loss":
            row["partition"] = "confirm" if int(sha256(row["group"].encode()).hexdigest(), 16) % 3 == 0 else "discovery"
            selected.append(row)
        elif ours["result"] == "win": wins.append(row)
    wins = sorted(wins, key=lambda r: sha256(r["matchId"].encode()).hexdigest())[:18]
    for r in wins: r["partition"] = "control"
    rows = sorted(selected, key=lambda r: r["createdAt"]) + wins
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "source": "INFERRED111 interval after17:46; no historic compiled identity in listings", "our_ladder": ladder["DOOMSDAY"],
              "snapshots": snapshots, "counts": dict(Counter(r["partition"] for r in rows)), "matches": rows}
    write(HERE / "LIVE111_DISCOVERY_SPLIT.json", result)
    print({"counts": result["counts"], "our_ladder": result["our_ladder"]}, flush=True)


if __name__ == "__main__": main()
