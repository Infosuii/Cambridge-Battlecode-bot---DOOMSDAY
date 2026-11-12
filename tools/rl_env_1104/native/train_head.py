"""PPO update of the native target head (JOHNDOE's TargetHead, clna-head-abi-v1) on native-head-v1 release shards.

Policy at the blend boundary (latent physical-group action, fixed downstream executor):
    pi(g | h) = (1 - alpha(h)) [g == reference] + alpha(h) * sum_{slots s -> g} softmax(native + residual(h))(s)
Only the head (11826 params) is trained; the native runtime that produced its inputs is frozen. Return convention
mc-terminal-gamma1-v1 (G = the team's final outcome for every decision of a complete game); advantage = G - mean
outcome over the batch's games. Clipped PPO ratio on the full mixture probability; each game contributes the SUM of
its decisions' surrogate terms and games are averaged (as train_gate.py, JOHNDOE #66).

Gates before any update: shards are native-head-v1 with the head ABI hash of head_export.py; the starting head is the
exact deployed header the batch was collected with (--header, version must equal the shard's) or a checkpoint whose
version equals it; the logged logp replays within 2e-4; reward_spec and proven outcomes as train_gate.py; optional
--map-manifest restricts to the training split; a batch with zero outcome variance is refused.
Writes head.pt (head, Adam state, ABI hash, update count, version) and clna_head_w.h for the next collection.

usage: python tools/rl_env_1104/native/train_head.py --shards runs/rl_env_1104/<ns> --header <the batch's clna_head_w.h>
          --out runs/rl_env_1104/head-update-01 [--map-manifest M.json] [--epochs 4 --lr 1e-3 --clip 0.2]
          [--resume <dir>/head.pt]
"""
import argparse
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import contract as C  # noqa: E402
import head_export as HX  # noqa: E402
import head_rows as HR  # noqa: E402
from target_head import TargetHead  # noqa: E402

REWARD_SPEC_ID = "mc-terminal-gamma1-v1"
P = 14


def load(root, game_offset, train_maps, want_version):
    keys = ("head_ctx", "head_camp", "head_feat", "head_native", "head_valid", "head_map", "ref_slot", "action",
            "logp", "reward")
    rows = {k: [] for k in keys + ("game",)}
    games, rejected = [], []
    for man, cols in C.iter_shards(root, layout=2, action_schema="native-head-v1"):
        hd = man.get("head", {})
        if not man.get("head_inputs") or hd.get("abi_hash") != HX.HEAD_ABI_HASH:
            raise SystemExit(f"{root}: not a clna-head-abi-v1 shard")
        if hd.get("version") != want_version:
            raise SystemExit(f"{root}: collected with head {hd.get('version')}, starting head is {want_version}")
        spec_ok = str(man.get("reward_spec", "")).startswith(REWARD_SPEC_ID + ":")
        for e, meta in enumerate(man["episodes"]):
            if not meta.get("ppo_eligible"):
                continue
            sel = cols["episode"] == e
            why = None
            if train_maps is not None and meta.get("map_file", "").replace(chr(92), "/").split("/")[-1] not in train_maps:
                why = f"map {meta.get('map_file')} is not in the manifest training split"
            elif not spec_ok:
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
                              outcome=meta["terminal_outcome"], decisions=int(sel.sum()), skips=meta.get("skips")))
            for k in keys:
                rows[k].append(cols[k][sel])
            rows["game"].append(np.full(int(sel.sum()), gi))
    if not games:
        return None, games, rejected
    return {k: np.concatenate(v) for k, v in rows.items()}, games, rejected


def tensors(R):
    n = len(R["action"])
    feat = HR.features(R["head_feat"].reshape(-1, 4)).reshape(n, 10, 4)
    valid = R["head_valid"].astype(bool)
    return dict(ctx=torch.from_numpy(R["head_ctx"].astype(np.float32) * np.float32(1 / 1024)),
                camp=torch.from_numpy((R["head_camp"].astype(np.float32) * np.float32(1 / 1024)).reshape(n, 10, 16)),
                feat=torch.from_numpy(feat), nat=torch.from_numpy(R["head_native"].astype(np.float32)),
                valid=torch.from_numpy(valid), map=torch.from_numpy(np.where(valid, R["head_map"], 0).astype(np.int64)),
                ref=torch.from_numpy(R["ref_slot"].astype(np.int64)), act=torch.from_numpy(R["action"].astype(np.int64)),
                logp=torch.from_numpy(R["logp"].astype(np.float64)), G=torch.from_numpy(R["reward"].astype(np.float64)),
                game=torch.from_numpy(R["game"].astype(np.int64)))


