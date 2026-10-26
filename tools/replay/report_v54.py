"""Render the frozen v53 snapshot and paired replay measurements; no builds."""
from collections import defaultdict
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]


def main():
    matches = json.loads((ROOT / 'data/ladder/v53_since_live_analysis_20261025.json').read_text())
    evidence = json.loads((ROOT / 'research/v54/V54_EVIDENCE.json').read_text())
    rows = evidence['games']['v53_all_losses'] + evidence['games']['v53_all_wins']
    by_id = {r['id']: r for r in rows}
    assert len(matches) == len(by_id) == 75
    assert {m['matchId'] for m in matches} == set(by_id)
    lines = [
        '# V53 latest-game review for v54', '',
        'Frozen snapshot: games created through 2026-10-25 13:30:12 UTC. '
        '75 finished games, 36 wins: ranked 5/10, unranked 31/65. '
        'All 75 have decoded replay measurements. This is a descriptive sample, not a controlled version comparison.', '',
        'Equipment is original shard-purchase gold currently represented by inventory. '
        'Ratios are medians of within-game ratios, excluding games with zero opponent equipment; '
        'denominator counts are in V54_EVIDENCE.json. Deaths are round-sampled. '
        'Map/opponent/draft records are confounded by each other and have small samples. '
        'Do not counter-pick from these raw win rates.', '',
        '## Maps, ordered by losses then score margin', '',
        '| Map | Wins / games | Mean banked-gem margin | Median R250 equipment ratio |',
        '|---|---:|---:|---:|',
    ]
    maps = defaultdict(list)
    for r in rows:
        maps[r['map']].append(r)
    for name, rs in sorted(maps.items(), key=lambda x: (sum(r['win'] for r in x[1])-len(x[1]), sum(r['score'][0]-r['score'][1] for r in x[1])/len(x[1]))):
        ratios = [r['gear']['250'][0]/r['gear']['250'][1] for r in rs if '250' in r['gear'] and r['gear']['250'][1]>0]
        ratio = f'{median(ratios):.2f}' if ratios else 'n/a'
        lines.append(f"| {name} | {sum(r['win'] for r in rs)}/{len(rs)} | {sum(r['score'][0]-r['score'][1] for r in rs)/len(rs):+.1f} | {ratio} |")
    lines += ['', '## Opponents', '', '| Opponent | Wins / games |', '|---|---:|']
    opponents = defaultdict(list)
    for r in rows:
        opponents[r['opponent']].append(r)
    for name, rs in sorted(opponents.items(), key=lambda x: (sum(r['win'] for r in x[1])/len(x[1]), x[0])):
        lines.append(f"| {name} | {sum(r['win'] for r in rs)}/{len(rs)} |")
    lines += ['', '## Our draft sets (at least three games)', '',
              'These are draft-pick IDs, not runtime champion-type IDs (Cassi/Issac is one pick). '
              '0 Ryth; 1 Vesper; 2 Vendetta; 3 Cassi/Issac; 4 Stellar; 5 Prism; '
              '6 Marcella; 7 Willow; 8 Ren; 9 Varg; 10 Tavi; 11 Heart of Ruin. '
              'Order is ignored in this table; map, enemy draft and controller behavior remain essential confounders.', '',
              '| Our pick IDs | Wins / games | Maps represented |', '|---|---:|---|']
    drafts = defaultdict(list)
    for r in rows:
        drafts[tuple(sorted(r['draft'][0]))].append(r)
    for picks, rs in sorted(drafts.items(), key=lambda x: (-len(x[1]), x[0])):
        if len(rs) >= 3:
            lines.append(f"| {', '.join(map(str, picks))} | {sum(r['win'] for r in rs)}/{len(rs)} | {', '.join(sorted({r['map'] for r in rs}))} |")
    lines += ['', '## The ten ranked games', '',
              '| Match | Map / opponent | Result | Banked gems | End reason |', '|---|---|---|---:|---|']
    for m in matches:
        if m['kind'] != 'ranked':
            continue
        r = by_id[m['matchId']]
        lines.append(f"| `{r['id']}` | {r['map']} / {r['opponent']} | {'win' if r['win'] else 'loss'} | {r['score'][0]}–{r['score'][1]} | {m['endReason']} |")
    lines += ['', '## Concrete trajectories to investigate first', '',
              'These trajectories identify when the gap appears. They do not establish which '
              'missed action caused it; reconstruct actor-level jobs before changing the policy.', '']
    selected = []
    for name in ['01boss_battle', '01concentrated_wealth', '00elkring', '00swirl', '00stampede', '00fragment']:
        rs = [r for r in rows if r['map'] == name and not r['win']]
        if rs:
            selected.append(min(rs, key=lambda r: r['score'][0]-r['score'][1]))
    selected += [by_id['d1769f18-e33d-462e-85b1-4cc6d1719d02']]
    for r in selected:
        lines += [f"### {r['map']} against {r['opponent']} ({'win' if r['win'] else 'loss'})", '',
                  f"Match `{r['id']}`; {r['rounds']} rounds; banked gems {r['score'][0]}–{r['score'][1]}. "
                  f"Our draft {r['draft'][0]}; opponent {r['draft'][1]}.", '',
                  '| Checkpoint | Us | Opponent |', '|---|---:|---:|']
        for checkpoint in ['100', '250', '500', '1000']:
            if checkpoint in r['gear']:
                g, d = r['gear'][checkpoint], r['early_deaths'][checkpoint]
                lines.append(f'| R{checkpoint} equipment | {g[0]} | {g[1]} |')
                lines.append(f'| R{checkpoint} deaths so far | {d[0]} | {d[1]} |')
        for key, label in [('deaths', 'Final sampled deaths'), ('dead_rounds', 'Champion-rounds dead'),
                           ('bank_count', 'Completed banks'), ('first_bank', 'First bank round'), ('median_bank', 'Median bank amount')]:
            a, b = r[key]
            lines.append(f"| {label} | {a if a is not None else 'none'} | {b if b is not None else 'none'} |")
        lines += ['', 'Next inspection: align first camp targets, captures and reward owners, '
                  'purchases, recalls, deaths, and objective/bank attempts. Separate economy lost '
                  'before contact from economy lost because of contact.', '']
    lines += ['## Reproduction', '',
              '`python tools/replay/report_v54.py` regenerates this report from committed snapshots '
              'and `V54_EVIDENCE.json`. The underlying replay audit can be regenerated from local '
              'downloads using `v53_audit.mjs` and `strategic_metrics.py`. Raw replays are deliberately excluded from Git.', '']
    output = ROOT / 'research/v54/V54_MATCH_REVIEW.md'
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(rows)} games -> {output}')


if __name__ == '__main__':
    main()
