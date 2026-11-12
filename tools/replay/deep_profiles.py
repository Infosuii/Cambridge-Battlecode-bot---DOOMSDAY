"""Examined-only opponent scorecards; geometric proxies are not policy intent."""
import json
from collections import Counter, defaultdict
from statistics import median
from deep_preflight import ROOT
from deep_detector_report import save, wilson
from deep_timeline_report import cluster_mean
from deep_json import save_table

STUDY=ROOT/'research/deep-2026-10-28'
LOCAL=ROOT/'artifacts/local-only/deep-2026-10-28'


def mean(values):
    return sum(values)/len(values) if values else None


def main():
    timelines=json.loads((STUDY/'TIMELINE_DATA.json').read_text(encoding='utf-8'))
    run=LOCAL/'profile-examined-v1';receipt=json.loads((run/'run.json').read_text(encoding='utf-8'))
    assert receipt['partition']=='examined' and receipt['passed']==385 and receipt['failed']==0
    openings={(r['match_id'],r['team']):r for r in timelines['opening_rows']}
    rows=[]
    for row in timelines['rows']:
        row=dict(row);mid=row['match_id'];native=json.loads((LOCAL/'replays/examined'/(mid+'.summary.json')).read_text(encoding='utf-8'))
        profile=json.loads((run/(mid+'.json')).read_text(encoding='utf-8'))
        assert profile['code_sha256']==receipt['code_sha256'] and profile['passed']
        size=max(native['match']['width'],native['match']['height'])
        row['geometry_band']='compact' if size<=41 else 'medium' if size<=64 else 'large'
        row['side_metrics']={}
        for label,side in [('us',row['own_side']),('them',1-row['own_side'])]:
            team='teamA' if side==0 else 'teamB'
            ev=[(e['kind'],v) for e in native['events'] if e['owner'].get('team')==team for v in e['entries']]
            final=row['final'][label];contact=profile['teams'][side]
            row['side_metrics'][label]={**final,**contact,
                'deaths':sum(k=='death' for k,v in ev),
                'high_bag_loss_events':sum(k=='gemLoss' and int(v['value'])>=40 for k,v in ev),
                'high_bag_loss_gems':sum(int(v['value']) for k,v in ev if k=='gemLoss' and int(v['value'])>=40),
                'camp_gems':row['capture_gems'][0 if label=='us' else 1],
                'opening':openings[mid,label]}
        rows.append(row)
    by_opponent=defaultdict(list)
    for r in rows:by_opponent[r['opponent']].append(r)
    learn=sorted(name for name,rs in by_opponent.items() if rs[0]['cohort']=='Learn')
    climb=sorted((name for name,rs in by_opponent.items() if rs[0]['cohort']=='Climb'),key=lambda n:(-sum(r['result']=='loss' for r in by_opponent[n]),-len(by_opponent[n]),n))[:3]
    profiles=[];matchups=[]
    for opponent,rs in sorted(by_opponent.items()):
        for band in ('compact','medium','large'):
            group=[r for r in rs if r['geometry_band']==band]
            if not group:continue
            wins=sum(r['result']=='win' for r in group);margin=cluster_mean(group,'final_margin','map')
            label='observed wins' if wins else 'uncertain'
            if not wins and len(group)>=5 and margin['mean'] < -300 and margin['interval95'] and margin['interval95'][1]<0:label='observed one-sided'
            matchups.append({'opponent':opponent,'cohort':rs[0]['cohort'],'geometry_band':band,'n':len(group),'wins':wins,'win_rate':wins/len(group),'wilson95':wilson(wins,len(group)),'margin':margin,'interpretation':label})
        if opponent not in learn+climb:continue
        profile={'opponent':opponent,'cohort':rs[0]['cohort'],'n':len(rs),'maps':len({r['map'] for r in rs}),'wins':sum(r['result']=='win' for r in rs),
                 'margin':cluster_mean(rs,'final_margin','map'),'sides':dict(Counter('A' if r['own_side']==0 else 'B' for r in rs)),
                 'economy':{},'metrics':{},'openings':{}}
        for mark in (100,250,500):
            present=[r for r in rs if str(mark) in r['curve']]
            profile['economy'][str(mark)]={'n':len(present),'paired_mean':{s:{f:mean([r['curve'][str(mark)][s][f] for r in present]) for f in ('collected','earned_gold','equipment_cost','banked')} for s in ('us','them')}}
        for side in ('us','them'):
            vals=[r['side_metrics'][side] for r in rs]
            total=lambda f:sum(v[f] for v in vals)
            ratio=lambda a,b:total(a)/total(b) if total(b) else None
            profile['metrics'][side]={f:mean([v[f] for v in vals]) for f in ('deaths','vision_fraction','middle_vision_fraction','wards_placed','dead_rounds','travel_rounds','stationary_rounds','channel_rounds','fuel_outs','high_bag_loss_events','high_bag_loss_gems')}
            profile['metrics'][side].update(conversion=ratio('banked','collected'),middle_share_of_camp_gems=ratio('middle_gems','camp_gems'),damage_per_contact_champion_round=ratio('contact_damage','contact_champion_rounds'),basic_focus_rate=ratio('multi_attacker_target_rounds','basic_target_rounds'),low_hp_separation_rate=ratio('separating_rounds','low_hp_near_enemy_rounds'),contact_champion_rounds=total('contact_champion_rounds'),basic_target_rounds=total('basic_target_rounds'),low_hp_near_enemy_rounds=total('low_hp_near_enemy_rounds'))
            os=[v['opening'] for v in vals];purchases=[o['first_purchase'] for o in os if o['first_purchase'] is not None];large=[o['first_large_observed_gem_reward'][0] for o in os if o['first_large_observed_gem_reward']]
            drafts=Counter(tuple(o['draft']) for o in os)
            profile['openings'][side]={'games':len(os),'modal_draft':[{'draft':list(k),'games':n} for k,n in drafts.most_common(3)],'first_purchase':{'n':len(purchases),'median_round':median(purchases) if purchases else None},'first_large_reward':{'n':len(large),'median_round':median(large) if large else None},'target_rows':'TIMELINE_DATA.json opening_rows: per physical actor, first three observed camp targets and receipt rounds; group IDs are map-local.'}
        profiles.append(profile)
    data={'evidence':'measured historical comparisons; no causal exploits','hands_off_used':0,'run_receipt':receipt,'selection':{'Learn':learn,'Climb':climb},'profiles':profiles,'matchups':matchups,'rows':rows,'definition_file':'P5_PROFILE_SPEC.json'}
    save_table(STUDY/'PROFILE_DATA.json',data)
    lines=['# Opponents and matchup scorecard','','Measured on 360 examined DOOMSDAY games. Profiles cover all five Learn opponents and the three Climb opponents with most observed losses. These are historical study cohorts, not a current ladder claim. All 385 examined replay contact extracts passed; 413,705 round boundaries. Five calibration games passed and basic-focus counts independently matched accepted-input target sets for both teams.','','## Paired scorecard','','Each cell is **ours / opponent** in the same games. Gems are cumulative collected, not income per round; mark-specific coverage follows the value. Damage denominator is contact-exposed champion-rounds. Contact is omniscient distance<=6, focus is basic attacks only, and separation includes displacement. These do not establish visibility, combat skill or retreat intent.','','| Opponent | n W/L | R100 gems | R250 gems | R500 gems | Conversion | Deaths/game | Contact damage | Basic focus | Low-HP separation |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for p in profiles:
        u,t=p['metrics']['us'],p['metrics']['them'];eco=p['economy']
        def e(mark):
            a=eco[str(mark)];return f"{a['paired_mean']['us']['collected']:.1f}/{a['paired_mean']['them']['collected']:.1f} (n={a['n']})"
        def pair(f,pct=False):return '/'.join('n/a' if v is None else f'{100*v:.1f}%' if pct else f'{v:.1f}' for v in (u[f],t[f]))
        lines.append(f"| {p['opponent']} | {p['n']} {p['wins']}/{p['n']-p['wins']} | {e(100)} | {e(250)} | {e(500)} | {pair('conversion',True)} | {pair('deaths')} | {pair('damage_per_contact_champion_round')} | {pair('basic_focus_rate',True)} | {pair('low_hp_separation_rate',True)} |")
    lines+=['','| Opponent | n | Wards/game | Final vision | Middle camp-gem share | Dead rounds/game | Travel rounds/game | Stationary rounds/game | Channel rounds/game | Fuel-outs/game |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for p in profiles:
        u,t=p['metrics']['us'],p['metrics']['them']
        def pair(f,pct=False):return '/'.join('n/a' if v is None else f'{100*v:.1f}%' if pct else f'{v:.1f}' for v in (u[f],t[f]))
        lines.append(f"| {p['opponent']} | {p['n']} | {pair('wards_placed')} | {pair('vision_fraction',True)} | {pair('middle_share_of_camp_gems',True)} | {pair('dead_rounds')} | {pair('travel_rounds')} | {pair('stationary_rounds')} | {pair('channel_rounds')} | {pair('fuel_outs')} |")
    lines+=['','Time categories are per physical body and are proxies, not avoidable time. Stationary includes useful fighting/capturing. Final vision is one boundary, not whole-game vision. Pooled contact/focus/separation denominators, all economy gold/equipment rows and per-game values are in PROFILE_DATA.json.','','## Draft, opening and exploitable-error hypotheses','']
    for p in profiles:
        t=p['openings']['them'];m=p['metrics']['them'];draft=t['modal_draft'][0]
        lines += [f"### {p['opponent']} ({p['cohort']}, n={p['n']})",'',f"Most frequent ordered draft: {', '.join(draft['draft'])} ({draft['games']}/{p['n']} games). Opponent first-purchase median R{t['first_purchase']['median_round']} (n={t['first_purchase']['n']}); first >=20-gem team receipt median R{t['first_large_reward']['median_round']} (n={t['first_large_reward']['n']}). Map-local first-three target paths and rosters are preserved in TIMELINE_DATA.json, not pooled as globally equivalent camps.", '',f"Opponent loses >=40 gems in {m['high_bag_loss_events']:.2f} native loss events/game, {m['high_bag_loss_gems']:.1f} gems/game (n={p['n']}); this is an observed opportunity ceiling, not an exposed-bag/over-chase proof. Test a visible-carrier opportunity rule against matched states before treating it as an exploit. Opponent code and intent were not inspected.",'']
    lines+=['## Matchups by map size','','The requested map-family comparison uses reproducible size bands (compact<=41, medium42–64, large>=65 max dimension). It does not classify walls, islands, gates or bushes, and cannot establish a structural loss. “Observed one-sided” means n>=5, zero wins, mean margin<-300 and map-bootstrap upper bound<0. “Observed wins” is evidence of historical wins only.','','| Opponent | Band | n | W | Win% (Wilson95) | Mean margin (map95) | Description |','|---|---|---:|---:|---|---|---|']
    for r in matchups:
        ci=r['wilson95'];margin=r['margin'];interval=margin['interval95']
        lines.append(f"| {r['opponent']} | {r['geometry_band']} | {r['n']} | {r['wins']} | {100*r['win_rate']:.1f}% [{100*ci[0]:.1f},{100*ci[1]:.1f}] | {margin['mean']:.1f} ({'insufficient maps' if interval is None else f'[{interval[0]:.1f},{interval[1]:.1f}]'}) | {r['interpretation']} |")
    (STUDY/'P5_OPPONENTS.md').write_bytes(('\n'.join(lines)+'\n').encode())
    print(json.dumps({'profiles':len(profiles),'matchup_strata':len(matchups),'own_games':len(rows),'hands_off_used':0}))


if __name__=='__main__':main()
