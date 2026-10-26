"""Paired ladder A/B: replay the match groups other teams ran against v58, with the same opponent bot, maps and sides.

The local bench only measures our own lineage and does not predict the ladder (research/v59/V59_LOSS_ANALYSIS.md), so
a candidate's final check is the ladder itself. Match groups always play our active submission; `--source-group` pins
the opponent's bot to the version it used in that earlier group, so the comparison is paired game by game.

  python tools/replay/ladder_ab.py plan                      # show the sets and v58's record on them
  python tools/replay/ladder_ab.py queue [--sets N] [--yes]  # dry run unless --yes; uses N of today's 50 groups
  python tools/replay/ladder_ab.py collect --since <ISO time> # paired comparison against v58

Queueing spends the team's shared quota and plays whatever is active, so it is the user's decision.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'research/v59/V59_LADDER_AB_PLAN.json'
CLI = ROOT / 'tools/vendor/cambc.exe'


def cli(args):
    for attempt in range(6):
        r = subprocess.run([str(CLI)] + args, capture_output=True, text=True, encoding='utf8', errors='replace', timeout=180)
        if 'Rate limit' not in (r.stdout + r.stderr):
            return r
        time.sleep(3 + 2 * attempt)
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=['plan', 'queue', 'collect'])
    ap.add_argument('--sets', type=int, default=0, help='queue only the N sets v58 did worst on (0 = all)')
    ap.add_argument('--repeat', type=int, default=1, help='groups per set')
    ap.add_argument('--match-v58', type=int, default=0, help='groups per set = min(this, groups v58 played on it); overrides --repeat')
    ap.add_argument('--yes', action='store_true', help='actually queue (otherwise print the commands)')
    ap.add_argument('--since', help='collect: our groups created after this time')
    a = ap.parse_args()
    sets = json.loads(PLAN.read_text(encoding='utf8'))['sets']
    sets.sort(key=lambda s: s['v58_wins'] / s['v58_games'])
    if a.action == 'plan':
        for s in sets:
            print(f"{s['opponent'][:22]:22} v58 {s['v58_wins']:2}/{s['v58_games']:2}  {','.join(s['maps'])}  sides {''.join(s['sides'])}")
        print(f"{len(sets)} sets, v58 {sum(s['v58_wins'] for s in sets)}/{sum(s['v58_games'] for s in sets)}")
        return
    if a.action == 'queue':
        chosen = sets[:a.sets] if a.sets else sets
        log = ROOT / 'research/v59/ladder_ab_queue.jsonl'
        for s in chosen:
            for _ in range(min(a.match_v58, s['v58_groups']) if a.match_v58 else a.repeat):
                args = ['match-groups', 'create', s['opponentId'], '--source-group', s['sourceGroup'],
                        '--maps', ','.join(s['maps']), '--sides', ','.join(s['sides']), '--json']
                if not a.yes:
                    print('DRY RUN: cambc ' + ' '.join(args))
                    continue
                r = cli(args)
                rec = dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), opponent=s['opponent'], set=s['sourceGroup'],
                           ok=r.returncode == 0, out=(r.stdout + r.stderr)[-2000:])
                with log.open('a', encoding='utf8') as f:
                    f.write(json.dumps(rec) + '\n')
                print(s['opponent'], 'queued' if rec['ok'] else 'FAILED: ' + rec['out'][-300:])
        return
    # collect: our unranked games since the time, matched to the plan by opponent + map list + sides
    if not a.since:
        raise SystemExit('collect needs --since')
    found, cursor = {}, None
    for _ in range(20):
        args = ['matches', 'list', '--team', 'me', '--kind', 'unranked', '--limit', '100', '--json'] + (['--cursor', cursor] if cursor else [])
        d = json.loads(cli(args).stdout)
        for m in d['matches']:
            found[m['matchId']] = m
        cursor = d.get('nextCursor')
        if not cursor or min(m['createdAt'] for m in d['matches']) < a.since:
            break
    games = [m for m in found.values() if m['createdAt'] > a.since and m['status'] == 'finished']
    by_group = defaultdict(list)
    for m in games:
        by_group[m['groupId']].append(m)
    key = lambda name, maps, sides: (name, tuple(maps), tuple(sides))
    plan = {key(s['opponent'], s['maps'], s['sides']): s for s in sets}
    rows = defaultdict(lambda: [0, 0])
    for gid, ms in by_group.items():
        ms.sort(key=lambda m: m['position'])
        us = [next(t for t in m['teams'] if t['name'] == 'DOOMSDAY') for m in ms]
        them = next(t for t in ms[0]['teams'] if t['name'] != 'DOOMSDAY')['name']
        k = key(them, [m['map'] for m in ms], [u['side'] for u in us])
        if k in plan:
            rows[k][0] += sum(u['result'] == 'win' for u in us)
            rows[k][1] += len(us)
    tw = tn = bw = bn = 0
    for k, (w, n) in sorted(rows.items(), key=lambda kv: plan[kv[0]]['v58_wins'] / plan[kv[0]]['v58_games']):
        s = plan[k]
        print(f"{s['opponent'][:22]:22} candidate {w:2}/{n:2} = {w / n:.2f}   v58 {s['v58_wins']:2}/{s['v58_games']:2} = {s['v58_wins'] / s['v58_games']:.2f}")
        tw, tn, bw, bn = tw + w, tn + n, bw + s['v58_wins'], bn + s['v58_games']
    if tn:
        print(f'TOTAL candidate {tw}/{tn} = {tw / tn:.3f}; v58 on the same sets {bw}/{bn} = {bw / bn:.3f}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
