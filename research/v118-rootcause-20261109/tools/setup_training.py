import ast,shutil
from project import ROOT,BASE,save,sha

def setup():
    source=BASE/'training/agent2/lab';dest=ROOT/'training/agent2/lab'
    for name in ['team_reward.py']:
        shutil.copy2(source/name,dest/name)
    text=(source/'train.py').read_text(encoding='utf-8');tree=ast.parse(text)
    needed={'timelines','at','priv_features','gae_game','vfeat','live_logits','blend'}
    header='''import numpy as np
import torch
from nn_model import BLK,split_blocks
ENS=2.
NF=500
PF=71
TEAM_WIN=True
GAMMA,LAMBDA=1.,.995
TL_METRICS=('gems','submittedGems','earnedGold','kills','assists','deaths')
'''
    extracted=[ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed]
    assert len(extracted)==len(needed)
    (dest/'policy_math.py').write_text(header+'\n\n'.join(extracted)+'\n',encoding='utf-8')
    save(ROOT/'training/math-provenance.json',{'source':str(source/'train.py'),'sha256':sha(source/'train.py'),'functions':sorted(needed)})
if __name__=='__main__':setup()
