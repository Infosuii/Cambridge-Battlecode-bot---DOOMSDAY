"""Economic diagnostics from official summaries; gold earned is kept separate from gold held."""
import argparse,collections,json
from pathlib import Path
EVAL=Path(r'C:\projects\cambridge battlecode\battlecode part 2\jd-eval')

def game_metrics(d,team):
    champs=[c for c in d['champions'] if c['team']==team]
    fields=['earnedGold','gold','spentGold','collectedGems','submittedGems','gems','deaths','kills']
    result={k:sum(float(c['metrics'].get(k,0)) for c in champs) for k in fields}
    events=[e for e in d['events'] if e['owner'].get('team')==team]
    result['gems_lost']=sum(float(x['value']) for e in events if e['kind']=='gemLoss' for x in e['entries'])
    result['gems_stolen']=sum(float(x['value']) for e in events if e['kind']=='gemCollection' for x in e['entries'] if x['context']=='champion' and x.get('target',{}).get('team')!=team)
    clears=[x['timestamp']['round'] for e in events if e['kind']=='campClear' for x in e['entries']]
    result['camp_clears']=len(clears)
    result['late_clears_after_600']=sum(x>=600 for x in clears)
    result['rounds']=d['match']['roundsStarted']
    # Time-to-win is censored for non-finishes; never replace missing wins with zero rounds.
    deposits=sorted((x['timestamp']['round'],int(x['value'])) for e in events if e['kind']=='gemSubmission' for x in e['entries'])
    total=0;finish=None
    for rnd,value in deposits:
        total+=value
        if total>=1000:finish=rnd;break
    result['finish_round']=finish
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('runs',nargs='+');a=p.parse_args();by=collections.defaultdict(list)
    for run in a.runs:
        out=EVAL/'runs'/run;meta=json.loads((out/'run.json').read_text())
        for cell in meta['cells_list']:
            for arm in ['cand','base']:
                stem='__'.join([arm,cell['opp'],cell['map'],cell['side']]);path=out/'games'/(stem+'.json')
                if not path.exists():raise SystemExit('Missing summary '+str(path))
                m=game_metrics(json.loads(path.read_text()),'team'+cell['side']);by[arm].append(m)
    result={}
    for arm,rows in by.items():
        result[arm]=dict(games=len(rows),means={k:round(sum(r[k] for r in rows)/len(rows),3) for k in rows[0] if k!='finish_round'},finishes=sum(r['finish_round'] is not None for r in rows),mean_finish_round=round(sum(r['finish_round'] for r in rows if r['finish_round'] is not None)/max(1,sum(r['finish_round'] is not None for r in rows)),2))
    result['definitions']={'collectedGems':'May include transfers; gems_stolen uses champion-target collection events only','finish_round':'Censored when below1000; mean over finishers is descriptive, not causal','gold':'Held at match end; earnedGold is cumulative official earned metric'}
    dest=Path('research/jd-g5070-resume-0715')/('ECONOMY_'+a.runs[0]+'.json');dest.write_text(json.dumps(result,indent=2));print(dest);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
