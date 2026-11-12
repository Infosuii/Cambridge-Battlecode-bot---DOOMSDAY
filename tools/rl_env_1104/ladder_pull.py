"""Pull our ranked ladder matches since --since: the match list (with each match's version, from --window activation
times) and every match's full download (replay, our logs, our fuel trace), cached so reruns only fetch new matches.
Read-only platform calls; HTTP 429 answers are retried after the delay the CLI reports (or 30 s).

usage: python -I tools/rl_env_1104/ladder_pull.py --since 2026-11-09T23:50 --window v130=2026-11-09T23:50 \
           --window v131=2026-11-10T03:25 ... [--cache artifacts/tmp/ladder_1110] [--no-download]
"""
import argparse, json, os, re, subprocess, sys, time

CLI = r"C:/Users/info/.venvs/cambc5/Scripts/cambc.exe"


def call(args, want_json=True):
    for attempt in range(8):
        p = subprocess.run([CLI] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode == 0:
            return json.loads(p.stdout) if want_json else p.stdout
        m = re.search(r"retry after (\d+)", p.stderr + p.stdout)
        wait = int(m.group(1)) + 1 if m else 30
        print(f"  cambc {' '.join(args[:2])} failed ({p.stderr.strip()[:120]}); retry in {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError("cambc kept failing: " + " ".join(args))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--window", action="append", required=True)
    ap.add_argument("--cache", default="artifacts/tmp/ladder_1110")
    ap.add_argument("--no-download", action="store_true")
    a = ap.parse_args()
    wins = sorted((w.split("=", 1)[1], w.split("=", 1)[0]) for w in a.window)
    os.makedirs(os.path.join(a.cache, "zips"), exist_ok=True)
    matches, cursor = [], None
    while True:
        d = call(["matches", "list", "--team", "me", "--kind", "ranked", "--limit", "100", "--json"] + (["--cursor", cursor] if cursor else []))
        page = d.get("matches", [])
        matches += [m for m in page if m["createdAt"] >= a.since]
        cursor = d.get("nextCursor")
        if not cursor or not page or min(m["createdAt"] for m in page) < a.since:
            break
    for m in matches:
        v = None
        for start, name in wins:
            if m["createdAt"] >= start:
                v = name
        m["version"] = v
        us = [t for t in m["teams"] if t.get("name") == "DOOMSDAY"]
        op = [t for t in m["teams"] if t.get("name") != "DOOMSDAY"]
        m["us"], m["opp"] = (us[0] if us else {}), (op[0] if op else {})
    json.dump(matches, open(os.path.join(a.cache, "matches.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = {}
    for m in matches:
        r = by.setdefault(m["version"], [0, 0])
        r[0] += m["us"].get("result") == "win"
        r[1] += 1
    print(f"{len(matches)} ranked matches since {a.since}:", {k: f"{w}/{n}" for k, (w, n) in sorted(by.items(), key=lambda x: str(x[0]))}, flush=True)
    if a.no_download:
        return
    todo = [m for m in matches if not os.path.exists(os.path.join(a.cache, "zips", m["matchId"] + ".zip"))]
    print(f"downloading {len(todo)} matches", flush=True)
    for i, m in enumerate(todo):
        out = os.path.join(a.cache, "zips", m["matchId"] + ".zip")
        tmp = out + ".part"
        call(["matches", "download", m["matchId"], "-o", tmp], want_json=False)
        os.replace(tmp, out)
        if i % 20 == 0:
            print(f"  {i + 1}/{len(todo)}", flush=True)
    print("PULL_DONE", flush=True)


if __name__ == "__main__":
    main()
