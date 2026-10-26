"""Validate completeness, identity, SHA256s, outcomes, and event/metric agreement."""
from collections import Counter
import hashlib
import zipfile
from collect import ROOT,OUT,ME,SINCE,UNTIL,read,save

def main():
    listing=read(OUT/'finished-top25.json')
    manifest=read(OUT/'manifest.json')
    assert not manifest['errors'],manifest['errors']
    ids={m['matchId'] for m in listing}
    assert len(ids)==len(listing)==len(manifest['matches'])
    assert ids=={r['matchId'] for r in manifest['matches']}
    metas={m['matchId']:m for m in listing}
    errors=[];engines=Counter();capture=Counter();faults=Counter();replays=0
    for e in manifest['matches']:
        p=ROOT/e['summary'];d=read(p);m=metas[e['matchId']]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
        if e.get('replay'):
            archive=ROOT/e['replay']
            with zipfile.ZipFile(archive) as z:
                assert z.testzip() is None,e['matchId']
                assert 'replay.repl26a' in z.namelist(),e['matchId']
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            if 'replaySha256' in e:assert digest==e['replaySha256'],e['matchId']
            e['replaySha256']=digest;replays+=1
        assert SINCE<=m['createdAt']<=UNTIL
        us=next(t for t in m['teams'] if t['teamId']==ME)
        side='team'+us['side'].upper()
        assert (d['match']['outcome']==side)==(us['result']=='win'),m['matchId']
        engines[d['match']['engineVersion']]+=1
        capture[d['diagnostics']['detailedCaptureComplete']]+=1
        for who in ['teamA','teamB']:
            faults['ours' if who==side else 'opponents']+=d['diagnostics']['botFaults'][who]
            for metric,kind in [('deaths','death'),('submittedGems','gemSubmission')]:
                native=sum(float(c['metrics'][metric]) for c in d['champions'] if c['team']==who)
                events=sum(float(x['value']) for ev in d['events'] if ev['kind']==kind and ev['owner'].get('team')==who for x in ev['entries'])
                if abs(native-events)>0.01:errors.append(dict(matchId=m['matchId'],team=who,metric=metric,native=native,events=events))
    assert not errors,errors[:10]
    if replays:assert replays==len(read(OUT/'losses.json'))
    save(OUT/'manifest.json',manifest)
    result=dict(status='passed',matches=len(listing),losses=len(read(OUT/'losses.json')),fullLossReplaysValidated=replays,summaryDownloadErrors=manifest['errors'],
                uniqueIds=True,sha256sVerified=True,outcomesVerified=True,eventMetricsVerified=True,engines=dict(engines),
                detailedCaptureComplete={str(k):v for k,v in capture.items()},botFaults=dict(faults))
    save(OUT/'validation.json',result)
    print(result)

if __name__=='__main__':main()
