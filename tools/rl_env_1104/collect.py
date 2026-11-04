"""Collect cl1 teacher traces from the official local engine into rlenv-2 shards (task rl-env-collector-1104).

The recorder bot is bots/claude-rlenv-1104 built with CLRL_REC=1 as a non-release build (the recorder runs inside
debug_block, so release builds and fuel accounting are unchanged). Each game runs through `cambc run-batch`; our team's
stdout CLR1 rows plus the match summary become one episode. Standard library only.

usage (repo root):
  python tools/rl_env_1104/collect.py --run-ns smoke-01 --maps maps/ladder-pool/00corners.map26a [...] \
      --opponent bots/v92 --sides A,B --jobs 2 [--rounds N] [--out runs/rl_env_1104]
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
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import contract as C  # noqa: E402

CLI = os.path.join(ROOT, "tools", "vendor", "cambc.exe" if os.name == "nt" else "cambc")
TWIN = "bots/v92"  # the debug twin: plain v92, whose behaviour the recorder must not change
LAYOUT, SCHEMA = 10, "target13-cl1"
LAY = C.LAYOUTS[LAYOUT]
NF, NA = LAY.nf, C.ACTION_SCHEMAS[SCHEMA].n
C_OFF, C_W = LAY.offset("c"), LAY.width("c")
LOG_LIMIT = 64 * 1024 * 1024
# Smoke reward for teacher traces only, NOT the RL objective (the learner defines win/loss + potential-based shaping).
REWARD_SPEC = ("teacher-smoke-v0: own team submitted-gems gain / 100 over the decision interval; +1 / -1 / 0 at game "
               "end. Diagnostic only: the deposit term can dominate the terminal term")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def prepare_recorder(work: str) -> tuple:
    """Copy the recorder source with CLRL_REC 1 prepended to bot.h; build it once (debug) to record its hash."""
    src = os.path.join(ROOT, "bots", "claude-rlenv-1104", "src")
    dest = os.path.join(work, "bots", "clrl_rec")
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, os.path.join(dest, "src"), ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
    bh = os.path.join(dest, "src", "bot.h")
    with open(bh, encoding="utf-8") as f:
        text = f.read()
    with open(bh, "w", encoding="utf-8", newline="") as f:
        f.write("#define CLRL_REC 1\n" + text)
    wasm = os.path.join(work, "clrl_rec-debug.wasm")
    r = subprocess.run([CLI, "build", os.path.relpath(dest, ROOT), "--output", wasm], cwd=ROOT, capture_output=True,
                       text=True, timeout=900)
    if r.returncode or not os.path.exists(wasm):
        raise SystemExit("recorder build failed:\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return rel(dest), sha256(wasm)


def rel(path: str) -> str:
    """Repo-relative path with forward slashes (cambc run-batch rejects backslash paths in manifests)."""
    return os.path.relpath(path, ROOT).replace("\\", "/")


def absp(path: str) -> str:
    """Absolute path with forward slashes: run-batch resolves manifest paths relative to the manifest's folder."""
    return os.path.abspath(os.path.join(ROOT, path)).replace("\\", "/")


