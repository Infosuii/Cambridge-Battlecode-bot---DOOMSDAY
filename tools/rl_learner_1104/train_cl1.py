"""Sequence-aware teacher warm start. This is BC, never PPO or ladder evidence."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch.nn import functional as F
from rl_learner_1104.cl1 import CampPointer, PREPROCESS_VERSION, SOURCE_ENCODER


def load_sequences(root, contract_path):
    spec = importlib.util.spec_from_file_location('trajectory_contract', contract_path)
    contract = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = contract
    spec.loader.exec_module(contract)
    sequences, provenance, map_splits = {'train': [], 'dev': []}, [], {}
    for manifest_path in sorted(Path(root).rglob('shard.json')):
        m, c = contract.load_shard(str(manifest_path.parent), use_numpy=True)
        errors = contract.validate(m, c)
        if errors:
            raise ValueError(str(manifest_path) + ': ' + '; '.join(errors[:5]))
        if (m['layout'], m['action_schema'], m['sampling']) != (10, 'target13-cl1', 'teacher'):
            raise ValueError('BC smoke requires isolated CL1 teacher shards')
        if m['policy']['source_commit'] != SOURCE_ENCODER:
            raise ValueError('encoder version changed: audit mapping before loading')
        provenance.append({'path': str(manifest_path), 'sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                           'policy': m['policy'], 'engine': m['engine']})
        for episode, meta in enumerate(m['episodes']):
            split = meta['split']
            if split not in sequences or meta['status'] != 'terminated' or not meta['reward_complete']:
                raise ValueError('incomplete/unknown episode cannot enter teacher smoke')
            mh = meta['map_hash']
            if mh in map_splits and map_splits[mh] != split:
                raise ValueError('map leakage across splits')
            map_splits[mh] = split
            rows = np.flatnonzero((c['episode'] == episode) & (c['boundary'] == 0))
            for body in np.unique(c['body_id'][rows]):
                ix = rows[c['body_id'][rows] == body]
                ix = ix[np.argsort(c['act_round'][ix], kind='stable')]
                if not len(ix):
                    continue
                if not c['reset'][ix[0]]:
                    raise ValueError('sequence starts without reset')
                sequences[split].append({
                    'x': torch.from_numpy(c['x_fresh'][ix].copy()),
                    'y': torch.from_numpy(c['teacher_action'][ix].astype(np.int64)),
                    'mask': torch.from_numpy(c['mask'][ix].astype(bool)),
                    'reset': torch.from_numpy(c['reset'][ix].astype(bool)),
                    'changed': torch.from_numpy(c['changed'][ix].astype(bool))})
    if not all(sequences.values()):
        raise ValueError('need nonempty train and dev with disjoint maps')
    return sequences, provenance, map_splits


def batches(sequences, batch_size, shuffle=False):
    order = list(range(len(sequences)))
    if shuffle:
        random.shuffle(order)
    for start in range(0, len(order), batch_size):
        seqs = [sequences[i] for i in order[start:start + batch_size]]
        n, length = len(seqs), max(len(s['y']) for s in seqs)
        out = {'x': torch.zeros(length, n, 448, dtype=torch.int16),
               'y': torch.zeros(length, n, dtype=torch.long),
               'mask': torch.ones(length, n, 13, dtype=torch.bool),
               'reset': torch.ones(length, n, dtype=torch.bool),
               'changed': torch.zeros(length, n, dtype=torch.bool),
               'valid': torch.zeros(length, n, dtype=torch.bool)}
        for j, s in enumerate(seqs):
            count = len(s['y'])
            for k in s:
                out[k][:count, j] = s[k]
            out['valid'][:count, j] = True
        yield out


def pass_sequences(model, sequences, optimizer=None, chunk=32, batch_size=8):
    training = optimizer is not None
    model.train(training)
    totals = dict(rows=0, correct=0, changed_rows=0, changed_correct=0, nll=0., nearest_correct=0)
    with torch.set_grad_enabled(training):
        for b in batches(sequences, batch_size, shuffle=training):
            hidden = model.initial_state(b['y'].shape[1])
            for begin in range(0, len(b['y']), chunk):
                losses, count = [], 0
                for t in range(begin, min(begin + chunk, len(b['y']))):
                    valid = b['valid'][t]
                    logits, h = model(b['x'][t], hidden, b['reset'][t])
                    hidden = torch.where(valid[:, None], h, hidden)
                    if not valid.any():
                        continue
                    legal = b['mask'][t][valid]
                    labels = b['y'][t][valid]
                    if not legal.gather(1, labels[:, None]).all():
                        raise ValueError('illegal teacher label')
                    scores = logits[valid].masked_fill(~legal, -torch.inf)
                    loss = F.cross_entropy(scores, labels, reduction='sum')
                    losses.append(loss)
                    n = int(valid.sum())
                    count += n
                    pred = scores.argmax(-1)
                    changed = b['changed'][t][valid]
                    totals['rows'] += n
                    totals['correct'] += int((pred == labels).sum())
                    totals['changed_rows'] += int(changed.sum())
                    totals['changed_correct'] += int(((pred == labels) & changed).sum())
                    totals['nearest_correct'] += int((legal.long().argmax(-1) == labels).sum())
                    totals['nll'] += float(loss.detach())
                if training and count:
                    optimizer.zero_grad(set_to_none=True)
                    (torch.stack(losses).sum() / count).backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
                    optimizer.step()
                hidden = hidden.detach()
    return {**totals, 'accuracy': totals['correct'] / totals['rows'],
            'changed_accuracy': totals['changed_correct'] / max(1, totals['changed_rows']),
            'nearest_accuracy': totals['nearest_correct'] / totals['rows'],
            'mean_nll': totals['nll'] / totals['rows']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--contract', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--epochs', type=int, default=3)
    args = p.parse_args()
    random.seed(1104); np.random.seed(1104); torch.manual_seed(1104)
    torch.set_num_threads(2)
    started = time.monotonic()
    data, provenance, splits = load_sequences(args.data, args.contract)
    actor = CampPointer()
    optimizer = torch.optim.Adam(actor.parameters(), lr=0.001)
    report = {'kind': 'BC_WARMSTART_SMOKE_NOT_RL', 'epoch': 2, 'session': 'johndoe-rl-learner-e2-20261104-1418',
              'preprocess': PREPROCESS_VERSION, 'encoder_source': SOURCE_ENCODER,
              'parameters': sum(p.numel() for p in actor.parameters()), 'map_splits': splits,
              'provenance': provenance, 'initial_dev': pass_sequences(actor, data['dev']), 'epochs': [],
              'limits': ['Only 2 maps / 4 games: interface diagnostic, not generalization evidence.',
                         'Teacher macro labels only; no PPO, learned primitives or win-rate claim.',
                         'af91 collector predates malformed-row/provenance fixes; recollect before RL.',
                         'Target12 conflates none/outside; CL1 field visibility audit pending.']}
    for epoch in range(args.epochs):
        train = pass_sequences(actor, data['train'], optimizer)
        dev = pass_sequences(actor, data['dev'])
        report['epochs'].append({'epoch': epoch + 1, 'train': train, 'dev': dev})
        print(json.dumps(report['epochs'][-1]), flush=True)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': actor.state_dict(), 'preprocess': PREPROCESS_VERSION,
                'encoder_source': SOURCE_ENCODER, 'initialization': 'independent-random-seed-1104',
                'sampling': 'teacher-BC-only', 'task_epoch': 2}, out / 'actor_bc_smoke.pt')
    report['wall_seconds'] = time.monotonic() - started
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('saved', str(out), flush=True)


if __name__ == '__main__':
    main()
