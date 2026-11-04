"""Check the original camp-walk opportunities against both exact releases."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json

from large_roster_stress import HERE, bench, read
from pg_dash_followup import read_turn

OUT = bench.CACHE / "prewalk-clear-behavior/games"


def clears(doc, team):
    return [(event["owner"]["id"], e["target"]["id"], e["timestamp"]["round"], e["x"], e["y"])
            for event in doc["events"] if event["kind"] == "campClear" and event["owner"]["team"] == team
            for e in event["entries"]]


def actions(turn):
    return [action for action in turn["executed_actions"] if action["kind"] in (4, 5, 6)]


def verify_cell(job):
    probe, base, candidate = job
    key = f"0-{base['opponent']}-{base['map']}-{base['side']}"
    base_dir, new_dir = (OUT / f"{arm}-{key}" for arm in ("base", "window"))
    old, new = (read(p / "native.json") for p in (base_dir, new_dir))
    same_draft = old["roster"]["draft"] == new["roster"]["draft"]
    error = any(any(d["diagnostics"]["botFaults"].values()) or d["diagnostics"]["codes"] for d in (old, new))
    matched = []
    if not same_draft or error or not probe["opportunities"]:
        return {"same_draft": same_draft, "error": bool(error), "matched": matched}
    team = "team" + base["side"]
    actors = sorted(c["id"] for c in new["roster"]["champions"] if c["team"] == team)
    old_clears, new_clears = clears(old, team), clears(new, team)
    for rnd, slot, _, _ in probe["opportunities"]:
        actor = actors[slot]
        events = [e for e in new_clears if e[0] == actor and e[2] == rnd and
                  not any(b[1] == e[1] and b[2] == rnd for b in old_clears)]
        if not events:
            continue
        b, c = (read_turn(directory, rnd, base["side"], actor) for directory in (base_dir, new_dir))
        if not b or not c or b["observation"] != c["observation"]:
            continue
        before, after = actions(b), actions(c)
        if not before or not after or before[0]["kind"] != 4 or after[0]["kind"] != 6:
            continue
        for _, group, _, x, y in events:
            if after[0]["to"] != {"x": x, "y": y}:
                continue
            later = min((r for _, g, r, _, _ in old_clears if g == group and r > rnd), default=None)
            matched.append({"map": base["map"], "opponent": base["opponent"], "side": base["side"],
                            "group": group, "round": rnd, "base_later_clear": later,
                            "base": b, "candidate": c})
    return {"same_draft": same_draft, "error": bool(error), "matched": matched}


def main():
    probes = read(HERE / "CAST_BEFORE_WALK_PROBE.json")["rows"]
    behavior = read(HERE / "PREWALK_CLEAR_BEHAVIOR.json")
    rows = behavior["rows"]
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    key = ("map", "map_hash", "opponent", "side", "engine_seed")
    assert all(tuple(p[k] for k in key) == tuple(b[k] for k in key) == tuple(c[k] for k in key)
               for p, (b, c) in zip(probes, pairs, strict=True))
    with ThreadPoolExecutor(max_workers=5) as pool:
        checks = list(pool.map(verify_cell, ((p, b, c) for p, (b, c) in zip(probes, pairs, strict=True))))
    matches = [m for r in checks for m in r["matched"]]
    errors = sum(r["error"] for r in checks)
    drafts_changed = sum(not r["same_draft"] for r in checks)
    by_opponent = defaultdict(int)
    for b, c in pairs:
        by_opponent[b["opponent"]] += c["camp_gems"] - b["camp_gems"]
    maps = sorted({r["map"] for r in matches})
    opponents = sorted({r["opponent"] for r in matches})
    passed = (len(pairs) == 64 and not errors and not drafts_changed and
              behavior["delta"]["inferred_camp_gold"] >= 0 and all(v > 0 for v in by_opponent.values()) and
              len(maps) >= 2 and len(opponents) == 2)
    result = {"sha256": behavior["binaries"]["release"], "n": len(pairs), "errors": errors,
              "drafts_changed": drafts_changed, "delta": behavior["delta"], "camp_gems_by_opponent": by_opponent,
              "matched_earlier_clears": len(matches), "maps": maps, "opponents": opponents, "pass": passed}
    with (HERE / "PREWALK_CLEAR_EXACT_CLEARS.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump({**result, "matched": matches}, f, indent=2)
        f.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
