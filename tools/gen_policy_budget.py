"""Generate the direct-policy budget from its separate, measured configuration. No build/game/training."""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def render(cfg=None):
    doc=json.loads((ROOT/'models/policy_v2_budget.json').read_text())
    if cfg is not None:
        e=cfg['encoder'];m=doc['model']
        if any(e[k]!=m[k] for k in ('global_hidden','entity_hidden','ctx')) or any(h['hidden']!=m['head_hidden'] for h in cfg['heads']):
            raise ValueError('architecture needs a new measured direct-policy budget')
    allowed=('turn_allowance','action_reserve','tail_reserve','observation','candidate','head_base','per_candidate','log','log_per_candidate')
    if set(doc['policy'])!=set(allowed) or any(type(v) is not int or not 0<v<1000000 for v in doc['policy'].values()):
        raise ValueError('invalid direct-policy fuel budget')
    body=',\n'.join('    .'+key+'='+str(doc['policy'][key])+'u' for key in allowed)
    return '// GENERATED from models/policy_v2_budget.json. Direct-policy only.\n#pragma once\n#include "nn_policy_core.h"\nnamespace nnp {\ninline constexpr Budget kPolicyBudget{\n'+body+'\n};\n}\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'bot/src/nn_policy_budget.h')
    a=p.parse_args();out=a.out.resolve();out.relative_to(ROOT);out.write_text(render(),encoding='utf-8',newline='\n');print(out)
