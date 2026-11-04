"""First bounded update of the native exploration gate (task rl-env-collector-1104, JOHNDOE #52/#59/#61).

Policy at the blend boundary (latent physical-group action):
    pi(g | h) = (1 - alpha(h)) * [g == reference] + alpha(h) * q(g),   alpha(h) = sigmoid(b + w . x(h))
q = the frozen native runtime's softmax mass per physical group (logged), x = the 8 legal gate inputs (logged). Only
the gate (w, b) is trained. Return convention mc-terminal-gamma1-v1: G = the team's final outcome for every decision
of a complete game. Advantage = G - mean outcome over the batch's games. Clipped PPO ratio on the full mixture
probability; each game contributes the SUM of its decisions' surrogate terms (all bodies), and games are averaged
(JOHNDOE #66: a per-game mean would shrink the weight of every decision in a long game).

Data checks (#66): a shard must carry reward_spec mc-terminal-gamma1-v1, and every row of an eligible episode must
equal that episode's proven terminal outcome; any other episode is rejected and listed in the report.

Checkpoints (#66): the run saves gate.pt = gate parameters, the gate ABI hash (inputs, formula, kN), the Adam state,
the behaviour eps0 and the update count. --resume CHECKPOINT continues from one (ABI must match).

Gates before any update: (1) the mixture formula matches JOHNDOE's native_oracle fixtures; (2) the logged logp
replays from the shard columns at the collection gate within 2e-4. Exports a new clna_gate.h.

usage: python tools/rl_env_1104/native/train_gate.py --shards runs/rl_env_1104/<ns> --fixtures FIXTURES.json
          --out runs/rl_env_1104/gate-update-01 [--epochs 4 --lr 0.05 --clip 0.2] [--resume <dir>/gate.pt]
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import contract as C  # noqa: E402

REWARD_SPEC_ID = "mc-terminal-gamma1-v1"
# The gate's interface: changing any input, its scaling, the count or the formula changes this hash, and a checkpoint
# trained under another ABI is refused.
GATE_ABI = ("clna-gate-abi-v1|alpha=sigmoid(b+w.x)|pi=(1-alpha)[g=ref]+alpha*q(g)|kN=8|"
            "q(ref),max q,entropy(q)/log(#cand),round/2000,gems/100,hp/max_hp,min(enemies,6)/6,#cand/14")
GATE_ABI_HASH = hashlib.sha256(GATE_ABI.encode()).hexdigest()


def oracle_check(path):
    """Mixture probabilities and chosen log-probability vs the oracle (masked softmax, aliases merged)."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    worst = 0.0
    for c in d["cases"]:
        lg = np.array(c["proposal_logits"], dtype=np.float64)
        m = np.array(c["mask"], dtype=bool)
        e = np.where(m, np.exp(lg - lg[m].max()), 0.0)
        q = e / e.sum()
        phys = {}
        for p, g in zip(q, c["proposal_to_physical"]):
            phys[g] = phys.get(g, 0.0) + p
        al = c["alpha"]
        pr = {g: al * v + ((1 - al) if g == c["reference"] else 0.0) for g, v in phys.items()}
        pr.setdefault(c["reference"], 1 - al)
        for g, want in zip(c["physical_order"], c["probabilities"]):
            worst = max(worst, abs(pr.get(g, 0.0) - want))
        worst = max(worst, abs(math.log(pr[c["chosen"]]) - c["log_probability"]))
    return len(d["cases"]), worst


def load(root, game_offset):
    rows = dict(q=[], ref=[], a=[], logp=[], x=[], G=[], game=[])
    games, rejected = [], []
    for man, cols in C.iter_shards(root, layout=2, action_schema="native-blend-eps-v1"):
        spec_ok = str(man.get("reward_spec", "")).startswith(REWARD_SPEC_ID + ":")
        for e, meta in enumerate(man["episodes"]):
            if not meta.get("ppo_eligible"):
                continue
            sel = cols["episode"] == e
            why = None
            if not spec_ok:
                why = f"reward_spec {str(man.get('reward_spec'))[:40]!r} is not {REWARD_SPEC_ID}"
            elif meta.get("terminal_outcome") not in (-1, 0, 1) or meta.get("status") != "terminated":
                why = f"no proven outcome (status {meta.get('status')}, outcome {meta.get('terminal_outcome')})"
            elif not sel.any():
                why = "no decisions"
            elif not np.all(cols["reward"][sel] == float(meta["terminal_outcome"])):
                why = "reward rows differ from the proven game outcome"
            if why:
                rejected.append(dict(shard=root, key=meta.get("key"), reason=why))
                continue
            gi = game_offset + len(games)
            games.append(dict(key=meta["key"], map=meta["map_file"], side=meta["side"],
                              outcome=meta["terminal_outcome"], decisions=int(sel.sum())))
            rows["q"].append(cols["cand_q"][sel])
            rows["ref"].append(cols["ref_slot"][sel])
            rows["a"].append(cols["action"][sel])
            rows["logp"].append(cols["logp"][sel])
            rows["x"].append(cols["gate_x"][sel])
            rows["G"].append(cols["reward"][sel])
            rows["game"].append(np.full(int(sel.sum()), gi))
    if not games:
        return None, games, rejected
    return {k: np.concatenate(v) for k, v in rows.items()}, games, rejected


