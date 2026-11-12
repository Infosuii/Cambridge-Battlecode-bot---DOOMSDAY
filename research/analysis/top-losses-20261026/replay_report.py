"""Report all replay findings with native-summary crosschecks and measurement limitations."""
from collections import Counter
import statistics as st
from collect import OUT,read,save

def avg(xs):
    xs=list(xs);return round(st.fmean(xs),3) if xs else None
def ratio(n,d):return round(n/max(1,d),4)

def aggregate(pairs):
    out={'games':len(pairs)}
    for label in ['us','them']:
        ix=lambda r:(0 if r['side']=='a' else 1) if label=='us' else (1 if r['side']=='a' else 0)
        ts=[f['teams'][ix(r)] for f,r in pairs]
        ds=[d for f,r in pairs for d in f['deaths'] if d['team']==ix(r)]
        ss=[f['spellAudit'][ix(r)] for f,r in pairs]
        out[label]={k:avg(t[k]/max(1,t['contact']) for t in ts) for k in ['outnumbered','alone','contactHpLost']}
        out[label].update(deathSamples=len(ds),isolatedDeathShare=ratio(sum(d['allies8']==0 for d in ds),len(ds)),
            outnumberedDeathShare=ratio(sum(d['enemies8']>d['allies8']+1 for d in ds),len(ds)),
            respawnRepeatShare=ratio(sum(d.get('sinceRespawn') is not None and d['sinceRespawn']<=60 for d in ds),len(ds)),
            nearHomeDeathShare=ratio(sum(d['spawnDist']<=15 for d in ds),len(ds)),
            deadTimeFraction=avg(t['deadRounds']/max(1,t['deadRounds']+t['aliveRounds']) for t in ts),
            contactEntries=sum(s['offensiveEntries'] for s in ss),
            noOffensiveReadyShare=ratio(sum(s['entryNoOffensiveReady'] for s in ss),sum(s['offensiveEntries'] for s in ss)),
            campCooldownEntryShare=ratio(sum(s['entryWithCampCooldown'] for s in ss),sum(s['offensiveEntries'] for s in ss)),
            longStationaryIntervals=sum(len([x for x in f['stagnations'] if x['team']==ix(r)]) for f,r in pairs))
    return out

def main():
    metas={r['matchId']:r for r in read(OUT/'metrics.json')}
    fs=read(OUT/'all-loss-fights.json')
    assert len(fs)==len(read(OUT/'losses.json'))==len({f['id'] for f in fs})
    pairs=[(f,metas[f['id']]) for f in fs]
    cohorts={'current-engine':[(f,r) for f,r in pairs if r['engine']=='2.0.0'],
             'historical-engine':[(f,r) for f,r in pairs if r['engine']!='2.0.0']}
    for a in ['v60','v61','v62c']:cohorts[a]=[(f,r) for f,r in pairs if r['arm']==a]
    data={k:aggregate(v) for k,v in cohorts.items()}
    mismatches=[];identityErrors=[]
    for f,r in pairs:
        expected=[r['us']['final']['submittedGems'],r['them']['final']['submittedGems']] if r['side']=='a' else [r['them']['final']['submittedGems'],r['us']['final']['submittedGems']]
        if f['finalState']['submittedGems']!=expected:identityErrors.append(dict(matchId=r['matchId'],expected=expected,replay=f['finalState']['submittedGems']))
        if f['finalState']['outcome']!=(2 if r['side']=='a' else 1):identityErrors.append(dict(matchId=r['matchId'],problem='outcome disagrees'))
        names=['Ryth','Vesper Vale','Vendetta','Cassi','Issac','Stellar','Prism','Marcella','Willow','Ren','Varg','Tavi','Heart of Ruin']
        for label,k in [('us',0 if r['side']=='a' else 1),('them',1 if r['side']=='a' else 0)]:
            expectedNames=sorted(c['name'] for c in r[label]['heroes'])
            replayNames=sorted(names[c['type']] for c in f['finalState']['champions'] if c['team']==k)
            if expectedNames!=replayNames:identityErrors.append(dict(matchId=r['matchId'],problem='roster disagrees',side=label))
            native=r[label]['final']['deaths'];sample=sum(d['team']==k for d in f['deaths'])
            if native!=sample:mismatches.append(dict(matchId=r['matchId'],team=label,native=native,roundBoundarySamples=sample))
    save(OUT/'replay-aggregates.json',data)
    save(OUT/'replay-crosscheck.json',dict(matches=len(fs),engineMatched=True,finalBankOutcomeRosterMatched=not identityErrors,identityMismatches=identityErrors,deathSampleMismatches=mismatches))
    assert not identityErrors,identityErrors[:5]
    lines=['# Full replay review','','Every recorded loss is decoded with its matching engine and a complete hash-pinned visualiser bundle. Current and historical engines remain separate.','',
       'Counts of contact, time and death position use round boundaries. Cooldowns use actual champion turns and that champion’s own visible enemies within six tiles. Contact-entry shares are weighted by number of entries; positioning ratios are means of per-game shares.','']
    for name,d in data.items():
        lines += [f"## {name}: {d['games']} losses",'', '| Observation | DOOMSDAY | Opponent |','|---|---:|---:|']
        for k in d['us']:lines.append(f"| {k} | {d['us'][k]} | {d['them'][k]} |")
        lines.append('')
    lines += ['## Death sampling crosscheck','',f"{len(mismatches)} team/match counts differ from native summary deaths. The native summary remains the authority for exact death totals; replay context is limited to captured death transitions.",'',
      '## Interpretation limits','',
      '- An enemy’s omniscient position at a death does not prove our bot could see that enemy before committing. It identifies a dangerous encounter, not a proven observation bug.',
      '- An offensive ability on cooldown after a camp cast is a measured sequencing event. It is not proof that holding the ability would have won the fight.',
      '- Ready abilities are not automatically legal or useful casts. Channeling, control effects, target rules, range and tactical objectives also matter.',
      '- contactHpLost measures net HP drops during contact, including camp damage and effects of healing. It is not an exact measurement of incoming player damage.',
      '- Hostile-cast classification uses own-perspective target positions and ability radius. It omits attack-reset, healing, shields and non-damaging dashes from hostile counts. Kills during the cast can remove a target from the post-action state and undercount it.',
      '- Long stationary intervals can include deliberate camping, capture or resource denial. They are review flags, not automatic pathfinding defects.',
      '- The 502-loss corpus is exhaustive for the fixed match window and top-25 definition; it does not prove all possible controller bugs have been discovered.']
    (OUT/'REPLAY_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(data)
    print('death-count discrepancies',len(mismatches))

if __name__=='__main__':main()
