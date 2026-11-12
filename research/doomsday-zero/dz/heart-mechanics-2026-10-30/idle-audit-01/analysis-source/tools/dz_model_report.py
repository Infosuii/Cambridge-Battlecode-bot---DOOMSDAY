"""Freeze a diagnostic model-calibration audit from completed DZ trace capsules.

Requires Node24 and the pinned engine2.0.0 replay assets. Standard-library Python.
No match execution, network, opponent source, or live state is used here.
"""
import argparse
import collections
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCES=('tools/dz_model_report.py','tools/dz_model_audit.mjs',
         'tools/replay/model_audit_core.mjs','tools/replay/engine.mjs')


def errors(pairs,unit='rounds'):
    if not pairs:
        return dict(n=0,median_absolute_relative_error=None,aggregate_signed_bias=None,
                    median_absolute_error=None,p90_absolute_error=None,unit=unit)
    absolute=sorted(abs(p-o) for p,o in pairs)
    relative=[abs(p-o)/o for p,o in pairs if o>0]
    return dict(n=len(pairs),median_absolute_relative_error=statistics.median(relative) if relative else None,
                aggregate_signed_bias=sum(p-o for p,o in pairs)/sum(o for _,o in pairs) if sum(o for _,o in pairs)>0 else None,
                median_absolute_error=statistics.median(absolute),unit=unit,
                p90_absolute_error=absolute[min(len(absolute)-1,int(.9*len(absolute)))])


