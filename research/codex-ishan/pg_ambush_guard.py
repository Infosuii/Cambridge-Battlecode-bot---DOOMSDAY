"""Guard full re-observation after a successful counter-ambush move."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from pg_dash_camps import prepare as prepare_dash, read
from pg_tail_guard import frozen_cases
from qualify_local import partition
from trace_pg_dash_turns import CASES

HERE = Path(__file__).resolve().parent


def prepare(src, enabled):
    prepare_dash(src, enabled, True, False)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_AMBUSH_GUARD {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", ((
        "        // We moved (into the attacker's bush, or away from it): look again before deciding.\n        w.update(round);",
        """        // We moved (into the attacker's bush, or away from it): look again before deciding.
#if CODEX_PG_AMBUSH_GUARD
        // Keep the defensive move and refresh at the start of the next turn when another observation is unaffordable.
        if (!rb::fits(rb::kReserve.observe, rb::kTailReserve)) return;
#endif
        w.update(round);"""),))


def verify(wasm):
    _, controls, exact_affected = frozen_cases()
    base = exact_affected + [e for e, _ in controls]
    assert len(exact_affected) == 2
    maps = {p.stem: p for p in partition("dev")}
    for opponent in {r["opponent"] for r in base}:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = bench.CACHE / "pg-ambush-exact-dev"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = [("exact", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in base]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(bench.one, jobs))
    for b, c in zip(base, rows, strict=True):
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    actions = []
    for champion, round_number, actor, opponent, map_name, side in CASES:
        game = bench.OUT / "games" / f"exact-0-{opponent}-{map_name}-{side}"
        replay = game / "raw.repl26a"
        output = game / "turn.json"
        with ZipFile(next(game.glob("*.repl26a"))) as archive:
            replay.write_bytes(archive.read("replay.repl26a"))
        with (game / "turn.log").open("wb") as log:
            rc = subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(round_number), str("AB".index(side)),
                                 str(actor), output], cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}).returncode
        prior = read(HERE / "pg-dash-turns" / f"{champion}-{round_number}.json")["executed_actions"][:2]
        current = read(output)["executed_actions"][:2] if rc == 0 else []
        assert [a["kind"] for a in prior] == [14, 4]
        actions.append({"champion": champion, "round": round_number, "same_ward_and_move": prior == current,
                        "baseline": prior, "candidate": current})
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    passed = (not errors and all(r["fuel_outs"] == 0 for r in rows) and
              all(a["same_ward_and_move"] for a in actions))
    result = {"wasm": bench.digest(wasm), "engine": bench.ENGINE, "n": len(rows), "pass": passed,
              "fault_or_code_cells": errors, "fuel": [sum(r["fuel_outs"] for r in group) for group in (base, rows)],
              "actions": actions, "base": base, "candidate": rows}
    with (HERE / "PG_AMBUSH_DEV.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k not in ("base", "candidate")}, flush=True)


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
