"""Summarise examined timelines, exact race identities and paired openings."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from deep_preflight import ROOT
from deep_detector_report import save

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'
MARKS = (50, 100, 250, 500)
FIELDS = ('banked', 'collected', 'lost', 'carried', 'earned_gold', 'equipment_cost', 'alive',
          'capture_gold', 'kill_gold', 'bank_bonus_gold', 'other_or_unclassified_gold', 'middle_gems',
          'vision_fraction', 'middle_vision_fraction', 'wards_placed', 'dead_rounds', 'travel_rounds',
          'stationary_rounds', 'channel_rounds', 'fuel_outs')


def cluster_mean(rows, field, cluster):
    groups = defaultdict(list)
    for row in rows:
        if row.get(field) is not None:
            groups[row[cluster]].append(row[field])
    if not groups:
        return None
    values = np.array([[sum(v), len(v)] for v in groups.values()])
    draws = np.random.default_rng(20261028).integers(0, len(values), size=(2000, len(values)))
    summed = values[draws].sum(axis=1)
    return {'n': int(values[:, 1].sum()), 'clusters': len(values),
            'mean': float(values[:, 0].sum() / values[:, 1].sum()),
            'interval95': np.quantile(summed[:, 0] / summed[:, 1], [.025, .975]).tolist() if len(groups) > 1 else None}


def aggregate(rows):
    out = {'n': len(rows)}
    if not rows:
        return out
    for name in ('final_margin', 'income_margin', 'loss_preservation_margin', 'carried_margin', 'capture_income_margin'):
        out[name] = float(np.mean([r[name] for r in rows]))
    out['final'] = {side: {f: float(np.mean([r['final'][side][f] for r in rows])) for f in FIELDS} for side in ('us', 'them')}
    out['conversion'] = {side: sum(r['final'][side]['banked'] for r in rows) / max(1, sum(r['final'][side]['collected'] for r in rows)) for side in ('us', 'them')}
    out['curves'] = {}
    for mark in MARKS:
        present = [r for r in rows if str(mark) in r['curve']]
        out['curves'][str(mark)] = {'n': len(present), 'paired_mean': {side: {f: float(np.mean([r['curve'][str(mark)][side][f] for r in present])) for f in FIELDS} for side in ('us', 'them')} if present else {}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    args = ap.parse_args()
    run = json.loads((args.run / 'run.json').read_text(encoding='utf-8'))
    assert run['partition'] == 'examined' and run['passed'] == 385 and not run['failed']
    catalog = {r['match_id']: r for r in json.loads((LOCAL / 'restored-catalog.json').read_text(encoding='utf-8')) if r['partition'] == 'examined'}
    rows, opening_rows = [], []
    for mid, meta in catalog.items():
        game = json.loads((args.run / (mid + '.json')).read_text(encoding='utf-8'))
        assert game['code_sha256'] == run['code_sha256']
        if meta['source'] == 'top-v-top':
            continue
        native = json.loads((LOCAL / 'replays/examined' / (mid + '.summary.json')).read_text(encoding='utf-8'))
        own = 0 if meta['side'] == 'a' else 1
        enemy = 1 - own
        final = {s: {f: game['rows'][-1]['teams'][t][f] for f in FIELDS} for s, t in [('us', own), ('them', enemy)]}
        u, t = final['us'], final['them']
        race = {'final_margin': u['banked'] - t['banked'], 'income_margin': u['collected'] - t['collected'],
                'loss_preservation_margin': t['lost'] - u['lost'], 'carried_margin': t['carried'] - u['carried']}
        assert race['final_margin'] == race['income_margin'] + race['loss_preservation_margin'] + race['carried_margin']
        ids = {c['id']: (0 if c['team'] == 'teamA' else 1) for c in game['roster']}
        capture_gems = [sum(int(e['value']) for e in game['events'] if e['kind'] == 'gemCollection' and isinstance(e['target'], dict) and e['target'].get('kind') == 'campGroup' and ids[e['owner']['id']] == s) for s in (own, enemy)]
        curve = {}
        for mark in MARKS:
            sample = next((r for r in game['rows'] if r['r'] == mark), None)
            if sample:
                curve[str(mark)] = {s: {f: sample['teams'][team][f] for f in FIELDS} for s, team in [('us', own), ('them', enemy)]}
        row = {k: meta[k] for k in ('match_id', 'group_id', 'cohort', 'map', 'opponent', 'opponent_id', 'source', 'result')}
        row.update(rounds=game['rounds'], own_side=own, final=final, curve=curve, **race,
                   capture_income_margin=capture_gems[0] - capture_gems[1], capture_gems=capture_gems)
        for mark in (100, 250):
            for f in ('equipment_cost', 'collected', 'earned_gold', 'banked'):
                row[f'{f}_gap_{mark}'] = curve[str(mark)]['us'][f] - curve[str(mark)]['them'][f] if str(mark) in curve else None
        rows.append(row)
        for label, team in [('us', own), ('them', enemy)]:
            events = [e for e in game['events'] if ids.get(e['owner']['id']) == team]
            buys = [e for e in events if e['kind'] in ('buyItem', 'buyConsumable')]
            reward = defaultdict(int)
            for e in events:
                if e['kind'] == 'gemCollection' and isinstance(e['target'], dict) and e['target'].get('kind') == 'campGroup':
                    reward[(e['timestamp']['round'], e['target']['id'])] += int(e['value'])
            large = next(((r, group, gems) for (r, group), gems in sorted(reward.items()) if gems >= 20 and r <= 250), None)
            starts = {str(c['id']): [a for a in game['opening'][str(c['id'])] if a['r'] <= 250] for c in game['roster'] if ids[c['id']] == team}
            target_cards = {}
            for actor, targets in starts.items():
                target_cards[actor] = [dict(a, first_team_gem_receipt=next((r for (r, group), amount in sorted(reward.items()) if group == a['group'] and r >= a['r']), None)) for a in targets]
            opening_rows.append({'match_id': mid, 'map': meta['map'], 'cohort': meta['cohort'], 'result': meta['result'], 'team': label,
                                 'draft': [c['champion'] for c in native['roster']['draft'] if c['team'] == ('teamA' if team == 0 else 'teamB')],
                                 'physical_roster': [c['name'] for c in game['roster'] if ids[c['id']] == team], 'targets': target_cards,
                                 'first_purchase': min((e['timestamp']['round'] for e in buys), default=None),
                                 'first_large_observed_gem_reward': large,
                                 'large_grouping': None if not large else next(({'r': r['r'], 'alive': r['teams'][team]['alive'], 'spread': r['teams'][team]['spread']} for r in reversed(game['rows']) if r['r'] <= large[0] - 5), None)})
    assert len(rows) == 360
    groups = {'all': rows}
    for cohort in sorted({r['cohort'] for r in rows}):
        groups[cohort] = [r for r in rows if r['cohort'] == cohort]
    summaries = {k: {result: aggregate([r for r in v if r['result'] == result]) for result in ('loss', 'win')} for k, v in groups.items()}
    openings = {k: {result: {field: {cluster: cluster_mean([r for r in v if r['result'] == result], field, cluster) for cluster in ('map', 'opponent_id')}
                           for field in ('equipment_cost_gap_100', 'equipment_cost_gap_250', 'collected_gap_100', 'collected_gap_250', 'earned_gold_gap_100', 'earned_gold_gap_250', 'banked_gap_100', 'banked_gap_250')}
                    for result in ('loss', 'win')} for k, v in groups.items()}
    data = {'evidence': 'measured identities and paired associations; not avoidable costs', 'timeline_code_sha256': run['code_sha256'],
            'hands_off_used': 0, 'own_games': 360, 'top_reference_games': 25, 'summary': summaries, 'opening_gaps': openings,
            'rows': rows, 'opening_rows': opening_rows,
            'limits': ['Paired openings compare opponents in the same game/map, not a randomized strategy intervention.',
                       'Deaths can transfer gems; capture income and denial are not independent causal components.',
                       'Travel/stationary categories are round-boundary proxies; stationary includes necessary combat/capture.',
                       'Captures counts cover native gem-reward receipts; gold-only captures are covered by capture gold.',
                       'First large opening means observed team reward >=20 gems; grouping is team spread five rounds before receipt, not the exact first attack.']}
    save(STUDY / 'TIMELINE_DATA.json', data)
    receipt = {k: v for k, v in run.items() if k != 'results'}
    receipt.update(total_resource_checks=sum(r['checks'] for r in run['results']),
                   classified_gold=sum(r['coverage']['classified_gold'] for r in run['results']),
                   unclassified_gold=sum(r['coverage']['unclassified_gold'] for r in run['results']))
    save(STUDY / 'TIMELINE_SCREEN.json', receipt)
    lines = ['# Resource race and openings', '',
             '**Measured identities; paired associations.** 360 examined DOOMSDAY games (191 losses,169 wins); 25 top-v-top references are separately available for the model/matched controls. Hands-off use: zero.', '',
             'All 385 replay timelines pass native resource clocks and gem conservation. Gold sources use exact capture-phase deltas and native kill/bank cursor deltas; unmatched earned gold remains residual.', '',
             '`banked margin = collected margin + (enemy lost − our lost) + (enemy carried − our carried)` is an exact accounting identity. It is not a counterfactual: killed bags can enter the other team’s collected income.', '',
             '| Cohort/outcome | n | Mean banked margin | Collected margin | Loss preservation | End carried margin |',
             '|---|---:|---:|---:|---:|---:|']
    for cohort, values in summaries.items():
        for outcome, a in values.items():
            if a['n']:
                lines.append(f"| {cohort}/{outcome} | {a['n']} | {a['final_margin']:.1f} | {a['income_margin']:.1f} | {a['loss_preservation_margin']:.1f} | {a['carried_margin']:.1f} |")
    lines += ['', '## Paired opening equipment gaps', '', 'Our current inventory cost minus the opponent’s at the same round. Cost is not combat power. Intervals resample maps or opponents, preserving paired games; these are descriptive and unadjusted for draft/roster differences.', '',
              '| Cohort/outcome | R100 n/mean | R250 n/mean | R100 map 95% | R100 opponent 95% |', '|---|---:|---:|---|---|']
    for cohort, values in openings.items():
        for outcome, d in values.items():
            a, b = d['equipment_cost_gap_100']['map'], d['equipment_cost_gap_250']['map']
            opp = d['equipment_cost_gap_100']['opponent_id']
            if a:
                lines.append(f"| {cohort}/{outcome} | {a['n']}/{a['mean']:+.1f} | {b['n']}/{b['mean']:+.1f} | {a['interval95']} | {opp['interval95']} |")
    lines += ['', '## Scope of opening evidence', '',
              'TIMELINE_DATA.json records both rosters, each physical champion’s first three observed camp targets, first later team gem receipt for each target, first purchase, observed large-reward timing and pre-receipt team spread. A receipt is not proof that the initial targeter captured the camp. Gold-only captures, rejected calls, hidden targets and policy intentions are outside those opening labels.', '',
              'Exact R50/R100/R250/R500 resource, equipment, vision and time-proxy paired means and per-game rows are in TIMELINE_DATA.json. Games ending before a mark are omitted at that mark, with coverage reported. Middle uses minimum distance over every original camp tile to each team’s initial spawn positions, as in camp_clear.mjs.', '',
              'Vision is the union of official per-champion vision buffers; visible-enemy summaries are the union of those observations. Decision cards require the acting champion’s own view. Travel and stationary time must not be equated with wasted time. Model and cards follow separately.']
    (STUDY / 'P3_TIMELINES.md').write_bytes(('\n'.join(lines) + '\n').encode())
    print(json.dumps({'own_games': len(rows), 'resource_checks': receipt['total_resource_checks'], 'unclassified_gold': receipt['unclassified_gold'],
                      'loss_decomposition': summaries['all']['loss']}))


if __name__ == '__main__':
    main()
