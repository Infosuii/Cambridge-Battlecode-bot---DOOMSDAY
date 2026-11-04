"""Checks for run_eval.py (JOHNDOE #70): paired() against JOHNDOE's PAIRED_EVALUATION_FIXTURES, and the refusals that
must happen before any build (unknown split name, zero maps, provisional confirmation).

usage (repo root): python tools/rl_env_1104/eval/test_run_eval.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import run_eval as E  # noqa: E402

FIXTURES = os.path.join(ROOT, "research", "rl_env_1104", "eval", "PAIRED_EVALUATION_FIXTURES.json")


def test_fixtures() -> int:
    with open(FIXTURES, encoding="utf-8") as f:
        d = json.load(f)
    for c in d["cases"]:
        if "expected_error" in c:
            try:
                E.paired(c["rows"], c["expected_cells"])
            except ValueError as e:
                assert str(e) == c["expected_error"], (c["case"], e)
            else:
                raise AssertionError(f"{c['case']}: no error")
            continue
        got = E.paired(c["rows"], c["expected_cells"])
        for k, want in c["expected"].items():
            assert got[k] == want, (c["case"], k, got[k], want)
    return len(d["cases"])


def refuses(args: list, needle: str, man: dict) -> None:
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "m.json")
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(man, f)
        out = os.path.join("runs", "rl_env_1104", "eval", "_test_must_not_exist")
        r = subprocess.run([sys.executable, os.path.join(HERE, "run_eval.py"), "--manifest", mp, "--candidate",
                            "c=bots/v92", "--opponent", "o=bots/v92", "--out", out] + args, cwd=ROOT,
                           capture_output=True, text=True)
        assert r.returncode != 0 and needle in r.stderr, (args, r.stderr[-500:])
        assert not os.path.exists(os.path.join(ROOT, out)), "refusal created the output directory"


def main() -> None:
    n = test_fixtures()
    m = dict(status="PROVISIONAL_REQUIRES_GEOMETRY_AUDIT", maps=[dict(file="00corners.map26a", split="development",
                                                                    family="f", sha256="0" * 64)])
    refuses(["--split", "confirmation"], "invalid choice", m)
    refuses(["--split", "training"], "has no maps", m)
    refuses(["--split", "confirmation_reserved"], "without --confirm", m)
    refuses(["--split", "confirmation_reserved", "--confirm"], "PROVISIONAL", m)
    refuses(["--split", "development", "--sides", ","], "no cells", m)
    refuses(["--split", "development", "--reference", "x"], "not a candidate", m)
    print(f"OK: {n} paired fixture cases, 6 refusals")


if __name__ == "__main__":
    main()
