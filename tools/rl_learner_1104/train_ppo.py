"""One bounded real-shard PPO update, checkpoint and runtime re-export.

No match is launched. Bad data fails before optimization. Synthetic fixtures are
marked as such in the report and never described as actual game training.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import torch
from rl_learner_1104.cl1 import CampPointer, GLOBAL_WIDTH, PREPROCESS_VERSION
from rl_learner_1104.model import Critic
from rl_learner_1104.on_policy import update
from rl_learner_1104.rollout_io import read_columns, trajectories


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--actor',required=True)
    p.add_argument('--shard',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--epochs',type=int,default=2)
    p.add_argument('--resume')
    args=p.parse_args()
    out=Path(args.out)
    if out.exists():
        raise ValueError('use a new output namespace; no checkpoint overwrite')
    torch.set_num_threads(2);torch.manual_seed(1104)
    actor_bytes=Path(args.actor).read_bytes()
    actor_hash=hashlib.sha256(actor_bytes).hexdigest()
    spec=json.loads(actor_bytes)
    if spec['format']!='jd-cl1-pointer-f32-v1' or spec['preprocess']!=PREPROCESS_VERSION:
        raise ValueError('actor format mismatch; Agent2-native weights cannot load here')
    actor=CampPointer(**spec.get('architecture',{}))
    state={k:torch.tensor(v['values'],dtype=torch.float32).reshape(v['shape']) for k,v in spec['tensors'].items()}
    if any(not torch.isfinite(v).all() for v in state.values()):
        raise ValueError('nonfinite actor tensor')
    actor.load_state_dict(state,strict=True)
    critic=Critic(GLOBAL_WIDTH)
    actor_opt=torch.optim.Adam(actor.parameters(),lr=3e-4)
    critic_opt=torch.optim.Adam(critic.parameters(),lr=3e-4)
    iteration=0
    if args.resume:
        previous=torch.load(args.resume,weights_only=True,map_location='cpu')
        if previous['actor_json_sha256']!=actor_hash:
            raise ValueError('resume state does not match currently collected policy')
        critic.load_state_dict(previous['critic'],strict=True)
        actor_opt.load_state_dict(previous['actor_optimizer']);critic_opt.load_state_dict(previous['critic_optimizer'])
        torch.set_rng_state(previous['torch_rng']);iteration=previous['iteration']
    man,cols,column_hashes=read_columns(args.shard)
    origin=man.get('data_origin')
    if origin not in ('engine','synthetic-test'):
        raise ValueError('declare data_origin engine or synthetic-test')
    batch=trajectories(man,cols,actor_hash)
    result=update(actor,critic,batch,actor_hash,epochs=args.epochs,
                  actor_optimizer=actor_opt,critic_optimizer=critic_opt)
    out.mkdir(parents=True,exist_ok=False)
    checkpoint=out/'actor_checkpoint.pt'
    torch.save(dict(state_dict=actor.state_dict(),architecture=actor.architecture,preprocess=PREPROCESS_VERSION,
                    encoder_source=man['policy']['encoder_sha256'],
                    sampling='synthetic-test-PPO' if origin=='synthetic-test' else 'complete-own-policy-PPO',task_epoch=3),checkpoint)
    exported=subprocess.run([sys.executable,str(Path(__file__).with_name('export_cl1.py')),
                             '--checkpoint',str(checkpoint),'--raw',str(Path(args.shard)/'x_fresh.bin'),
                             '--out',str(out/'export')],capture_output=True,text=True,check=True)
    new_hash=hashlib.sha256((out/'export'/'actor.json').read_bytes()).hexdigest()
    torch.save(dict(actor_json_sha256=new_hash,critic=critic.state_dict(),actor_optimizer=actor_opt.state_dict(),
                    critic_optimizer=critic_opt.state_dict(),torch_rng=torch.get_rng_state(),iteration=iteration+1),out/'trainer_state.pt')
    report=dict(status='SYNTHETIC_TEST_ONLY' if origin=='synthetic-test' else 'REAL_GAME_PPO_UPDATE_COMPLETED',
                task_epoch=3,input_actor_sha256=actor_hash,output_actor_sha256=new_hash,
                input_manifest_sha256=hashlib.sha256((Path(args.shard)/'shard.json').read_bytes()).hexdigest(),
                column_sha256=column_hashes,iteration=iteration+1,result=result,
                export_check=exported.stdout.strip(),limits='No playing-strength or fuel claim from optimizer success.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
