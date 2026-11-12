"""Compile unchanged production options/candidate code against an explicitly synthetic SDK fixture."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cxx", required=True)
    parser.add_argument("--sdk-syntax", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="strategy_synthetic_", dir=ROOT / "artifacts" / "tmp") as temp:
        stage = Path(temp)
        if args.sdk_syntax:
            sdk = stage / "sdk_syntax"
            sdk.mkdir()
            for source in (ROOT / "bot" / "src").glob("*.h"):
                shutil.copy2(source, sdk / source.name)
            shutil.copy2(ROOT / "bot" / "src" / "nn_policy_strategy.cpp", sdk / "nn_policy_strategy.cpp")
            (sdk / "nn_policy_config.h").write_text("#pragma once\n#define NN_POLICY_V2 1\n#define NN_POLICY_LOG 0\n#define NN_POLICY_SAMPLE 0\n")
            subprocess.run([args.cxx, "-std=c++20", "-fsyntax-only", "-I", str(ROOT / "sdk" / "cpp"), "nn_policy_strategy.cpp"], cwd=sdk, check=True)
            print("actual SDK strategy native syntax passed")
        for name in ["nn_policy_strategy.cpp", "nn_policy_options.h", "nn_policy_candidates.h", "nn_policy_candidates.cpp", "nn_rt.h", "nn_config.h"]:
            shutil.copy2(ROOT / "bot" / "src" / name, stage / name)
        for name in ["bot.h", "common.h", "test.cpp"]:
            shutil.copy2(Path(__file__).with_name("fixture") / name, stage / name)
        (stage / "nn_policy_config.h").write_text("#pragma once\n#define NN_POLICY_V2 1\n")
        exe = stage / "fixture.exe"
        subprocess.run([args.cxx, "-std=c++20", "-O2", "-ffp-contract=off", "nn_policy_strategy.cpp", "nn_policy_candidates.cpp", "test.cpp", "-o", str(exe)], cwd=stage, check=True)
        subprocess.run([str(exe)], cwd=stage, check=True)

if __name__ == "__main__":
    main()
