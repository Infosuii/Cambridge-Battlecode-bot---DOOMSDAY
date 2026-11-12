"""Lossless bridge between R1's runtime header and JOHNDOE's learner checkpoint.
Importing a header cannot restore optimizer state: it explicitly starts a NEW optimizer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import torch
from head import TargetHead
from train_head import ABI,weight_hash

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--r1-tools',type=Path,required=True,help='pinned directory containing head_export.py and target_head.py')
p.add_argument('--import-header',type=Path);p.add_argument('--export-checkpoint',type=Path)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if bool(a.import_header)==bool(a.export_checkpoint):raise ValueError('choose exactly one direction')
if a.out.exists():raise ValueError('output must be new')
sys.path.insert(0,str(a.r1_tools.resolve()));import head_export as HX
if a.import_header:
    model,version=HX.load_header(str(a.import_header))
    own=TargetHead();own.load_state_dict(model.state_dict(),strict=True)
    ck=dict(state=own.state_dict(),optimizer=None,updates=0,architecture=ABI,feature_abi=HX.HEAD_ABI_HASH,
            weights_sha256=weight_hash(own),source_runtime_version=version,
            source_header_sha256=hashlib.sha256(a.import_header.read_bytes()).hexdigest(),
            optimizer_reset_reason='runtime header contains weights only; no optimizer continuity claimed')
    torch.save(ck,a.out)
    print(json.dumps({k:v for k,v in ck.items() if k not in ('state','optimizer')}))
else:
    ck=torch.load(a.export_checkpoint,weights_only=True,map_location='cpu')
    if ck['architecture']!=ABI or ck['feature_abi']!=HX.HEAD_ABI_HASH:raise ValueError('architecture/feature ABI mismatch')
    model=TargetHead();model.load_state_dict(ck['state'],strict=True)
    if weight_hash(model)!=ck['weights_sha256']:raise ValueError('checkpoint integrity')
    text,version=HX.header(model,'jd-u'+str(ck['updates']));a.out.write_text(text)
    restored,restored_version=HX.load_header(str(a.out))
    if restored_version!=version or weight_hash(restored)!=ck['weights_sha256']:
        a.out.unlink();raise ValueError('header roundtrip failed')
    print(json.dumps(dict(version=version,weights_sha256=weight_hash(restored),scope='weight export, not runtime validation')))