def build_hash(bot: str, work: str, release: bool) -> str:
    """SHA-256 of `bot` built in the same mode the games use (run-batch builds it the same way)."""
    out = os.path.join(work, os.path.basename(bot.rstrip("/")) + ("-release" if release else "-debug") + ".wasm")
    r = subprocess.run([CLI, "build", bot] + (["--release"] if release else []) + ["--output", out], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    if r.returncode or not os.path.exists(out):
        raise SystemExit(f"build of {bot} failed: " + r.stdout[-2000:])
    return sha256(out)


def git_head() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


def timeline_at(runs: list, round_: int) -> int:
    """Value of a run-length timeline at a round (sample k = value after round k-1; runs start at sample 0)."""
    t = 0
    for run in runs:
        if round_ < t + run["duration"]:
            return int(run["value"])
        t += run["duration"]
    return int(runs[-1]["value"]) if runs else 0


def parse_rows(stdout: str, bad: list | None = None) -> list:
    """CLR1 rows; malformed ones (wrong field count, bad base64, wrong length) are counted into `bad`, never dropped
    silently: the caller marks the episode incomplete."""
    rows = []
    for line in stdout.splitlines():
        if not line.startswith("CLR1 "):
            continue
        q = line.split(" ")
        try:
            if len(q) != 10:
                raise ValueError("field count")
            x = struct.unpack(f"<{NF}h", base64.b64decode(q[9], validate=True))
        except Exception:
            if bad is not None:
                bad.append(line[:80])
            continue
        rows.append(dict(round=int(q[1]), slot=int(q[2]), body=int(q[3]), macro=int(q[4]), prim=int(q[5]),
                         dx=max(-127, min(127, int(q[6]))), dy=max(-127, min(127, int(q[7]))), reset=int(q[8]), x=x))
    return rows


def fuel_trace(bundle: str, team_l: str) -> tuple:
    """Per-turn charged fuel of one team: header quanta (8), draft turns (one per pick), champion turns."""
    with zipfile.ZipFile(bundle) as z:
        d = z.read(f"team-{team_l}.fuel")
    n = (len(d) - 13) // 8  # 13-byte header (magic "a62leuf", version), then one u64 per entry
    return struct.unpack(f"<{n}Q", d[13:13 + 8 * n])


def twin_rounds(rec: tuple, twin: tuple, header: int, picks: int, bodies: int) -> dict:
    """round -> (delta, diverged) comparing the recorder's and the twin's champion turns round by round."""
    out = {}
    a, b = rec[header + picks:], twin[header + picks:]
    for r in range(max(len(a), len(b)) // bodies + 1):
        x, y = a[r * bodies:(r + 1) * bodies], b[r * bodies:(r + 1) * bodies]
        if not x and not y:
            break
        out[r] = (sum(x) - sum(y), 1 if list(x) != list(y) else 0)
    return out


def episode_from(bundle: str, summary_path: str | None, side: str, meta_base: dict, twin: dict | None = None) -> tuple:
    """Build (meta, column lists) for our team in one finished or cut game."""
    team_l = side.lower()
    with zipfile.ZipFile(bundle) as z:
        out = z.read(f"team-{team_l}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
    bad: list = []
    rows = parse_rows(out, bad)
    summary = None
    if summary_path and os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as f:
            summary = json.load(f)
    our = "teamA" if side == "A" else "teamB"
    if summary:
        m = summary["match"]
        # True boundary: a game can end inside a round (finalRoundPartial); the last started round then counts.
        end_round = int(m["roundsStarted"]) if m.get("finalRoundPartial") else int(m["roundsCompleted"])
        outcome = m["outcome"]
        status = "terminated"
        tl = next(t["runs"] for t in summary["teamTimelines"] if t["owner"] == our and t["metric"] == "submittedGems")
        meta = dict(meta_base, map_hash=m["mapHash"], seed=m["seed"], rounds_completed=int(m["roundsCompleted"]),
                    rounds_started=int(m["roundsStarted"]), final_round_partial=bool(m.get("finalRoundPartial")),
                    final_substep=m.get("finalSubstep"), end_round=end_round, outcome=outcome, reward_complete=True,
                    engine_build_hash=m.get("engineBuildHash"), engine_version=m.get("engineVersion"),
                    bot_faults=summary.get("diagnostics", {}).get("botFaults"))
    else:
        end_round, outcome, tl = max([r["round"] for r in rows] or [0]), None, None
        status = "truncated"
        meta = dict(meta_base, map_hash=meta_base["map_file_sha256"], seed=None, rounds_completed=end_round,
                    outcome=None, reward_complete=False)
    if len(out.encode()) >= LOG_LIMIT - 4096:
        status = "truncated_log"
        meta["reward_complete"] = False
    if bad:
        status = "incomplete" if status == "terminated" else status
        meta["reward_complete"] = False
    meta["malformed_rows"] = len(bad)
    meta.update(status=status, our_team=our)

    tw = {}
    if twin is not None and summary and twin.get("summary"):
        picks = sum(1 for p in summary["roster"]["draft"] if p["team"] == our)
        bodies = sum(1 for ch in summary["champions"] if ch["team"] == our)
        tw = twin_rounds(fuel_trace(bundle, team_l), fuel_trace(twin["bundle"], team_l), 8, picks, bodies)
        div = [r for r, (_, dv) in sorted(tw.items()) if dv]
        ts = twin["summary"]
        meta.update(twin_wasm_sha256=twin["wasm_sha256"], twin_rounds=len(tw), twin_rounds_diverged=len(div),
                    twin_first_diverged_round=div[0] if div else None,
                    twin_outcome_equal=(ts["match"]["outcome"] == summary["match"]["outcome"] and
                                        [t["submittedGems"] for t in ts["teams"]] ==
                                        [t["submittedGems"] for t in summary["teams"]]))
    rows.sort(key=lambda r: (r["body"], r["round"]))
    cols = {c: [] for c in C.required_columns({"hidden_size": 0, "stale_block": False, "prim_labels": True,
                                                 "fuel_twin": twin is not None})}
    for i, r in enumerate(rows):
        last = i + 1 == len(rows) or rows[i + 1]["body"] != r["body"]
        nxt = end_round if last else rows[i + 1]["round"]
        mask = [1 if r["x"][C_OFF + k * C_W] == 1 else 0 for k in range(NA - 1)] + [1]
        reward = 0.0
        if tl is not None:
            reward = (timeline_at(tl, nxt) - timeline_at(tl, r["round"])) / 100.0
            if last and status == "terminated":
                reward += 1.0 if outcome == our else (-1.0 if outcome in ("teamA", "teamB") else 0.0)
        cols["x_fresh"] += r["x"]
        cols["has_stale"].append(0)
        cols["feat_round"].append(r["round"])
        cols["stale_round"].append(-1)
        cols["act_round"].append(r["round"])
        cols["body_id"].append(r["body"])
        cols["slot"].append(r["slot"])
        cols["mask"] += mask
        cols["action"].append(r["macro"])
        cols["teacher_action"].append(r["macro"])
        cols["executed"].append(r["macro"])
        cols["logp"].append(float("nan"))
        cols["has_logp"].append(0)
        cols["weight"].append(1.0)
        cols["changed"].append(1 if i == 0 or rows[i - 1]["body"] != r["body"] or rows[i - 1]["macro"] != r["macro"] else 0)
        cols["reset"].append(r["reset"])
        cols["reward"].append(reward)
        cols["dt_rounds"].append(max(0, nxt - r["round"]))
        cols["terminated"].append(1 if last and status == "terminated" else 0)
        cols["truncated"].append(1 if last and status != "terminated" else 0)
        cols["boundary"].append(0)
        cols["bootstrap_valid"].append(0)  # teacher traces never bootstrap
        cols["prim"].append(r["prim"])
        cols["move_dx"].append(r["dx"])
        cols["move_dy"].append(r["dy"])
        if twin is not None:
            d, dv = tw.get(r["round"], (0, 1))  # a round missing from either trace counts as diverged
            cols["fuel_delta"].append(max(-2**31, min(2**31 - 1, d)))
            cols["fuel_diverged"].append(dv)
    cols.pop("episode", None)
    return meta, cols, rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-ns", required=True)
    ap.add_argument("--maps", nargs="+", required=True)
    ap.add_argument("--opponent", default="bots/v92")
    ap.add_argument("--sides", default="A,B")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--rounds", type=int)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out", default=os.path.join("runs", "rl_env_1104"))
    ap.add_argument("--no-twin", action="store_true", help="skip the v92 debug twin (no fuel_delta/fuel_diverged)")
    a = ap.parse_args()

    run_dir = os.path.join(ROOT, a.out, a.run_ns)
    work = os.path.join(ROOT, "artifacts", "tmp", "rl_env_1104", a.run_ns)
    os.makedirs(work, exist_ok=True)
    bot, rec_hash = prepare_recorder(work)
    opp = a.opponent.replace("\\", "/")
    base = dict(layout=LAYOUT, action_schema=SCHEMA, sampling="teacher", stale_block=False, hidden_size=0, prim_labels=True,
                fuel_twin=not a.no_twin,
                reward_spec=REWARD_SPEC, run_ns=a.run_ns, log_limit=LOG_LIMIT, fuel_quantum=None,
                policy=dict(name="v92-teacher(clrl_rec)", wasm_sha256=rec_hash, build="debug", flags=["CLRL_REC=1"],
                            source_commit=git_head()),
                engine=dict(cambc="4.0.0", engine="2.0.0"))
    writer = C.ShardWriter(run_dir, base)
    done = writer.done_keys()
    opp_hash = build_hash(opp, work, release=False)
    twin_hash = None if a.no_twin else build_hash(TWIN, work, release=False)

    games, lines = [], []
    for mp in a.maps:
        for side in a.sides.split(","):
            # Retry key: map content + recorder build + opponent build + mode + side (not the basename alone).
            key = f"{sha256(os.path.join(ROOT, mp))[:16]}|{rec_hash[:16]}|{opp_hash[:16]}|debug|{side}"
            if key in done:
                continue
            gi = len(games)
            rep = os.path.join(work, f"g{gi}.repl26a")
            st = os.path.join(work, f"g{gi}.json")
            for p in (rep, st):
                if os.path.exists(p):
                    os.remove(p)
            pair = (absp(bot), absp(opp)) if side == "A" else (absp(opp), absp(bot))
            lines.append(f"{pair[0]} {pair[1]} {absp(mp)} {absp(rep)} --statistics {absp(st)} --json")
            g = dict(key=key, map=mp, side=side, rep=rep, st=st)
            if not a.no_twin:  # the same game with plain v92 in our seat, same (debug) build mode
                trep, tst = os.path.join(work, f"g{gi}t.repl26a"), os.path.join(work, f"g{gi}t.json")
                for p in (trep, tst):
                    if os.path.exists(p):
                        os.remove(p)
                tp = (absp(TWIN), absp(opp)) if side == "A" else (absp(opp), absp(TWIN))
                lines.append(f"{tp[0]} {tp[1]} {absp(mp)} {absp(trep)} --statistics {absp(tst)} --json")
                g.update(trep=trep, tst=tst)
            games.append(g)
    if not games:
        print("nothing to do (all games already in shards)")
        return
    man = os.path.join(work, "batch.txt")
    with open(man, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    cmd = [CLI, "run-batch", rel(man), "--jobs", str(a.jobs), "--json", "--color", "never",
           "--log-limit", str(LOG_LIMIT), "--timeout", str(a.timeout)]
    if a.rounds:
        cmd += ["--rounds", str(a.rounds)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    with open(os.path.join(work, "batch.log"), "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n---\n" + r.stderr)

    report = []
    for g in games:
        bundle = g["rep"]
        if not os.path.exists(bundle):
            cands = [os.path.join(os.path.dirname(bundle), n) for n in os.listdir(os.path.dirname(bundle))
                     if n.startswith(os.path.basename(bundle))]
            bundle = cands[0] if cands else None
        if not bundle:
            report.append((g["map"] + " " + g["side"], "failed (no replay bundle)"))
            continue
        meta_base = dict(key=g["key"], map_file=g["map"], build_mode="debug", map_file_sha256=sha256(os.path.join(ROOT, g["map"])),
                         opponent=dict(name=opp, wasm_sha256=opp_hash), side=g["side"])
        twin = None
        if not a.no_twin:
            ts = None
            if os.path.exists(g["tst"]):
                with open(g["tst"], encoding="utf-8") as f:
                    ts = json.load(f)
            ok = os.path.exists(g["trep"]) and ts is not None
            twin = dict(bundle=g["trep"] if ok else None, summary=ts if ok else None, wasm_sha256=twin_hash)
        meta, cols, rows = episode_from(bundle, g["st"], g["side"], meta_base, twin)
        if not rows:
            report.append((g["map"] + " " + g["side"], "failed (no CLR1 rows)"))
            continue
        writer.add_episode(meta, cols)
        tws = ""
        if twin is not None:
            tws = (f" | twin: {meta.get('twin_rounds_diverged')}/{meta.get('twin_rounds')} rounds diverged, first "
                   f"{meta.get('twin_first_diverged_round')}, outcome equal {meta.get('twin_outcome_equal')}")
        report.append((g["map"] + " " + g["side"], f"{meta['status']} rows={len(rows)} malformed={meta['malformed_rows']} "
                                                  f"outcome={meta['outcome']} our={meta['our_team']}{tws}"))
    shard = writer.flush()
    for k, s in report:
        print(f"{k}: {s}")
    if shard:
        m, c = C.load_shard(shard, use_numpy=False)
        errs = C.validate(m, c)
        print(f"shard {os.path.relpath(shard, ROOT)}: rows {m['rows']}, episodes {len(m['episodes'])}, "
              f"validate: {'OK' if not errs else errs[:5]}")


if __name__ == "__main__":
    main()
