"""Collect on-policy cl1 actor rollouts (CLRL_ACT) from the official local engine into rlenv-2 shards.

Builds bots/claude-rlenv-1104 with CLRL_ACT=1 and the given actor.json (exported to exact float32 weights), as a
non-release build (logging lives in debug_block; the actor itself is charged as in release). Plays each game through
`cambc run-batch`, joins our team's CLA1 decision rows with the CLX1 executed rows and the match summary, and writes
one episode per game in the format of JOHNDOE tools/rl_learner_1104/FIRST_PPO_RUN.md (schema target13-cl1-nofarm-v1,
sampling complete). Integrity problems are never filtered away: a fuel-out, a replaced action, a repeated round, a
malformed row, a log cut or a missing summary make the episode PPO-ineligible and are reported.

usage (repo root):
  python tools/rl_env_1104/collect_policy.py --actor ACTOR.json --run-ns pol-smoke-01 \
      --maps maps/ladder-pool/00corners.map26a --opponent bots/v92 --sides A --jobs 1 [--rounds N]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect as K  # noqa: E402
import contract as C  # noqa: E402

ROOT, CLI = K.ROOT, K.CLI
SCHEMA = "target13-cl1-nofarm-v1"
NF, NA = C.LAYOUTS[10].nf, C.ACTION_SCHEMAS[SCHEMA].n
ENCODER_FILES = ("clrl_rec.h", "clrl_act.h", "clrl_actor.h")


def encoder_sha() -> str:
    h = hashlib.sha256()
    for f in ENCODER_FILES:
        with open(os.path.join(ROOT, "bots", "claude-rlenv-1104", "src", f), "rb") as fh:
            h.update(f.encode() + b"\0" + fh.read())
    return h.hexdigest()


def prepare_actor_bot(work: str, actor: str) -> tuple:
    src = os.path.join(ROOT, "bots", "claude-rlenv-1104", "src")
    dest = os.path.join(work, "bots", "clrl_act")
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, os.path.join(dest, "src"), ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
    subprocess.run([sys.executable, os.path.join(HERE, "export_actor.py"), actor,
                    os.path.join(dest, "src", "clrl_actor_weights.h")], check=True, capture_output=True)
    bh = os.path.join(dest, "src", "bot.h")
    with open(bh, encoding="utf-8") as f:
        text = f.read()
    with open(bh, "w", encoding="utf-8", newline="") as f:
        f.write("#define CLRL_ACT 1\n" + text)
    wasm = os.path.join(work, "clrl_act-debug.wasm")
    r = subprocess.run([CLI, "build", K.rel(dest), "--output", wasm], cwd=ROOT, capture_output=True, text=True,
                       timeout=900)
    if r.returncode or not os.path.exists(wasm):
        raise SystemExit("actor build failed: " + r.stdout[-3000:] + r.stderr[-3000:])
    return K.rel(dest), K.sha256(wasm)


def parse(stdout: str) -> tuple:
    """CLA1 decisions and CLX1 executed rows; malformed lines are counted, never silently dropped."""
    dec, exe, bad = [], {}, 0
    for line in stdout.splitlines():
        if line.startswith("CLA1 "):
            q = line.split(" ")
            try:
                if len(q) != 10:
                    raise ValueError
                x = struct.unpack(f"<{NF}h", base64.b64decode(q[9], validate=True))
                dec.append(dict(round=int(q[1]), slot=int(q[2]), body=int(q[3]), a=int(q[4]), logp=float(q[5]),
                                reset=int(q[6]), mask=int(q[7]), v92=int(q[8]), x=x))
            except Exception:
                bad += 1
        elif line.startswith("CLX1 "):
            q = line.split(" ")
            try:
                exe[(int(q[1]), int(q[3]))] = int(q[4])
            except Exception:
                bad += 1
    return dec, exe, bad


def episode(bundle: str, summary: dict | None, side: str, meta: dict) -> tuple:
    team_l, our = side.lower(), ("teamA" if side == "A" else "teamB")
    with zipfile.ZipFile(bundle) as z:
        raw = z.read(f"team-{team_l}.stdout")
    # The engine pads stdout with NUL bytes where a suspended turn lost output: treat them as line breaks, so an
    # intact row before the padding still parses and any split row is counted as malformed, never misread.
    out = raw.replace(bytes(1), b"\n").decode("utf-8", "replace")
    dec, exe, bad = parse(out)
    flags = dict(incomplete=False, fuel_failed=False, log_cut=False)
    problems = []
    if bad:
        flags["incomplete"] = True
        problems.append(f"{bad} malformed rows")
    if len(raw) >= K.LOG_LIMIT - 4096:
        flags["log_cut"] = True
        problems.append("stdout at log limit")
    if summary is None:
        flags["incomplete"] = True
        problems.append("no match summary (unfinished game)")
        status, end_round, outcome = "truncated", max([d["round"] for d in dec] or [0]), None
    else:
        m = summary["match"]
        status = "terminated"
        end_round = int(m["roundsStarted"]) if m.get("finalRoundPartial") else int(m["roundsCompleted"])
        outcome = m["outcome"]
        fuel_outs = sum(len(e["entries"]) for e in summary["events"]
                        if e["kind"] == "fuelExhausted" and e["owner"].get("team") == our)
        faults = summary.get("diagnostics", {}).get("botFaults", {}).get(our, 0)
        if fuel_outs:
            flags["fuel_failed"] = True
            problems.append(f"{fuel_outs} fuel-outs")
        if faults:
            flags["incomplete"] = True
            problems.append(f"{faults} bot faults")
        scores = {t["team"]: int(t["submittedGems"]) for t in summary["teams"]}
        theirs = "teamB" if our == "teamA" else "teamA"
        meta.update(map_hash=m["mapHash"], seed=m["seed"], engine_build_hash=m.get("engineBuildHash"),
                    rounds_completed=int(m["roundsCompleted"]), end_round=end_round,
                    final_scores=dict(ours=scores.get(our, 0), theirs=scores.get(theirs, 0)),
                    terminal_outcome=(1 if outcome == our else (-1 if outcome == theirs else 0)),
                    fuel_outs=fuel_outs, bot_faults=faults)
    dec.sort(key=lambda d: (d["body"], d["round"]))
    replaced = repeated = 0
    cols = {c: [] for c in C.required_columns(dict(hidden_size=0, stale_block=False, decision_index=True))}
    for i, d in enumerate(dec):
        last = i + 1 == len(dec) or dec[i + 1]["body"] != d["body"]
        first = i == 0 or dec[i - 1]["body"] != d["body"]
        if not first and dec[i - 1]["round"] == d["round"]:
            repeated += 1
        ex = exe.get((d["round"], d["body"]))
        if ex is None or ex != d["a"]:
            replaced += 1
        nxt = end_round if last else dec[i + 1]["round"]
        cols["x_fresh"] += d["x"]
        cols["has_stale"].append(0)
        cols["feat_round"].append(d["round"])
        cols["stale_round"].append(-1)
        cols["act_round"].append(d["round"])
        cols["body_id"].append(d["body"])
        cols["slot"].append(d["slot"])
        cols["mask"] += [(d["mask"] >> k) & 1 for k in range(NA)]
        cols["action"].append(d["a"])
        cols["teacher_action"].append(d["v92"])  # v92's own choice at the same point (diagnostic)
        cols["executed"].append(ex if ex is not None else -1)
        cols["logp"].append(d["logp"])
        cols["has_logp"].append(1)
        cols["weight"].append(1.0)
        cols["changed"].append(1 if first or dec[i - 1]["a"] != d["a"] else 0)
        cols["reset"].append(d["reset"])
        cols["reward"].append(0.0)  # the learner recomputes team-win/potential rewards from public scores
        cols["dt_rounds"].append(max(0, nxt - d["round"]))
        cols["terminated"].append(1 if last and status == "terminated" else 0)
        cols["truncated"].append(1 if last and status != "terminated" else 0)
        cols["boundary"].append(0)
        cols["bootstrap_valid"].append(0)
        cols["decision_index"].append(0 if first else cols["decision_index"][-1] + 1)
    if replaced:
        flags["incomplete"] = True
        problems.append(f"{replaced} decisions replaced or without an executed row")
    if repeated:
        flags["incomplete"] = True
        problems.append(f"{repeated} repeated same-round decisions")
    if not dec:
        flags["incomplete"] = True
        problems.append("no decisions")
    cols.pop("episode", None)
    eligible = status == "terminated" and not any(flags.values())
    meta.update(status=status, our_team=our, outcome=outcome, decisions=len(dec), problems=problems,
                reward_complete=eligible, ppo_eligible=eligible, **flags)
    return meta, cols, dec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--run-ns", required=True)
    ap.add_argument("--maps", nargs="+", required=True)
    ap.add_argument("--opponent", default="bots/v92")
    ap.add_argument("--sides", default="A")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--rounds", type=int)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", default=os.path.join("runs", "rl_env_1104"))
    a = ap.parse_args()

    run_dir = os.path.join(ROOT, a.out, a.run_ns)
    work = os.path.join(ROOT, "artifacts", "tmp", "rl_env_1104", a.run_ns)
    os.makedirs(work, exist_ok=True)
    bot, wasm_sha = prepare_actor_bot(work, a.actor)
    actor_sha = K.sha256(a.actor)
    opp = a.opponent.replace("\\", "/")
    opp_hash = K.build_hash(opp, work, release=False)
    base = dict(layout=10, action_schema=SCHEMA, sampling="complete", stale_block=False, hidden_size=0,
                decision_index=True, preprocess="jd-cl1-af91-v1", temperature=1.0,
                observation_point="farm-pre-actor", data_origin="engine", reward_spec="jd-teamwin-potential-v1",
                run_ns=a.run_ns, log_limit=K.LOG_LIMIT,
                policy=dict(name="clrl-act", actor_json_sha256=actor_sha, wasm_sha256=wasm_sha,
                            encoder_sha256=encoder_sha(), build="debug", flags=["CLRL_ACT=1"],
                            source_commit=K.git_head()),
                engine=dict(cambc="4.0.0", engine="2.0.0"))
    writer = C.ShardWriter(run_dir, base)
    done = writer.done_keys()
    games, lines = [], []
    for mp in a.maps:
        for side in a.sides.split(","):
            key = f"{K.sha256(os.path.join(ROOT, mp))[:16]}|{wasm_sha[:16]}|{opp_hash[:16]}|debug|{side}"
            if key in done:
                continue
            gi = len(games)
            rep, st = os.path.join(work, f"g{gi}.repl26a"), os.path.join(work, f"g{gi}.json")
            for p in (rep, st):
                if os.path.exists(p):
                    os.remove(p)
            pair = (K.absp(bot), K.absp(opp)) if side == "A" else (K.absp(opp), K.absp(bot))
            lines.append(f"{pair[0]} {pair[1]} {K.absp(mp)} {K.absp(rep)} --statistics {K.absp(st)} --json")
            games.append(dict(key=key, map=mp, side=side, rep=rep, st=st))
    if not games:
        print("nothing to do")
        return
    man = os.path.join(work, "batch.txt")
    with open(man, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    cmd = [CLI, "run-batch", K.rel(man), "--jobs", str(a.jobs), "--json", "--color", "never",
           "--log-limit", str(K.LOG_LIMIT), "--timeout", str(a.timeout)] + (["--rounds", str(a.rounds)] if a.rounds else [])
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    with open(os.path.join(work, "batch.log"), "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n---\n" + r.stderr)
    for g in games:
        if not os.path.exists(g["rep"]):
            print(f"{g['map']} {g['side']}: failed (no replay bundle)")
            continue
        summary = None
        if os.path.exists(g["st"]):
            with open(g["st"], encoding="utf-8") as f:
                summary = json.load(f)
        meta = dict(key=g["key"], map_file=g["map"], map_file_sha256=K.sha256(os.path.join(ROOT, g["map"])),
                    opponent=dict(name=opp, wasm_sha256=opp_hash), side=g["side"], build_mode="debug")
        if summary is None:
            meta["map_hash"] = meta["map_file_sha256"]
        meta, cols, dec = episode(g["rep"], summary, g["side"], meta)
        writer.add_episode(meta, cols)
        print(f"{g['map']} {g['side']}: {meta['status']} decisions={meta['decisions']} outcome={meta.get('outcome')} "
              f"scores={meta.get('final_scores')} ppo_eligible={meta['ppo_eligible']} problems={meta['problems']}")
    shard = writer.flush()
    if shard:
        m, c = C.load_shard(shard, use_numpy=False)
        errs = C.validate(m, c)
        print(f"shard {K.rel(shard)}: rows {m['rows']}, validate: {'OK' if not errs else errs[:5]}")
        print(f"actor sha256 {actor_sha}\npolicy wasm sha256 {wasm_sha}\nencoder sha256 {base['policy']['encoder_sha256']}")


if __name__ == "__main__":
    main()
