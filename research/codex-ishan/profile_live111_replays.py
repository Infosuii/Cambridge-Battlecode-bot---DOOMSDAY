"""Profile every previously frozen new-source replay without outcome reselection."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write


def run(partition):
    subprocess.run([sys.executable, HERE / "profile_engine3_replays.py", partition,
                    "--prefix", "LIVE111", "--data-dir", bench.CACHE / "live111-discovery-20261105"],
                   cwd=bench.ROOT, check=True)


if __name__ == "__main__":
    split = read(HERE / "LIVE111_DISCOVERY_SPLIT.json")
    write(HERE / "LIVE111_DISCOVERY_REPLAY_SAMPLE.json", {
        "selection": "All79 already frozen EXP180 matches; no replay-level reselection",
        "split_sha256": bench.digest(HERE / "LIVE111_DISCOVERY_SPLIT.json"), "matches": split["matches"]})
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, ("discovery", "control")))
    run("confirm")
