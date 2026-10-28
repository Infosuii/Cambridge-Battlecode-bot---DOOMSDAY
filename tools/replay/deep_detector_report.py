"""Report preregistered examined-game flags, with map/opponent uncertainty.

Reads no held-out detector data or raw replay. Flags remain associations/proxies.
"""
import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT

STUDY = ROOT / 'research/deep-2026-10-28'
IDS = [f'D{i}' for i in range(1, 12)]
TIME_DENOM = {'D1': 'idle_eligible_turns', 'D2': 'alive_observed_turns',
              'D6': 'alive_complete_turns', 'D9': 'alive_observed_turns', 'D10': 'observed_turns'}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0, center - radius), min(1, center + radius)]


def actor_events(actor, metric):
    detector, _, subtype = metric.partition(':')
    values = actor['detectors'][detector]['events']
    return [x for x in values if not subtype or x['subtype'] == subtype]


def observed(row, metric):
    return any(actor_events(actor, metric) for actor in row['actors'])


def aggregate(rows, metric):
    detector = metric.split(':')[0]
    flagged = sum(observed(row, metric) for row in rows)
    total_events = sum(len(actor_events(actor, metric)) for row in rows for actor in row['actors'])
    result = {'n': len(rows), 'flagged': flagged, 'occurrence': flagged / len(rows) if rows else None,
              'wilson95': wilson(flagged, len(rows)), 'events': total_events}
    if detector in TIME_DENOM:
        numerator = 0
        denominator = sum(actor['denominators'][TIME_DENOM[detector]] for row in rows for actor in row['actors'])
        for row in rows:
            for actor in row['actors']:
                rounds = set()
                for event in actor_events(actor, metric):
                    if event['turns']:
                        rounds.update(range(event['start'], event['end'] + 1))
                numerator += len(rounds)
        result.update(flagged_champion_turns=numerator, eligible_champion_turns=denominator,
                      flagged_per_1000=1000 * numerator / denominator if denominator else None)
    event_denominator = {'D3': 'native_deaths', 'D4': 'moves', 'D7': 'complete_turns',
                         'D8': 'bank_attempts', 'D11': 'vision_eligible_deaths'}.get(detector)
    if detector == 'D5' and ':' in metric:
        event_denominator = 'gem_reward_clear_episodes' if metric.endswith('reward_to_enemy_after_native_clear') else 'capture_progress_transitions'
    if event_denominator:
        denominator = sum(actor['denominators'].get(event_denominator, 0) for row in rows for actor in row['actors'])
        if detector == 'D8':
            denominator -= sum(actor['descriptors']['bank_attempts_censored'] for row in rows for actor in row['actors'])
        result.update(event_numerator=total_events, event_denominator=denominator,
                      event_rate=total_events / denominator if denominator else None)
    return result


def cluster_interval(rows, metric, cluster, seed, measure='occurrence'):
    groups = defaultdict(lambda: [0, 0, 0, 0])
    for row in rows:
        offset = 2 if row['won'] else 0
        if measure == 'event_rate':
            values = aggregate([row], metric)
            groups[row[cluster]][offset] += values['event_numerator']
            groups[row[cluster]][offset + 1] += values['event_denominator']
        else:
            groups[row[cluster]][offset] += int(observed(row, metric))
            groups[row[cluster]][offset + 1] += 1
    overlap = sum(value[1] > 0 and value[3] > 0 for value in groups.values())
    if len(groups) < 2 or not any(not r['won'] for r in rows) or not any(r['won'] for r in rows):
        return {'clusters': len(groups), 'clusters_with_both_outcomes': overlap, 'valid_replicates': 0, 'interval95': None}
    values = list(groups.values())
    token = f'{seed}|{metric}|{cluster}|{len(rows)}'.encode() if measure == 'occurrence' else f'{seed}|{metric}|{cluster}|{len(rows)}|event_rate'.encode()
    rng = random.Random(int(hashlib.sha256(token).hexdigest()[:16], 16))
    estimates = []
    for _ in range(2000):
        totals = [0, 0, 0, 0]
        for value in rng.choices(values, k=len(values)):
            for i in range(4):
                totals[i] += value[i]
        if totals[1] and totals[3]:
            estimates.append(totals[0] / totals[1] - totals[2] / totals[3])
    estimates.sort()
    ci = [estimates[int(.025 * (len(estimates) - 1))], estimates[int(.975 * (len(estimates) - 1))]] if len(estimates) >= 1000 else None
    return {'clusters': len(groups), 'clusters_with_both_outcomes': overlap, 'valid_replicates': len(estimates), 'interval95': ci}


