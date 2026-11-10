"""Decode downloaded ladder matches (ladder_pull.py cache) into dump.mjs JSON: one frame per round and every action step.
Losses first, newest first, for the versions given; skips matches already decoded. Runs --workers node processes.
usage: python -I tools/rl_env_1104/ladder_decode.py --cache artifacts/tmp/ladder_1110 --versions v130 v134 v135 [--workers 2]
"""
import argparse, concurrent.futures as cf, json, os, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def decode(zpath, out):
    with zipfile.ZipFile(zpath) as z:
        name = next(n for n in z.namelist() if n.endswith(".repl26a"))
        data = z.read(name)
    if data[:2] == b"PK":  # a bundle inside the bundle
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as z2:
            data = z2.read(next(n for n in z2.namelist() if n.endswith(".repl26a")))
    with tempfile.NamedTemporaryFile(suffix=".repl26a", delete=False) as f:
        f.write(data)
        tmp = f.name
    try:
        p = subprocess.run(["node", os.path.join(ROOT, "tools", "replay3", "dump.mjs"), tmp, out + ".part"],
                           capture_output=True, text=True)
        if p.returncode == 0:
            os.replace(out + ".part", out)
            return True, p.stdout.strip()
        return False, p.stderr.strip()[-300:]
    finally:
        os.unlink(tmp)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--versions", nargs="+", required=True)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    matches = json.load(open(os.path.join(a.cache, "matches.json"), encoding="utf-8"))
    os.makedirs(os.path.join(a.cache, "dumps"), exist_ok=True)
    todo = [m for m in matches if m.get("version") in a.versions]
    todo.sort(key=lambda m: (m["us"].get("result") != "loss", m["createdAt"]), reverse=False)
    todo.sort(key=lambda m: m["us"].get("result") != "loss")  # losses first; newest first within each
    jobs = []
    for m in todo:
        z = os.path.join(a.cache, "zips", m["matchId"] + ".zip")
        out = os.path.join(a.cache, "dumps", m["matchId"] + ".json")
        if os.path.exists(z) and not os.path.exists(out):
            jobs.append((z, out, m))
    print(f"{len(jobs)} matches to decode", flush=True)
    done = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for (z, out, m), (ok, msg) in zip(jobs, ex.map(lambda j: decode(j[0], j[1]), jobs)):
            done += 1
            if not ok:
                print(f"  FAIL {m['matchId']} {m.get('map')}: {msg}", flush=True)
            if done % 10 == 0:
                print(f"  {done}/{len(jobs)}", flush=True)
    print("DECODE_DONE", flush=True)


if __name__ == "__main__":
    main()
