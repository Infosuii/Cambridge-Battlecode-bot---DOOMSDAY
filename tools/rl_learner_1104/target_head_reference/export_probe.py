"""Generate deterministic synthetic float32 export fixtures, not training data."""
import json
from pathlib import Path
import torch
from head import TargetHead

torch.set_num_threads(1);torch.manual_seed(1104)
root=Path(__file__).resolve().parent
probe=root.parent/'head-export-probe'
src=probe/'bots/submission/src';src.mkdir(parents=True,exist_ok=True)
m=TargetHead()
with torch.no_grad():
    for p in m.parameters():p.normal_(0,.12)
    m.gate.bias.fill_(-.4)
B,K,P=32,10,7
x=torch.randn(B,160);c=torch.randn(B,K,16);f=torch.randn(B,K,4)
l=torch.randn(B,K+1)*3;valid=torch.rand(B,K+1)>.25
ids=torch.randint(P,(B,K+1));ref=ids[:,0].clone();valid[:,0]=True
with torch.no_grad():expected,alpha,_=m(x,c,f,l,valid,ids,ref,P)
packed=[]
for name in ('context','query','key','features','far','gate'):
    layer=getattr(m,name)
    packed.extend(layer.weight.detach().T.contiguous().flatten().tolist());packed.extend(layer.bias.detach().tolist())
assert len(packed)==11826
arrays={'weights':packed,'contexts':x.flatten().tolist(),'camps':c.flatten().tolist(),'features':f.flatten().tolist(),'native':l.flatten().tolist()}
header=['#pragma once']
for name,values in arrays.items():header.append('inline const float '+name+'[] = {'+','.join(float(v).hex()+'f' for v in values)+'};')
header.append('inline const bool valid[] = {'+','.join('true' if v else 'false' for v in valid.flatten().tolist())+'};')
for name,values in [('mapping',ids.flatten().tolist()),('references',ref.tolist())]:header.append('inline const int '+name+'[] = {'+','.join(map(str,values))+'};')
(src/'fixtures.h').write_text('\n'.join(header)+'\n')
(src/'optimized_head.h').write_text((root/'optimized_head.h').read_text())
(src/'bot.cpp').write_text('''#include <cambc.h>
#include <cstdio>
#include "fixtures.h"
#include "optimized_head.h"
int main(){for(int b=0;b<32;++b){double p[7],a; jd_head::probabilities(weights,contexts+b*160,camps+b*160,features+b*40,native+b*11,10,valid+b*11,mapping+b*11,references[b],7,p,a);std::printf("EXPORT %d %.17g",b,a);for(double v:p)std::printf(" %.17g",v);std::printf("\\n");}std::fflush(stdout);cambc::resign();cambc::end_turn();}
''')
(root/'export_expected.json').write_text(json.dumps({'probabilities':expected.tolist(),'alpha':alpha.flatten().tolist()}))
print(json.dumps({'fixtures':B,'parameters':len(packed),'probe':str(probe)}))
