"""Make a bot directory of the native target-head build for evaluation (run_eval.py), configured exactly as
collect_native.py --head builds it: CLNA_EPS, CLNA_RLOG 1, CLNA_HEAD 1 (+ optional CLNA_HEAD_MIN) and a given
clna_head_w.h. The release logging build IS the evaluated artifact (JOHNDOE #69).

usage: python tools/rl_env_1104/native/make_head_bot.py --out artifacts/tmp/rl_env_1104/eval-bots/head1 \
           --header runs/rl_env_1104/head-update-01/clna_head_w.h [--eps 0.02] [--head-min 35000]
"""
import argparse
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--header", required=True)
    ap.add_argument("--eps", type=float, default=0.02)
    ap.add_argument("--head-min", type=int)
    ap.add_argument("--cond", action="store_true", help="conditional head (CLNA_COND): cheap gate, one-shot head on invoke")
    a = ap.parse_args()
    out = os.path.join(ROOT, a.out)
    if os.path.exists(out):
        raise SystemExit("output directory must be new")
    src = os.path.join(ROOT, "bots", "claude-native-1104", "src")
    shutil.copytree(src, os.path.join(out, "src"), ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
    shutil.copyfile(os.path.join(ROOT, a.header), os.path.join(out, "src", "clna_head_w.h"))
    ch = os.path.join(out, "src", "common.h")
    with open(ch, encoding="utf-8") as f:
        text = f.read()
    defs = f"#define CLNA_EPS {a.eps!r}\n#define CLNA_RLOG 1\n#define CLNA_HEAD 1\n"
    if a.head_min:
        defs += f"#define CLNA_HEAD_MIN {a.head_min}\n"
    if a.cond:
        defs += "#define CLNA_COND 1\n"
    with open(ch, "w", encoding="utf-8", newline="") as f:
        f.write(defs + text)
    print(out)


if __name__ == "__main__":
    main()
