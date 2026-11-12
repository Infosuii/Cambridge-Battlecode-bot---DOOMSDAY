"""EXP280: fixed model equivalence and all frozen task errors, no model fitting."""
import random
from statistics import mean, median
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from varg_capability import wave,reference


if __name__=='__main__':
    geometry=read(HERE/'CAMP_GEOMETRY_RAW.json');checked=0
    def check(camps):
        global checked
        a=wave(camps);b,history=reference(camps)
        assert a['sequence']==b
        count=0
        for w in a['waves']:
            count+=w['attacks'];assert w['hp_after']==history[count-1]
        checked+=1
    for r in geometry['rows']:
        for g in r['groups']:
            check([{'id':c['handle'],'position':[c['x'],c['y']],'hp':c['hp'],'strength':c['strength']} for c in g['camps']])
    public=checked;rng=random.Random(280)
    for k in range(600):
        n=1+k%12;points=rng.sample([(x,y) for x in range(8) for y in range(8)],n)
        camps=[{'id':i,'position':list(p),'hp':rng.choice([0,1,49,50,51,120,200,2400]),'strength':rng.choice([0,0,3,20])} for i,p in enumerate(points)]
        check(camps)
    for bad in ([],[{'id':0,'position':[0,0],'hp':.5,'strength':0}]):
        try:wave(bad)
        except ValueError:pass
        else:raise AssertionError('invalid accepted')
    raw=read(HERE/'VARG_CLEAR_OBSERVATIONS.json');audit=read(HERE/'VARG_CLEAR_RECOUNT.json')
    assert audit['pass'] and audit['raw_sha256']==bench.digest(HERE/'VARG_CLEAR_OBSERVATIONS.json')
    rows=[]
    for r,a in zip(raw['rows'],audit['rows'],strict=True):
        assert all(r[k]==a[k] for k in ('map','side','mode'))
        o=r['observation'];design=o['design'];f=o['frames']
        pred=wave(design) if design else None
        eligible=o['reason']==1 and not a['missing_camp_snapshots'] and a['outside_group_damage']==0
        old=sum(c['hp'] for c in design)/(50*(1.6 if len(design)>1 else 1)) if design else None
        assert all(x['strength']==50 for x in f)
        rows.append({'map':r['map'],'side':r['side'],'mode':r['mode'],'reason':o['reason'],'eligible':eligible,
                     'members':len(design),'actual_attacks':len(f),'old_basic_forecast':old,'ideal_wave_attacks':pred['attacks'] if pred else None,
                     'old_absolute_error':abs(old-len(f)) if eligible else None,
                     'wave_absolute_error':abs(pred['attacks']-len(f)) if eligible else None,
                     'attack_phase_rounds':o['last_round']-o['first_round']+1 if f else None,
                     'ideal_sequence_matches':pred['sequence']==[x['primary'] for x in f] if eligible else None,
                     'outside_group_damage':a['outside_group_damage'],'clipped_hits':a['clipped_hits']})
    summary={}
    for mode in ('multi','isolated'):
        eligible=[r for r in rows if r['mode']==mode and r['eligible']]
        summary[mode]={'eligible':len(eligible),'old_mae':mean(r['old_absolute_error'] for r in eligible),
                       'wave_mae':mean(r['wave_absolute_error'] for r in eligible),
                       'wave_exact_count':sum(r['wave_absolute_error']==0 for r in eligible),
                       'wave_exact_sequence':sum(r['ideal_sequence_matches'] for r in eligible),
                       'median_actual_attack_phase':median(r['attack_phase_rounds'] for r in eligible),
                       'median_attacks':median(r['actual_attacks'] for r in eligible)}
    result={'integer_model_proof':True,'public_groups':public,'synthetic_cases':checked-public,
            'geometry_sha256':bench.digest(HERE/'CAMP_GEOMETRY_RAW.json'),'raw_sha256':bench.digest(HERE/'VARG_CLEAR_OBSERVATIONS.json'),
            'recount_sha256':bench.digest(HERE/'VARG_CLEAR_RECOUNT.json'),'model_sha256':bench.digest(HERE/'varg_capability.py'),
            'summary':summary,'rows':rows,'limits':'Initial integer HP/50strength, ideal unrestricted primary/range, no spell/production float/complete survival or win validation. No fitted coefficient.'}
    write(HERE/'VARG_CLEAR_MODEL_ANALYSIS.json',result);print({k:v for k,v in result.items() if k not in ('rows','limits')},flush=True)
