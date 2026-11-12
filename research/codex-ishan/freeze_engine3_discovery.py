"""Inventory fresh losses with the established collector, freeze the new-engine cohort."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, HERE, read

OUT = bench.CACHE / "engine3-discovery-20261105"
OUR = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
RIVALS = {"QS2isLaw", "0xDEADBEEF", "bentheboss"}


def write(path, data):
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(data, out, indent=2, ensure_ascii=False)
        out.write("\n")


def main():
    assert bench.digest(CLI) == CLI_HASH
    OUT.mkdir()
    raw = OUT / "raw"
    raw.mkdir()
    spec = importlib.util.spec_from_file_location("losses_recent", bench.ROOT / "tools/ladder/losses_recent.py")
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.CLI = str(CLI)
    original = collector.cli_json
    snapshots = []

    def capture(args, *more, **kwargs):
        result = original(args, *more, **kwargs)
        filename = f"{len(snapshots):03d}-{args[0]}.json"
        write(raw / filename, result)
        snapshots.append({"args": args, "path": filename, "sha256": bench.digest(raw / filename)})
        return result

    collector.cli_json = capture
    collector.download = lambda *args: None
    sys.argv = [str(spec.origin), "--hours", "48", "--min-rating", "2000", "--out",
                str((OUT / "inventory48").relative_to(bench.ROOT)), "--replays",
                str((OUT / "unused-replays").relative_to(bench.ROOT))]
    collector.main()
    ladder = read(OUT / "inventory48/ladder.json")
    our_rating = ladder["DOOMSDAY"]["rating"]
    census = {m["matchId"]: m for item in snapshots if item["args"][0] == "matches"
              for m in read(raw / item["path"])["matches"]}
    cohort, controls = [], []
    for match in sorted(census.values(), key=lambda m: m["createdAt"]):
        teams = {t["teamId"]: t for t in match["teams"]}
        if match["status"] != "finished" or OUR not in teams or match["createdAt"] < "2026-11-05T00:31:00Z":
            continue
        ours = teams[OUR]
        rival = next(t for ident, t in teams.items() if ident != OUR)
        if any(t["engineVersion"] != "3.0.0" for t in teams.values()):
            continue
        if rival["name"] not in RIVALS and ladder.get(rival["name"], {}).get("rating", -1) <= our_rating:
            continue
        row = {"matchId": match["matchId"], "createdAt": match["createdAt"], "map": match["map"],
               "side": ours["side"], "opponent": rival["name"], "result": ours["result"],
               "group": match.get("groupId") or match["matchId"], "our_draft": ours.get("draftPicks"),
               "their_draft": rival.get("draftPicks"), "kind": match["kind"]}
        if row["result"] == "loss":
            cohort.append(row)
        elif row["result"] == "win":
            controls.append(row)
    controls = sorted(controls, key=lambda r: sha256(r["matchId"].encode()).hexdigest())[:18]
    for row in cohort:
        row["partition"] = "confirm" if int(sha256(row["group"].encode()).hexdigest(), 16) % 3 == 0 else "discovery"
    for row in controls:
        row["partition"] = "control"
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "engine": "3.0.0",
              "protocol": "All current-engine losses to current above-us/rivals since inferred v108 source interval; whole-group SHA split, wins hash-selected before metrics. No causal or strength claim.",
              "source_identity": "INFERRED interval only; listings do not expose our compiled source hash",
              "snapshots": snapshots, "our_ladder": ladder["DOOMSDAY"],
              "counts": dict(Counter(row["partition"] for row in cohort + controls)),
              "opponents": dict(Counter(row["opponent"] for row in cohort)), "matches": cohort + controls}
    write(HERE / "LIVE109_DISCOVERY_SPLIT.json", result)
    print(json.dumps({k: result[k] for k in ("created_utc", "counts", "opponents", "our_ladder")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
