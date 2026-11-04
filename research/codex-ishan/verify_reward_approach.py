"""Verify the three registered approach moves and their exact camp payouts."""
import json

from analyze_prewalk_payout import payouts
from verify_prewalk_clear import HERE, bench, read, read_turn, actions, clears

OUT = bench.CACHE / "reward-approach-behavior/games"


def main():
    result = read(HERE / "REWARD_APPROACH_BEHAVIOR.json")
    rows = result["rows"]
    probes = read(HERE / "REWARD_APPROACH_PROBE.json")["rows"]
    details, matches = [], []
    errors = draft_changes = 0
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for p, (b, c) in zip(probes, pairs, strict=True):
        assert all(p[k] == b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        key = f"0-{b['opponent']}-{b['map']}-{b['side']}"
        bdir, cdir = (OUT / f"{a}-{key}" for a in ("base", "window"))
        old, new = (read(folder / "native.json") for folder in (bdir, cdir))
        draft_changes += old["roster"]["draft"] != new["roster"]["draft"]
        errors += any(any(d["diagnostics"]["botFaults"].values()) or d["diagnostics"]["codes"] for d in (old, new))
        if not p["opportunities"]:
            continue
        team = "team" + b["side"]
        actors = sorted(ch["id"] for ch in new["roster"]["champions"] if ch["team"] == team)
        old_clear, new_clear = (clears(d, team) for d in (old, new))
        for rnd, slot, _, x, y in p["opportunities"]:
            actor = actors[slot]
            previous, current = (read_turn(folder, rnd, b["side"], actor) for folder in (bdir, cdir))
            info = {"map": b["map"], "opponent": b["opponent"], "side": b["side"], "round": rnd, "actor": actor,
                    "same_observation": bool(previous and current and previous["observation"] == current["observation"]),
                    "old_turn": previous, "new_turn": current, "payout": None}
            details.append(info)
            if not info["same_observation"]:
                continue
            old_action, new_action = actions(previous), actions(current)
            target = {"x": x, "y": y}
            if (not old_action or not new_action or old_action[0]["kind"] != 4 or new_action[0]["kind"] != 4 or
                    old_action[0]["to"] == target or new_action[0]["to"] != target):
                continue
            for who, group, clear_round, _, _ in new_clear:
                if who != actor or not rnd <= clear_round <= rnd + 3:
                    continue
                if not any(g == group and rnd <= r <= rnd + 5 for _, g, r, _, _ in old_clear):
                    continue
                bp, cp = (payouts(d, team, group, rnd, min(rnd + 20, 300)) for d in (old, new))
                if bp and cp and cp[0][0] < bp[0][0]:
                    info["payout"] = {"group": group, "base": bp[0][0], "candidate": cp[0][0]}
                    matches.append(info)
                    break
    maps = sorted({r["map"] for r in matches})
    opponents = sorted({r["opponent"] for r in matches})
    delta = result["delta"]
    passed = (len(pairs) == 64 and not errors and not draft_changes and delta["camp_gems"] >= 0 and
              delta["inferred_camp_gold"] >= 0 and len(maps) >= 2 and len(opponents) == 2)
    report = {"sha256": result["binaries"]["release"], "n": len(pairs), "errors": errors, "draft_changes": draft_changes,
              "delta": delta, "maps": maps, "opponents": opponents, "matches": len(matches), "pass": passed}
    with (HERE / "REWARD_APPROACH_EXACT.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "details": details}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
