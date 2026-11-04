"""Duel pipeline (research/x3/DUEL.md): upload candidates one at a time (each upload cancels a queued compile), wait
for each compile, then play the v92 baseline arm and every candidate arm on the same plan, and restore v92.
  python tools/replay/duel_pipeline.py --plan P.json --base 80 --cands v92af v92a3i v92bru v92own [--have NAME=VER ...]"""
import argparse, json, subprocess, sys, time
from pathlib import Path
from ladder_duel import required_pin_sources
ROOT = Path(__file__).resolve().parents[2]; CLI = str(ROOT / 'tools/vendor/cambc.exe')
def subs():
    for _ in range(10):
        r = subprocess.run([CLI, 'submissions', 'list', '--json'], capture_output=True)
        try: return json.loads(r.stdout.decode('utf-8'))
        except ValueError: time.sleep(10)
    raise SystemExit('no submissions list')
def items(d): return d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))
def upload(name):
    for attempt in range(8):
        before = {s['version'] for s in items(subs())}
        r = subprocess.run([CLI, 'submit', f'bots/{name}', '--note', f'duel candidate {name}'], capture_output=True, cwd=ROOT)
        out = (r.stdout + r.stderr).decode('utf-8', 'replace')
        for _ in range(6):
            new = [s for s in items(subs()) if s['version'] not in before and s.get('fileName', '').startswith(name) or (s['version'] not in before)]
            if new: break
            time.sleep(10)
        if new:
            v = max(s['version'] for s in new); print(name, 'uploaded as', v, flush=True)
            for _ in range(120):  # wait for the compile
                st = next(s['status'] for s in items(subs()) if s['version'] == v)
                if st not in ('queued', 'compiling', 'building', 'pending'):
                    print(name, v, 'status', st, flush=True); return v if st in ('active', 'inactive', 'ready') else None
                time.sleep(15)
            return None
        print(name, 'upload failed, retry', attempt, out[-120:], flush=True); time.sleep(30 + 30 * attempt)
    return None
ap = argparse.ArgumentParser(); ap.add_argument('--plan', required=True); ap.add_argument('--base', type=int, required=True)
ap.add_argument('--cands', nargs='*', default=[]); ap.add_argument('--have', nargs='*', default=[]); ap.add_argument('--recheck', default='', help='arm name: replay the base version at the end (opponent drift check)'); a = ap.parse_args()
vers = dict(x.split('=') for x in a.have)
# One pipeline at a time: a second uploader puts its builds live in the middle of our arms.
LOCK = ROOT / 'research/x3/duel/.pipeline.lock'
LOCK.parent.mkdir(parents=True, exist_ok=True)
try:
    import os as _os
    if LOCK.exists():
        pid = int(LOCK.read_text().strip() or 0)
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            alive = bool(h); ctypes.windll.kernel32.CloseHandle(h) if h else None
        except Exception:
            alive = True
        if alive and pid != _os.getpid():
            raise SystemExit(f'another duel pipeline (pid {pid}) holds {LOCK}; stop it first')
    LOCK.write_text(str(_os.getpid()))
except SystemExit:
    raise
duel = [sys.executable, str(ROOT / 'tools/replay/ladder_duel.py')]
attempted = False
try:
    for _ in range(120):  # never upload while another compile is queued: the upload would cancel it
        if not any(s['status'] in ('queued', 'compiling', 'building', 'pending') for s in items(subs())): break
        time.sleep(15)
    else:
        raise SystemExit('a compile is still queued; no upload attempted')
    # Each candidate is uploaded right before its own arm (an upload goes live when compiled, so never during an arm).
    arms = [('v92', a.base)] + [(c, None) for c in a.cands] + ([(a.recheck, a.base)] if a.recheck else [])
    for arm, v in arms:
        plan = json.loads(Path(a.plan).read_text(encoding='utf8'))
        if arm in plan['arms']: print('arm', arm, 'already played'); continue
        required_pin_sources(plan, arm)
        if v is None:
            if arm in vers:
                v = int(vers[arm])
            else:
                attempted = True
                v = upload(arm)
            if not v: print('skip', arm, '(no compiled version)', flush=True); continue
        attempted = True
        t0 = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        subprocess.run(duel + ['run', '--plan', a.plan, '--version', str(v), '--arm', arm], check=True)
        t1 = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        # Contamination check: did any other version become active while this arm's games were played?
        others = [s for s in items(subs()) if s['version'] != v and s.get('status') in ('active', 'inactive') and t0 <= s.get('statusAt', '')[:19] <= t1 and s.get('createdAt', '')[:19] >= t0]
        if others:
            print(f"CONTAMINATED arm {arm}: versions {[s['version'] for s in others]} were uploaded during it", flush=True)
            pl = json.loads(Path(a.plan).read_text(encoding='utf8')); pl['arms'][arm]['contaminated'] = [s['version'] for s in others]
            Path(a.plan).write_text(json.dumps(pl, indent=1, ensure_ascii=False) + chr(10), encoding='utf8')
        subprocess.run(duel + ['report', '--plan', a.plan, '--arms', 'v92', arm] if arm != 'v92' else duel + ['report', '--plan', a.plan, '--arms', 'v92'], check=True)
finally:
    if attempted:
        subprocess.run(duel + ['restore', '--version', str(a.base)], check=True)
    LOCK.unlink(missing_ok=True)
print('PIPELINE_DONE', flush=True)
