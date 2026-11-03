"""Duel pipeline (research/x3/DUEL.md): upload candidates one at a time (each upload cancels a queued compile), wait
for each compile, then play the v92 baseline arm and every candidate arm on the same plan, and restore v92.
  python tools/replay/duel_pipeline.py --plan P.json --base 80 --cands v92af v92a3i v92bru v92own [--have NAME=VER ...]"""
import argparse, json, subprocess, sys, time
from pathlib import Path
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
for _ in range(120):  # never upload while another compile is queued: the upload would cancel it
    if not any(s['status'] == 'queued' for s in items(subs())): break
    time.sleep(15)
duel = [sys.executable, str(ROOT / 'tools/replay/ladder_duel.py')]
# Each candidate is uploaded right before its own arm (an upload goes live when compiled, so never during an arm).
arms = [('v92', a.base)] + [(c, None) for c in a.cands] + ([(a.recheck, a.base)] if a.recheck else [])
for arm, v in arms:
    plan = json.loads(Path(a.plan).read_text(encoding='utf8'))
    if arm in plan['arms']: print('arm', arm, 'already played'); continue
    if v is None:
        v = int(vers[arm]) if arm in vers else upload(arm)
        if not v: print('skip', arm, '(no compiled version)', flush=True); continue
    subprocess.run(duel + ['run', '--plan', a.plan, '--version', str(v), '--arm', arm])
    subprocess.run(duel + ['report', '--plan', a.plan, '--arms', 'v92', arm] if arm != 'v92' else duel + ['report', '--plan', a.plan, '--arms', 'v92'])
subprocess.run(duel + ['restore', '--version', str(a.base)])
print('PIPELINE_DONE', flush=True)
