"""Test the isolated travel address optimization on original v92."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from shutil import copytree

from large_roster_stress import HERE, bench, native_fuel, read
from pg_dash_followup import read_turn, stress_cases
from pg_travel_scan import apply_scan

OUT = bench.CACHE / "v92-travel-scan-stress"


def prepare(src, enabled):
    copytree(bench.ROOT / "bots/v92/src", src)
    apply_scan(src, enabled)


def game(row):
    return OUT / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}"


def identity(event):
    return event["timestamp"]["round"], event["owner"]["id"]


def ordinary_actions(turn):
    return [a for a in turn["executed_actions"] if a["kind"] not in (3, 26)]


def verify_pair(pair, round1_only=False):
    b, c = pair
    assert all(b[k] == c[k] for k in ("opponent", "map_hash", "engine_seed", "side"))
    bd, cd = (read(game(r) / "native.json") for r in pair)
    draft_equal = bd["roster"]["draft"] == cd["roster"]["draft"]
    errors = any(any(d["diagnostics"]["botFaults"].values()) or d["diagnostics"]["codes"] for d in (bd, cd))
    if not draft_equal or errors:
        return {"draft_equal": draft_equal, "error": bool(errors), "preserved": [], "removed_round1": []}
    previous, current = ({identity(e) for e in native_fuel(r, OUT)} for r in pair)
    removed_round1 = sorted(actor for rnd, actor in previous - current if rnd == 1)
    preserved = []
    for rnd, actor in sorted(previous - current):
        if round1_only and rnd != 1:
            continue
        old, new = (read_turn(game(r), rnd, r["side"], actor) for r in pair)
        if old and new and old["observation"] == new["observation"]:
            actions = ordinary_actions(old)
            after = ordinary_actions(new)
            if (actions and actions == after[:len(actions)]) or (round1_only and not actions and after):
                preserved.append({"round": rnd, "actor": actor, "actions": actions})
    return {"draft_equal": draft_equal, "error": bool(errors), "preserved": preserved, "removed_round1": removed_round1}


def verify(wasm, *, round1_only=False, field_pack=False):
    global OUT
    if field_pack:
        OUT = bench.CACHE / "v92-field-pack-stress"
    elif round1_only:
        OUT = bench.CACHE / "v92-field-order-stress"
    base = bench.CACHE / bench.OPPS["v92"][0]
    assert bench.digest(base) == bench.OPPS["v92"][1]
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    jobs = [(arm, 0, o, m, s, binary) for o, m, s in stress_cases()
            for arm, binary in (("base", base), ("candidate", wasm))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(bench.one, jobs))
        pairs = list(zip(rows[::2], rows[1::2], strict=True))
        checks = list(pool.map(lambda p: verify_pair(p, round1_only), pairs))
    fuel = [sum(r["fuel_outs"] for r in arm) for arm in (rows[::2], rows[1::2])]
    round1 = [sum(r["round1_fuel_outs"] for r in arm) for arm in (rows[::2], rows[1::2])]
    increases = sum(c["fuel_outs"] > b["fuel_outs"] or c["round1_fuel_outs"] > b["round1_fuel_outs"] for b, c in pairs)
    drafts = sum(not k["draft_equal"] for k in checks)
    errors = sum(k["error"] for k in checks)
    preserved = sum(len(k["preserved"]) for k in checks)
    removed_round1 = sum(len(k["removed_round1"]) for k in checks)
    passed = len(pairs) == 39 and fuel[1] < fuel[0] and not any((increases, drafts, errors))
    passed = passed and (removed_round1 > 0 if field_pack else preserved > 0)
    if round1_only:
        passed = passed and round1[1] < round1[0]
    report = {"sha256": bench.digest(wasm), "engine": bench.ENGINE, "n": len(pairs), "fuel": fuel,
              "round1": round1, "increased": increases, "drafts_changed": drafts, "errors": errors,
              "preserved": preserved, "removed_round1": removed_round1, "pass": passed}
    name = "V92_FIELD_PACK_EXACT.json" if field_pack else (
        "V92_FIELD_ORDER_EXACT.json" if round1_only else "V92_TRAVEL_SCAN_EXACT.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as f:
        json.dump({**report, "rows": rows, "checks": checks}, f, indent=2)
        f.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        verify(args.verify)
