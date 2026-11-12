"""Exact preregistered EXP208 resource ledger, independently checked against native totals."""
from collections import Counter
import json
from math import isclose
from statistics import mean, median

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import ENGINE, HERE, read
from freeze_engine3_discovery import write
from freeze_live111c_discovery import OUT, PREFIX

KEYS = ('camp', 'fight_in', 'fight_out', 'camp_loss', 'banked', 'clears')
COMPONENTS = ('production', 'fights', 'camp_loss', 'conversion')


def ledger(doc, team, round_limit=None):
    values = Counter({k: 0 for k in KEYS})
    for event in doc['events']:
        if event['owner'].get('team') != team:
            continue
        kind = event['kind']
        if kind not in ('gemCollection', 'gemLoss', 'gemSubmission', 'campClear'):
            continue
        for entry in event['entries']:
            if round_limit is not None and entry['timestamp']['round'] > round_limit:
                continue
            if kind == 'gemCollection':
                key = {'campGroup': 'camp', 'champion': 'fight_in'}[entry['context']]
            elif kind == 'gemLoss':
                key = {'champion': 'fight_out', 'camp': 'camp_loss'}[entry['context']]
            else:
                key = {'gemSubmission': 'banked', 'campClear': 'clears'}[kind]
            values[key] += float(entry['value'])
    values['held'] = values['camp'] + values['fight_in'] - values['fight_out'] - values['camp_loss'] - values['banked']
    values['net_fight'] = values['fight_in'] - values['fight_out']
    values['gems_per_clear'] = values['camp'] / values['clears'] if values['clears'] else None
    if round_limit is None:
        # These observations are independent of the event identity above.
        held = sum(float(c['metrics']['gems']) for c in doc['champions'] if c['team'] == team)
        banked = next(float(t['submittedGems']) for t in doc['teams'] if t['team'] == team)
        champion_banked = sum(float(c['metrics']['submittedGems']) for c in doc['champions'] if c['team'] == team)
        assert isclose(banked, champion_banked, abs_tol=1e-6)
        terminal = doc['match']['roundsStarted'] + 1
        assert isclose(held, timeline(doc, team, 'gems', terminal), abs_tol=1e-6)
        assert isclose(banked, timeline(doc, team, 'submittedGems', terminal), abs_tol=1e-6)
    else:
        held = timeline(doc, team, 'gems', round_limit)
        banked = timeline(doc, team, 'submittedGems', round_limit)
    assert isclose(values['held'], held, abs_tol=1e-6), (team, round_limit, values, held)
    assert isclose(values['banked'], banked, abs_tol=1e-6), (team, round_limit, values, banked)
    return dict(values)


def margins(ours, rival):
    parts = {'production': ours['camp'] - rival['camp'],
             'fights': ours['net_fight'] - rival['net_fight'],
             'camp_loss': rival['camp_loss'] - ours['camp_loss'],
             'conversion': rival['held'] - ours['held']}
    margin = ours['banked'] - rival['banked']
    assert isclose(sum(parts.values()), margin, abs_tol=1e-6)
    # Count ties explicitly. Nonnegative final margins may lose on other rules.
    minimum = min(parts.values())
    dominant = [k for k, v in parts.items() if v == minimum] if margin < 0 else []
    return {'banked_margin': margin, 'components': parts, 'most_negative': dominant}


def aggregate(rows):
    if not rows:
        return {'n': 0}
    return {'n': len(rows), 'groups': len({r['group'] for r in rows}),
            'mean_banked_margin': mean(r['banked_margin'] for r in rows),
            'mean_components': {k: mean(r['components'][k] for r in rows) for k in COMPONENTS},
            'most_negative_unique': dict(Counter(r['most_negative'][0] for r in rows if len(r['most_negative']) == 1)),
            'most_negative_ties': sum(len(r['most_negative']) > 1 for r in rows),
            'nonnegative_banked_margin': sum(r['banked_margin'] >= 0 for r in rows),
            'held_covers_banked_deficit': sum(r['banked_margin'] < 0 and r['ours']['held'] >= -r['banked_margin'] for r in rows),
            'mean_ours_rival': {k: [mean(r[side][k] for r in rows) for side in ('ours', 'rival')] for k in KEYS + ('held',)},
            'median_gems_per_clear': [median(r[side]['gems_per_clear'] for r in rows if r[side]['gems_per_clear'] is not None) for side in ('ours', 'rival')]}


if __name__ == '__main__':
    selected = read(HERE / f'{PREFIX}_DISCOVERY_SPLIT.json')['matches']
    rows = []
    for match in selected:
        path = OUT / 'summaries' / (match['matchId'] + '.json')
        doc = read(path)
        assert doc['diagnostics']['detailedCaptureComplete']
        assert (doc['match']['engineVersion'], doc['match']['engineBuildHash']) == ('3.0.0', ENGINE)
        team = 'team' + match['side'].upper()
        rival = 'teamB' if team == 'teamA' else 'teamA'
        ours, theirs = ledger(doc, team), ledger(doc, rival)
        row = {k: match[k] for k in ('matchId', 'group', 'opponent', 'partition', 'result')}
        row.update({'native_sha256': bench.digest(path), 'rounds': doc['match']['roundsCompleted'],
                    'ours': ours, 'rival': theirs, **margins(ours, theirs), 'phases': {}})
        for round_limit in (150, 300, 800):
            if doc['match']['roundsCompleted'] < round_limit:
                continue
            a, b = ledger(doc, team, round_limit), ledger(doc, rival, round_limit)
            row['phases'][str(round_limit)] = {'ours': a, 'rival': b, **margins(a, b)}
        rows.append(row)
    reports = {}
    for part in ('discovery', 'control', 'confirm'):
        subset = [r for r in rows if r['partition'] == part]
        reports[part] = {**aggregate(subset),
                         'per_opponent': {n: aggregate([r for r in subset if r['opponent'] == n]) for n in sorted({r['opponent'] for r in subset})},
                         'phases': {str(t): aggregate([{**r, **r['phases'][str(t)]} for r in subset if str(t) in r['phases']]) for t in (150, 300, 800)}}
    result = {'scope': 'Outcome-selected descriptive cohort; group-correlated, inferred source identity. Components are accounting, not causal interventions. Camp gems per clear also includes timing, sharing, reward mix and capture attribution.',
              'team_tool_reference': '0025c27e:tools/rl_env_1104/strategy/resource_breakdown.py',
              'split_sha256': bench.digest(HERE / f'{PREFIX}_DISCOVERY_SPLIT.json'),
              'independent_terminal_and_phase_checks_pass': True, 'reports': reports, 'rows': rows}
    write(HERE / f'{PREFIX}_RESOURCE_REPORT.json', result)
    print(json.dumps({p: {k: v for k, v in report.items() if k not in ('per_opponent', 'phases')} for p, report in reports.items()}, indent=2))
