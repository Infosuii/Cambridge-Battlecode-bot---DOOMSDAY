"""Later direct-policy data/preflight/bounded fitting. No training without explicit authorization."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from nfs.policy.training import prepare,preflight,fit
from nfs.policy.model import HEAD_IDS

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--receipts',nargs='+',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
    for name in ('preflight','fit'):
        q=sub.add_parser(name)
        for option in ('model-dir','train','validation'):q.add_argument('--'+option,type=Path,required=True)
        q.add_argument('--head',choices=HEAD_IDS,default='move');q.add_argument('--mode',choices=('ppo','imitation'),default='ppo')
        if name=='fit':
            q.add_argument('--out',type=Path,required=True);q.add_argument('--minutes',type=float,default=5)
            q.add_argument('--epochs',type=int,default=4);q.add_argument('--seed',type=int,default=20261024)
            q.add_argument('--i-authorize-training',action='store_true')
            q.add_argument('--resume-checkpoint',type=Path)
            q.add_argument('--device',choices=('auto','cpu','cuda'),default='auto')
            q.add_argument('--evaluation-config',type=Path)
    a=p.parse_args()
    if a.command=='prepare':print(prepare(a.receipts,a.out))
    elif a.command=='preflight':print(json.dumps(preflight(a.model_dir,a.train,a.validation,a.head,a.mode)[0],indent=2))
    else:print(json.dumps(fit(a.model_dir,a.train,a.validation,a.out,head=a.head,mode=a.mode,
        authorized=a.i_authorize_training,minutes=a.minutes,epochs=a.epochs,seed=a.seed,resume_checkpoint=a.resume_checkpoint,
        device=a.device,evaluation_config=a.evaluation_config),indent=2))

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps(dict(ok=False,error_type=type(error).__name__,error=str(error))));raise SystemExit(2)
