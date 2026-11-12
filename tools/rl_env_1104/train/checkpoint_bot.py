"""Make an evaluable bot directory from a training checkpoint: the base bot's source with the checkpoint's exported
nn_weights.h (student_w_<it>.h). Release builds then contain exactly what the trainer evaluated.

usage: python -I tools/rl_env_1104/train/checkpoint_bot.py <base_src_dir> <student_w_N.h> <out_bot_dir>
"""
import hashlib
import os
import shutil
import sys


def main() -> None:
    base, weights, out = sys.argv[1], sys.argv[2], sys.argv[3]
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(base, os.path.join(out, "src"))
    shutil.copy(weights, os.path.join(out, "src", "nn_weights.h"))
    h = hashlib.sha256(open(os.path.join(out, "src", "nn_weights.h"), "rb").read()).hexdigest()
    print(out, "nn_weights", h[:12])


if __name__ == "__main__":
    main()
