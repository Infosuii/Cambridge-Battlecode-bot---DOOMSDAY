"""Render prediction-first descriptive cards and nearest-state winner controls."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from deep_preflight import ROOT
from deep_detector_report import save
from winprob import features

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'
CATEGORIES = {'enemy_bank': 'Opponent bank in the swing window',
              'own_death': 'Our native death in the swing window',
              'repeat_death': 'Registered D3 repeat death in the swing window',
              'large_bag_loss': 'Our native gem loss >=40 in the swing window',
              'enemy_purchase': 'Opponent purchase in the swing window',
              'enemy_camp_income': 'Opponent camp gem receipt in the swing window',
              'unclassified_state_change': 'None of the six event labels above'}
KINDS = {4: 'move', 5: 'attack', 6: 'cast', 9: 'priority', 11: 'recall', 12: 'bank_start', 13: 'buy',
         14: 'ward', 15: 'consumable', 16: 'cancel_channel', 18: 'bank_complete', 20: 'altar_lock',
         21: 'teleport_channel', 22: 'teleport_complete', 23: 'movement_blocked', 25: 'sell', 26: 'fuel', 27: 'fault'}


def tiny(c):
    p = c['p']
    return f"{c['id']}@{p['x']},{p['y']} hp{c['hp']:.0f}/{c['max_hp']:.0f} bag{c['bag']}" if p else f"{c['id']} dead={not c['alive']} hp{c['hp']:.0f} bag{c['bag']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--detectors', type=Path, default=LOCAL / 'detector-examined-v3')
    args = ap.parse_args()
    sample = json.loads((STUDY / 'MOMENT_SAMPLE.json').read_text(encoding='utf-8'))
    prediction_path = STUDY / 'CARD_PREDICTIONS.json'
    pred_hash = hashlib.sha256(prediction_path.read_bytes()).hexdigest()
    predictions = {r['card_id']: r for r in json.loads(prediction_path.read_text(encoding='utf-8'))['rows']}
    metadata = [r for r in json.loads((LOCAL / 'restored-catalog.json').read_text(encoding='utf-8')) if r['partition'] == 'examined']
    bymeta = {r['match_id']: r for r in metadata}
    # Winner controls, fixed scale Euclidean matching; maps preferred within caliper.
    pools = {kind: {'x': [], 'meta': []} for kind in ('own_win', 'top_winner')}
    for meta in metadata:
        kind = 'top_winner' if meta['source'] == 'top-v-top' else 'own_win' if meta['result'] == 'win' else None
        if not kind:
            continue
        game = json.loads((args.run / (meta['match_id'] + '.json')).read_text(encoding='utf-8'))
        own = (0 if game['outcome'] == 'teamA' else 1) if kind == 'top_winner' else (0 if meta['side'] == 'a' else 1)
        xx = features(game) * (-1 if own else 1)
        for i, row in enumerate(game['rows']):
            if row['terminal'] or row['initial'] or row['r'] % 10 or row['r'] > game['rounds'] - 15:
                continue
            pools[kind]['x'].append(np.r_[xx[i], row['r'] / game['max_rounds'] * 2])
            pools[kind]['meta'].append({'match_id': meta['match_id'], 'map': meta['map'], 'r': row['r'], 'own_side': own})
    for pool in pools.values():
        pool['x'] = np.array(pool['x'])
    cache = {}
    def load(mid):
        if mid not in cache:
            cache[mid] = json.loads((args.run / (mid + '.json')).read_text(encoding='utf-8'))
        return cache[mid]
    def match(card, kind):
        pool = pools[kind]
        x = np.r_[card['start_features'], card['start'] / 2000 * 2]
        distances = np.sqrt(((pool['x'] - x) ** 2).sum(axis=1))
        eligible = np.array([m['match_id'] != card['match_id'] for m in pool['meta']])
        same_map = np.array([m['map'] == card['map'] for m in pool['meta']]) & eligible
        candidate = np.flatnonzero(same_map & (distances <= 2.5))
        if not len(candidate):
            candidate = np.flatnonzero(eligible & (distances <= 2.5))
        if not len(candidate):
            return None
        i = min(candidate, key=lambda i: (distances[i], pool['meta'][i]['match_id'], pool['meta'][i]['r']))
        m = pool['meta'][i]
        g = load(m['match_id'])
        before = next(r for r in g['rows'] if r['r'] == m['r'])
        after = next(r for r in g['rows'] if r['r'] >= m['r'] + 10)
        team, label = m['own_side'], 'teamA' if m['own_side'] == 0 else 'teamB'
        own_events = [e for e in g['events'] if before['r'] < e['timestamp']['round'] <= after['r'] and e['owner']['team'] == label]
        return dict(m, distance=float(distances[i]), same_map=m['map'] == card['map'],
                    end=after['r'], banked_change=after['teams'][team]['banked'] - before['teams'][team]['banked'],
                    collected_change=after['teams'][team]['collected'] - before['teams'][team]['collected'],
                    lost_change=after['teams'][team]['lost'] - before['teams'][team]['lost'],
                    equipment_change=after['teams'][team]['equipment_cost'] - before['teams'][team]['equipment_cost'],
                    actions=dict(Counter(KINDS.get(a['kind'], str(a['kind'])) for a in g['actions'] if before['r'] < a['r'] <= after['r'] and any(c['id'] == a['actor'] and c['team'] == label for c in g['roster']))),
                    native_events=dict(Counter(e['kind'] for e in own_events)))
    rows, match_rows = [], []
    folder = STUDY / 'cards'
    folder.mkdir(exist_ok=True)
    for card in sample['rows']:
        cid = card['card_id']
        context = json.loads((LOCAL / 'card-contexts' / (cid + '.json')).read_text(encoding='utf-8'))
        assert context['predictions_sha256'] == pred_hash
        prediction = predictions[cid]
        ownlabel = 'teamA' if card['own_side'] == 0 else 'teamB'
        events = [e for e in context['events'] if card['start'] < e['timestamp']['round'] <= card['end']]
        own = [e for e in events if e['owner']['team'] == ownlabel]
        enemy = [e for e in events if e['owner']['team'] != ownlabel]
        det = json.loads((args.detectors / (card['match_id'] + '.json')).read_text(encoding='utf-8'))
        repeats = [e for a in det['actors'] if a['team'] == card['own_side'] for e in a['detectors']['D3']['events'] if card['start'] < e['start'] <= card['end']]
        tags = {'enemy_bank': any(e['kind'] == 'gemSubmission' for e in enemy), 'own_death': any(e['kind'] == 'death' for e in own),
                'repeat_death': bool(repeats), 'large_bag_loss': any(e['kind'] == 'gemLoss' and int(e['value']) >= 40 for e in own),
                'enemy_purchase': any(e['kind'] in ('buyItem', 'buyConsumable') for e in enemy),
                'enemy_camp_income': any(e['kind'] == 'gemCollection' and isinstance(e['target'], dict) and e['target'].get('kind') == 'campGroup' for e in enemy)}
        tags['unclassified_state_change'] = not any(tags.values())
        controls = {k: match(card, k) for k in pools}
        match_rows.append({'card_id': cid, 'controls': controls})
        actionmix = Counter(KINDS.get(a['kind'], str(a['kind'])) for a in context['actions'] if card['start'] < a['r'] <= card['end'])
        focus_obs = [o for o in context['observations'] if card['start'] < o['r'] <= card['end']]
        attacks_enemy = 0
        for a in context['actions']:
            if a['kind'] not in (5, 6) or not card['start'] < a['r'] <= card['end']:
                continue
            obs = next((o for o in focus_obs if o['r'] == a['r']), None)
            if obs and any(e['p'] == a['to'] for e in obs['enemies']):
                attacks_enemy += 1
        row = {k: card[k] for k in ('card_id', 'match_id', 'cohort', 'map', 'opponent', 'kind', 'start', 'center', 'end', 'p_before', 'p_after', 'drop')}
        row.update(tags, actor_id=prediction['actor_id'], lone_prerequisites=prediction['lone_guard_prerequisites'],
                   observed_attacks_or_casts_at_turn_start_enemy=attacks_enemy,
                   prediction_status='rule-conditional; no confirmed violation without effective-rule trace')
        rows.append(row)
        o = prediction['pre_window_observation']
        g = load(card['match_id'])
        before = next(r for r in g['rows'] if r['r'] == card['start'])['teams'][card['own_side']]
        largest = sorted(card['feature_probability_change'].items(), key=lambda p: abs(p[1]), reverse=True)[:3]
        lines = [f"# {cid}: {card['kind']} R{card['center']}", '',
                 f"Game `{card['match_id']}` · {card['cohort']} · {card['map']} · {card['opponent']} · {card['result']}",
                 f"Model window R{card['start']}–{card['end']}; context R{card['start']-20}–{card['end']+20}; own side {card['own_side']}; focus {prediction['actor_id']}.",
                 f"P(win) {card['p_before']:.3f} → {card['p_after']:.3f}; selected drop {card['drop']:.3f} (association).",
                 f"Expected first (frozen b490a1d): {prediction['expectation']}",
                 f"Actor-own pre-turn R{o['r']}/input{o['input']}: {tiny(o['self'])}; healthy allies≤4={prediction['healthy_friends4']}.",
                 'Visible enemies≤8: ' + ('; '.join(tiny(e) for e in o['enemies']) or 'none at this sample'),
                 'Own team at model start: ' + '; '.join(f"{c['id']}@{c['p']} hp{c['hp']:.0f} bag{c['gems']}" for c in before['self']),
                 f"Focus actions inside model window: {dict(actionmix)}; casts/basic targets matching turn-start visible enemy positions={attacks_enemy}.",
                 'Observed focus states: ' + (' → '.join(f"R{q['r']} {tiny(q['self'])}" for q in (focus_obs[:1] + focus_obs[-1:])) or 'no owned turn in this interval'),
                 'Own native events: ' + str(dict(Counter(e['kind'] for e in own))),
                 'Opponent native events: ' + str(dict(Counter(e['kind'] for e in enemy))),
                 'Event labels: ' + ', '.join(k for k, value in tags.items() if value),
                 'Largest signed model components: ' + ', '.join(f'{k} {v:+.3f}' for k, v in largest),
                 f"Matched own win: {controls['own_win']}", f"Matched top winner: {controls['top_winner']}",
                 'Judgement: descriptive review candidate; a death, bank, purchase or attack is not by itself a policy mistake.',
                 'Source: bot.cpp:3988–4018 (V75 guard), :6726–6885 (effective knobs); common.h:1332–1345 (defaults).',
                 'Limits: target TTK/one-turn-kill exception, hidden memory, build flags and exact effective thresholds are untraced; shared team views do not replace actor vision.']
        assert len(lines) <= 25
        (folder / (cid + '.md')).write_bytes(('\n'.join(lines) + '\n').encode())
    csvio = io.StringIO(newline='')
    writer = csv.DictWriter(csvio, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    (STUDY / 'error_analysis.csv').write_bytes(csvio.getvalue().encode())
    selected = [r for r in rows if r['kind'] == 'loss']
    total = sum(r['drop'] for r in selected)
    summary = {}
    for tag, title in CATEGORIES.items():
        subset = [r for r in selected if r[tag]]
        summary[tag] = {'definition': title, 'moments': len(subset), 'moment_share': len(subset) / len(selected),
                        'surrogate_drop_sum': sum(r['drop'] for r in subset),
                        'surrogate_drop_share': sum(r['drop'] for r in subset) / total,
                        'unique_loss_games': len({r['match_id'] for r in subset}),
                        'control_win_moments': sum(r[tag] for r in rows if r['kind'] == 'win_control')}
    result = {'cards': len(rows), 'loss_cards': len(selected), 'distinct_losses': len({r['match_id'] for r in selected}),
              'control_wins': len(rows) - len(selected), 'hands_off_used': 0, 'category_summary': summary,
              'lone_prerequisite_cards': sum(r['lone_prerequisites'] for r in rows),
              'lone_prerequisite_with_enemy_target_action': [r['card_id'] for r in rows if r['lone_prerequisites'] and r['observed_attacks_or_casts_at_turn_start_enemy']],
              'status': 'descriptive cards; no exact rule violation or causal fix established', 'rows': rows}
    save(STUDY / 'CARD_DATA.json', result)
    save(STUDY / 'MATCHED_CONTROLS.json', {'method': 'fixed-scale Euclidean distance on ten pre-state features plus 2*round progress; prefer same map within distance2.5, else global within2.5; winners selected on final outcome',
        'limits': 'No causal control: opponent/draft/latent memory and survivor selection remain; controls can repeat. Native events/action counts are observed ten-round follow-up, not prescription.',
        'coverage': {k: {'matched': sum(r['controls'][k] is not None for r in match_rows),
                        'same_map': sum(r['controls'][k] is not None and r['controls'][k]['same_map'] for r in match_rows),
                        'distinct_games': len({r['controls'][k]['match_id'] for r in match_rows if r['controls'][k]})} for k in pools}, 'rows': match_rows})
    lines = ['# Moment review: event labels and surrogate ceilings', '',
             '105 prediction-first cards cover 90 moments from 65 distinct examined losses and 15 control wins. Exact actor-own observations and conditional rule expectations were committed in b490a1d before the subsequent action extractor ran. The 65 loss games span Learn20/Climb30/Other15 and multiple maps.', '',
             '**Association only.** These overlapping labels describe what happened inside selected model-drop windows. Their shares are selection-weighted surrogate ceilings for further review; they are not avoidable win rate, causal regret, or a proven fix ceiling. Labels can overlap and sum above100%.', '',
             '| Event label | Loss moments /90 | Distinct losses /65 | Share of selected surrogate drop | Control-win moments /15 |', '|---|---:|---:|---:|---:|']
    for tag, r in sorted(summary.items(), key=lambda kv: -kv[1]['surrogate_drop_share']):
        lines.append(f"| {r['definition']} | {r['moments']} | {r['unique_loss_games']} | {r['surrogate_drop_share']:.1%} | {r['control_win_moments']} |")
    lines += ['', f"The V75 lone-guard public prerequisites hold in {result['lone_prerequisite_cards']}/105 pre-window focus observations. Enemy-target actions later appear in cards {result['lone_prerequisite_with_enemy_target_action']}; neither a cast nor an attack proves the guard was bypassed, because the one-turn-kill exception, flee weaving and exact target/risk branch require traces.", '',
              'The frozen source defaults disable V75_BAG; a high-bag fighter is not automatically violating that rule. Effective map/lab values and compiler overrides remain unverified against the server build. This avoids interpreting every surprise as a bug.', '',
              'MATCHED_CONTROLS.json supplies nearest-state own-win and top-winner examples, observed follow-up actions/events and caliper coverage. Controls were chosen among winners, can repeat, and retain draft/opponent/memory confounding. Similar state and a different outcome do not establish a better decision.', '',
              'Full local contexts preserve each selected actor’s turn-start own view over the expanded window and every recorded focus action. Cards are capped at25 lines; error_analysis.csv has one row per card. Hand auditing, exact reproduction and effective-rule traces are the next gate before marking these event labels as mistakes.']
    (STUDY / 'P4_CARDS.md').write_bytes(('\n'.join(lines) + '\n').encode())
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