def policy_logp(m, t):
    pol, alpha, _ = m(t["ctx"], t["camp"], t["feat"], t["nat"], t["valid"], t["map"], t["ref"], P)
    return torch.log(pol[torch.arange(len(t["act"])), t["act"]].double()), alpha.flatten().double()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shards", nargs="+", required=True)
    ap.add_argument("--header", help="the clna_head_w.h the batch was collected with (fresh start)")
    ap.add_argument("--resume", help="head.pt whose version collected the batch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--clip", type=float, default=0.2)
    ap.add_argument("--map-manifest")
    a = ap.parse_args()
    if bool(a.header) == bool(a.resume):
        raise SystemExit("give exactly one of --header / --resume")
    if os.path.exists(a.out):
        raise SystemExit("output directory must be new")
    torch.manual_seed(1104)
    ck = None
    if a.resume:
        ck = torch.load(a.resume, weights_only=True)
        if ck["head_abi_hash"] != HX.HEAD_ABI_HASH:
            raise SystemExit("checkpoint head ABI differs")
        m = TargetHead()
        m.load_state_dict(ck["head"])
        start_ver = ck["version"]
    else:
        m, start_ver = HX.load_header(a.header)
    train_maps = None
    if a.map_manifest:
        with open(a.map_manifest, encoding="utf-8") as f:
            train_maps = {x["file"] for x in json.load(f)["maps"] if x["split"] == "training"}
    R, games, rejected = None, [], []
    for root in a.shards:
        part, g, rj = load(root, len(games), train_maps, start_ver)
        games += g
        rejected += rj
        if part is not None:
            R = part if R is None else {k: np.concatenate([R[k], part[k]]) for k in R}
    for r in rejected:
        print("rejected episode", r)
    if R is None:
        raise SystemExit("no eligible episodes")
    t = tensors(R)
    with torch.no_grad():
        lp0, al0 = policy_logp(m, t)
    replay_err = float((lp0 - t["logp"]).abs().max())
    if replay_err > 2e-4:
        raise SystemExit(f"behaviour logp replay failed: {replay_err}")
    outcomes = np.array([g["outcome"] for g in games], dtype=np.float64)
    if float(outcomes.std()) == 0.0:
        raise SystemExit(f"all {len(games)} games have outcome {outcomes[0]:+g}: zero advantage, no learning signal")
    adv = t["G"] - float(outcomes.mean())
    ng = len(games)
    opt = torch.optim.Adam(m.parameters(), lr=a.lr)
    if ck is not None:
        opt.load_state_dict(ck["optimizer"])
    os.makedirs(a.out)
    hist = []
    for ep in range(a.epochs):
        lp, al = policy_logp(m, t)
        ratio = torch.exp(lp - t["logp"])
        surr = torch.minimum(ratio * adv, torch.clamp(ratio, 1 - a.clip, 1 + a.clip) * adv)
        loss = -torch.zeros(ng, dtype=torch.float64).index_add(0, t["game"], surr).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        with torch.no_grad():
            hist.append(dict(epoch=ep, loss=float(loss.detach()), approx_kl=float((t["logp"] - lp).mean()),
                             alpha_mean=float(al.mean()), clip_frac=float(((ratio - 1).abs() > a.clip).double().mean())))
    with torch.no_grad():
        lp1, al1 = policy_logp(m, t)
        explore1 = float((1 - torch.exp(lp1)[t["act"] == t["ref"]]).mean()) if bool((t["act"] == t["ref"]).any()) else None
    updates = (ck["updates"] if ck is not None else 0) + a.epochs
    text, ver = HX.header(m, f"u{updates}")
    with open(os.path.join(a.out, "clna_head_w.h"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    torch.save(dict(head=m.state_dict(), optimizer=opt.state_dict(), head_abi=HX.HEAD_ABI, head_abi_hash=HX.HEAD_ABI_HASH,
                    updates=updates, version=ver, collected_with=start_ver, resumed_from=a.resume or ""),
               os.path.join(a.out, "head.pt"))
    rep = dict(kind="native target-head PPO update (mc-terminal-gamma1-v1); NOT a strength claim", version=ver,
               collected_with=start_ver, behaviour_replay_max_error=replay_err, games=games, decisions=int(len(t["act"])),
               outcome_mean=float(outcomes.mean()), epochs=hist, params=sum(p.numel() for p in m.parameters()),
               alpha_before=dict(mean=float(al0.mean()), min=float(al0.min()), max=float(al0.max())),
               alpha_after=dict(mean=float(al1.mean()), min=float(al1.min()), max=float(al1.max())),
               logged_ref_rows_nonref_mass_after=explore1, shards=a.shards, rejected_episodes=rejected,
               objective="sum of decision surrogates per game, mean over games", reward_spec=REWARD_SPEC_ID,
               head_abi_hash=HX.HEAD_ABI_HASH, resumed_from=a.resume, updates=updates, lr=a.lr, clip=a.clip)
    with open(os.path.join(a.out, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("version", "collected_with", "behaviour_replay_max_error", "decisions",
                                          "outcome_mean", "alpha_before", "alpha_after", "updates")}, indent=1))
    print("rejected episodes", len(rejected))
    print("epochs", [(h["epoch"], round(h["loss"], 4), round(h["approx_kl"], 6), round(h["clip_frac"], 4)) for h in hist])


if __name__ == "__main__":
    main()