def comparison(rows, metric, seed):
    losses = [r for r in rows if not r['won']]
    wins = [r for r in rows if r['won']]
    loss = aggregate(losses, metric)
    win = aggregate(wins, metric)
    result = {'losses': loss, 'wins': win,
            'occurrence_difference': loss['occurrence'] - win['occurrence'] if losses and wins else None,
            'map_cluster': cluster_interval(rows, metric, 'map', seed),
            'opponent_cluster': cluster_interval(rows, metric, 'opponent_id', seed)}
    if 'event_rate' in loss:
        result['event_rate_difference'] = loss['event_rate'] - win['event_rate'] if loss['event_rate'] is not None and win['event_rate'] is not None else None
        result['event_rate_map_cluster'] = cluster_interval(rows, metric, 'map', seed, 'event_rate')
        result['event_rate_opponent_cluster'] = cluster_interval(rows, metric, 'opponent_id', seed, 'event_rate')
    return result


def pct(value):
    return 'n/a' if value is None else f'{100 * value:.1f}%'


def interval(value):
    return 'insufficient support' if value is None else f'[{100 * value[0]:+.1f}, {100 * value[1]:+.1f}] pp'


def cell(value):
    ci = value['wilson95']
    return f"{value['flagged']}/{value['n']} ({pct(value['occurrence'])}; {pct(ci[0])}–{pct(ci[1])})" if ci else 'n=0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    run = json.loads((args.run / 'run.json').read_text(encoding='utf-8'))
    spec = json.loads((STUDY / 'DETECTOR_SPEC.json').read_text(encoding='utf-8'))
    spec_hash = hashlib.sha256((STUDY / 'DETECTOR_SPEC.json').read_bytes()).hexdigest()
    code_hash = hashlib.sha256((ROOT / 'tools/replay/detectors.mjs').read_bytes()).hexdigest()
    assert run['partition'] == 'examined' and run['passed'] == 385 and run['failed'] == 0
    assert run['code_sha256'] == code_hash and run['spec_sha256'] == spec_hash
    catalog = {r['match_id']: r for r in json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/restored-catalog.json').read_text(encoding='utf-8'))}
    manifest = json.loads((STUDY / 'CANDIDATE_MANIFEST.json').read_text(encoding='utf-8'))
    expected = {r['match_id'] for r in manifest['rows'] if r['partition'] == 'examined'}
    rows, reference = [], []
    observations = Counter()
    subtypes = set()
    for mid in sorted(expected):
        data = json.loads((args.run / f'{mid}.json').read_text(encoding='utf-8'))
        assert data['partition'] == 'examined' and all(data['validation'].values())
        assert data['spec_sha256'] == spec_hash and data['code_sha256'] == code_hash
        meta = catalog[mid]
        observations.update(data['validation_samples'])
        for actor in data['actors']:
            for detector in IDS:
                subtypes.update(detector + ':' + event['subtype'] for event in actor['detectors'][detector]['events'])
        if meta['source'] == 'top-v-top':
            for team in (0, 1):
                side = next(s for s in meta['sides'] if s['side'] == ('a' if team == 0 else 'b'))
                reference.append({'match_id': mid, 'map': meta['map'], 'cohort': 'Top-v-top',
                    'won': side['result'] == 'win', 'opponent_id': 'paired-reference',
                    'actors': [a for a in data['actors'] if a['team'] == team]})
        else:
            own_team = 0 if meta['side'] == 'a' else 1
            rows.append({**meta, 'won': meta['result'] == 'win',
                         'actors': [a for a in data['actors'] if a['team'] == own_team], 'rounds': data['rounds']})
    metrics = IDS + sorted(subtypes)
    comparisons = {}
    for cohort in ['All', 'Learn', 'Climb', 'Other']:
        subset = rows if cohort == 'All' else [r for r in rows if r['cohort'] == cohort]
        comparisons[cohort] = {metric: comparison(subset, metric, spec['reporting']['bootstrap_seed']) for metric in metrics}
    # The reference uses map clusters, retaining both paired teams in each draw.
    reference_stats = {metric: comparison(reference, metric, spec['reporting']['bootstrap_seed']) for metric in IDS}
    strata = {}
    for field in ['map', 'opponent', 'cohort']:
        strata[field] = {str(value): {metric: {'losses': aggregate([r for r in rows if r[field] == value and not r['won']], metric),
                                               'wins': aggregate([r for r in rows if r[field] == value and r['won']], metric)} for metric in metrics}
                         for value in sorted({r[field] for r in rows})}
    examples = {}
    for metric in metrics:
        candidates = []
        for row in rows:
            if row['won']:
                continue
            for actor in row['actors']:
                for event in actor_events(actor, metric):
                    candidates.append({'match_id': row['match_id'], 'map': row['map'], 'opponent': row['opponent'],
                        'cohort': row['cohort'], 'champion': actor['id'], 'name': actor['name'], **event})
        candidates.sort(key=lambda e: (e['turns'], e['end'] - e['start']), reverse=True)
        selected = []
        for candidate in candidates:
            if any(c['match_id'] == candidate['match_id'] for c in selected):
                continue
            selected.append(candidate)
            if len(selected) == 3:
                break
        examples[metric] = selected
    counts = {cohort: {'games': len(group), 'wins': sum(r['won'] for r in group), 'losses': sum(not r['won'] for r in group),
                       'maps': len({r['map'] for r in group}), 'opponents': len({r['opponent_id'] for r in group})}
              for cohort, group in [('All', rows), *[(c, [r for r in rows if r['cohort'] == c]) for c in ['Learn', 'Climb', 'Other']]]}
    frame_rates = {c: {metric: {'losses': aggregate([r for r in rows if not r['won'] and (c == 'All' or r['cohort'] == c)], metric),
                                'wins': aggregate([r for r in rows if r['won'] and (c == 'All' or r['cohort'] == c)], metric)}
                      for metric in TIME_DENOM} for c in counts}
    per_game = [{'match_id': r['match_id'], 'map': r['map'], 'opponent': r['opponent'], 'cohort': r['cohort'], 'won': r['won'],
                 'metrics': {metric: aggregate([r], metric) for metric in metrics}} for r in rows]
    report = {'evidence_label': 'association', 'updated_at': datetime.now(timezone.utc).isoformat(),
              'engine': '2.0.0', 'spec_sha256': spec_hash, 'code_sha256': code_hash,
              'examined_games': 385, 'own_examined_games': len(rows), 'reference_games': len(reference) // 2,
              'hands_off_games_processed': 0, 'counts': counts, 'validation_samples': dict(observations),
              'comparisons': comparisons, 'reference': reference_stats, 'strata': strata,
              'frame_rates': frame_rates, 'examples': examples, 'per_game': per_game,
              'limits': ['Exploratory multiple comparisons; no multiplicity correction. Hands-off confirmation remains pending.',
                         'Unequal opponent exposure and map/draft/version confounding remain. Flags can be legitimate behaviour.',
                         'D4 is movement, not hidden mode. D8 excludes rejected SDK calls. D9 ground stranding and D11 vision are sampled proxies.']}
    save(STUDY / 'DETECTOR_DATA.json', report)
    nloss = counts['All']['losses']
    nwin = counts['All']['wins']
    text = f'''# Examined-game detector screen

**Association, not causal bug attribution.** Engine 2.0.0; thresholds registered
before examined trajectories in commit 148d845 / DETECTOR_SPEC.json.

All 385 examined games pass snapshot/event checks: {len(rows)} DOOMSDAY games
({nloss} losses, {nwin} wins) and {len(reference)//2} top-v-top reference games.
The 165 hands-off games have **not** had detectors run or decision trajectories reviewed.
Five calibration games remain excluded. DETECTOR_VALIDATION.json records their checks.

## Coverage

| Primary cohort | Games | Wins | Losses | Maps | Opponents |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
    for cohort, value in counts.items():
        text += f"| {cohort} | {value['games']} | {value['wins']} | {value['losses']} | {value['maps']} | {value['opponents']} |\n"
    text += '''
## Losses compared with wins

Each occurrence means at least one of our physical champions triggered the flag
in that game. Cells give count/n, rate and Wilson 95% interval. Difference is
loss-minus-win; clustered intervals resample whole maps or whole opponents
(2,000 bootstrap draws). These are exploratory, unadjusted multiple comparisons.
DETECTOR_DATA.json also contains every subtype and map/opponent/cohort table.
Clustered intervals describe the marginal study contrast; they do not adjust away
map/opponent confounding. Cluster overlap counts are retained in the JSON. This
purposive corpus is not a random or rank-proportional sample of ladder opponents.

| Flag | Losses (Wilson 95%) | Wins (Wilson 95%) | Difference | Map-cluster 95% | Opponent-cluster 95% |
| --- | --- | --- | ---: | --- | --- |
'''
    for detector in IDS:
        value = comparisons['All'][detector]
        text += f"| {detector} | {cell(value['losses'])} | {cell(value['wins'])} | {100*value['occurrence_difference']:+.1f} pp | {interval(value['map_cluster']['interval95'])} | {interval(value['opponent_cluster']['interval95'])} |\n"
    text += '\n## Registered time-based flag durations\n\nAll own-game rows; overlapping subtype ranges are counted once per champion.\nThese are pooled measured durations, not independent-turn confidence intervals.\n\n| Flag | Loss flagged/eligible champion-turns | Win flagged/eligible champion-turns |\n| --- | ---: | ---: |\n'
    for detector in TIME_DENOM:
        value = frame_rates['All'][detector]
        loss, win = value['losses'], value['wins']
        text += f"| {detector} | {loss['flagged_champion_turns']}/{loss['eligible_champion_turns']} | {win['flagged_champion_turns']}/{win['eligible_champion_turns']} |\n"
    text += '''
## Rates per eligible event

These registered denominators address differing opportunities to trigger a flag.
D3 is repeated deaths / all native deaths; D8 is interruptions / observed bank
attempts excluding censored attempts; D11 is sampled visibility gaps / eligible
enemy-champion deaths. Intervals below still describe marginal associations.

| Flag | Loss events/exposure | Win events/exposure | Rate difference | Map-cluster 95% | Opponent-cluster 95% |
| --- | ---: | ---: | ---: | --- | --- |
'''
    for detector in ['D3', 'D8', 'D11']:
        value = comparisons['All'][detector]
        loss, win = value['losses'], value['wins']
        difference = value['event_rate_difference']
        text += f"| {detector} | {loss['event_numerator']}/{loss['event_denominator']} ({pct(loss['event_rate'])}) | {win['event_numerator']}/{win['event_denominator']} ({pct(win['event_rate'])}) | {100*difference:+.1f} pp | {interval(value['event_rate_map_cluster']['interval95'])} | {interval(value['event_rate_opponent_cluster']['interval95'])} |\n"
    text += '\n## Subtypes to examine next\n\nRanked descriptively by loss-minus-win occurrence in Climb, the rating-relevant cohort.\nA positive interval under both clustering choices is still association and requires\nmatched cards, visible-state review and eventual hands-off confirmation.\n\n| Subtype | Climb loss flags/n | Climb win flags/n | Difference | Map-cluster 95% | Opponent-cluster 95% |\n| --- | ---: | ---: | ---: | --- | --- |\n'
    ranked = sorted(((m, comparisons['Climb'][m]) for m in metrics if ':' in m and comparisons['Climb'][m]['occurrence_difference'] is not None),
                    key=lambda item: item[1]['occurrence_difference'], reverse=True)
    for metric, value in ranked[:8]:
        text += f"| {metric} | {value['losses']['flagged']}/{value['losses']['n']} | {value['wins']['flagged']}/{value['wins']['n']} | {100*value['occurrence_difference']:+.1f} pp | {interval(value['map_cluster']['interval95'])} | {interval(value['opponent_cluster']['interval95'])} |\n"
    text += '\n## Example loss rounds\n\nSelection is descriptive: longest registered episodes, distinct game IDs. Full\ncontexts and additional examples are in DETECTOR_DATA.json; no hands-off game appears.\n'
    for metric, _ in ranked[:5]:
        text += '\n' + metric + ':\n\n'
        for example in examples[metric]:
            url = 'https://2026a.battlecode.co.uk/game/visualiser/' + example['match_id']
            text += f"- [{example['match_id'][:8]}]({url}), {example['map']} vs {example['opponent']}, {example['name']} #{example['champion']}: rounds {example['start']}–{example['end']}, first flag {example['fired_round']}.\n"
    text += '''
## Validation, limits and next action

The extractor uses the engine's actual channel/stun state, official camp-group
identities and capture timers. Every examined game reconciles native fuel, wards,
purchases, banks and faults against replay steps, and each sampled turn-start own state agrees
with its omniscient counterpart. All masks and decoders use the pinned official assets.
Semantic tests cover channel/attack/capture/stun exclusions, passive displacement,
death/incomplete-turn censoring, gaps, overlapping ranges and Greed equipment cost.

Coverage limits are part of the registered definitions: D4 measures tile oscillation,
not hidden mode changes; D5 progress is sampled at round boundaries and reward ownership
means native last-clear ownership; D8 cannot observe rejected SDK calls or prove dynamic
gate inaccessibility; D9's ground component omits ability/teleport escape; D11 samples
the five preceding own-turn observations, not continuous vision or the death round.
Positive faults were absent from calibration, so their positive-event semantics have
less validation than fuel events. No flag alone is an actionable bot-code change.

Next: Session 2 round timelines, income/conversion/denial/time decomposition, openings,
game-separated calibrated win probability, then diverse loss/win cards and ceilings.
Do not queue wave 2 until FAST_FINDINGS.md and hypothesis/prediction/decision rules exist.
'''
    (STUDY / 'P2_DETECTORS.md').write_bytes(text.encode('utf-8'))
    print(json.dumps({'own_games': len(rows), 'own_losses': nloss, 'own_wins': nwin,
                      'reference_games': len(reference)//2, 'hands_off_processed': 0,
                      'top_climb_subtypes': [{'metric': m, 'difference': value['occurrence_difference'],
                          'map95': value['map_cluster']['interval95'], 'opponent95': value['opponent_cluster']['interval95']} for m,value in ranked[:5]]}))


if __name__ == '__main__':
    main()
