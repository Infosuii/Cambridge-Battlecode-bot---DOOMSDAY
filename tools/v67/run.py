"""Run the fixed v67 benchmark, save exact output, and record native statistics."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--set', action='append', default=[], metavar='NAME=VALUE')
    ap.add_argument('--opponent', default='v65')
    ap.add_argument('--seeds', nargs='+', type=int, default=[1, 2])
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--holdout', action='store_true')
    ap.add_argument('--record-existing', action='store_true')
    ap.add_argument('--note', default='')
    a = ap.parse_args()
    if a.holdout and a.set:
        ap.error('freeze source before running a holdout')
    if any(s in (3, 4) for s in a.seeds) and not a.holdout:
        ap.error('seeds 3/4 are reserved for the frozen holdout')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', a.run):
        ap.error('run must be a directory name')
    out = ROOT / 'artifacts/evaluations/v67' / a.run
    if a.record_existing and a.set:
        ap.error('historical runs cannot change source settings')
    src = (out / 'build' / f'src-bot-s{a.seeds[0]}' / 'src') if a.record_existing else ROOT / 'bots/v67/src'
    if not src.is_dir():
        ap.error('missing exact source snapshot for benchmark')
    common = src / 'common.h'
    code = common.read_bytes().decode('utf8')
    if a.record_existing:
        # Reconstruct the source input before local_duel's documented seed rewrite.
        code = re.sub(rf'^#define NOVA_SEED {a.seeds[0]}\r?$',
                      lambda m: '#define NOVA_SEED 1' + ('\r' if m[0].endswith('\r') else ''), code, flags=re.M)
    end = '\r\n' if '\r\n' in code else '\n'
    changes = {}
    for setting in a.set:
        name, value = setting.split('=', 1)
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', name) or not re.fullmatch(r'[-+0-9.eEfF,uU]+', value):
            ap.error('invalid --set')
        pattern = rf'(^#define {name} )[^\r\n]*'
        if re.search(pattern, code, flags=re.M):
            code = re.sub(pattern, lambda m: m[1] + value, code, flags=re.M)
        else:
            code = f'#define {name} {value}{end}' + code
        changes[name] = value
    if changes:
        common.write_bytes(code.encode('utf8'))
    if code.splitlines().count('#define NOVA_SEED 1') != 1:
        raise SystemExit('v67 must have exactly one #define NOVA_SEED 1')
    hashes = {p.relative_to(src).as_posix(): hashlib.sha256(code.encode('utf8') if p == common else p.read_bytes()).hexdigest()
              for p in sorted(src.rglob('*')) if p.is_file()}
    frozen = json.loads((ROOT / 'research/v67/V65_SOURCE_SHA256.json').read_text())
    for name, sha in frozen.items():
        if hashlib.sha256((ROOT / 'bots/v65/src' / name).read_bytes()).hexdigest() != sha:
            raise SystemExit('v65 source changed: ' + name)
    if not a.record_existing:
        command = [sys.executable, 'tools/proxy/local_duel.py', '--plan', 'research/v59/duel_top1.json',
                   '--bot', 'bots/v67', '--name', 'v67', '--proxy', 'bots/' + a.opponent,
                   '--seeds', *map(str, a.seeds), '--workers', str(a.workers), '--replays', '--out', str(out)]
        p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf8', errors='replace')
        out.mkdir(parents=True, exist_ok=True)
        (out / 'benchmark-output.txt').write_text(p.stdout + p.stderr, encoding='utf8', newline='\n')
        print(p.stdout + p.stderr, end='', flush=True)
        if p.returncode:
            raise SystemExit(p.returncode)
    run = json.loads((out / 'games.json').read_text(encoding='utf8'))
    rows = run['games']
    if run['seeds'] != a.seeds or Path(run['proxy']).name != a.opponent:
        raise SystemExit('run metadata does not match the requested seeds/opponent')
    plan = json.loads((ROOT / 'research/v59/duel_top1.json').read_text(encoding='utf8'))
    expected = sorted((seed, gi, k + 1, name, side)
                      for seed in a.seeds for gi, group in enumerate(plan['groups'])
                      for k, (name, side) in enumerate(zip(group['maps'], group['sides'])))
    actual = sorted((r['seed'], r['group'], r['slot'], r['map'], r['side']) for r in rows)
    if actual != expected:
        raise SystemExit('benchmark does not contain the exact complete fixed schedule')
    if len(rows) != 120 * len(a.seeds):
        raise SystemExit('incomplete benchmark')
    metrics, opponents, per_map = Counter(), Counter(), {}
    for row in rows:
        d = json.loads((ROOT / row['folder'] / 'summary.json').read_text(encoding='utf8'))
        ours = 'team' + row['side'].upper()
        theirs = 'teamB' if ours == 'teamA' else 'teamA'
        metrics['faults'] += int(d['diagnostics']['botFaults'][ours])
        opponents['faults'] += int(d['diagnostics']['botFaults'][theirs])
        for c in d['champions']:
            total = metrics if c['team'] == ours else opponents
            for key in ('deaths', 'kills', 'earnedGold', 'collectedGems'):
                total[key] += int(c['metrics'][key])
        group = per_map.setdefault(row['map'], Counter())
        group.update(games=1, wins=int(row['win']), margin=row['margin'], fuel=row['fuel'], opp_fuel=row['opp_fuel'])
    n = len(rows)
    record = dict(run=a.run, note=a.note, opponent=a.opponent, seeds=a.seeds, holdout=a.holdout, games=n,
                  wins=sum(r['win'] for r in rows), draws=sum(r['draw'] for r in rows),
                  positive_margin_wins=sum(r['margin'] > 0 for r in rows),
                  margin=sum(r['margin'] for r in rows) / n, fuel=sum(r['fuel'] for r in rows),
                  opponent_fuel=sum(r['opp_fuel'] for r in rows), metrics=dict(metrics), opponent_metrics=dict(opponents),
                  per_map=per_map, source_sha256=hashes, changes=changes)
    record['source_snapshot'] = str(src.relative_to(ROOT)).replace('\\','/')
    record['candidate_path'] = run['bot']
    (out / 'audit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8', newline='\n')
    log = ROOT / 'research/v67/RESULTS.jsonl'
    with log.open('a', encoding='utf8', newline='\n') as f:
        f.write(json.dumps(record) + '\n')
    report = ROOT / 'research/v67/RESULTS.md'
    if not report.exists():
        report.write_text('# v67 experiments\n\nFixed 120-slot schedule. Margins are v67 minus opponent.\n\n'
                          '| Run | Change | Opponent | Seeds | Wins/games | Margin | Deaths/game | Kills/game | Gold/game | Fuel v67/opp | Faults v67/opp |\n'
                          '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|\n', encoding='utf8', newline='\n')
    with report.open('a', encoding='utf8', newline='\n') as f:
        f.write(f'| {a.run} | {a.note} | {a.opponent} | {a.seeds} | {record["wins"]}/{n} | {record["margin"]:+.1f} | '
                f'{metrics["deaths"]/n:.2f} | {metrics["kills"]/n:.2f} | {metrics["earnedGold"]/n:.0f} | '
                f'{record["fuel"]}/{record["opponent_fuel"]} | {metrics["faults"]}/{opponents["faults"]} |\n')
    print(json.dumps({k:record[k] for k in ('run','wins','positive_margin_wins','games','margin','fuel','opponent_fuel','metrics')}, indent=2))


if __name__ == '__main__':
    main()