def summarize(records):
    all_contacts=[r for r in records if r['quote']['contact'] and r['quote']['status']==0 and r['quote']['state'] in (0,1)]
    # A separate late single-live quote can overlap the baseline clear window.
    # It belongs to the shield cohort only, never another baseline timing case.
    contacts=[r for r in all_contacts if not r['quote'].get('shield_sample',0)]
    completed=[r for r in contacts if r['outcome']=='cleared']
    def solo_clear(r):
        return (r['outcome']=='cleared' and r['own_basic_attacks']>0 and r['other_damage_events']==0
                and r['unknown_damage_events']==0 and r['own_nonbasic_damage_events']==0
                and abs(r['memory_hp_difference'])<.03 and r['quote']['seen']==r['quote']['round'])
    solo=[r for r in completed if solo_clear(r)]
    damage=[r for r in solo if r['other_hp_loss']<.03 and r['quote']['loss']>0]
    unshared_damage=[r for r in damage if r.get('bystander_context_known') and
                     not r['potential_tank_bystanders'] and r['target_camp_other_hp_loss']<.03]
    timed_damage=[r for r in unshared_damage if r['quote'].get('clock_status')==0 and 'timed_loss' in r['quote']]
    shield=[r for r in all_contacts if solo_clear(r) and r['other_hp_loss']<.03 and r['quote']['loss']>0
            and r.get('bystander_context_known') and not r['potential_tank_bystanders'] and r['target_camp_other_hp_loss']<.03
            and r['champion_type']==10 and r['quote'].get('shield_status')==0 and r['quote'].get('shield_mode',0)==0
            and r['quote'].get('shield_live')==1 and r.get('native_initial_live_members')==1
            and r.get('shield_member_matches') and r['healing']<.03]
    mixed=[r for r in all_contacts if solo_clear(r) and r['other_hp_loss']<.03 and r['quote']['loss']>0
           and r.get('bystander_context_known') and not r['potential_tank_bystanders'] and r['target_camp_other_hp_loss']<.03
           and r['champion_type']==10 and r['quote'].get('shield_status')==0 and r['quote'].get('shield_mode')==1
           and r['quote'].get('shield_live',0)>1 and r.get('member_hp_hash_matches') and r.get('native_static_positions')
           and r.get('native_damaging_live_members')==1 and r.get('shield_target_matches') and r['quote'].get('enemies')==0
           and r.get('own_movement_events',1)==0 and r.get('camp_movement_events',1)==0 and r['healing']<.03]
    heart=[r for r in all_contacts if solo_clear(r) and r['other_hp_loss']<.03 and r['quote']['loss']>0
           and r.get('bystander_context_known') and not r['potential_tank_bystanders'] and r['target_camp_other_hp_loss']<.03
           and r['champion_type']==12 and r['quote'].get('shield_status')==0 and r['quote'].get('shield_mode')==2
           and r['quote'].get('missing_health_bonus')==.5 and r['quote'].get('shield_live')==1
           and r.get('native_initial_live_members')==1 and r.get('shield_member_matches') and r.get('member_hp_hash_matches')
           and r.get('native_damaging_live_members')==1 and r.get('shield_target_matches') and r.get('native_static_positions')
           and r.get('own_movement_events',1)==0 and r.get('camp_movement_events',1)==0 and r['healing']<.03]
    clocks=[r for r in solo if r['quote'].get('clock_status')==0 and 'clock' in r['quote']]
    # These kits have no HP-dependent basic strength or splash in the pinned
    # metadata. This restricted stratum is not a full-role model gate.
    constant_clocks=[r for r in clocks if r['champion_type'] in (1,2,7)]
    arrivals=[r for r in records if not r['quote']['contact'] and r['quote']['new'] and r['quote']['field']
              and 0<=r['quote']['dist']<65535 and r['arrival_round'] is not None]
    clear_pairs=lambda rs:[(r['quote']['attacks']+.25*r['quote']['members'],r['clear_round']-r['quote']['round']+1) for r in rs]
    return dict(quotes=len(records),outcomes=dict(collections.Counter(r['outcome'] for r in records)),
                contact_predictions=len(contacts),contact_clears=len(completed),
                assisted_contact_clears=sum(r['other_damage_events']>0 for r in completed),
                all_contact_clear=errors(clear_pairs(completed)),solo_basic_clear=errors(clear_pairs(solo)),
                solo_work_only_clear=errors([(r['quote']['attacks'],r['clear_round']-r['quote']['round']+1) for r in solo]),
                solo_clock_clear=errors([(r['quote']['clock'],r['clear_round']-r['quote']['round']+1) for r in clocks]),
                constant_kit_clock_clear=errors([(r['quote']['clock'],r['clear_round']-r['quote']['round']+1) for r in constant_clocks]),
                realized_reset_actions=sum(len(r.get('reset_actions',[])) for r in solo),
                solo_target_damage=errors([(r['quote']['loss'],r['target_camp_hp_loss']) for r in damage],unit='HP'),
                damage_context_known=sum(bool(r.get('bystander_context_known')) for r in damage),
                damage_potential_bystanders=sum(bool(r.get('potential_tank_bystanders')) for r in damage),
                damage_observed_other_tanking=sum(r.get('target_camp_other_hp_loss',0)>.03 for r in damage),
                solo_unshared_target_damage=errors([(r['quote']['loss'],r['target_camp_hp_loss']) for r in unshared_damage],unit='HP'),
                solo_unshared_timed_damage=errors([(r['quote']['timed_loss'],r['target_camp_hp_loss']) for r in timed_damage],unit='HP'),
                constant_kit_unshared_timed_damage=errors([(r['quote']['timed_loss'],r['target_camp_hp_loss']) for r in timed_damage if r['champion_type'] in (1,2,7)],unit='HP'),
                varg_single_live_shield_damage=errors([(r['quote']['shield_loss'],r['target_camp_hp_loss']) for r in shield],unit='HP'),
                varg_single_live_unshielded_damage=errors([(r['quote']['loss'],r['target_camp_hp_loss']) for r in shield],unit='HP'),
                varg_single_live_shield_time=errors([(r['quote']['shield_rounds'],r['clear_round']-r['quote']['round']+1) for r in shield]),
                varg_mixed_splash_shield_damage=errors([(r['quote']['shield_loss'],r['target_camp_hp_loss']) for r in mixed],unit='HP'),
                varg_mixed_splash_unshielded_damage=errors([(r['quote']['loss'],r['target_camp_hp_loss']) for r in mixed],unit='HP'),
                varg_mixed_splash_time=errors([(r['quote']['shield_rounds'],r['clear_round']-r['quote']['round']+1) for r in mixed]),
                varg_mixed_splash_naive_time=errors(clear_pairs(mixed)),
                mixed_shield_casts=dict(predicted=sum(r['quote']['shield_casts'] for r in mixed),observed=sum(len(r.get('shield_actions',[])) for r in mixed)),
                heart_single_live_shield_time=errors([(r['quote']['shield_rounds'],r['clear_round']-r['quote']['round']+1) for r in heart]),
                heart_single_live_shield_damage=errors([(r['quote']['shield_loss'],r['target_camp_hp_loss']) for r in heart],unit='HP'),
                heart_single_live_unshielded_damage=errors([(r['quote']['loss'],r['target_camp_hp_loss']) for r in heart],unit='HP'),
                heart_shield_casts=dict(predicted=sum(r['quote']['shield_casts'] for r in heart),observed=sum(len(r.get('shield_actions',[])) for r in heart)),
                late_shield_contact_predictions=sum(bool(r['quote'].get('shield_sample',0)) for r in all_contacts),
                shield_status_outcomes=dict(collections.Counter(f"{r['quote']['shield_status']}:{r['outcome']}"
                                           for r in all_contacts if 'shield_status' in r['quote'])),
                shield_casts=dict(predicted=sum(r['quote']['shield_casts'] for r in shield),
                                  observed=sum(len(r.get('shield_actions',[])) for r in shield)),
                # Quote is before this turn's move. D moves first permit
                # post-move contact on quote_round + D - 1, not + D.
                cached_field_arrival=errors([(max(0,r['quote']['dist']-r['quote']['range']-1),r['arrival_round']-r['quote']['round']) for r in arrivals]),
                coverage='Only logged bodies/rounds. Censored/dead/unmatched episodes stay in outcomes, never score as successful clears.',
                gate_status='V-M1 remains open: diagnostic sample, no full-role holdout or prospective validation; solo upper-bound gate is not a crew elapsed-time model.')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs',nargs='+',required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--node',default=shutil.which('node'));ap.add_argument('--rounds',type=int,default=500)
    a=ap.parse_args()
    if not a.node or a.rounds<1:ap.error('Node24 and positive rounds are required')
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    frozen=output/'analysis-source'
    for name in SOURCES:
        target=frozen/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    work=ROOT/'artifacts/tmp/model-audit'/output.name;work.mkdir(parents=True,exist_ok=True)
    records=[];inputs=[]
    env=dict(os.environ);env['NFS_REPLAY_ENGINE']='2.0.0'
    for name in a.runs:
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):raise ValueError('invalid run name')
        folder=ROOT/'research/dz/runs'/name
        result=json.loads((folder/'results.json').read_text());prov=json.loads((folder/'provenance.json').read_text())
        if not prov['trace']:raise ValueError('calibration needs a diagnostic trace build')
        inputs.append(dict(run=name,candidate_sha256=prov['candidate_sha256'],
                           capsule_sha256=hashlib.sha256((folder/'evidence.zip').read_bytes()).hexdigest()))
        with zipfile.ZipFile(folder/'evidence.zip') as z:
            if z.testzip() is not None:raise ValueError('corrupt capsule')
            for game in result['per_game']:
                if any(game.get(k,1) for k in ('faults','fuel_outs','caught_action_errors','caught_module_errors')):raise ValueError('unclean diagnostic trace')
                cell=f"{game['map']}-{game['side']}";prefix='games/'+cell+'/'
                stdout=z.read(prefix+'candidate.stdout')
                if b'DZ_MODEL ' not in stdout:raise ValueError('missing prediction observations')
                bundles=[n for n in z.namelist() if n.startswith(prefix) and n.endswith('.repl26a') and Path(n).name not in ('lifecycle.repl26a','priority.repl26a')]
                if len(bundles)!=1:raise ValueError('ambiguous native replay')
                raw=z.read(bundles[0])
                if hashlib.sha256(raw).hexdigest()!=game['replay_sha256']:raise ValueError('native replay digest mismatch')
                with zipfile.ZipFile(io.BytesIO(raw)) as native:replay=native.read('replay.repl26a')
                p=work/(name+'-'+cell);p.mkdir(exist_ok=True)
                (p/'replay.bin').write_bytes(replay);(p/'candidate.stdout').write_bytes(stdout)
                target=output/(name+'-'+cell+'.json')
                command=[a.node,'--no-warnings',str(frozen/'tools/dz_model_audit.mjs'),str(p/'replay.bin'),str(p/'candidate.stdout'),str(target),str(a.rounds)]
                run=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
                if run.returncode:
                    (output/'FAILURE.json').write_text(json.dumps(dict(run=name,cell=cell,stderr=run.stderr),indent=2)+'\n',newline='\n')
                    raise RuntimeError(run.stderr)
                audit=json.loads(target.read_text())
                for r in audit['records']:r.update(run=name,map=game['map'],side=game['side'])
                records.extend(audit['records']);print(cell,run.stdout.strip(),flush=True)
    report=summarize(records);report.update(inputs=inputs,source={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},
        strata={str(key):summarize([r for r in records if r['quote']['cluster']==key]) for key in (0,1)},
        champion_strata={str(key):summarize([r for r in records if r.get('champion_type')==key])
                         for key in sorted({r['champion_type'] for r in records if 'champion_type' in r})})
    (output/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source','inputs','strata')},indent=2))


if __name__=='__main__':main()
