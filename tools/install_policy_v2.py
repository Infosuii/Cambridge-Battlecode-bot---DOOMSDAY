"""Install an explicitly untrained direct-policy experiment into a disposable source copy. No build or training."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from nfs.policy.model import build_model,init_untrained,HEAD_IDS
from nfs.policy.export import export_model,load_blob,load_model

PROFILES=('direct_untrained','direct_uniform','direct_record','direct_sample_record')

def install(destination:Path,profile:str,model_dir:Path|None=None,seed:int=20261024,record_head:str='all'):
    destination=destination.resolve()
    scratch=(ROOT/'artifacts/tmp').resolve()
    if not destination.is_relative_to(scratch) or destination==scratch:
        raise ValueError('direct experiments must use a dedicated artifacts/tmp directory')
    if destination.exists():raise FileExistsError(f'fresh destination required: {destination}')
    if profile not in PROFILES:raise ValueError('unknown experimental profile')
    if record_head not in ('all',*HEAD_IDS):raise ValueError('unknown record head')
    log_mask=510 if record_head=='all' else 1<<HEAD_IDS[record_head]
    src=destination/'src';src.mkdir(parents=True)
    for path in (ROOT/'bot/src').iterdir():
        if path.is_file():shutil.copy2(path,src/path.name)
    # Keep inherited draft as-is; no v1 residual heads may run together with this interpretation.
    from install_models import install as legacy_install
    legacy_install('teacher_exact',src,quiet=True)
    zero=profile=='direct_uniform'
    if model_dir is not None and zero:raise ValueError('uniform control cannot override its zero-logit model')
    if not 0<=seed<2**63:raise ValueError('seed must be a nonnegative signed64 integer')
    status='untrained'
    provenance=dict(synthetic=True,source='seeded synthetic initialization',seed=20261024,
                    zero_logits=zero,training_games=0,parameter_updates=0)
    if model_dir is None:model=init_untrained(build_model('policy_v2'),20261024,zero_logits=zero)
    else:
        expected=build_model('policy_v2').cfg
        old,_=load_blob(model_dir,expected_obs=expected['obs']['obs_schema_hash'],expected_action=expected['action_schema_hash'])
        model=load_model(model_dir)
        if model.cfg!=expected:raise ValueError('changed architecture requires fresh engine budget calibration')
        status=old['status'];provenance=old['provenance']
    from gen_policy_budget import render as render_budget
    (src/'nn_policy_budget.h').write_text(render_budget(model.cfg),encoding='utf-8',newline='\n')
    exported=destination/'model'
    manifest=export_model(model,'policy_v2_untrained',exported,status,provenance)
    load_blob(exported)
    weights='nn_policy_weights_policy_v2_untrained.h'
    shutil.copy2(exported/weights,src/weights)
    (src/'nn_policy_installed.h').write_text(
        '#pragma once\n#include "'+weights+'"\nnamespace nnp {\n'
        'inline constexpr const nnpm::PolicyDesc& kInstalled=nnpw_policy_v2_untrained::kDesc;\n}\n',encoding='utf-8')
    (src/'nn_policy_config.h').write_text(
        f'// Development experiment, model status: {status}. Never a release selection.\n#pragma once\n'
        '#define NN_POLICY_V2 1\n'
        '#define NN_POLICY_TELEMETRY 1\n'
        f'#define NN_POLICY_SEED {seed}ull\n'
        f'#define NN_POLICY_LOG_HEAD_MASK {log_mask}\n'
        f'#define NN_POLICY_LOG {int("record" in profile)}\n'
        f'#define NN_POLICY_SAMPLE {int(profile=="direct_sample_record")}\n',encoding='utf-8')
    (destination/'policy_install.json').write_text(json.dumps(dict(profile=profile,status=status,seed=seed,record_head=record_head,
        interpretation_version=2,model_checksum=manifest['checksum'],obs_schema_hash=manifest['obs_schema_hash'],
        action_schema_hash=manifest['action_schema_hash'],training_games=0,parameter_updates=0,
        budget_status='engine-calibrated component ceilings on reused maps; conservative refusals remain'),indent=2)+'\n',encoding='utf-8')
    return destination

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest',required=True,type=Path)
    ap.add_argument('--profile',choices=PROFILES,default='direct_untrained')
    ap.add_argument('--model-dir',type=Path)
    ap.add_argument('--seed',type=int,default=20261024)
    ap.add_argument('--record-head',choices=('all',*HEAD_IDS),default='all')
    args=ap.parse_args()
    print(install(ROOT/args.dest,args.profile,args.model_dir,args.seed,args.record_head))
