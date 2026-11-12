"""Proxy opponent, step 5: fit the proxy's fight knobs so it plays v65 the way the top teams played v65 on the ladder.

  python tools/proxy/fit_style.py --space research/proxy/fit_space.json --out artifacts/evaluations/proxy-fit/<run>
         [--passes 2] [--seeds 1] [--base bots/proxy] [--probe bots/v65]

Each candidate is bots/proxy with some `#define` values changed (tools/make_variant.py). It plays the ladder duel's
schedule against the probe (v65) with tools/proxy/local_duel.py --per-team --replays, its replays are measured with
tools/proxy/fight_style.mjs, and its fingerprint against v65 is compared with the top teams' fingerprint against v65
on the ladder (research/proxy/style_ladder.json, class top@v65; the probe side with us:v65). The loss is a weighted
sum of squared, scaled differences (TARGETS below). Coordinate search: each pass tries every value of every knob with
the others at the current best, and keeps a change only when it lowers the loss.

The space file: {"KNOB": [value, ...], ...}, first value = the starting point. Every evaluation is appended to
<out>/fit_log.jsonl; finished candidates are reused when the search is resumed.
The fitted knobs say only how well v65 can be made to look like a top team against v65; whether the result gives
the ladder's verdicts on other versions is checked separately (tools/proxy/compare.py).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/proxy'))
import style_report as sr  # noqa: E402

PY = sys.executable
# (measure, side, scale, weight): side "proxy" compares the proxy with top@v65, "probe" compares v65 with us:v65.
TARGETS = [('margin', 'proxy', 100.0, 2.0), ('deaths', 'proxy', 2.0, 1.0), ('deaths', 'probe', 2.0, 1.0),
           ('back_off', 'proxy', 0.03, 1.0), ('walk_in', 'proxy', 0.03, 1.0), ('alone_in_contact', 'proxy', 0.03, 1.0),
           ('focus_shared', 'proxy', 0.03, 1.0), ('died5|contact', 'proxy', 0.01, 1.0)]


def run(cmd, log):
    with open(log, 'a', encoding='utf8') as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f'failed ({p.returncode}): {" ".join(map(str, cmd))}; see {log}')


def evaluate(cand, a, out):
    """Fingerprints of the proxy and the probe for one candidate {knob: value}."""
    name = 'c' + hashlib.sha1(json.dumps(cand, sort_keys=True).encode()).hexdigest()[:10]  # short: Windows paths
    cdir = out / name
    fp_path = cdir / 'fingerprint.json'
    if fp_path.exists():
        return name, json.loads(fp_path.read_text(encoding='utf8'))
    cdir.mkdir(parents=True, exist_ok=True)
    log = cdir / 'log.txt'
    bot = cdir / 'bot'
    run([PY, str(ROOT / 'tools/make_variant.py'), str(a.base), str(bot)] + [f'{k}={v}' for k, v in cand.items()], log)
    duel = cdir / 'duel'
    if not (duel / 'games.json').exists():
        run([PY, str(ROOT / 'tools/proxy/local_duel.py'), '--plan', str(a.plan), '--bot', str(a.probe), '--name', 'probe',
             '--proxy', str(bot), '--per-team', '--replays', '--seeds', *map(str, a.seeds), '--workers', str(a.workers),
             '--out', str(duel)], log)
    style = cdir / 'style.jsonl'
    env_cmd = ['node', '--no-warnings', str(ROOT / 'tools/proxy/fight_style.mjs'), str(style), str(duel / 'replays')]
    with open(log, 'a', encoding='utf8') as f:
        p = subprocess.run(env_cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, 'NFS_REPLAY_ENGINE': '2.0.0'})
    if p.returncode:
        raise RuntimeError('fight_style failed; see ' + str(log))
    games = sr.load([str(style)], [str(duel / 'replays/index.json')])
    for g, info in games:
        info['bots'] = {k: ('probe' if v == 'probe' else 'proxy') for k, v in info['bots'].items()}
    fp = sr.fingerprint(games)
    fp_path.write_text(json.dumps(fp, indent=1) + '\n', encoding='utf8', newline='\n')
    return name, fp


def loss(fp, target):
    total, parts = 0.0, {}
    for key, side, scale, weight in TARGETS:
        mine = fp[side].get(key)
        want = target['top@v65' if side == 'proxy' else 'us:v65'].get(key)
        if mine is None or want is None:
            continue
        z = (mine - want) / scale
        parts[f'{side}:{key}'] = round(mine, 3)
        total += weight * z * z
    return total, parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--space', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--passes', type=int, default=2)
    ap.add_argument('--seeds', type=int, nargs='+', default=[1])
    ap.add_argument('--workers', type=int, default=18)
    ap.add_argument('--base', default=str(ROOT / 'bots/proxy'))
    ap.add_argument('--probe', default=str(ROOT / 'bots/v65'))
    ap.add_argument('--plan', default=str(ROOT / 'research/v59/duel_top1.json'))
    ap.add_argument('--target', default=str(ROOT / 'research/proxy/style_ladder.json'))
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if not out.is_relative_to(ROOT / 'artifacts'):
        raise SystemExit('output inside artifacts/ required')
    out.mkdir(parents=True, exist_ok=True)
    space = json.loads(Path(a.space).read_text(encoding='utf8'))
    target = json.loads(Path(a.target).read_text(encoding='utf8'))
    flog = out / 'fit_log.jsonl'
    best = {k: v[0] for k, v in space.items()}
    seen = {}

    def score(cand):
        key = json.dumps(cand, sort_keys=True)
        if key not in seen:
            name, fp = evaluate(cand, a, out)
            l, parts = loss(fp, target)
            seen[key] = l
            with open(flog, 'a', encoding='utf8') as f:
                f.write(json.dumps(dict(candidate=cand, name=name, loss=round(l, 3), **parts)) + '\n')
            print(f'loss {l:8.2f}  {cand}  {parts}', flush=True)
        return seen[key]

    best_loss = score(best)
    for p in range(a.passes):
        changed = False
        for k, values in space.items():
            for v in values:
                if v == best[k]:
                    continue
                cand = dict(best, **{k: v})
                l = score(cand)
                if l < best_loss:
                    best, best_loss, changed = cand, l, True
        print(f'pass {p + 1}: best {best_loss:.2f} {best}', flush=True)
        if not changed:
            break
    (out / 'best.json').write_text(json.dumps(dict(best=best, loss=best_loss), indent=1) + '\n', encoding='utf8', newline='\n')


if __name__ == '__main__':
    main()
