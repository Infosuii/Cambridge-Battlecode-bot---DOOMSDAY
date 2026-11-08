"""Restore a subset of the content-addressed agentic research snapshot (research/agentic-improvement-20261107).

Reads archives straight from the git branch with `git show` (no checkout), verifies every object hash, and writes
only the files whose path starts with one of the given prefixes. Never executes anything it restores.

usage: python -I tools/rl_env_1104/restore_subset.py <out_dir> <prefix> [<prefix> ...] [--ref origin/research/...]
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import zipfile

SNAP = "research/agentic-improvement-20261107"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("prefix", nargs="+")
    ap.add_argument("--ref", default="origin/research/agentic-improvement-20261107")
    ap.add_argument("--list", action="store_true", help="only list matching paths and sizes")
    a = ap.parse_args()
    show = lambda path: subprocess.run(["git", "show", f"{a.ref}:{SNAP}/{path}"], capture_output=True, check=True).stdout
    idx = json.loads(show("index/artifacts.json"))
    files = {p: s for p, s in idx["files"].items() if p.startswith(tuple(a.prefix))}
    total = sum(s["bytes"] for s in files.values())
    print(f"{len(files)} files, {total / 1e6:.1f} MB")
    if a.list:
        for p in sorted(files):
            print(p, files[p]["bytes"])
        return
    by_archive = {}
    for p, s in files.items():
        o = idx["objects"][s["sha256"]]
        by_archive.setdefault(o["archive"], []).append((p, s, o["entry"]))
    for arch, items in sorted(by_archive.items()):
        z = zipfile.ZipFile(io.BytesIO(show(arch)))
        for p, s, entry in items:
            data = z.read(entry)
            assert hashlib.sha256(data).hexdigest() == s["sha256"] and len(data) == s["bytes"], p
            tgt = os.path.realpath(os.path.join(a.out, p))
            assert tgt.startswith(os.path.realpath(a.out)), p
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            with open(tgt, "wb") as f:
                f.write(data)
        print(arch, len(items), "files")


if __name__ == "__main__":
    main()
