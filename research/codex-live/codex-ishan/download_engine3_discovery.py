"""Fetch frozen current-engine cases; selection is fixed before replay metrics."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib.util
import json

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, read
from freeze_engine3_discovery import OUT, RIVALS, write


def prepare():
    sample = read(HERE / "LIVE109_DISCOVERY_SPLIT.json")
    actual = {m["matchId"]: m["kind"] for item in sample["snapshots"] if item["args"][0] == "matches"
              for m in read(OUT / "raw" / item["path"])["matches"]}
    audit_path = HERE / "LIVE109_DISCOVERY_METADATA_AUDIT.json"
    if not audit_path.exists():
        corrections = {r["matchId"]: actual[r["matchId"]] for r in sample["matches"] if r["kind"] != actual[r["matchId"]]}
        write(audit_path, {"reason": "A ranked match can also have groupId. Use the explicit kind field from saved raw listings, not presence of groupId. Frozen split and match membership unchanged.",
                           "n_corrected_kind_labels": len(corrections), "corrections": corrections,
                           "actual_kind_counts": dict(Counter(actual[r["matchId"]] for r in sample["matches"]))})
    path = HERE / "LIVE109_DISCOVERY_REPLAY_SAMPLE.json"
    if not path.exists():
        groups = defaultdict(list)
        for row in sample["matches"]:
            groups[row["partition"], row["opponent"]].append(row)
        chosen = []
        for (partition, opponent), rows in sorted(groups.items()):
            used = set()
            limit = (6 if opponent in RIVALS else 2) if partition != "control" else 1
            for row in sorted(rows, key=lambda r: sha256(r["matchId"].encode()).hexdigest()):
                key = row["map"], row["side"], tuple(row["our_draft"]), tuple(row["their_draft"])
                if key in used:
                    continue
                used.add(key)
                chosen.append({**row, "kind": actual[row["matchId"]]})
                if len(used) == limit:
                    break
        write(path, {"protocol": "Within each frozen partition and opponent, stable match-ID hash order; one representative per observed map/side/draft tuple, at most6 for requested rivals or2 for others, one per control opponent. Metrics not read before freezing. Confirmation remains unopened until patterns are frozen.",
                     "counts": dict(Counter(r["partition"] for r in chosen)), "matches": chosen})
    return sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("summaries", "replays"))
    parser.add_argument("--confirmation", action="store_true")
    args = parser.parse_args()
    assert bench.digest(CLI) == CLI_HASH
    sample = prepare()
    spec = importlib.util.spec_from_file_location("losses_recent", bench.ROOT / "tools/ladder/losses_recent.py")
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.CLI = str(CLI)
    rows = sample["matches"] if args.mode == "summaries" else read(HERE / "LIVE109_DISCOVERY_REPLAY_SAMPLE.json")["matches"]
    if args.mode == "replays" and not args.confirmation:
        rows = [r for r in rows if r["partition"] != "confirm"]
    directory = OUT / args.mode
    directory.mkdir(exist_ok=True)

    def fetch(row):
        mid = row["matchId"]
        suffix = ".json" if args.mode == "summaries" else ".zip"
        command = ["matches", "summary", "--json", mid] if args.mode == "summaries" else ["matches", "download", mid]
        path = directory / (mid + suffix)
        assert collector.fetch(command, path), mid
        if args.mode == "summaries":
            doc = read(path)
            assert (doc["match"]["engineVersion"], doc["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
            assert doc["diagnostics"]["detailedCaptureComplete"]
        return mid

    with ThreadPoolExecutor(max_workers=2) as pool:
        for index, mid in enumerate(pool.map(fetch, rows), 1):
            if index % 20 == 0 or index == len(rows):
                print(f"{args.mode} {index}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
