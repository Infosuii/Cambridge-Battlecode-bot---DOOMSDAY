"""Focused native fixture for the pure opportunity inventory; synthetic only."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class PolicyScheduleTests(unittest.TestCase):
    def test_native_synthetic_opportunities(self):
        configured = os.environ.get("NFS_TEST_CXX") or os.environ.get("CXX")
        candidates = [configured, shutil.which("g++"),
                      str(ROOT / "artifacts/tmp/native-toolchain/w64devkit/bin/g++.exe"),
                      "C:/msys64/ucrt64/bin/g++.exe"]
        compiler = next((p for p in candidates if p and Path(p).is_file()), None)
        if compiler is None:
            self.skipTest("native C++ compiler unavailable; set NFS_TEST_CXX")
        scratch = ROOT / "artifacts" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="policy_schedule_", dir=scratch) as temp:
            executable = Path(temp) / ("schedule.exe" if os.name == "nt" else "schedule")
            built = subprocess.run([compiler, "-std=c++20", "-O2", "-I", str(ROOT / "bot/src"),
                                    str(ROOT / "tests/cpp/policy_schedule_test.cpp"), "-o", str(executable)],
                                   text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            ran = subprocess.run([str(executable)], text=True, capture_output=True)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            self.assertIn("synthetic policy schedule fixture passed", ran.stdout)

if __name__ == "__main__":
    unittest.main()
