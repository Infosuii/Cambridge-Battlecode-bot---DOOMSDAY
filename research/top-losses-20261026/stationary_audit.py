"""Inspect the actual own-turn state inside every long stationary interval, with explicit limits."""
import concurrent.futures as cf
import os
import subprocess
from collect import ROOT,OUT,RAW,read,save
from analyze import at

def main():
    metas={r['matchId']:r for r in read(OUT/'metrics.json')}
    cases=[]
    for f in read(OUT/'all-loss-fights.json'):
        r=metas[f['id']];k=0 if r['side']=='a' else 1
        for x in f['stagnations']:
            if x['team']==k:cases.append(dict(matchId=f['id'],map=r['map'],arm=r['arm'],engine=r['engine'],opponent=r['opponent'],**x))
    def run(pair):
        i,c=pair;r=metas[c['matchId']];folder=RAW/c['matchId'];dest=folder/f'stationary-{i}.json'
        sample=(c['startRound']+c['endRound'])//2
        args=['node','--no-warnings',str(OUT/'inspect_stall.mjs'),str(dest),str(folder/'inner/replay.repl26a'),str(sample),str(c['champion'])]
        p=subprocess.run(args,env=dict(os.environ,NFS_REPLAY_ENGINE=c['engine']),capture_output=True,text=True,encoding='utf8',errors='replace',timeout=60)
        if p.returncode:raise RuntimeError(c['matchId']+': '+p.stderr[-500:])
        d=read(dest);s=d['self']
        assert c['startRound']<=d['round']<=c['endRound']
        summary=read(ROOT/r['source']['summary'])
        changes={}
        for metric in ['earnedGold','collectedGems','submittedGems']:
            timeline=next(t for t in summary['championTimelines'] if t['owner'].get('id')==c['champion'] and t['metric']==metric)
            changes[metric]=at(timeline,c['endRound'])-at(timeline,c['startRound'])
        result=dict(**c,sampleRound=d['round'],canMove=d['canMove'],canAttack=d['canAttack'],legalNeighbors=d['legalNeighbors'],
            health=s['health'],maxHealth=s['maxHealth'],channelTimer=s['channelTimer'],channelType=s['channelType'],buffs=s['buffs'],
            gemsAtSample=s['gems'],worldLiveCamps=d['worldLiveCamps'],nearbyVisibleCamps=len(d['nearbyCamps']),
            nearbyEnemies=sum(x['team']!=d['team'] and x['alive'] for x in d['nearbyChampions']),resourceChange=changes)
        return result
    result=[]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(run,enumerate(cases)):result.append(r)
    save(OUT/'stationary-cases.json',result)
    print('intervals',len(result),'current engine',sum(c['engine']=='2.0.0' for c in result),
          'can move with legal neighbors and no channel',sum(bool(c['canMove'] and c['legalNeighbors'] and c['channelTimer']==0) for c in result),
          'zero economic change',sum(not any(c['resourceChange'].values()) for c in result))

if __name__=='__main__':main()
