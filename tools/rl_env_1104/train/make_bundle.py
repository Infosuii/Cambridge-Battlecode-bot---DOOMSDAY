"""Build a slim, local-only training bundle for a remote CPU box (e.g. a GitHub Codespace via `gh codespace cp`).

Never committed or pushed: the tarball is written under artifacts/tmp. It mirrors the layout the trainer expects:
  bundle/cl_train.sh
  bundle/training/agent2/lab/{train,train_ops,nn_model,nn_export,quant_policy,team_reward}.py   (this tools/ copy)
  bundle/training/v4/{cambc.toml,cmake,sdk,maps_ladder96,maps_sel12,maps_pooltrain,bots/<league + base>/src}
  bundle/training/runs/release-es/auto_es_g12_parent.pt      (v112's exact network)
  bundle/reference/nn-rl6-original/nn_rl6/value_10.pt        (critic init)
Build caches, rollouts, replays, maps_real250 and unused bots are left out; nnfinal ships as its pinned prebuilt WASM.

usage: python -I tools/rl_env_1104/train/make_bundle.py artifacts/tmp/agentic_restore artifacts/tmp/cl_bundle.tar.gz [--bots a,b,...]
"""
import argparse
import os
import tarfile

LAB_FILES = ("train.py", "train_ops.py", "nn_model.py", "nn_export.py", "quant_policy.py", "team_reward.py")
DEFAULT_BOTS = "cl112,v112,v111,nnm4,nnm4n1,nnm4n2,v92,ref_x1,ref_x3ctr,ref_p65pack,v86h,x3inv,nnfinal"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("restore")
    ap.add_argument("out")
    ap.add_argument("--bots", default=DEFAULT_BOTS)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    r = a.restore
    v4 = os.path.join(r, "training", "v4")
    with tarfile.open(a.out, "w:gz") as t:
        t.add(os.path.join(r, "cl_train.sh"), "bundle/cl_train.sh")
        for f in LAB_FILES:
            t.add(os.path.join(here, f), f"bundle/training/agent2/lab/{f}")
        for item in ("cambc.toml", "cmake", "sdk", "maps_ladder96", "maps_sel12", "maps_pooltrain"):
            t.add(os.path.join(v4, item), f"bundle/training/v4/{item}")
        for b in a.bots.split(","):
            src = os.path.join(v4, "bots", b, "src")
            t.add(src, f"bundle/training/v4/bots/{b}/src")
            if b == "nnfinal":
                for kind in ("build", "build-release"):
                    t.add(os.path.join(v4, "bots", b, ".cambc", kind, "bot-injected.wasm"),
                          f"bundle/training/v4/bots/{b}/.cambc/{kind}/bot-injected.wasm")
        t.add(os.path.join(r, "training", "runs", "release-es", "auto_es_g12_parent.pt"),
              "bundle/training/runs/release-es/auto_es_g12_parent.pt")
        t.add(os.path.join(r, "reference", "nn-rl6-original", "nn_rl6", "value_10.pt"),
              "bundle/reference/nn-rl6-original/nn_rl6/value_10.pt")
    print(a.out, round(os.path.getsize(a.out) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
