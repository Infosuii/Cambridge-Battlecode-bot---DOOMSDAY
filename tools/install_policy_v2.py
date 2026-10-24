"""Install an explicitly untrained direct-policy experiment into a disposable source copy. No build or training."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from nfs.policy.model import build_model,init_untrained
from nfs.policy.export import export_model,load_blob

PROFILES=('direct_untrained','direct_uniform','direct_record','direct_sample_record')

def install(destination:Path,profile:str):
    destination=destination.resolve()
    scratch=(ROOT/'artifacts/tmp').resolve()
    if not destination.is_relative_to(scratch) or destination==scratch:
        raise ValueError('direct experiments must use a dedicated artifacts/tmp directory')
    if destination.exists():raise FileExistsError(f'fresh destination required: {destination}')
    if profile not in PROFILES:raise ValueError('unknown experimental profile')
    src=destination/'src';src.mkdir(parents=True)
    for path in (ROOT/'bot/src').iterdir():
        if path.is_file():shutil.copy2(path,src/path.name)
    # Keep inherited draft as-is; no v1 residual heads may run together with this interpretation.
    from install_models import install as legacy_install
    legacy_install('teacher_exact',src,quiet=True)
    zero=profile=='direct_uniform'
    model=init_untrained(build_model('policy_v2'),20261024,zero_logits=zero)
    exported=destination/'model'
    manifest=export_model(model,'policy_v2_untrained',exported,'untrained',
                         dict(synthetic=True,source='seeded synthetic initialization',seed=20261024,
                              zero_logits=zero,training_games=0,parameter_updates=0))
    load_blob(exported)
    weights='nn_policy_weights_policy_v2_untrained.h'
    shutil.copy2(exported/weights,src/weights)
    (src/'nn_policy_installed.h').write_text(
        '#pragma once\n#include "'+weights+'"\nnamespace nnp {\n'
        'inline constexpr const nnpm::PolicyDesc& kInstalled=nnpw_policy_v2_untrained::kDesc;\n}\n',encoding='utf-8')
    (src/'nn_policy_config.h').write_text(
        '// SYNTHETIC UNTRAINED experiment. Never a release selection.\n#pragma once\n'
        '#define NN_POLICY_V2 1\n'
        '#define NN_POLICY_TELEMETRY 1\n'
        f'#define NN_POLICY_LOG {int("record" in profile)}\n'
        f'#define NN_POLICY_SAMPLE {int(profile=="direct_sample_record")}\n',encoding='utf-8')
    (destination/'policy_install.json').write_text(json.dumps(dict(profile=profile,status='untrained',
        interpretation_version=2,model_checksum=manifest['checksum'],obs_schema_hash=manifest['obs_schema_hash'],
        action_schema_hash=manifest['action_schema_hash'],training_games=0,parameter_updates=0,
        budget_status='provisional; complete call-site engine calibration pending'),indent=2)+'\n',encoding='utf-8')
    return destination

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest',required=True,type=Path)
    ap.add_argument('--profile',choices=PROFILES,default='direct_untrained')
    args=ap.parse_args()
    print(install(ROOT/args.dest,args.profile))
