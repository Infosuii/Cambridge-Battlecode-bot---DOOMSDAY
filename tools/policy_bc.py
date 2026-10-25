"""Bounded behaviour-cloning training of the policy-v2 network from replay-derived rows (tools/replay/bc_dataset.py).

    python tools/policy_bc.py --data <bc_dataset dir> --out artifacts/runs/<fresh> --minutes 20 --epochs 30
                              --device cuda --i-authorize-training [--init models/policy_v2_untrained] [--train encoder,move]

Cross-entropy over legal candidates (nfs.policy.losses.imitation_loss) for every head in the dataset, with per-head
minibatches mixed within each epoch. Trains the shared encoder and the named heads (default: all heads in the data); every other parameter stays frozen. Validation is a disjoint set of matches: every
epoch reports loss and top-1 accuracy next to the always-hold and uniform-legal baselines and the initial model.
Checkpoints are atomic per epoch; the best-validation-loss weights are exported with the existing exporter. Never
promotes, installs or submits anything.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs.policy import losses as L  # noqa: E402
from nfs.policy import candidates as C, observation as O  # noqa: E402
from nfs.policy.export import export_model, load_blob, load_model  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, device):
    with np.load(path, allow_pickle=False) as z:
        return {k: torch.as_tensor(z[k]).to(device) for k in ('obs', 'feat', 'legal', 'label', 'context', 'head')}


HEAD_NAME = {h['id']: h['name'] for h in C.SCHEMA['heads']}


def evaluate(model, data, batch):
    model.eval()
    out = {}
    with torch.no_grad():
        for hid in data['head'].unique().tolist():
            ix = torch.nonzero(data['head'] == hid).squeeze(1)
            total, correct, loss_sum = 0, 0, 0.0
            for s in range(0, len(ix), batch):
                b = ix[s:s + batch]
                legal = data['legal'][b].bool()
                logits = model(data['obs'][b], HEAD_NAME[hid], data['feat'][b], legal, data['context'][b])
                loss, _ = L.imitation_loss(logits, legal, data['label'][b], imitation_mask=torch.ones(len(b), dtype=torch.bool, device=b.device))
                loss_sum += float(loss) * len(b); total += len(b)
                correct += int((logits.argmax(-1) == data['label'][b]).sum())
            out[HEAD_NAME[hid]] = dict(loss=loss_sum / total, accuracy=correct / total, rows=total)
    model.train()
    rows = sum(v['rows'] for v in out.values())
    return dict(heads=out, loss=sum(v['loss'] * v['rows'] for v in out.values()) / rows)


def baselines(data):
    out = {}
    for hid in data['head'].unique().tolist():
        m = data['head'] == hid
        legal, label = data['legal'][m].bool(), data['label'][m]
        b = dict(uniform_legal_accuracy=float((1.0 / legal.sum(1).float()).mean()),
                 majority_index_accuracy=float((label == label.mode().values).float().mean()))
        name = HEAD_NAME[hid]
        if name in ('move', 'combat'):
            # Hold is kind 3 (move: feature 9, combat: feature 0), the largest kind value among the candidates.
            kind = data['feat'][m][:, :, 9 if name == 'move' else 0].masked_fill(~legal, -1)
            b['always_hold_accuracy'] = float((kind.argmax(1) == label).float().mean())
        out[name] = b
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--init', type=Path, default=ROOT / 'models/policy_v2_untrained')
    p.add_argument('--train', default=None, help='comma list; default encoder + every head in the data')
    p.add_argument('--minutes', type=float, default=20)
    p.add_argument('--epochs', type=int, default=30)
    p.add_argument('--batch', type=int, default=8192)
    p.add_argument('--lr', type=float, default=3e-3)
    p.add_argument('--patience', type=int, default=3)
    p.add_argument('--seed', type=int, default=20261025)
    p.add_argument('--device', choices=('cuda', 'cpu'), default='cuda')
    p.add_argument('--move-distance-offset', type=float, default=0.0,
                   help='augment move batches: add U(0, tiles) to every candidate goal distance (relative order unchanged)')
    p.add_argument('--i-authorize-training', action='store_true')
    a = p.parse_args()
    if not a.i_authorize_training:
        raise SystemExit('explicit --i-authorize-training required; no training performed')
    if not 0 < a.minutes <= 240 or not 1 <= a.epochs <= 200:
        raise SystemExit('bounded run: 0 < minutes <= 240, 1..200 epochs')
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh run directory inside artifacts/ required')
    if a.device == 'cuda' and not torch.cuda.is_available():
        raise SystemExit('CUDA requested but unavailable')
    manifest = json.loads((a.data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['obs_schema_hash'] != O.OBS_SCHEMA_HASH or manifest['action_schema_hash'] != C.ACTION_SCHEMA_HASH:
        raise SystemExit('dataset schema hashes differ from the current policy-v2 schema')
    heads = manifest['heads']
    device = torch.device(a.device)
    torch.manual_seed(a.seed)
    train, val = load(a.data / 'train.npz', device), load(a.data / 'validation.npz', device)
    init_manifest, _ = load_blob(a.init)
    model = load_model(a.init).to(device)
    trainable = set(a.train.split(',')) if a.train else {'encoder', *heads}
    for name, param in model.named_parameters():
        param.requires_grad_(any(name.startswith('heads.' + h + '.') for h in trainable - {'encoder'}) or
                             ('encoder' in trainable and not name.startswith('heads.')))
    params = [q for q in model.parameters() if q.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=a.lr, weight_decay=1e-4)
    out.mkdir(parents=True)

    def event(kind, **fields):
        with (out / 'metrics.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(dict(event=kind, time_unix=time.time(), **fields)) + '\n')

    base = dict(baselines(val), initial=evaluate(model, val, a.batch))
    event('start', device=str(device), gpu=torch.cuda.get_device_name(0) if a.device == 'cuda' else None, heads=heads,
          trainable=sorted(trainable), trainable_parameters=sum(q.numel() for q in params),
          total_parameters=sum(q.numel() for q in model.parameters()), train_rows=len(train['label']), validation_rows=len(val['label']),
          init_checksum=init_manifest['checksum'], data_manifest=manifest, validation_baselines=base)
    deadline, start = time.time() + a.minutes * 60, time.time()
    best, best_state, stale, history, stop, updates = None, None, 0, [], 'epochs_complete', 0
    n = len(train['label'])
    for epoch in range(a.epochs):
        batches = []
        for hid in train['head'].unique().tolist():
            idx = torch.nonzero(train['head'] == hid).squeeze(1)
            idx = idx[torch.randperm(len(idx), device=device)]
            batches += [(hid, idx[s:s + a.batch]) for s in range(0, len(idx), a.batch)]
        epoch_loss, seen = 0.0, 0
        for j in torch.randperm(len(batches)).tolist():
            if time.time() >= deadline:
                stop = 'deadline'; break
            hid, ix = batches[j]
            legal = train['legal'][ix].bool()
            feat = train['feat'][ix]
            if a.move_distance_offset and HEAD_NAME[hid] == 'move':
                # Absolute goal distance should not change which step makes progress: shift both distance features
                # (scale 50, clip [0,4]) of all candidates by one random offset per decision.
                shift = torch.rand(len(ix), 1, device=device) * (a.move_distance_offset / 50)
                feat = feat.clone(); feat[:, :, 2:4] = (feat[:, :, 2:4] + shift.unsqueeze(-1)).clamp(0, 4) * legal.unsqueeze(-1)
            logits = model(train['obs'][ix], HEAD_NAME[hid], feat, legal, train['context'][ix])
            loss, _ = L.imitation_loss(logits, legal, train['label'][ix], imitation_mask=torch.ones(len(ix), dtype=torch.bool, device=device))
            if not torch.isfinite(loss):
                stop = 'nonfinite_loss'; break
            optimizer.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0, error_if_nonfinite=True)
            optimizer.step(); updates += 1
            epoch_loss += float(loss.detach()) * len(ix); seen += len(ix)
        if stop in ('nonfinite_loss',):
            break
        metrics = dict(epoch=epoch, updates=updates, train_loss=epoch_loss / max(1, seen), validation=evaluate(model, val, a.batch),
                       elapsed_seconds=time.time() - start, samples_per_second=updates * a.batch / max(1e-6, time.time() - start),
                       gpu_peak_bytes=torch.cuda.max_memory_allocated() if a.device == 'cuda' else 0)
        history.append(metrics); event('epoch', **metrics)
        state = dict(model={k: v.detach().cpu() for k, v in model.state_dict().items()}, optimizer=optimizer.state_dict(), epoch=epoch,
                     updates=updates, metrics=metrics, data_manifest_sha256=sha(a.data / 'manifest.json'))
        torch.save(state, out / 'checkpoint.partial.pt'); (out / 'checkpoint.partial.pt').replace(out / 'checkpoint.pt')
        if best is None or metrics['validation']['loss'] < best['validation']['loss']:
            best, best_state, stale = metrics, state['model'], 0
        else:
            stale += 1
        if stale >= a.patience:
            stop = 'early_stopping'; break
        if stop == 'deadline':
            break
    report = dict(status='trained' if best else 'unmodified', heads=heads, stop=stop, updates=updates, epochs=len(history),
                  best_epoch=best and best['epoch'], best_validation=best and best['validation'], validation_baselines=base,
                  history=history, submitted=False, promoted=False)
    if best_state is not None:
        model.load_state_dict(best_state)
        trained = sorted(trainable)
        export_model(model.cpu(), 'policy_v2_bc', out / 'export', 'trained', dict(
            synthetic=False, source='behaviour cloning from official 1.0.3 platform replays (tools/policy_bc.py)',
            trained_heads=sorted(trainable - {'encoder'}), shared_encoder_frozen='encoder' not in trainable,
            remaining_untrained_heads=sorted(set(C.HEAD_IDS) - trainable), training_data=str(a.data.resolve()),
            data_manifest_sha256=sha(a.data / 'manifest.json'), rule_inputs=manifest.get('rule_inputs'),
            best_validation=best['validation'], parameter_updates=updates, init_checksum=init_manifest['checksum']))
    (out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    event('stop', reason=stop, updates=updates, best_validation=report['best_validation'])
    print(json.dumps({k: v for k, v in report.items() if k != 'history'}, indent=1))


if __name__ == '__main__':
    main()
