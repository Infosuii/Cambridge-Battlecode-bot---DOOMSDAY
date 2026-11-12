"""Compile and exercise production economy code against a synthetic SDK host; no engine/training."""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cxx", required=True)
    args = parser.parse_args()
    source = (ROOT / "bot/src/nn_policy_economy.cpp").read_text()
    source = source.replace('#include "nn_policy_config.h"', '#define NN_POLICY_V2 1')
    source = source.replace('#include "bot.h"', '#include "synthetic_shim.h"')
    source = source.replace('#include "nn_policy_options.h"', '')
    with tempfile.TemporaryDirectory(prefix="synthetic-economy-", dir=HERE) as temp:
        scratch = Path(temp)
        (scratch / "economy_under_test.cpp").write_text(source)
        output = scratch / "test.exe"
        command = [args.cxx, "-std=c++20", "-O0", "-Wall", "-Wextra", "-I", str(HERE), "-I", str(scratch),
                   "-I", str(ROOT / "bot/src"), str(HERE / "synthetic_test.cpp"),
                   str(ROOT / "bot/src/nn_policy_candidates.cpp"), "-o", str(output)]
        compiled = subprocess.run(command, text=True, capture_output=True)
        if compiled.returncode:
            print(compiled.stdout + compiled.stderr)
            return compiled.returncode
        ran = subprocess.run([str(output)], text=True, capture_output=True)
        report = {"synthetic": True, "passed": ran.returncode == 0, "returncode": ran.returncode,
                  "stdout": ran.stdout, "stderr": ran.stderr, "compiler_warnings": compiled.stderr}
        (HERE / "synthetic_result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return ran.returncode


if __name__ == "__main__":
    raise SystemExit(main())
