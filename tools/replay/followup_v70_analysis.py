"""Descriptive current-version economy, repeated deaths and bag conversion; no refit."""
import json
from collections import Counter,defaultdict
from statistics import median
from deep_preflight import ROOT
from deep_detector_report import save,wilson
from deep_timeline_report import cluster_mean
from deep_json import save_table
from deep_final_confirmation import d3
from puppet.screen_recall_loops import episodes
S=ROOT/'research/followup-v70-2026-10-29';L=ROOT/'artifacts/local-only/followup-v70-2026-10-29'
MARKS=(25,50,75,100,150,250,500)
FIELDS=('collected','banked','gems','lost','earned_gold','gold','spent_gold','equipment_cost','capture_gold','kill_gold','bank_bonus_gold','deaths','middle_gems','enemy_territory_gems')
def mean(v):return sum(v)/len(v) if v else None


def main():
    manifest=json.loads((S/'MANIFEST.json').read_text(encoding='utf-8'));run=json.loads((L/'metrics/run.json').read_text(encoding='utf-8'));assert run['passed']==85 and not run['failed'];rows=[];heroes=[]
    downloads={r['match_id']:r for r in json.loads((S/'DOWNLOADS.json').read_text(encoding='utf-8'))['rows']}
    for meta in manifest['rows']:
        mid=meta['match_id'];native=json.loads((L/'replays'/(mid+'.summary.json')).read_text(encoding='utf-8'));game=json.loads((L/'metrics'/(mid+'.json')).read_text(encoding='utf-8'));assert game['code_sha256']==run['code_sha256']
        own=0 if meta['our_side']=='a' else 1;team='teamA' if own==0 else 'teamB';ids={c['id'] for c in native['roster']['champions'] if c['team']==team};flat=[dict(v,kind=e['kind'],owner=e['owner']) for e in native['events'] for v in e['entries']]
        out=dict(meta);out['replay_sha256']=downloads[mid]['replay_sha256'];out['curve']={str(g['r']):{'us':g['teams'][own],'them':g['teams'][1-own]} for g in game['rows'] if g['r'] in MARKS}
        out['final']={'us':game['rows'][-1]['teams'][own],'them':game['rows'][-1]['teams'][1-own]};u,t=out['final']['us'],out['final']['them']
        out.update(final_margin=u['banked']-t['banked'],income_margin=u['collected']-t['collected'],preservation_margin=t['lost']-u['lost'],carry_margin=t['gems']-u['gems'])
        assert out['final_margin']==out['income_margin']+out['preservation_margin']+out['carry_margin'];assert out['our_score']==u['banked'] and out['opponent_score']==t['banked']
        faults=native['diagnostics']['botFaults'];out['faults']={'us':faults[team],'them':faults['teamB' if team=='teamA' else 'teamA']}
        out['fuel']={s:sum(int(e['value']) for e in flat if e['kind']=='fuelExhausted' and (e['owner']['id'] in ids)==(s=='us')) for s in ('us','them')}
        out['first_purchase']={s:min((e['timestamp']['round'] for e in flat if e['kind']=='buyItem' and (e['owner']['id'] in ids)==(s=='us')),default=None) for s in ('us','them')}
        out['first_bank']={s:min((e['timestamp']['round'] for e in flat if e['kind']=='gemSubmission' and (e['owner']['id'] in ids)==(s=='us')),default=None) for s in ('us','them')}
        repeated,_=d3(native);out['repeated_deaths']=sum(actor in ids for actor,r in repeated);out['deaths']=sum(len(e['entries']) for e in native['events'] if e['kind']=='death' and e['owner']['id'] in ids)
        loops=[e for e in episodes(game['actions'],native) if e['actor'] in ids];out['loop_episodes']=len(loops);out['loop_restart_turns']=sum(e['turns'] for e in loops);out['winning_bag_loop']=any(e['previous_round_winning_bag_every_round'] for e in loops)
        out['loop_details_local']=loops
        deathkeys={(e['owner']['id'],e['timestamp']['round'],e['timestamp']['input']) for e in flat if e['kind']=='death'}
        baglosses=[e for e in flat if e['kind']=='gemLoss' and e['owner']['id'] in ids and (e['owner']['id'],e['timestamp']['round'],e['timestamp']['input']) in deathkeys]
        out['large_bag_deaths']=sum(int(e['value'])>=40 for e in baglosses);out['large_bag_gems']=sum(int(e['value']) for e in baglosses if int(e['value'])>=40)
        for mark in (100,250):
            c=out['curve'].get(str(mark));out[f'equipment_gap_{mark}']=c['us']['equipment_cost']-c['them']['equipment_cost'] if c else None
            out[f'capture_gold_gap_{mark}']=c['us']['capture_gold']-c['them']['capture_gold'] if c else None
        sample=next((g for g in game['rows'] if g['r']==100),None)
        if sample:
            for c in sample['champions']:
                heroes.append({'match_id':mid,'map':meta['map'],'opponent':meta['opponent'],'result':meta['result'],'side':'us' if c['team']==own else 'them',**{k:c[k] for k in ('id','name','alive','earned_gold','gold','collected','banked','deaths','equipment_cost','capture_gold','kill_gold','bank_bonus_gold','spent_gold','monster_damage','champion_damage')}})
        rows.append(out)
    def aggregate(rs):
        out={'n':len(rs),'wins':sum(r['result']=='win' for r in rs),'maps':len({r['map'] for r in rs}),'groups':len({r['group_id'] for r in rs}),'sides':dict(Counter(r['our_side'] for r in rs))}
        out['win_wilson95']=wilson(out['wins'],len(rs));out['final_margin']=mean([r['final_margin'] for r in rs]);out['decomposition']={f:mean([r[f] for r in rs]) for f in ('income_margin','preservation_margin','carry_margin')}
        out['curves']={}
        for mark in MARKS:
            present=[r for r in rs if str(mark) in r['curve']];out['curves'][str(mark)]={'n':len(present),'mean':{s:{f:mean([r['curve'][str(mark)][s][f] for r in present]) for f in FIELDS} for s in ('us','them')}}
        for mark in (100,250):
            out[f'equipment_gap_{mark}']={k:cluster_mean(rs,f'equipment_gap_{mark}',k) for k in ('map','group_id')};out[f'capture_gold_gap_{mark}']={k:cluster_mean(rs,f'capture_gold_gap_{mark}',k) for k in ('map','group_id')}
        out['conversion']={s:sum(r['final'][s]['banked'] for r in rs)/max(1,sum(r['final'][s]['collected'] for r in rs)) for s in ('us','them')}
        out['fuel']={s:sum(r['fuel'][s] for r in rs) for s in ('us','them')};out['faults']={s:sum(r['faults'][s] for r in rs) for s in ('us','them')}
        out['repeated_deaths']=sum(r['repeated_deaths'] for r in rs);out['deaths']=sum(r['deaths'] for r in rs)
        out['loop_games']=sum(r['loop_episodes']>0 for r in rs);out['winning_bag_loop_games']=sum(r['winning_bag_loop'] for r in rs);out['large_bag_deaths']=sum(r['large_bag_deaths'] for r in rs);out['large_bag_gems']=sum(r['large_bag_gems'] for r in rs)
        out['first_purchase_median']={s:median(v) if (v:=[r['first_purchase'][s] for r in rs if r['first_purchase'][s] is not None]) else None for s in ('us','them')};return out
    seen=set();unique=[]
    for row in rows:
        if row['replay_sha256'] not in seen:unique.append(row);seen.add(row['replay_sha256'])
    groups={'All':rows,'Ranked':[r for r in rows if r['kind']=='ranked'],'BattleCats':[r for r in rows if r['opponent']=='BattleCats'],
            'Unique trajectories':unique,'Unique BattleCats':[r for r in unique if r['opponent']=='BattleCats']}
    groups.update({'Opponent:'+n:[r for r in rows if r['opponent']==n] for n in sorted({r['opponent'] for r in rows})})
    summaries={name:{'all':aggregate(rs),'loss':aggregate([r for r in rs if r['result']=='loss']),'win':aggregate([r for r in rs if r['result']=='win'])} for name,rs in groups.items()}
    hero_groups=defaultdict(list);unique_ids={r['match_id'] for r in unique}
    for h in heroes:
        if h['match_id'] in unique_ids:hero_groups[h['side'],h['result'],h['name']].append(h)
    hero_summary=[{'side':key[0],'result':key[1],'name':key[2],'appearances':len(hs),'games':len({h['match_id'] for h in hs}),'mean':{f:mean([h[f] for h in hs]) for f in ('earned_gold','gold','collected','banked','deaths','equipment_cost','capture_gold','spent_gold','monster_damage','champion_damage')},'zero_collected':sum(h['collected']==0 for h in hs),'dead_at_r100':sum(not h['alive'] for h in hs)} for key,hs in sorted(hero_groups.items())]
    map_groups=defaultdict(list)
    for r in unique:map_groups[r['map']].append(r)
    map_summary=[{'map':name,'n':len(rs),'wins':sum(r['result']=='win' for r in rs),'sides':dict(Counter(r['our_side'] for r in rs)),'mean_margin':mean([r['final_margin'] for r in rs]),'equipment_gap_100':mean([r['equipment_gap_100'] for r in rs if r['equipment_gap_100'] is not None]),'fuel_us':sum(r['fuel']['us'] for r in rs)} for name,rs in sorted(map_groups.items())]
    duplicates=defaultdict(list)
    for row in rows:duplicates[row['replay_sha256']].append(row['match_id'])
    hero_pairs=defaultdict(list)
    for row in unique:
        hs=[h for h in heroes if h['match_id']==row['match_id']]
        for name in {h['name'] for h in hs}:
            sides={s:[h for h in hs if h['name']==name and h['side']==s] for s in ('us','them')}
            if all(sides.values()):
                hero_pairs[name,row['result']].append({f:mean([h[f] for h in sides['us']])-mean([h[f] for h in sides['them']]) for f in ('earned_gold','capture_gold','equipment_cost','collected','deaths')})
    paired_summary=[{'name':key[0],'result':key[1],'same_game_same_hero_pairs':len(v),'mean_own_minus_opponent':{f:mean([r[f] for r in v]) for f in v[0]}} for key,v in sorted(hero_pairs.items())]
    result={'evidence':'exploratory current-version associations; not causal version comparison','games':85,'unique_replay_trajectories':len(unique),'duplicate_sets':[{'replay_sha256':h,'match_ids':ids} for h,ids in duplicates.items() if len(ids)>1],'validation':run,'summaries':summaries,'hero_and_map_summary_basis':'deduplicated exact raw replay bytes; hero_r100_rows retain all game IDs for audit','hero_r100_summary':hero_summary,'paired_same_hero_r100':paired_summary,'hero_r100_rows':heroes,'map_summary':map_summary,'rows':rows}
    save_table(S/'ANALYSIS_DATA.json',result)
    print(json.dumps({'games':85,'distinct_trajectories':len(unique),'unique_wins':len([r for r in unique if r['result']=='win']),'raw_wins':len([r for r in rows if r['result']=='win'])}))
if __name__=='__main__':main()
