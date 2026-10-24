"""JSON interfaces for a separate training-operations agent. No training or submission in these commands."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
from nfs.policy.operations import compare,comparison_plan,status,inspect_game,list_checkpoints,list_versions,build_baseline,export_checkpoint

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('status');q.add_argument('--run',type=Path,required=True)
    q=sub.add_parser('build-baseline');q.add_argument('--out',type=Path,required=True)
    q=sub.add_parser('export-checkpoint');q.add_argument('--checkpoint',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
    q=sub.add_parser('list-checkpoints');q.add_argument('--run',type=Path,required=True)
    q=sub.add_parser('list-versions');q.add_argument('--root',type=Path,default=ROOT/'artifacts/runs')
    q=sub.add_parser('inspect-game');q.add_argument('--folder',type=Path,required=True);q.add_argument('--side',choices=('A','B'),default='A');q.add_argument('--tail',type=int,default=20)
    for command in ('plan-comparison','compare'):
        q=sub.add_parser(command);q.add_argument('--candidate',type=Path,required=True);q.add_argument('--previous',type=Path,nargs='*',default=[])
        q.add_argument('--maps',nargs='+',default=['00rows']);q.add_argument('--max-games',type=int,default=8)
        if command=='compare':q.add_argument('--out',type=Path,required=True)
        if command=='compare':q.add_argument('--max-seconds',type=int,default=300)
    a=p.parse_args()
    if a.command=='status':result=status(a.run)
    elif a.command=='build-baseline':result=build_baseline(a.out)
    elif a.command=='export-checkpoint':result=export_checkpoint(a.checkpoint,a.out)
    elif a.command=='list-checkpoints':result=list_checkpoints(a.run)
    elif a.command=='list-versions':result=list_versions(a.root)
    elif a.command=='inspect-game':result=inspect_game(a.folder,a.side,a.tail)
    elif a.command=='plan-comparison':result=comparison_plan(a.candidate,a.previous,a.maps,max_games=a.max_games)
    else:result=compare(a.candidate,a.previous,a.maps,a.out,max_games=a.max_games,max_seconds=a.max_seconds)
    print(json.dumps(dict(ok=True,result=result),indent=2))

if __name__=='__main__':
    try:main()
    except Exception as e:
        print(json.dumps(dict(ok=False,error_type=type(e).__name__,error=str(e))));raise SystemExit(2)
