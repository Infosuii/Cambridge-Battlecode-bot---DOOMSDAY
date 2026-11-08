"""Read-only paired interaction and common-horizon native failure review."""
from pathlib import Path
import json
import hashlib
import sys
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
sys.path.insert(0,str(BASE/'autonomy'))
from local_review import metrics
WD=BASE/'training/runs/bounded-delivery-retune-v1'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    training=read(WD/'o-training.json');result=read(WD/'o-result.json')
    ctrl='auto_rt7_o_c000';a='auto_rt7_o_k10p';b='auto_rt7_o_k09n';ab='auto_rt7_o_j001';stage='auto_rt7_o_k14n'
    paths={label:BASE/'autonomy/data/benchmarks'/('bounded-delivery-retune-20261107-o-'+label)/'results.json' for label in ('train','fresh','repairs')}
    rows={label:read(path) for label,path in paths.items()}
    def score(panel,name):
        own=[r['score'] for r in rows[panel] if r['candidate']==name and r['opponent']=='v111'];assert len(own)==96
        return sum(own)/len(own)
    interaction={}
    for key in ('reference_gain','direct_rate'):
        v=training['scores'];interaction[key]=v[ab][key]-v[a][key]-v[b][key]+training['parent'][key]
    cells={(r['candidate'],r['map'],r['opponent'],r['side']):r for r in rows['fresh']}
    reports=[]
    for map_name,opponent,side in [('00collision','ref_p65pack','a'),('03homonoliths','ref_x1','b')]:
        names=[ctrl,a,b,ab,stage];loaded={n:read(cells[(n,map_name,opponent,side)]['file']) for n in names}
        horizon=min(600,*[d['match']['roundsCompleted'] for d in loaded.values()]);team='team'+side.upper()
        reports.append({'map':map_name,'opponent':opponent,'side':side,'common_horizon':horizon,
                        'candidates':{n:{'score':cells[(n,map_name,opponent,side)]['score'],
                                         'rounds_completed':d['match']['roundsCompleted'],
                                         'common_horizon':metrics(d,team,horizon),
                                         'native_sha256':digest(cells[(n,map_name,opponent,side)]['file'])} for n,d in loaded.items()}})
    output={'scope':'Descriptive, post-selection analysis of a fixed completed TRAIN/FRESH panel. Does not change candidates or final protocol. Selected cases are not an estimate of failure frequency; matched strategy interventions produce different trajectories.',
            'effective_parameters':{'9':'Wait weight multiplied by exp(0.4*k9)','10':'Required helper pool multiplied by exp(0.3*k10)','14':'Staging timeout max(1,base+lround(3*k14)); -0.5 changes integer-rounded waiting, subject to profiles/clamp'},
            'train_metrics':{n:training['scores'][n] for n in [a,b,ab,'auto_rt7_o_j002',stage]},
            'train_control':training['parent'],'fresh_metrics':{n:result['fresh_scores'][n] for n in [a,b,ab,'auto_rt7_o_j002',stage]},
            'fresh_control_direct_rate':score('fresh',ctrl),'train_paired_A_B_interaction':interaction,
            'fresh_domain_deltas_vs_control':{n:result['domain_reference_deltas'][n] for n in [a,b,ab,'auto_rt7_o_j002',stage]},
            'common_horizon_failures':reports,
            'conclusions':['Full joint repair lost the individual TRAIN benefits: negative reference and direct-score interaction. A source-correct combination can still be strategically harmful.',
                           'Damped joint repair had positive FRESH reference gain but weak direct score. Reference-only optimization would conceal this weakness.',
                           'Shorter staging wait was the only direction satisfying the registered cross-panel qualification and domain constraints. Its FRESH direct score remains below50%; final validation is still required.',
                           'Selected regressions include death/collection changes and unbanked gems. Full-game count differences can reflect different match lengths; common-horizon views are supplied before proposing a causal mechanism.'],
            'input_sha256':{str(p.relative_to(BASE)):digest(p) for p in paths.values()}}
    target=Path(__file__).resolve().parent/'research/agentic-improvement-20261107/findings/original-arm-interaction-review.json'
    target.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps({'interaction':interaction,'fresh_control_direct':output['fresh_control_direct_rate'],'common_horizons':[r['common_horizon'] for r in reports],'report':str(target)}))

if __name__=='__main__':main()
