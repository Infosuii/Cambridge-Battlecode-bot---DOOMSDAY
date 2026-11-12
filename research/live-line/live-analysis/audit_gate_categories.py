"""Recompute both arms of a finished stage with verified runtime map categories."""
import argparse
from collections import defaultdict
import json

import ablate_dev as bench
from engine3_pool import HERE, read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("L1", "L2"))
    stage = parser.parse_args().stage
    source = read(HERE / f"ENGINE3_RETRY_{stage}.json")
    rows = read(bench.CACHE / f"engine3-retry-{stage.lower()}" / "rows.json")
    cache = read(HERE / f"ENGINE3_CATEGORIES_{'DEV' if stage == 'L1' else 'SELECT'}.json")
    grouped = defaultdict(list)
    for base, candidate in zip(rows[::2], rows[1::2], strict=True):
        label = cache["maps"][base["map"]]
        assert base["map_hash"] == candidate["map_hash"] == label["map_hash"]
        grouped[label["category"]].append((base, candidate))
    categories = {name: bench.summary(pairs) for name, pairs in sorted(grouped.items())}
    passed = source["pass"] and all(r["delta_pp"] >= -10 for r in categories.values())
    result = {"stage": stage, "candidate_release": source["candidate_release"],
              "rules_sha256": cache["rules_sha256"], "original_pass": source["pass"],
              "n_pairs": len(rows) // 2, "categories": categories, "pass": passed}
    with (HERE / f"ENGINE3_RETRY_{stage}_CATEGORY_AUDIT.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
