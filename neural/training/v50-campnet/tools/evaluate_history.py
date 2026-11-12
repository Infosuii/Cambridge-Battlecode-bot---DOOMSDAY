"""Evaluate the preregistered historical-data extension without editing PPO."""
import argparse, hashlib, json, shutil, time, zipfile
from pathlib import Path
import torch
import train

ROOT=train.ROOT

def selection(workers):
    fit=json.loads((ROOT/'historical-training/fit.json').read_text())
    if fit.get('status')!='trained':
        train.write(ROOT/'historical-training/selection.json',dict(status='not_promoted',reason='Historical draft did not improve prediction validation.'))
        return None
    ckpt=torch.load(ROOT/'checkpoints/best-trained.pt',map_location=train.DEVICE,weights_only=False)
    policy=train.Policy().to(train.DEVICE);policy.load_state_dict(ckpt['policy'])
    header=ROOT/'historical-training/draft_net.h'
    weight_hash=hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in policy.state_dict().values())).hexdigest()
    fingerprint=hashlib.sha256((weight_hash+train.sha(header)).encode()).hexdigest()[:16]
    src=ROOT/f'historical-training/branches/{fingerprint}/src'
    shutil.copytree(ROOT/'candidate/src',src,dirs_exist_ok=True)
    shutil.copyfile(header,src/'draft_net.h')
    train.export_weights(policy,False,train.SEED,src)
    wasm=train.compile_bot(src,ROOT/f'builds/history-{fingerprint}.wasm',workers)
    protocol=json.loads((ROOT/'protocol.json').read_text())
    opponents=[ROOT/'builds/baseline.wasm',ROOT/'builds/recent-meta-proxy-0.wasm',ROOT/'builds/recent-meta-proxy-1.wasm']
    score,_=train.evaluate_artifact(wasm,f'history-selection-{fingerprint}',list(map(Path,protocol['selection_maps'])),opponents,workers)
    baseline=ckpt['selection']
    promoted=score['faults']==0 and (score['win_rate'],score['mean_gem_margin'])>(baseline['win_rate'],baseline['mean_gem_margin'])
    result=dict(status='promoted_on_selection' if promoted else 'not_promoted',fingerprint=fingerprint,
                gameplay_iteration=ckpt.get('iteration'),gameplay_weight_hash=weight_hash,
                historical_draft_sha256=train.sha(header),candidate_selection=score,
                same_gameplay_original_draft_selection=baseline,promoted=promoted,
                source=str(src),wasm=str(wasm),
                frozen_without_reading_final_results=True,
                rule='strictly better (selection win rate, mean gem margin), zero faults; final maps unused')
    train.write(ROOT/'historical-training/selection.json',result)
    print(json.dumps(result),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    if args.final and not (ROOT/'report.json').exists(): raise RuntimeError('PPO has not completed; final extension is premature')
    picked=selection(args.workers)
    if not args.final:return
    if not picked or not picked.get('promoted'):
        train.write(ROOT/'historical-training/final.json',dict(status='not_promoted',recommended_source=str(ROOT/'release/bot_neural.zip'),
                    explanation='Historical draft was trained and tested but did not beat the same gameplay model on selection maps. Original drafting retained.'))
        return
    # Branch selection above never reads either final-holdout result file.
    protocol=json.loads((ROOT/'protocol.json').read_text())
    opponents=[ROOT/'builds/baseline.wasm',ROOT/'builds/recent-meta-proxy-0.wasm',ROOT/'builds/recent-meta-proxy-1.wasm']
    score,wasm=train.evaluate_artifact(Path(picked['wasm']),'history-final-'+picked['fingerprint'],
                  list(map(Path,protocol['final_holdout_maps'])),opponents,args.workers)
    original=json.loads((ROOT/'evaluation/original-holdout.json').read_text())['summary']
    folder=ROOT/'release/bot_neural_history';shutil.copytree(picked['source'],folder/'src',dirs_exist_ok=True)
    shutil.copyfile(wasm,ROOT/'release/bot_neural_history.wasm')
    archive=ROOT/'release/bot_neural_history.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((folder/'src').glob('*')):z.write(p,'src/'+p.name)
    result=dict(status='evaluated',selection=picked,final_holdout=score,original_holdout=original,
                source=str(archive),source_sha256=train.sha(archive),wasm_sha256=train.sha(wasm),
                historical_training=json.loads((ROOT/'historical-training/fit.json').read_text()),
                limits='Observational historical draft pretraining; eight map clusters and local proxies do not establish ladder strength.')
    train.write(ROOT/'historical-training/final.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
