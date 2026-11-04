"""Collect native exploration-mixture rollouts (bots/claude-native-1104, CLNA_EPS) into rlenv-2 shards.

Builds the native bot (Agent 2 student_i2m backbone, frozen) with CLNA_EPS as a non-release build, plays games via
`cambc run-batch`, and turns our team's CNA1 decision rows + CNX1 executed rows + the match summary into one episode
per game, schema native-blend-eps-v1 (layout 2 features, 500 int16). Suspension-aware: fuel-out events from the
summary are mapped to the body and decision interval they fall in (fuel_out column), instead of rejecting the game.
A malformed row, a missing executed row, an index gap, a log cut or a missing summary make the episode ineligible.
Downstream reassignment by v92's later farm() code (executed group != chosen) is kept and flagged per row
(executed = -1 when the executed group is not a candidate) and counted per episode.

--head (implies --release): the target-head build (CLNA_HEAD, JOHNDOE #83 option d), schema native-head-v1, CNR2 rows
with every head input in the head_* columns (clna-head-abi-v1). Decisions the fuel guard skips (CNS2) are the
deterministic reference: counted per episode and reason, never given a logp.

usage (repo root):
  python tools/rl_env_1104/collect_native.py --eps 0.02 --run-ns nat-smoke-01 \
      --maps maps/ladder-pool/00corners.map26a --opponent bots/v92 --sides A [--jobs 1]
  ... --head [--head-header PATH/clna_head_w.h] [--head-min 50000]
"""
from __future__ import annotations

import argparse
import base64
import json
import math
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

sys.path.insert(0, os.path.join(HERE, "native"))
import head_export as HX  # noqa: E402
import head_rows as HR  # noqa: E402

ROOT, CLI = K.ROOT, K.CLI
SCHEMA, LAYOUT = "native-blend-eps-v1", 2
HEAD_SCHEMA = "native-head-v1"
GATE_N = 8
REWARD_SPEC = ("mc-terminal-gamma1-v1: every decision of the team's complete game gets the team's final outcome "
               "(+1 win / 0 draw / -1 loss) as its undiscounted return; no shaping, no bootstrap (JOHNDOE #61)")
NF, NA = C.LAYOUTS[LAYOUT].nf, C.ACTION_SCHEMAS[SCHEMA].n


