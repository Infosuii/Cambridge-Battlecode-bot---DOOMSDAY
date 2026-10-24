"""Run only the synthetic native SDK tactics harness; no engine matches or training."""
from pathlib import Path
import argparse
import json
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    compiler = args.compiler or root / "artifacts/tmp/native-toolchain/w64devkit/bin/g++.exe"
    compiler = compiler.resolve()
    output = root / "artifacts/tmp/v2_tactics_synthetic.exe"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(compiler), "-std=c++20", "-O1", "-Wno-subobject-linkage", "-ffunction-sections",
               "-fdata-sections", "-Wl,--gc-sections", "-Isdk/cpp", "-Ibot/src", "-include",
               "agents/v2_tactics_integration/active.h", "agents/v2_tactics_integration/test_synthetic.cpp",
               "bot/src/nn_policy_candidates.cpp", "-o", str(output)]
    subprocess.run(command, cwd=root, check=True)
    result = subprocess.run([str(output)], cwd=root, check=True, capture_output=True, text=True)
    print(result.stdout, end="")
    receipt = {"kind": "synthetic", "passed": True, "command": command,
               "stdout": result.stdout.strip(), "engine_matches": 0, "training_jobs": 0}
    (root / "agents/v2_tactics_integration/synthetic_result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