def mixture_logp(w, b, x, q, ref, a):
    alpha = torch.sigmoid(b + x @ w)
    pa = alpha * q[torch.arange(len(a)), a] + (1 - alpha) * (a == ref).to(q.dtype)
    return torch.log(pa), alpha


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shards", nargs="+", required=True)
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--eps0", type=float, default=0.02)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--clip", type=float, default=0.2)
    ap.add_argument("--resume", help="gate.pt from an earlier run (same gate ABI)")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit("output directory must be new")
    os.makedirs(a.out)
    n_fx, fx_err = oracle_check(a.fixtures)
    if fx_err > 1e-9:
        raise SystemExit(f"mixture formula disagrees with the oracle: {fx_err}")
    R, games, rejected = None, [], []
    for root in a.shards:
        part, g, rj = load(root, len(games))
        games += g
        rejected += rj
        if part is not None:
            R = part if R is None else {k: np.concatenate([R[k], part[k]]) for k in R}
    for r in rejected:
        print("rejected episode", r)
    if R is None:
        raise SystemExit("no eligible episodes")
    t = {k: torch.tensor(R[k], dtype=torch.float64) for k in ("q", "logp", "x", "G")}
    ref = torch.tensor(R["ref"], dtype=torch.long)
    act = torch.tensor(R["a"], dtype=torch.long)
    game = torch.tensor(R["game"], dtype=torch.long)
    ck = None
    if a.resume:
        ck = torch.load(a.resume, weights_only=True)
        if ck["gate_abi_hash"] != GATE_ABI_HASH:
            raise SystemExit(f"checkpoint gate ABI {ck['gate_abi_hash'][:12]} != {GATE_ABI_HASH[:12]}")
        w = ck["w"].clone().to(torch.float64).requires_grad_(True)
        b = ck["b"].clone().to(torch.float64).requires_grad_(True)
    else:
        w = torch.zeros(8, dtype=torch.float64, requires_grad=True)
        b = torch.tensor(math.log(a.eps0 / (1 - a.eps0)), dtype=torch.float64, requires_grad=True)
    with torch.no_grad():
        lp0, al0 = mixture_logp(w, b, t["x"], t["q"], ref, act)
    replay_err = float((lp0 - t["logp"]).abs().max())
    if replay_err > 2e-4:
        raise SystemExit(f"behaviour logp replay failed: {replay_err}")
    outcomes = np.array([g["outcome"] for g in games], dtype=np.float64)
    adv = t["G"] - float(outcomes.mean())
    ng = len(games)
    opt = torch.optim.Adam([w, b], lr=a.lr)
    if ck is not None:
        opt.load_state_dict(ck["optimizer"])
    hist = []
    for ep in range(a.epochs):
        lp, al = mixture_logp(w, b, t["x"], t["q"], ref, act)
        ratio = torch.exp(lp - t["logp"])
        surr = torch.minimum(ratio * adv, torch.clamp(ratio, 1 - a.clip, 1 + a.clip) * adv)
        per_game = torch.zeros(ng, dtype=torch.float64).index_add(0, game, surr)
        loss = -per_game.mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        with torch.no_grad():
            kl = float((t["logp"] - lp).mean())
        hist.append(dict(epoch=ep, loss=float(loss), approx_kl=kl, alpha_mean=float(al.mean()),
                         clip_frac=float(((ratio - 1).abs() > a.clip).double().mean())))
    with torch.no_grad():
        lp1, al1 = mixture_logp(w, b, t["x"], t["q"], ref, act)
    W = [float(np.float32(v)) for v in w.detach()]
    B = float(b.detach())
    ver = "clna-gate-v1-" + hashlib.sha256(json.dumps([W, B]).encode()).hexdigest()[:12]
    hdr = ("// Generated by tools/rl_env_1104/native/train_gate.py (" + ver + "). Do not edit.\n"
           "#pragma once\n#include <cmath>\nnamespace clna_gate {\ninline constexpr int kN = 8;\n"
           'inline constexpr char kVersion[] = "' + ver + '";\n'
           "inline constexpr float kW[kN] = {" + ", ".join(float.hex(v) + "f" for v in W) + "};\n"
           "inline const double kBias = " + repr(B) + ";\n}  // namespace clna_gate\n")
    with open(os.path.join(a.out, "clna_gate.h"), "w", encoding="utf-8", newline="\n") as f:
        f.write(hdr)
    updates = (ck["updates"] if ck is not None else 0) + a.epochs
    torch.save(dict(w=w.detach().clone(), b=b.detach().clone(), optimizer=opt.state_dict(), gate_abi=GATE_ABI,
                    gate_abi_hash=GATE_ABI_HASH, eps0=a.eps0, updates=updates, version=ver,
                    resumed_from=a.resume or ""), os.path.join(a.out, "gate.pt"))
    rep = dict(kind="first bounded native gate update (mc-terminal-gamma1-v1); NOT a strength claim", version=ver,
               oracle_cases=n_fx, oracle_max_error=fx_err, behaviour_replay_max_error=replay_err, games=games,
               decisions=int(len(act)), outcome_mean=float(outcomes.mean()), epochs=hist,
               alpha_before=dict(mean=float(al0.mean()), min=float(al0.min()), max=float(al0.max())),
               alpha_after=dict(mean=float(al1.mean()), min=float(al1.min()), max=float(al1.max())),
               gate_w=W, gate_b=B, shards=a.shards, rejected_episodes=rejected,
               objective="sum of decision surrogates per game, mean over games", reward_spec=REWARD_SPEC_ID,
               gate_abi_hash=GATE_ABI_HASH, resumed_from=a.resume, updates=updates)
    with open(os.path.join(a.out, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("version", "oracle_cases", "oracle_max_error", "behaviour_replay_max_error",
                                          "decisions", "outcome_mean", "alpha_before", "alpha_after", "updates")}, indent=1))
    print("rejected episodes", len(rejected))
    print("epochs", [(h["epoch"], round(h["loss"], 5), round(h["approx_kl"], 6), round(h["clip_frac"], 4))
                     for h in hist])


if __name__ == "__main__":
    main()