def prepare(work: str, eps: float, release: bool = False, head: bool = False, head_header: str | None = None,
            head_min: int | None = None) -> tuple:
    src = os.path.join(ROOT, "bots", "claude-native-1104", "src")
    dest = os.path.join(work, "bots", "clna")
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, os.path.join(dest, "src"), ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
    if head_header:
        shutil.copyfile(head_header, os.path.join(dest, "src", "clna_head_w.h"))
    ch = os.path.join(dest, "src", "common.h")
    with open(ch, encoding="utf-8") as f:
        text = f.read()
    defs = f"#define CLNA_EPS {eps!r}\n" + ("#define CLNA_RLOG 1\n" if release else "")
    if head:
        defs += "#define CLNA_HEAD 1\n" + (f"#define CLNA_HEAD_MIN {int(head_min)}\n" if head_min else "")
    with open(ch, "w", encoding="utf-8", newline="") as f:
        f.write(defs + text)
    wasm = os.path.join(work, "clna-release.wasm" if release else "clna-debug.wasm")
    r = subprocess.run([CLI, "build", K.rel(dest)] + (["--release"] if release else []) + ["--output", wasm], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    if r.returncode or not os.path.exists(wasm):
        raise SystemExit("native build failed: " + r.stdout[-3000:] + r.stderr[-3000:])
    return K.rel(dest), K.sha256(wasm)


def hexd(h: str) -> float:
    return struct.unpack("<d", int(h, 16).to_bytes(8, "little"))[0]


def parse(stdout: str) -> tuple:
    dec, exe, skips, bad = [], {}, 0, 0
    for line in stdout.splitlines():
        q = line.split(" ")
        try:
            if q[0] in ("CNR2", "CNR3"):  # target head: every input logged; logp = log of the logged p(chosen)
                h = HR.parse_cnr2(q)
                n, nu = h["n"], len(h["groups"])
                # residual-0 physical q of the frozen runtime (diagnostic cand_q): slot softmax merged by the mapping
                nat = [float(v) for v in h["native"]]
                mx = max(nat)
                ex = [math.exp(v - mx) for v in nat]
                qs = [0.0] * nu
                for j in range(n + 1):
                    qs[h["map"][j]] += ex[j] / sum(ex)
                dec.append(dict(round=h["round"], eround=-1, slot=h["slot"], body=h["body"], index=h["index"],
                                ref=h["ref"], chosen=h["chosen"], logp=math.log(h["p"]), eps=h["alpha"], v92=h["v92"],
                                nn=h["nn"], groups=h["groups"], q=qs, gx=[], x=(0,) * NF, head=h))
            elif q[0] == "CNS2":  # fuel guard / pairing skip: the reference acted, no stochastic decision
                skips += 1
            elif q[0] == "CNK":  # per-turn skip counts by reason (head builds after cfe27aa3)
                if len(q) != 8:
                    raise ValueError
                skips += sum(int(v) for v in q[4:8])
            elif q[0] == "CNR1":  # release logger: raw float bits, no features; logp rebuilt from the mixture
                nu = int(q[10])
                if len(q) != 11 + nu + GATE_N:
                    raise ValueError
                cands = [x.split(":") for x in q[11:11 + nu]]
                groups, qs = [int(g) for g, _ in cands], [hexd(v) for _, v in cands]
                alpha, ref, ch = hexd(q[7]), int(q[5]), int(q[6])
                p = alpha * qs[groups.index(ch)] + ((1 - alpha) if ch == ref else 0.0)
                dec.append(dict(round=int(q[1]), eround=-1, slot=int(q[2]), body=int(q[3]), index=int(q[4]), ref=ref,
                                chosen=ch, logp=math.log(p), eps=alpha, v92=int(q[8]), nn=int(q[9]), groups=groups,
                                q=qs, gx=[hexd(v) for v in q[11 + nu:11 + nu + GATE_N]], x=(0,) * NF))
            elif q[0] == "CNX3":
                exe[(int(q[3]), int(q[4]))] = (int(q[5]), -1)
            elif q[0] == "CNA2":
                nu = int(q[12])
                if len(q) != 13 + nu + GATE_N + 1:
                    raise ValueError
                cands = [tuple(x.split(":")) for x in q[13:13 + nu]]
                gx = [float(v) for v in q[13 + nu:13 + nu + GATE_N]]
                x = struct.unpack(f"<{NF}h", base64.b64decode(q[13 + nu + GATE_N], validate=True))
                dec.append(dict(round=int(q[1]), eround=int(q[2]), slot=int(q[3]), body=int(q[4]), index=int(q[5]),
                                ref=int(q[6]), chosen=int(q[7]), logp=float(q[8]), eps=float(q[9]), v92=int(q[10]),
                                nn=int(q[11]), groups=[int(g) for g, _ in cands], q=[float(v) for _, v in cands],
                                gx=gx, x=x))
            elif q[0] == "CNX2":  # paired by (body, decision index), never by cached round alone
                exe[(int(q[4]), int(q[5]))] = (int(q[6]), int(q[2]))
            elif q[0] == "CNS1":
                skips += 1
        except Exception:
            bad += 1
    return dec, exe, skips, bad


def episode(bundle: str, summary: dict | None, side: str, meta: dict, head: bool = False) -> tuple:
    team_l, our = side.lower(), ("teamA" if side == "A" else "teamB")
    theirs = "teamB" if our == "teamA" else "teamA"
    with zipfile.ZipFile(bundle) as z:
        raw = z.read(f"team-{team_l}.stdout")
    # The engine pads stdout with NUL bytes where a suspended turn lost output: treat them as line breaks, so an
    # intact row before the padding still parses and any split row is counted as malformed, never misread.
    dec, exe, skips, bad = parse(raw.replace(bytes(1), b"\n").decode("utf-8", "replace"))
    problems, flags = [], dict(incomplete=False, log_cut=False)
    if bad:
        flags["incomplete"] = True
        problems.append(f"{bad} malformed rows")
    if len(raw) >= K.LOG_LIMIT - 4096:
        flags["log_cut"] = True
        problems.append("stdout at log limit")
    fuel_rounds: dict = {}
    if summary is None:
        flags["incomplete"] = True
        problems.append("no match summary")
        status, end_round, outcome = "truncated", max([d["round"] for d in dec] or [0]), None
    else:
        m = summary["match"]
        status, outcome = "terminated", m["outcome"]
        end_round = int(m["roundsStarted"]) if m.get("finalRoundPartial") else int(m["roundsCompleted"])
        for e in summary["events"]:
            if e["kind"] == "fuelExhausted" and e["owner"].get("team") == our:
                fuel_rounds.setdefault(int(e["owner"]["id"]), []).extend(int(x["timestamp"]["round"]) for x in e["entries"])
        scores = {t["team"]: int(t["submittedGems"]) for t in summary["teams"]}
        meta.update(map_hash=m["mapHash"], seed=m["seed"], engine_build_hash=m.get("engineBuildHash"),
                    rounds_completed=int(m["roundsCompleted"]), end_round=end_round,
                    final_scores=dict(ours=scores.get(our, 0), theirs=scores.get(theirs, 0)),
                    terminal_outcome=(1 if outcome == our else (-1 if outcome == theirs else 0)),
                    fuel_outs=sum(len(v) for v in fuel_rounds.values()),
                    bot_faults=summary.get("diagnostics", {}).get("botFaults", {}).get(our, 0))
        if meta["bot_faults"]:
            flags["incomplete"] = True
            problems.append(f"{meta['bot_faults']} bot faults")
    dec.sort(key=lambda d: (d["body"], d["round"]))
    gaps = reassigned = no_exec = 0
    cols = {c: [] for c in C.required_columns(dict(hidden_size=0, stale_block=False, decision_index=True,
                                                    native_cands=True, gate_inputs=0 if head else GATE_N,
                                                    head_inputs=head))}
    if head and any("head" not in d for d in dec):
        flags["incomplete"] = True
        problems.append("non-head decision rows in a head episode")
        dec = [d for d in dec if "head" in d]
    for i, d in enumerate(dec):
        first = i == 0 or dec[i - 1]["body"] != d["body"]
        last = i + 1 == len(dec) or dec[i + 1]["body"] != d["body"]
        if not first and d["index"] != dec[i - 1]["index"] + 1:
            gaps += 1
        nxt = end_round if last else dec[i + 1]["round"]
        groups = (d["groups"] + [-1] * NA)[:NA]
        qs = (d["q"] + [0.0] * NA)[:NA]
        act = groups.index(d["chosen"]) if d["chosen"] in groups else -1
        ref = groups.index(d["ref"]) if d["ref"] in groups else -1
        ex_rec = exe.get((d["body"], d["index"]))
        ex_g, ex_round = (ex_rec if ex_rec is not None else (None, -1))
        if ex_g is None:
            no_exec += 1
            ex = -1
        else:
            ex = groups.index(ex_g) if ex_g in groups else -1
            reassigned += ex_g != d["chosen"]
        fo = any(d["round"] <= r < max(nxt, d["round"] + 1) for r in fuel_rounds.get(d["body"], []))
        cols["x_fresh"] += d["x"]
        cols["has_stale"].append(0)
        cols["feat_round"].append(d["round"])
        cols["stale_round"].append(-1)
        cols["act_round"].append(d["round"])
        cols["body_id"].append(d["body"])
        cols["slot"].append(d["slot"])
        cols["mask"] += [1 if g >= 0 else 0 for g in groups]
        cols["action"].append(act)
        cols["teacher_action"].append(ref)
        cols["executed"].append(ex)
        cols["logp"].append(d["logp"])
        cols["has_logp"].append(1)
        cols["weight"].append(1.0)
        cols["changed"].append(1 if first or dec[i - 1]["chosen"] != d["chosen"] else 0)
        cols["reset"].append(1 if first else 0)
        # mc-terminal-gamma1-v1: the team's final outcome for every decision (0 placeholder if the game is incomplete)
        cols["reward"].append(float(meta.get("terminal_outcome", 0)) if status == "terminated" else 0.0)
        cols["dt_rounds"].append(max(0, nxt - d["round"]))
        cols["terminated"].append(1 if last and status == "terminated" else 0)
        cols["truncated"].append(1 if last and status != "terminated" else 0)
        cols["boundary"].append(0)
        cols["bootstrap_valid"].append(0)
        cols["decision_index"].append(d["index"])
        cols["cand_group"] += groups
        cols["cand_q"] += qs
        cols["eps"].append(d["eps"])
        cols["ref_slot"].append(ref)
        cols["fuel_out"].append(1 if fo else 0)
        cols["gate_x"] += d["gx"]
        cols["engine_round"].append(d["eround"])
        cols["engine_round_done"].append(ex_round)
        if head:
            h, n = d["head"], d["head"]["n"]
            cols["head_ctx"] += [int(v) for v in h["x"]]
            cols["head_camp"] += [int(v) for v in h["ec"].flatten()] + [0] * (16 * (10 - n))
            cols["head_feat"] += [int(v) for v in h["ft"].flatten()] + [0] * (4 * (10 - n))
            nat = [float(v) for v in h["native"]]
            cols["head_native"] += nat[:n] + [0.0] * (10 - n) + [nat[n]]
            cols["head_valid"] += [1] * n + [0] * (10 - n) + [1]
            # slot -> index into this row's cand_group (= the logged physical group order)
            cols["head_map"] += h["map"][:n] + [-1] * (10 - n) + [h["map"][n]]
            cols["head_n"].append(n)
            cols["head_pub"].append(h["pub"])
            cols["head_ctx_round"].append(h["ctx_round"])
    if gaps:
        flags["incomplete"] = True
        problems.append(f"{gaps} decision-index gaps")
    if no_exec:
        flags["incomplete"] = True
        problems.append(f"{no_exec} decisions without an executed row")
    if not dec:
        flags["incomplete"] = True
        problems.append("no decisions")
    cols.pop("episode", None)
    eligible = status == "terminated" and not any(flags.values())
    meta.update(status=status, our_team=our, outcome=outcome, decisions=len(dec), skips=skips,
                reassigned=reassigned, fuel_out_rows=sum(cols["fuel_out"]), problems=problems,
                reward_complete=eligible, ppo_eligible=eligible, **flags)
    return meta, cols, dec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eps", type=float, required=True)
    ap.add_argument("--run-ns", required=True)
    ap.add_argument("--maps", nargs="+", required=True)
    ap.add_argument("--opponent", default="bots/v92")
    ap.add_argument("--sides", default="A")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", default=os.path.join("runs", "rl_env_1104"))
    ap.add_argument("--release", action="store_true",
                    help="release logging build (CLNA_RLOG): the collected build is the deployable one (JOHNDOE #69)")
    ap.add_argument("--head", action="store_true", help="target-head build (CLNA_HEAD), schema native-head-v1")
    ap.add_argument("--head-header", help="clna_head_w.h to build with (default: the one in bots/claude-native-1104/src)")
    ap.add_argument("--head-min", type=int, help="CLNA_HEAD_MIN fuel guard (default: nnrec.cpp's)")
    a = ap.parse_args()
    if a.head:
        a.release = True
    run_dir = os.path.join(ROOT, a.out, a.run_ns)
    work = os.path.join(ROOT, "artifacts", "tmp", "rl_env_1104", a.run_ns)
    os.makedirs(work, exist_ok=True)
    bot, wasm_sha = prepare(work, a.eps, a.release, a.head, a.head_header, a.head_min)
    opp = a.opponent.replace("\\", "/")
    opp_hash = K.build_hash(opp, work, release=a.release)
    mode = "release" if a.release else "debug"
    base = dict(layout=LAYOUT, action_schema=SCHEMA, sampling="complete", stale_block=False, hidden_size=0,
                decision_index=True, native_cands=True, gate_inputs=GATE_N, eps=a.eps,
                action_kind="latent_group_at_blend_boundary", executor="frozen v92 farm() after the blend (fixed)",
                return_convention="gamma=1 complete-game Monte Carlo: G_t = reward column = team outcome",
                observation_point="native-blend-farm", data_origin="engine",
                features_logged=not a.release, features=("absent: release logger (CNR1) logs q, gate inputs and alpha only; x_fresh zero" if a.release
                          else "layout 2 fresh features (CNA2)"), reward_spec=REWARD_SPEC, run_ns=a.run_ns, log_limit=K.LOG_LIMIT,
                policy=dict(name="native-blend-eps", backbone="agent2 student_i2m (frozen)",
                            checkpoint_sha256="05052b6e8ddeb8eaa4cef760b8b24dda9cfee794207b0a2d12d7b06bfae9e5ec",
                            wasm_sha256=wasm_sha, build=mode,
                            flags=[f"CLNA_EPS={a.eps}"] + (["CLNA_RLOG=1"] if a.release else []),
                            gate_header_sha256=K.sha256(os.path.join(bot, "src", "clna_gate.h")),
                            source_commit=K.git_head()),
                engine=dict(cambc="4.0.0", engine="2.0.0"))
    if a.head:
        _, head_ver = HX.load_header(os.path.join(ROOT, bot, "src", "clna_head_w.h"))
        base.update(action_schema=HEAD_SCHEMA, gate_inputs=0, head_inputs=True,
                    features="absent: x_fresh zero; the head's inputs are the head_* columns (clna-head-abi-v1)",
                    action_kind="latent_group_at_blend_boundary (target head)",
                    head=dict(abi=HX.HEAD_ABI, abi_hash=HX.HEAD_ABI_HASH, version=head_ver,
                              header_sha256=K.sha256(os.path.join(ROOT, bot, "src", "clna_head_w.h")),
                              guard_min_fuel=a.head_min or 35000, stage_min_fuel=7000,
                              skips="CNS2 rows: 1 camp snapshot unpaired, 2 reference outside slots, 3 fuel guard, 4 no completed context; the "
                                    "reference acts deterministically and no row/logp is stored"))
        base["policy"].update(name="native-target-head", flags=base["policy"]["flags"] + ["CLNA_HEAD=1"] +
                              ([f"CLNA_HEAD_MIN={a.head_min}"] if a.head_min else []))
    writer = C.ShardWriter(run_dir, base)
    done = writer.done_keys()
    games, lines = [], []
    for mp in a.maps:
        for side in a.sides.split(","):
            key = f"{K.sha256(os.path.join(ROOT, mp))[:16]}|{wasm_sha[:16]}|{opp_hash[:16]}|{mode}|{side}"
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
    r = subprocess.run([CLI, "run-batch", K.rel(man), "--jobs", str(a.jobs), "--json", "--color", "never",
                        "--log-limit", str(K.LOG_LIMIT), "--timeout", str(a.timeout)] + (["--release"] if a.release else []),
                       cwd=ROOT, capture_output=True, text=True)
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
                    opponent=dict(name=opp, wasm_sha256=opp_hash), side=g["side"], build_mode=mode)
        if summary is None:
            meta["map_hash"] = meta["map_file_sha256"]
        meta, cols, _ = episode(g["rep"], summary, g["side"], meta, head=a.head)
        writer.add_episode(meta, cols)
        print(f"{g['map']} {g['side']}: {meta['status']} {meta.get('final_scores')} decisions={meta['decisions']} "
              f"skips={meta['skips']} reassigned={meta['reassigned']} fuel_out_rows={meta['fuel_out_rows']} "
              f"fuel_outs={meta.get('fuel_outs')} ppo_eligible={meta['ppo_eligible']} problems={meta['problems']}")
    shard = writer.flush()
    if shard:
        m, c = C.load_shard(shard, use_numpy=False)
        errs = C.validate(m, c)
        print(f"shard {K.rel(shard)}: rows {m['rows']}, validate: {'OK' if not errs else errs[:5]}, wasm {wasm_sha[:16]}")


if __name__ == "__main__":
    main()
