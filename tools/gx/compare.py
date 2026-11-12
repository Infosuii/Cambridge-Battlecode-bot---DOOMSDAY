"""Compare paired GX gates; reject changed maps, sides, opponent bytes or engine version."""
import argparse
from collections import Counter
import json
from math import sqrt
from pathlib import Path


def load(path):
    result = json.loads(Path(path).read_text())
    rows = {(g["map"], g["side"]): g for g in result["per_game"]}
    if not rows or len(rows) != len(result["per_game"]) or len(rows) != result["games"]:
        raise ValueError(f"Missing or duplicate map/side: {path}")
    for field in ("candidate_sha256", "opponent_sha256", "engine", "engine_hash"):
        if len({r[field] for r in rows.values()}) != 1:
            raise ValueError(f"Mixed {field}: {path}")
    return rows


def pair(baseline, candidate):
    if baseline.keys() != candidate.keys():
        raise ValueError("Different map/side sets")
    metrics = Counter()
    for key, b in baseline.items():
        c = candidate[key]
        for field in ("map_sha256", "opponent_sha256", "engine", "engine_hash"):
            if b[field] != c[field]:
                raise ValueError(f"Changed {field}: {key}")
        bw, cw = (r["outcome"] == "team" + key[1] for r in (b, c))
        metrics.update(games=1, base=bw, wins=cw, gained=(cw and not bw), lost=(bw and not cw),
                       base_fuel_outs=b["fuel_outs"], fuel_outs=c["fuel_outs"], faults=c["faults"],
                       deaths=c["deaths"], base_deaths=b["deaths"], banked=c["banked"], base_banked=b["banked"],
                       collected=c["collected"], base_collected=b["collected"])
    return metrics


def summarise(m):
    g, l, n = m["gained"], m["lost"], m["games"]
    return dict(m, delta=g-l, z=round((g-l)/sqrt(g+l), 4) if g+l else 0.0,
                deaths_per_game=round(m["deaths"]/n, 4),
                base_deaths_per_game=round(m["base_deaths"]/n, 4),
                banked_per_game=round(m["banked"]/n, 4),
                base_banked_per_game=round(m["base_banked"]/n, 4))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--pair", nargs=3, action="append", metavar=("OPPONENT", "BASELINE", "CANDIDATE"), required=True)
    args = cli.parse_args()
    cells, total, hashes = {}, Counter(), set()
    for opponent, base_path, candidate_path in args.pair:
        if opponent in cells:
            cli.error(f"Duplicate opponent label: {opponent}")
        b, c = load(base_path), load(candidate_path)
        hashes.add(next(iter(c.values()))["candidate_sha256"])
        metrics = pair(b, c)
        cells[opponent] = summarise(metrics)
        total.update(metrics)
    if len(hashes) != 1:
        cli.error("Candidate bytes changed between opponent runs")
    report = summarise(total)
    print(json.dumps(dict(candidate_sha256=hashes.pop(), opponents=cells, total=report,
        pool_pass=(set(cells) == {"v92", "v86h", "x1bru"} and all(
            c["games"] == 172 and c["delta"] >= -3 for c in cells.values()
        ) and report["delta"] >= 10 and report["z"] >= 1.5 and report["faults"] == 0
        and 10*report["fuel_outs"] <= 11*report["base_fuel_outs"])), indent=2))


if __name__ == "__main__":
    main()
