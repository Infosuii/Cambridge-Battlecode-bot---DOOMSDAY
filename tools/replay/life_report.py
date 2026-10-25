"""Whole-life ladder analysis of one submitted version (offline; omniscient replay tools, never bot inputs).

Usage: python tools/replay/life_report.py <listing.json> <ladder.json> <tool out dir> <report.md>
Joins the match listing with run_life_tools.sh outputs and writes a markdown report plus <report>.json with every
per-game row. "Us" is DOOMSDAY; "opp" is the other team (the winner in our losses).
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics as st
import sys

PICKS = ['Ryth', 'Vesper', 'Vendetta', 'Cassi/Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart']
TYPES = ['Ryth', 'Vesper', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart']
FAM = ['monster', 'power', 'durability', 'treasure', 'jungle', 'home', 'bruiser']


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []


def gear(snap):
    return sum(n * (150 if i % 2 else 30) for c in snap['champions'] for i, n in c['items'])


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 2) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 2) if xs else None


def main():
    listing, ladder, tdir, outp = sys.argv[1:5]
    tdir, outp = Path(tdir), Path(outp)
    ms = {m['matchId']: m for m in load(listing) if m['status'] == 'finished'}
    rank = {r['name']: (r['rank'], r['rating']) for r in load(ladder)}
    audit = {a['id']: a for a in load(tdir / 'audit.json')}
    ledger = {g['id']: g for g in load(tdir / 'ledger.json')}
    still = {g['id']: g for g in load(tdir / 'still.json')}
    coh = {g['id']: g for g in load(tdir / 'cohesion.json')}
    hurt = {g['id']: g for g in load(tdir / 'hurt.json')}
    focus = {g['id']: g for g in load(tdir / 'focus.json')}
    kinds = {g['id']: g for g in load(tdir / 'kinds.json')}
    deaths = {g['id']: g for g in load(tdir / 'deaths.json')}
    home = {g['id']: g for g in load(tdir / 'home.json')}
    rows = []
    for mid, m in ms.items():
        if mid not in audit or mid not in ledger:
            continue
        me = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
        op = next(t for t in m['teams'] if t['name'] != 'DOOMSDAY')
        u = 'ab'.index(me['side'])
        a, L = audit[mid], ledger[mid]
        row = {'id': mid, 'map': m['map'], 'kind': m['kind'], 'opp': op['name'], 'opp_rank': rank.get(op['name'], (None,))[0],
               'win': me['result'] == 'win', 'side': me['side'], 'end': m.get('endReason'), 'rounds': a['rounds'],
               'score': [a['submitted_gems'][u], a['submitted_gems'][1 - u]], 'draft': [me['draftPicks'], op['draftPicks']], 't': {}}
        for side, t in (('us', u), ('opp', 1 - u)):
            T = a['teams'][t]
            snaps = {s['round']: s for s in T['snapshots']}
            x = {'deaths': T['deaths'], 'dead_rounds': T['dead_champion_rounds'], 'lost_on_death': T['lost_on_death'],
                 'banks': len(T['banks']), 'first_bank': T['banks'][0]['round'] if T['banks'] else None,
                 'bank_median': med([b['amount'] for b in T['banks']]), 'fuel_out': T['fuel_exhausted']}
            for r in (100, 250, 500, 1000):
                if r in snaps:
                    x[f'gear{r}'] = gear(snaps[r]); x[f'deaths{r}'] = snaps[r]['deaths']; x[f'banked{r}'] = snaps[r]['banked']
            acts = [ac for ac in L['actors'] if ac['team'] == t]
            n = max(1, len(acts))
            for W in (250, 500):
                tot = defaultdict(float)
                for ac in acts:
                    for k, v in ac['w'].get(str(W), {}).items():
                        tot[k] += v
                alive = max(1.0, tot['alive'])
                for k in ('clear', 'pvp', 'cast', 'travel', 'still', 'spawn'):
                    x[f'{k}{W}'] = tot[k] / alive
                x[f'capgold{W}'] = tot['cap_gold'] / n
                x[f'yield{W}'] = tot['cap_gold'] / max(1.0, tot['clear'] + tot['cast'])
                x[f'killgold{W}'] = tot['kill_gold']
            x['big_gems500'] = sum(e['gems'] for ac in acts for e in ac['cap_events'] if e['gems'] >= 20)
            x['first_buy'] = med([ac['first_buy'] for ac in acts])
            x['treasure250'] = sum(1 for ac in acts if ac['emblems'].get('treasure', 1e9) <= 250)
            x['treasure500'] = sum(1 for ac in acts if ac['emblems'].get('treasure', 1e9) <= 500)
            x['first_emblems'] = [sorted(ac['emblems'], key=ac['emblems'].get)[:3] for ac in acts]
            x['actors'] = len(acts)
            if mid in still:
                n0 = sum(1 for ac in L['actors'] if ac['team'] == 0)
                x['respawn_wait500'] = sum(r['len'] for r in still[mid]['runs'] if (0 if r['actor'] < n0 else 1) == t
                                           and r['ctx']['camp_dist'] <= 1 and not r['ctx']['camp_alive'] and not (r['ctx']['camp_dist'] == 0 and r['len'] <= 6)
                                           and r['fuel'] == 0 and r['ctx']['enemies'] == 0)
            if mid in coh:
                c = coh[mid]['teams'][t]
                x['contact'] = c['contact']; x['die5'] = c['die5'] / max(1, c['contact'])
                x['low_contact'] = (c['hpq'][0] + c['hpq'][1]) / max(1, c['contact'])
                x['full_die5'] = c['hpq_die'][3] / max(1, c['hpq'][3])
                x['alone'] = c['alone'] / max(1, c['contact'])
            if mid in hurt:
                h = hurt[mid]['teams'][t]; x['hurt_episodes'] = h['episodes']
            if mid in focus:
                f = focus[mid]['teams'][t]; x['dmg_per_contact'] = f['dmg_dealt'] / max(1, f['contact_rounds']); x['pvp_attack_rounds'] = f['attack_rounds']
            if mid in kinds:
                k = kinds[mid]['teams'][t]
                for key in ('teleport', 'lock', 'ward', 'dash', 'submit_bank'):
                    x[key] = k.get(key, 0)
                x['teleport250'] = k.get('teleport_r250', 0)
            if mid in home:
                hv = home[mid]['teams'][t]
                x['home_visits'] = hv['visits']; x['home_recalled'] = hv['recalled'] / max(1, hv['visits'])
                x['home_gold_in'] = hv['gold_in'] / max(1, hv['visits']); x['home_gap'] = hv['gap'] / max(1, hv['gaps'])
            if mid in deaths:
                ds = [d for d in deaths[mid]['deaths'] if d['team'] == t]
                x['deaths_alone'] = sum(1 for d in ds if d['allies4'] == 0)
                x['deaths_carry_gems'] = sum(d['gems'] for d in ds)
            row['t'][side] = x
        us, opp = row['t']['us'], row['t']['opp']
        r250 = (us.get('gear250', 0) / opp['gear250']) if opp.get('gear250') else None
        r500 = (us.get('gear500', 0) / opp['gear500']) if opp.get('gear500') else None
        row['gear_ratio250'], row['gear_ratio500'] = r250, r500
        if not row['win']:
            fam = []
            if r250 is not None and r250 < 0.75 and us.get('deaths250', 0) <= 1:
                fam.append('opening economy')
            if us.get('deaths250', 0) >= 3 and us.get('deaths250', 0) > opp.get('deaths250', 0) + 1:
                fam.append('early contact spiral')
            if r500 is not None and r500 >= 0.9:
                fam.append('conversion (gear parity or lead at R500)')
            if not fam:
                fam.append('mid-game slide')
            row['family'] = fam
        rows.append(row)
    L = [r for r in rows if not r['win']]
    W = [r for r in rows if r['win']]
    label = sys.argv[5] if len(sys.argv) > 5 else 'v53'
    interval = sys.argv[6] if len(sys.argv) > 6 else '2026-10-25 13:08:26-16:24:00 UTC'
    lines = [f'# {label} ladder replay analysis: where, why, and what winners do', '',
             f'Platform {label}; interval {interval}. {len(ms)} finished games in listing; {len(rows)} with decoded replays '
             f'({len(L)} losses, {len(W)} wins). Offline omniscient replay analysis with the pinned engine; descriptive, confounded by '
             'map, opponent and draft. Medians of per-game values unless stated; "opp" is the winner in our losses and the loser in our wins.', '']

    def table(title, groups, keys):
        lines.append(f'## {title}')
        lines.append('')
        lines.append('| Metric | ' + ' | '.join(f'{g} us | {g} opp' for g, _ in groups) + ' |')
        lines.append('|---|' + '---:|' * (2 * len(groups)))
        for key, label, agg in keys:
            cells = []
            for _, rs in groups:
                for side in ('us', 'opp'):
                    v = agg([r['t'][side].get(key) for r in rs])
                    cells.append('-' if v is None else (f'{v:.3f}' if isinstance(v, float) and abs(v) < 1 else f'{v:g}'))
            lines.append(f'| {label} | ' + ' | '.join(cells) + ' |')
        lines.append('')

    lines.append('## Listing results and replay coverage')
    lines.append('')
    for kind in ('ranked', 'unranked'):
        population = [m for m in ms.values() if m['kind'] == kind]
        rs = [r for r in rows if r['kind'] == kind]
        wins = sum(next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')['result'] == 'win' for m in population)
        if population:
            lines.append(f'- {kind}: {wins}/{len(population)} wins in listing; decoded {len(rs)} games ({sum(r["win"] for r in rs)} wins).')
    fams = Counter(f for r in L for f in r['family'])
    lines.append('- loss families (a loss can have several): ' + ', '.join(f'{k} {v}' for k, v in fams.most_common()))
    close = sum(1 for r in L if r['score'][0] - r['score'][1] >= -150)
    lines.append(f'- close losses (margin ≥ −150 gems): {close}/{len(L)}; median margin of losses '
                 f'{st.median(r["score"][0] - r["score"][1] for r in L):+.0f}')
    lines.append('')
    lines.append('| Map | W/L | mean margin | median R250 gear ratio | our deaths / opp deaths (median) |')
    lines.append('|---|---:|---:|---:|---:|')
    bym = defaultdict(list)
    for r in rows:
        bym[r['map']].append(r)
    for mp, rs in sorted(bym.items(), key=lambda kv: -sum(not r['win'] for r in kv[1])):
        lines.append(f'| {mp} | {sum(r["win"] for r in rs)}/{sum(not r["win"] for r in rs)} | '
                     f'{st.mean(r["score"][0] - r["score"][1] for r in rs):+.0f} | {med([r["gear_ratio250"] for r in rs])} | '
                     f'{med([r["t"]["us"]["deaths"] for r in rs])} / {med([r["t"]["opp"]["deaths"] for r in rs])} |')
    lines.append('')
    lines.append('| Opponent | rank now | W/L vs them |')
    lines.append('|---|---:|---:|')
    byo = defaultdict(list)
    for r in rows:
        byo[r['opp']].append(r)
    for o, rs in sorted(byo.items(), key=lambda kv: -sum(not r['win'] for r in kv[1]))[:20]:
        lines.append(f'| {o} | {rs[0]["opp_rank"]} | {sum(r["win"] for r in rs)}/{sum(not r["win"] for r in rs)} |')
    lines.append('')
    keys = [('gear100', 'equipment value R100', med), ('gear250', 'equipment value R250', med), ('gear500', 'equipment value R500', med),
            ('capgold250', 'capture gold per actor R250', med), ('capgold500', 'capture gold per actor R500', med),
            ('yield500', 'capture gold per attack/cast round R500', med), ('clear500', 'camp-attack share R500', med),
            ('travel500', 'moving share R500', med), ('still500', 'stationary off-spawn share R500', med),
            ('respawn_wait500', 'respawn-wait champion-rounds R500', med), ('big_gems500', 'gems from 20+ captures R500', med),
            ('first_buy', 'median first purchase round', med), ('treasure250', 'actors with Treasure R250', med),
            ('treasure500', 'actors with Treasure R500', med), ('deaths250', 'deaths by R250', med), ('deaths', 'deaths (game)', med),
            ('dead_rounds', 'champion-rounds dead', med), ('lost_on_death', 'gems lost on death', med),
            ('deaths_carry_gems', 'gems carried by our dead (death log)', med), ('banks', 'completed banks', med),
            ('first_bank', 'first bank round', med), ('bank_median', 'median bank size', med),
            ('contact', 'contact champion-rounds', med), ('die5', 'P(die within 5 | contact)', mean), ('low_contact', 'contact share below 50% hp', mean),
            ('full_die5', 'P(die within 5 | contact, hp ≥ 75%)', mean), ('alone', 'alone share of contact', mean),
            ('hurt_episodes', 'hurt-in-contact episodes', med), ('dmg_per_contact', 'enemy hp lost per contact round', mean),
            ('pvp_attack_rounds', 'rounds with PvP attacks', med), ('teleport', 'teleport hops', mean), ('teleport250', 'teleport hops by R250', mean),
            ('lock', 'altar-lock placements', mean), ('ward', 'ward placements', mean), ('dash', 'dash moves', mean),
            ('home_visits', 'spawn visits (alive)', med), ('home_recalled', 'share of spawn visits by recall', mean),
            ('home_gold_in', 'gold carried on arrival at spawn', med), ('home_gap', 'rounds between spawn visits', med),
            ('fuel_out', 'fuel-exhausted turns', mean)]
    table('Losses vs wins: us and the other team', [('losses', L), ('wins', W)], keys)
    for fam in [f for f, _ in fams.most_common()]:
        rs = [r for r in L if fam in r['family']]
        table(f'Loss family: {fam} ({len(rs)} games)', [(fam.split()[0], rs)], keys[:22])
    # Emblem order and drafts
    lines.append('## Item programmes (first three emblem families per actor)')
    lines.append('')
    for label, rs, side in (('our losses', L, 'us'), ('winners vs us', L, 'opp'), ('our wins', W, 'us')):
        first = Counter(fe[0] for r in rs for fe in r['t'][side]['first_emblems'] if fe)
        seq = Counter('>'.join(fe) for r in rs for fe in r['t'][side]['first_emblems'] if fe)
        lines.append(f'- {label}: first emblem ' + ', '.join(f'{k} {v}' for k, v in first.most_common(5)) +
                     '; top sequences ' + '; '.join(f'{k} {v}' for k, v in seq.most_common(5)))
    lines.append('')
    lines.append('## Drafts (draft-pick IDs; Cassi/Issac is one pick)')
    lines.append('')
    for label, rs, side in (('our losses', L, 0), ('winners vs us', L, 1), ('our wins', W, 0)):
        c = Counter(PICKS[p] for r in rs for p in r['draft'][side])
        lines.append(f'- {label} ({len(rs)} games): ' + ', '.join(f'{k} {v / len(rs):.2f}' for k, v in c.most_common()))
    lines.append('')
    # Opponent playbooks
    lines.append('## Playbooks of the teams that beat us most (their side of our losses)')
    lines.append('')
    for o, rs in sorted(byo.items(), key=lambda kv: -sum(not r['win'] for r in kv[1]))[:8]:
        lr = [r for r in rs if not r['win']]
        if len(lr) < 3:
            continue
        op = [r['t']['opp'] for r in lr]
        drafts = Counter(' '.join(PICKS[p] for p in sorted(r['draft'][1])) for r in lr).most_common(2)
        seq = Counter('>'.join(fe) for x in op for fe in x['first_emblems'] if fe).most_common(3)
        lines.append(f'### {o} (rank {lr[0]["opp_rank"]}, {len(lr)} wins over us)')
        lines.append(f'- drafts: ' + '; '.join(f'{d} ×{n}' for d, n in drafts))
        lines.append(f'- item sequences: ' + '; '.join(f'{d} ×{n}' for d, n in seq))
        for key, label in (('gear250', 'R250 equipment'), ('gear500', 'R500 equipment'), ('capgold250', 'capture gold/actor R250'),
                           ('first_bank', 'first bank'), ('banks', 'banks'), ('bank_median', 'bank size'), ('deaths', 'deaths'),
                           ('teleport', 'teleports'), ('lock', 'locks'), ('ward', 'wards'), ('clear500', 'camp-attack share'),
                           ('respawn_wait500', 'respawn waits'), ('dmg_per_contact', 'damage per contact round')):
            lines.append(f'- {label}: them {med([x.get(key) for x in op])}, us {med([r["t"]["us"].get(key) for r in lr])}')
        lines.append('')
    outp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    outp.with_suffix('.json').write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
