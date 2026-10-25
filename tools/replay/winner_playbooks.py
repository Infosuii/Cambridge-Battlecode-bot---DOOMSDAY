"""Readable item, first-target and bank details from local offline replay audits."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAMP = ['Ryth', 'Vesper', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart']
CAMP = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']
FAMILY = ['Monster', 'Power', 'Durability', 'Treasure', 'Jungle', 'Home', 'Bruiser']
STAT = ['strength', 'focus', 'health']


def inventory(items):
    return ', '.join(f'{n} {FAMILY[i//6]} {STAT[(i%6)//2]} {"emblem" if i%2 else "shard"}' for i, n in items) or 'none'


def main():
    data = ROOT / 'data/ladder'
    latest = json.loads((data / 'v53_since_live_analysis_20261025.json').read_text())
    refs = []
    for name in ['v53_top_wins_20261025.json', 'v54_diverse_top_wins_20261025.json']:
        refs += json.loads((data / name).read_text(encoding='utf-8-sig'))
    audit = {a['id']: a for a in json.loads((ROOT / 'artifacts/local-only/v53-review/audit-v54-complete.json').read_text())}
    chosen = {'4b83a884-dc91-4dca-a322-2819ef232d40', 'a3e51d17-9947-4049-a32a-cc04af7eefcf',
              '1902a393-1c2b-4a7f-b404-609c7dfd8d79', 'cbafcbf3-5484-4d59-8d53-f704e1572430',
              '1488fd4c-3f4b-464c-90b7-57ae90db8c60', '8c0ac9b6-7b22-41ea-8c6d-a62f9c1e4d96',
              'd1769f18-e33d-462e-85b1-4cc6d1719d02'}
    selected = [m for m in latest if m['matchId'] in chosen]
    assert len(selected) == 7 and len(refs) == 11
    lines = ['# Winner playbooks and paired v53 cases', '',
             'Direct replay observations, not inferred bot algorithms. '
             'The first-target list gives the first basic attack at each distinct camp tile across the team; '
             'it excludes casts and does not establish kill/capture order. '
             'Item tables show inventory at the R500 snapshot, not a recommended universal build. '
             'Bank amounts are increases in submitted score. '
             'Death counts are round-sampled. The reference wins are deliberately selected successful games.', '']
    for m in selected + refs:
        a = audit[m['matchId']]
        lines += [f"## {m['map']} — {m['matchId']}", '',
                  f"{a['rounds']} rounds; side A/B score {a['submitted_gems'][0]}/{a['submitted_gems'][1]}. "
                  f"{'Paired v53 case.' if m in selected else 'Selected top-team winning reference.'}", '']
        for team in m['teams']:
            if m not in selected and team['result'] != 'win':
                continue
            t = a['teams']['ab'.index(team['side'])]
            lines += [f"### {team['name']} — side {team['side']}, {team['result']}", '',
                      f"Draft-pick IDs {team['draftPicks']}; sampled deaths {t['deaths']}; "
                      f"completed banks {len(t['banks'])}.", '',
                      'First distinct camp targets: ' + '; '.join(f"R{x['round']} {CAMP[x['type']]} ({x['x']},{x['y']})" for x in t['first_targets'][:12]) + '.', '',
                      'First banks: ' + ('; '.join(f"R{x['round']} actor {x['actor']}: {x['amount']} gems" for x in t['banks'][:6]) or 'none') + '.', '']
            snap = next((s for s in t['snapshots'] if s['round'] == 500), None)
            if snap:
                lines += ['| R500 actor | Alive / HP | Carried gems / gold | Inventory |', '|---|---|---:|---|']
                for c in snap['champions']:
                    lines.append(f"| {c['id']} {CHAMP[c['type']]} | {c['alive']} / {c['hp']:g} of {c['max_hp']:g} | {c['gems']} / {c['gold']} | {inventory(c['items'])} |")
                lines += ['']
    lines += ['## Interpretation', '',
              'Reference winners use several carriers and objective schedules. The shared pattern to test '
              'is coordinated production and conversion, not one mandatory pick or item. '
              'Compare item ownership with the job that actor performs; bonus-income roles and survivable '
              'objective carriers are plausible advantages but require controlled implementation evidence. '
              'Cases with high capital and zero banking require an access/conversion explanation even '
              'when their farm is productive.', '',
              'Regenerate with `python tools/replay/winner_playbooks.py` after downloading the listed match IDs '
              'and creating the complete local audit. Raw replay bundles remain outside Git.', '']
    out = ROOT / 'artifacts/claude_ops/V54_WINNER_PLAYBOOKS.md'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(selected)} paired cases + {len(refs)} winning references -> {out}')


if __name__ == '__main__':
    main()
