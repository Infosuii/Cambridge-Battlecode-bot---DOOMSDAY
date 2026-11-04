"""Export our own trained pointer actor, plus portable parity fixtures.

No optimizer/critic/replay data is exported to the bot. Arrays use PyTorch row
major linear weights [out,in]; GRU gate order r,z,n, with reset AFTER recurrent
candidate affine, matching torch.nn.GRUCell. Runtime integration is a separate
step and must pass fixtures plus actual charged-fuel tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from rl_learner_1104.cl1 import CampPointer, PREPROCESS_VERSION, preprocess


def numpy_forward(state, entities, present, globals_, hidden, reset):
    def linear(x, name):
        return x @ state[name + '.weight'].T + state[name + '.bias']
    def sig(x):
        return 1 / (1 + np.exp(-x))
    pooled, encoded = [], {}
    for k in sorted(entities):
        z = np.maximum(linear(entities[k], 'encoders.' + k), 0)
        encoded[k] = z
        mask = present[k][..., None]
        count = mask.sum(1)
        mean = (z * mask).sum(1) / np.maximum(count, 1)
        maximum = np.where(mask, z, -np.inf).max(1)
        pooled.extend((mean, np.where(count > 0, maximum, 0)))
    context = np.maximum(linear(np.concatenate(pooled + [globals_], -1), 'context'), 0)
    h0 = hidden * (~reset)[:, None]
    gi = context @ state['memory.weight_ih'].T + state['memory.bias_ih']
    gh = h0 @ state['memory.weight_hh'].T + state['memory.bias_hh']
    ir, iz, inn = np.split(gi, 3, axis=-1)
    hr, hz, hn = np.split(gh, 3, axis=-1)
    r, z = sig(ir + hr), sig(iz + hz)
    n = np.tanh(inn + r * hn)
    hidden = (1 - z) * n + z * h0
    camp = np.concatenate((encoded['camp'], np.broadcast_to(hidden[:, None], (len(hidden), 12, 16))), -1)
    score = linear(np.tanh(linear(camp, 'pointer')), 'score')[..., 0]
    logits = np.concatenate((score, linear(hidden, 'none')), -1)
    mask = np.concatenate((present['camp'], np.ones((len(hidden), 1), dtype=bool)), -1)
    return np.where(mask, logits, -np.inf), hidden


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--raw', required=True, help='CL1 int16 binary, 448 columns')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    checkpoint = torch.load(args.checkpoint, weights_only=True, map_location='cpu')
    if checkpoint['preprocess'] != PREPROCESS_VERSION:
        raise ValueError('preprocess mismatch')
    model = CampPointer().eval()
    model.load_state_dict(checkpoint['state_dict'])
    state = {k: v.detach().numpy() for k, v in model.state_dict().items()}
    all_raw = np.fromfile(args.raw, dtype='<i2').reshape(-1, 448)
    selected = np.linspace(0, len(all_raw) - 1, 8, dtype=int)
    raw = torch.from_numpy(all_raw[selected].copy())
    torch.manual_seed(1104)
    h = torch.randn(8, 16) * .2
    reset = torch.tensor([1, 0, 1, 0, 0, 1, 0, 1], dtype=torch.bool)
    with torch.no_grad():
        logits, nh = model(raw, h, reset)
        entities, present, globals_ = preprocess(raw)
    np_logits, np_h = numpy_forward(state, {k: v.numpy() for k, v in entities.items()},
                                    {k: v.numpy() for k, v in present.items()}, globals_.numpy(), h.numpy(), reset.numpy())
    np.testing.assert_allclose(np_h, nh.numpy(), rtol=1e-5, atol=2e-6)
    np.testing.assert_allclose(np_logits, logits.numpy(), rtol=1e-5, atol=2e-6)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    tensors = {k: {'shape': list(v.shape), 'values': v.reshape(-1).tolist()} for k, v in state.items()}
    export = {'format': 'jd-cl1-pointer-f32-v1', 'preprocess': PREPROCESS_VERSION,
              'training': checkpoint['sampling'], 'encoder_source': checkpoint['encoder_source'],
              'pool_order': sorted(entities), 'hidden': 16, 'tensors': tensors,
              'limits': 'Hybrid macro policy; training provenance above. Not approved for ladder or full control.'}
    weights = json.dumps(export, separators=(',', ':')) + '\n'
    (out / 'actor.json').write_text(weights)
    header = ['#pragma once', '// Trained macro actor; see export provenance. Not a production candidate.', 'namespace jd_cl1_weights {']
    for k, v in state.items():
        vals = ','.join(format(float(x), '.9e') + 'f' for x in v.reshape(-1))
        header.append('inline constexpr float ' + k.replace('.', '_') + '[] = {' + vals + '};')
    header.append('}')
    (out / 'actor_weights.h').write_text('\n'.join(header) + '\n')
    fixture = {'format': export['format'], 'preprocess': PREPROCESS_VERSION,
               'actor_sha256': hashlib.sha256(weights.encode()).hexdigest(),
               'raw': raw.tolist(), 'hidden_in': h.tolist(), 'reset': reset.tolist(),
               'globals': globals_.tolist(), 'entities': {k: v.tolist() for k, v in entities.items()},
               'present': {k: v.tolist() for k, v in present.items()},
               'logits': [[float(v) if np.isfinite(v) else None for v in row] for row in logits.numpy()],
               'hidden_out': nh.tolist(), 'argmax': logits.argmax(-1).tolist(),
               'max_numpy_hidden_error': float(np.abs(np_h - nh.numpy()).max()),
               'tolerance': {'absolute': 2e-6, 'relative': 1e-5}}
    (out / 'parity.json').write_text(json.dumps(fixture, separators=(',', ':')) + '\n')
    print(json.dumps({'parameters': sum(v.size for v in state.values()), 'bytes_json': len(weights),
                      'max_numpy_hidden_error': fixture['max_numpy_hidden_error'], 'out': str(out)}))


if __name__ == '__main__':
    main()
