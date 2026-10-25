"""Analysis-only paired metrics for the v54 strategic review; does not build bots."""
from collections import defaultdict
import json
from pathlib import Path
import statistics as st

ROOT=Path(__file__).resolve().parents[2]

def main():
    data=ROOT/'data/ladder'
    v52=json.loads((data/'v52_since_live_20261025.json').read_text())
    control=json.loads((data/'v54_control_wins_20261025.json').read_text())
    v53=[]
    for name in ['hidden','meow']:
        v53+=json.loads((data/f'v53_group_{name}_status_20261025.json').read_text(encoding='utf-8-sig'))['matches']
    latest=json.loads((data/'v53_since_live_analysis_20261025.json').read_text())
    latest=[m for m in latest if m['status']=='finished']
    ranked=[m for m in latest if m['kind']=='ranked']
    targeted_ids={m['matchId'] for m in v53}
    others=[m for m in latest if m['kind']=='unranked' and m['matchId'] not in targeted_ids]
    meta={m['matchId']:m for m in v52+latest}
    audits=json.loads((ROOT/'artifacts/local-only/v53-review/audit-v54-complete.json').read_text())
    audit={a['id']:a for a in audits}
    def gear(s):return sum(n*(5 if i%2 else 1)*30 for c in s['champions'] for i,n in c['items'])
    def snap(t,r):return next((x for x in t['snapshots'] if x['round']==r),None)
    def stats(m):
        a=audit[m['matchId']];me=next(t for t in m['teams'] if t['name']=='DOOMSDAY');i='ab'.index(me['side']);j=1-i
        u,v=a['teams'][i],a['teams'][j]
        d={'id':m['matchId'],'map':m['map'],'kind':m['kind'],'opponent':next(t['name'] for t in m['teams'] if t['name']!='DOOMSDAY'),
           'win':me['result']=='win','rounds':a['rounds'],'score':[a['submitted_gems'][i],a['submitted_gems'][j]],
           'draft':[me['draftPicks'],next(t['draftPicks'] for t in m['teams'] if t['name']!='DOOMSDAY')],
           'deaths':[u['deaths'],v['deaths']], 'dead_rounds':[u['dead_champion_rounds'],v['dead_champion_rounds']],
           'early_attacks_champion':[u['early_champion_attacks'],v['early_champion_attacks']],
           'early_attacks_camp':[u['early_camp_attacks'],v['early_camp_attacks']],
           'first_bank':[t['banks'][0]['round'] if t['banks'] else None for t in [u,v]],
           'bank_count':[len(u['banks']),len(v['banks'])],
           'median_bank':[st.median(x['amount'] for x in t['banks']) if t['banks'] else None for t in [u,v]],
           'unspent_gold_per_alive_round':[round(t['unspent_gold_rounds']/max(1,t['alive_champion_rounds']),1) for t in [u,v]],
           'gear':{},'top_hero_gear_share':{},'early_deaths':{}}
        for r in [100,250,500,1000]:
            if not all(snap(t,r) for t in [u,v]):continue
            ss=[snap(t,r) for t in [u,v]]
            d['gear'][r]=[gear(s) for s in ss];d['early_deaths'][r]=[s['deaths'] for s in ss]
            d['top_hero_gear_share'][r]=[round(max((sum(n*(5 if i%2 else 1)*30 for i,n in c['items']) for c in s['champions']),default=0)/max(1,gear(s)),3) for s in ss]
        return d
    groups={'v52_losses':[m for m in v52 if m['matchId'] in audit and any(t['name']=='DOOMSDAY' and t['result']=='loss' for t in m['teams'])],
            'v52_winning_controls':control,'v53_targeted':[m for m in v53 if m['matchId'] in audit],
            'v53_ranked':[m for m in ranked if m['matchId'] in audit],
            'v53_other_unranked':[m for m in others if m['matchId'] in audit],
            'v53_all_losses':[m for m in latest if m['matchId'] in audit and any(t['name']=='DOOMSDAY' and t['result']=='loss' for t in m['teams'])],
            'v53_all_wins':[m for m in latest if m['matchId'] in audit and any(t['name']=='DOOMSDAY' and t['result']=='win' for t in m['teams'])]}
    rows={k:[stats(m) for m in ms] for k,ms in groups.items()}
    def medpair(rs,key):
        return [round(st.median([r[key][i] for r in rs if r[key][i] is not None]),1) for i in [0,1]]
    out={}
    for key,rs in rows.items():
        if not rs:continue
        s={'games':len(rs),'wins':sum(r['win'] for r in rs)}
        for col in ['deaths','dead_rounds','first_bank','median_bank','bank_count','early_attacks_camp','early_attacks_champion','unspent_gold_per_alive_round']:
            s[col+'_median']=medpair(rs,col)
        for r in [100,250,500]:
            rr=[x for x in rs if r in x['gear']]
            s[f'gear_R{r}_median']=[round(st.median(x['gear'][r][i] for x in rr),1) for i in [0,1]]
            ratios=[x['gear'][r][0]/x['gear'][r][1] for x in rr if x['gear'][r][1]>0]
            s[f'gear_R{r}_ratio_median']=round(st.median(ratios),3) if ratios else None
            s[f'gear_R{r}_ratio_games']=len(ratios)
            s[f'gear_R{r}_zero_opponent_games']=len(rr)-len(ratios)
            s[f'deaths_R{r}_median']=[round(st.median(x['early_deaths'][r][i] for x in rr),1) for i in [0,1]]
            s[f'top_hero_share_R{r}_median']=[round(st.median(x['top_hero_gear_share'][r][i] for x in rr),3) for i in [0,1]]
        out[key]=s
    result={'method':'paired game measurements, no causal attribution; winning controls are selected, not a random sample; round-sampled deaths; original shard-cost equipment value; ratios omit zero opponent equipment and report their denominator counts',
            'summary':out,'games':rows}
    (ROOT/'artifacts/claude_ops/V54_EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
