"""Capture the fixed new-source cohort, respecting platform backoff."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import subprocess
import sys

import ablate_dev as bench
from engine3_pool import CLI, ENGINE, HERE, read
from freeze_engine3_discovery import write

OUT = bench.CACHE / "live111-discovery-20261105"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("summaries", "replays"))
    args = parser.parse_args()
    sample = read(HERE / "LIVE111_DISCOVERY_SPLIT.json")
    spec = importlib.util.spec_from_file_location("losses_recent", bench.ROOT / "tools/ladder/losses_recent.py")
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.CLI = str(CLI)
    directory = OUT / args.mode
    directory.mkdir(exist_ok=True)
    def fetch(row):
        mid = row["matchId"]
        command = ["matches", "summary", "--json", mid] if args.mode == "summaries" else ["matches", "download", mid]
        path = directory / (mid + (".json" if args.mode == "summaries" else ".zip"))
        assert collector.fetch(command, path), mid
        if args.mode == "summaries":
            doc = read(path)
            assert (doc["match"]["engineVersion"], doc["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
            assert doc["diagnostics"]["detailedCaptureComplete"]
        return mid
    with ThreadPoolExecutor(max_workers=2) as pool:
        for n, mid in enumerate(pool.map(fetch, sample["matches"]), 1):
            if n % 20 == 0 or n == len(sample["matches"]): print(f"{args.mode} {n}/{len(sample['matches'])}", flush=True)
    if args.mode == "summaries":
        for part in ("discovery", "control", "confirm"):
            with (OUT / (part + "-native.log")).open("wb") as log:
                subprocess.run([sys.executable, HERE / "profile_engine3_discovery.py", part, "--prefix", "LIVE111", "--data-dir", OUT], cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            result = read(HERE / f"LIVE111_NATIVE_{part.upper()}.json")
            print({"partition": part, "n": result["n"], "groups": result["groups"], "patterns": result["patterns"]}, flush=True)


if __name__ == "__main__": main()
