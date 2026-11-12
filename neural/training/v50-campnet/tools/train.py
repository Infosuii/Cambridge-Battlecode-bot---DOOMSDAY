"""Local GPU PPO, recent-meta draft fitting, and independent engine evaluation.

All match execution uses the official CLI at its default competition fuel.
The original source is immutable. Historical games never become fake executable
opponents: explicitly named local proxies reuse our baseline gameplay.
"""
import argparse, concurrent.futures as cf, copy, datetime as dt, hashlib, json
import math, os, random, re, shutil, struct, subprocess, time, traceback, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
CLI = Path('C:/Users/omdha/Documents/Codex/2026-10-22/what/work/cambc.exe')
ARENA = CLI.parent / 'arena'
SDK = Path('C:/Users/omdha/AppData/Local/cambc/wasi-sdk-33')
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
NOW = dt.datetime.now(dt.timezone.utc)
SEED = 20261023
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
torch.set_num_threads(4)

def write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    tmp.replace(path)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def event(stage, **kw):
    row = dict(time=dt.datetime.now(dt.timezone.utc).isoformat(), stage=stage, **kw)
    with (ROOT / 'progress.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(row, default=str) + '\n')
    write(ROOT / 'status.json', row)
    print(json.dumps(row, default=str), flush=True)

def command(args, timeout=180, cwd=ROOT):
    r = subprocess.run([str(v) for v in args], cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    if r.returncode: raise RuntimeError('Command failed: ' + str(args[0]) + '\n' + (r.stdout + r.stderr)[-5000:])
    return r.stdout + r.stderr

def compile_bot(src, output, workers=12):
    """Content-addressed translation units: a weight update rebuilds one tiny file."""
    src = Path(src); output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    cache = ROOT / 'objects'; cache.mkdir(exist_ok=True)
    headers = b''.join(p.name.encode() + p.read_bytes() for p in sorted(src.glob('*.h'))
                       if p.name != 'neural_weights.h')
    flags = ['-O3', '-DNDEBUG', '-std=c++20', '-msimd128', '-mbulk-memory', '-mbulk-memory-opt',
             '-fwasm-exceptions', '-mllvm', '-wasm-use-legacy-eh=false', '--no-wasm-opt',
             '-Wno-constant-logical-operand', '-I' + str(ARENA / 'sdk/cpp')]
    def obj(p):
        deps = (src / 'neural_weights.h').read_bytes() if p.stem == 'neural_policy' else headers
        key = hashlib.sha256(p.read_bytes() + deps + '\n'.join(flags).encode()).hexdigest()
        out = cache / (p.stem + '-' + key + '.o')
        if not out.exists():
            log = command([SDK / 'bin/clang++.exe', *flags, '-c', p, '-o', out], timeout=300)
            if log: (cache / (out.stem + '.log')).write_text(log, encoding='utf-8')
        return out
    with cf.ThreadPoolExecutor(max_workers=min(workers, 9)) as ex:
        objects = list(ex.map(obj, sorted(src.glob('*.cpp'))))
    command([SDK / 'bin/clang++.exe', *flags, *objects,
             '-L' + str(SDK / 'share/wasi-sysroot/lib/wasm32-wasip1/eh'), '-lunwind', '-o', output])
    return output

class Policy(nn.Module):
    def __init__(self):
        super().__init__(); self.hidden = nn.Linear(18, 16); self.head = nn.Linear(16, 1)
        nn.init.normal_(self.hidden.weight, std=0.15); nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.head.weight); nn.init.zeros_(self.head.bias)
    def residual(self, x): return 4 * torch.tanh(self.head(torch.tanh(self.hidden(x.clamp(-8, 8)))).squeeze(-1) / 4)
    def forward(self, x, n):
        z = 4 * x[:, :, 0] + x[:, :, 17] + self.residual(x)
        return z.masked_fill(torch.arange(8, device=x.device)[None, :] >= n[:, None], -1e9)

class Critic(nn.Module):
    def __init__(self): super().__init__(); self.net = nn.Sequential(nn.Linear(18, 64), nn.Tanh(), nn.Linear(64, 1))
    def forward(self, x): return self.net(x[:, 0].clamp(-8, 8)).squeeze(-1)

def export_weights(policy, training, seed, src=None):
    src = Path(src or ROOT / 'candidate/src')
    with torch.no_grad():
        w = torch.cat([policy.hidden.weight.T.flatten(), policy.hidden.bias,
                       policy.head.weight.flatten(), policy.head.bias]).cpu().numpy()
    assert len(w) == 321 and np.isfinite(w).all()
    def literal(x):
        s = format(float(x), '.9g')
        return s + ('.0f' if '.' not in s and 'e' not in s else 'f')
    (src / 'neural_weights.h').write_text(
        '// Trained by tools/train.py. Layout: 18x16, bias16, head16, bias1.\n#pragma once\nnamespace ngp {\n'
        + f'inline constexpr bool kTraining = {str(training).lower()};\n'
        + f'inline constexpr unsigned kSeed = {seed}u;\n'
        + 'inline constexpr float kWeights[321] = {' + ','.join(literal(x) for x in w) + '};\n}\n', encoding='utf-8')
    return w

def bundle_records(folder, side):
    files = list(Path(folder).glob('*.repl26a'))
    if not files: return [], None
    with zipfile.ZipFile(files[0]) as z:
        text = z.read('team-' + side.lower() + '.stdout').decode('ascii', errors='replace')
    records = []
    for m in re.finditer(r'NGP1 ([0-9a-f]{1200})', text):
        raw = bytes.fromhex(m[1]); version, champ, rnd, n, pick, logp = struct.unpack_from('<5If', raw)
        obs = np.frombuffer(raw, dtype='<f4', offset=24).copy().reshape(8, 18)
        if version == 1 and 2 <= n <= 8 and pick < n and np.isfinite(obs).all() and math.isfinite(logp):
            records.append(dict(champion=champ, round=rnd, n=n, pick=pick, logp=logp, obs=obs))
    m = re.search(r'NGPMAP ([0-9a-f]{128})', text)
    feat = np.frombuffer(bytes.fromhex(m[1]), dtype='<f4').copy().tolist() if m else None
    return records, feat

def match(a, b, map_path, folder, candidate_side='A'):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    stats = folder / 'summary.json'
    if not stats.exists():
        log = command([CLI, 'run', a, b, '--map', map_path, '--out-dir', folder,
                       '--statistics', stats, '--json', '--release', '--log-limit', '16777216'], timeout=150)
        (folder / 'runner.log').write_text(log, encoding='utf-8')
    d = json.loads(stats.read_text(encoding='utf-8'))
    side = 'team' + candidate_side
    other = 'team' + ('B' if candidate_side == 'A' else 'A')
    scores = {x['team']: int(x['submittedGems']) for x in d['teams']}
    faults = d['diagnostics']['botFaults'][side]
    fuel = sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == side)
    cs = [c for c in d['champions'] if c['team'] == side]
    return dict(folder=str(folder), map=Path(map_path).stem, side=candidate_side,
                win=float(d['match']['outcome'] == side) if d['match']['outcome'] in (side, other) else 0.5,
                gems=scores[side], opponent_gems=scores[other], faults=faults, fuel=fuel,
                deaths=sum(int(c['metrics']['deaths']) for c in cs),
                gold=sum(int(c['metrics']['earnedGold']) for c in cs),
                collected=sum(int(c['metrics']['collectedGems']) for c in cs),
                rounds=d['match']['roundsStarted'], summary=d)

def run_jobs(jobs, workers):
    results = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(match, **j): j for j in jobs}
        for f in cf.as_completed(futures):
            try: results.append(f.result())
            except Exception as exc:
                event('match_failure', error=str(exc), folder=str(futures[f]['folder']))
                # Retry only incomplete jobs; successful deterministic games are never counted twice.
                job = futures[f]
                for attempt in range(2):
                    try:
                        time.sleep(0.5); results.append(match(**job)); break
                    except Exception:
                        if attempt == 1: raise
    return results

def timelines(d, side):
    out = {}
    for t in d['championTimelines']:
        owner = t['owner']
        if owner['team'] != 'team' + side or t['metric'] not in ('collectedGems', 'earnedGold', 'deaths', 'submittedGems'): continue
        arr = np.repeat(np.array([float(r['value']) for r in t['runs']]), [r['duration'] for r in t['runs']])
        out[owner['id'], t['metric']] = arr
    return out

def value_at(t, champion, metric, rnd):
    a = t.get((champion, metric))
    if a is None or not len(a): return 0.0
    return float(a[min(max(0, rnd), len(a) - 1)])

def training_samples(results):
    all_samples = []; map_feats = {}
    for result in results:
        if result['faults']: continue
        records, feat = bundle_records(result['folder'], result['side'])
        if feat: map_feats[result['map'], result['side']] = feat
        t = timelines(result['summary'], result['side'])
        by_champ = defaultdict(list)
        for row in records: by_champ[row['champion']].append(row)
        for champion, rows in by_champ.items():
            rows.sort(key=lambda r: r['round'])
            total = 0
            for i in reversed(range(len(rows))):
                row = rows[i]; rnd = row['round']
                nxt = rows[i + 1]['round'] if i + 1 < len(rows) else result['rounds']
                def delta(metric): return value_at(t, champion, metric, nxt) - value_at(t, champion, metric, rnd)
                # Dense economy rewards plus team outcome, with real deaths penalized.
                reward = (delta('collectedGems') + 0.025 * delta('earnedGold')
                          + 0.25 * delta('submittedGems') - 30 * delta('deaths')) / 50
                if i == len(rows) - 1:
                    reward += (result['win'] - 0.5) + (result['gems'] - result['opponent_gems']) / 2000
                total = reward + (0.98 ** (max(1, nxt - rnd) / 25)) * total
                all_samples.append((row, float(np.clip(total, -20, 20))))
    return all_samples, map_feats

def ppo_update(policy, critic, optimizer, samples):
    if len(samples) < 32: raise ValueError(f'Insufficient decision records: {len(samples)}')
    x = torch.tensor(np.stack([r['obs'] for r, _ in samples]), device=DEVICE)
    n = torch.tensor([r['n'] for r, _ in samples], device=DEVICE)
    action = torch.tensor([r['pick'] for r, _ in samples], device=DEVICE)
    old = torch.tensor([r['logp'] for r, _ in samples], device=DEVICE)
    returns = torch.tensor([v for _, v in samples], device=DEVICE)
    with torch.no_grad():
        exact = torch.distributions.Categorical(logits=policy(x, n)).log_prob(action)
        parity = float((exact - old).abs().max())
        if parity > 0.002: raise ValueError(f'C++ / Torch policy probability mismatch: {parity}')
        advantage = returns - critic(x)
        advantage = (advantage - advantage.mean()) / advantage.std().clamp(min=0.05)
    metrics = {}; stop = False
    for epoch in range(8):
        for idx in torch.randperm(len(x), device=DEVICE).split(512):
            dist = torch.distributions.Categorical(logits=policy(x[idx], n[idx]))
            logp = dist.log_prob(action[idx]); ratio = (logp - old[idx]).exp()
            actor_loss = -torch.minimum(ratio * advantage[idx], ratio.clamp(0.8, 1.2) * advantage[idx]).mean()
            critic_loss = nn.functional.smooth_l1_loss(critic(x[idx]), returns[idx])
            entropy = dist.entropy().mean()
            regularize = policy.residual(x[idx]).square().mean()
            loss = actor_loss + 0.5 * critic_loss - 0.005 * entropy + 0.001 * regularize
            optimizer.zero_grad(); loss.backward()
            nn.utils.clip_grad_norm_(list(policy.parameters()) + list(critic.parameters()), 0.5)
            optimizer.step()
            with torch.no_grad(): kl = float(((ratio - 1) - (logp - old[idx])).mean())
            metrics = dict(loss=float(loss.detach()), actor=float(actor_loss.detach()), critic=float(critic_loss.detach()),
                           entropy=float(entropy.detach()), kl=kl, epoch=epoch + 1)
            if kl > 0.035: stop = True; break
        if stop: break
    return dict(samples=len(samples), cpp_torch_max_logp_error=parity, **metrics)

def recent_data():
    matches = {}
    for p in [ROOT / 'recent-matches.json', *sorted((ROOT / 'data/recent').glob('*.json'))]:
        try: data = json.loads(p.read_text(encoding='utf-8-sig'))
        except (ValueError, OSError): continue
        for m in data.get('matches', []):
            created = dt.datetime.fromisoformat(m['createdAt'].replace('Z', '+00:00'))
            if created >= NOW - dt.timedelta(hours=24) and m.get('endReason') != 'forfeit' and m.get('status') == 'finished':
                matches[m['matchId']] = m
    rows = sorted(matches.values(), key=lambda x: x['createdAt'])
    write(ROOT / 'data/recent-filtered.json', rows)
    return rows

def make_proxy(rows, index, workers):
    counts = Counter()
    for m in rows:
        for t in m['teams']:
            if t['result'] == 'win':
                for k, c in enumerate(t.get('draftPicks', [])): counts[int(c)] += 1 / (k + 1)
    order = [c for c, _ in counts.most_common()] + [c for c in range(12) if c not in counts]
    if index == 1:
        # A second distinct recent composition starts with the second most popular champion.
        order = order[1:2] + order[:1] + order[2:]
    src = ROOT / f'proxies/recent-meta-{index}/src'
    shutil.copytree(ROOT / 'baseline/src', src, dirs_exist_ok=True)
    p = src / 'draft.cpp'; s = p.read_text(encoding='utf-8')
    marker = 'bool ml_draft_pick(std::uint32_t size) {'
    inject = '\n    { constexpr int order[12] = {' + ','.join(map(str, order)) + '''};
      const auto chosen = bc::draft::current_draft(team::ally);
      for (int c : order) {
          bool used = false;
          for (auto v : chosen) used = used || static_cast<int>(v) == c;
          if (!used) { bc::draft::pick(static_cast<cd>(c)); return true; }
      }
    }
'''
    assert marker in s; p.write_text(s.replace(marker, marker + inject, 1), encoding='utf-8')
    output = ROOT / f'builds/recent-meta-proxy-{index}.wasm'
    compile_bot(src, output, workers)
    write(output.with_suffix('.json'), dict(kind='local baseline gameplay proxy, not the real top-team executable',
                                          champion_order=order, recent_match_count=len(rows), sha256=sha(output)))
    return output

class DraftNet(nn.Module):
    def __init__(self):
        super().__init__(); self.hidden = nn.Linear(53, 64); self.head = nn.Linear(64, 1)
    def forward(self, x): return self.head(torch.tanh(self.hidden(x))).squeeze(-1)

def load_draft(path):
    s = Path(path).read_text(encoding='utf-8'); model = DraftNet().to(DEVICE)
    def arr(name):
        m = re.search(r'\b' + name + r'\s*(?:\[[^\]]*\])?\s*=\s*(\{[^}]+\}|[^;]+);', s)
        return np.array([float(x) for x in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', m[1])], dtype=np.float32)
    with torch.no_grad():
        model.hidden.weight.copy_(torch.tensor(arr('W1').reshape(53, 64).T, device=DEVICE))
        model.hidden.bias.copy_(torch.tensor(arr('b1'), device=DEVICE))
        model.head.weight.copy_(torch.tensor(arr('w2')[None, :], device=DEVICE))
        model.head.bias.copy_(torch.tensor(arr('b2'), device=DEVICE))
    return model

def export_draft(model, path):
    state = {k: v.detach().cpu().numpy() for k, v in model.state_dict().items()}
    def literal(v):
        s = format(float(v), '.9g'); return s + ('.0f' if '.' not in s and 'e' not in s else 'f')
    def line(name, a):
        a = a.flatten(); return f'inline constexpr float {name}[{len(a)}] = {{' + ','.join(literal(v) for v in a) + '};\n'
    text = '// Fine-tuned on recent ranked games by tools/train.py.\n#pragma once\nnamespace draft_net {\ninline constexpr int kIn=53, kHid=64;\n'
    text += line('W1', state['hidden.weight'].T) + line('b1', state['hidden.bias']) + line('w2', state['head.weight'])
    text += 'inline constexpr float b2 = ' + literal(state['head.bias'][0]) + ';\n}\n'
    Path(path).write_text(text, encoding='utf-8')

def fit_recent_draft(rows, map_features):
    data = []; groups = sorted({m['groupId'] for m in rows}, key=lambda g: max(m['createdAt'] for m in rows if m['groupId'] == g))
    hold = set(groups[max(1, int(0.8 * len(groups))):])
    for m in rows:
        map_name = m['map'].replace('_', '-')
        for t in m['teams']:
            side = t['side'].upper(); feat = map_features.get((map_name, side))
            if feat is None: continue
            theirs = next(x for x in m['teams'] if x['side'] != t['side'])
            ours, opp = t.get('draftPicks', []), theirs.get('draftPicks', [])
            size = len(ours)
            if size not in (3, 4, 5) or len(opp) != size or t['result'] not in ('win', 'loss'): continue
            # Match-derived full-composition labels. Side is encoded using its map features.
            x = np.zeros(53, dtype=np.float32); x[:16] = feat
            for c in ours: x[16 + int(c)] = 1
            for c in opp: x[28 + int(c)] = 1
            x[40 + size - 3] = 1; x[43] = float(side == 'A'); x[44] = 1
            data.append((x, float(t['result'] == 'win'), m['groupId'] in hold, m['matchId']))
    model = load_draft(ROOT / 'baseline/src/draft_net.h')
    if len(data) < 100 or len(hold) < 3:
        write(ROOT / 'draft-training.json', dict(status='not enough recent grouped data; original network retained', examples=len(data)))
        return False
    x = torch.tensor(np.stack([r[0] for r in data]), device=DEVICE)
    y = torch.tensor([r[1] for r in data], device=DEVICE)
    test = torch.tensor([r[2] for r in data], device=DEVICE, dtype=torch.bool)
    original = [p.detach().clone() for p in model.parameters()]
    opt = torch.optim.AdamW(model.parameters(), lr=0.0003, weight_decay=0.01)
    def metrics(mask):
        with torch.no_grad():
            z = model(x[mask]); return dict(loss=float(nn.functional.binary_cross_entropy_with_logits(z, y[mask])),
                                            accuracy=float(((z > 0) == (y[mask] > 0)).float().mean()))
    before = metrics(test); best = copy.deepcopy(model.state_dict()); best_loss = before['loss']; best_epoch = 0
    for epoch in range(250):
        pred = model(x[~test]); loss = nn.functional.binary_cross_entropy_with_logits(pred, y[~test])
        anchor = sum((p - p0).square().mean() for p, p0 in zip(model.parameters(), original))
        loss = loss + 2 * anchor
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1); opt.step()
        score = metrics(test)
        if score['loss'] < best_loss:
            best_loss = score['loss']; best = copy.deepcopy(model.state_dict()); best_epoch = epoch + 1
    model.load_state_dict(best)
    export_draft(model, ROOT / 'candidate/src/draft_net.h')
    torch.save(dict(model=model.state_dict(), baseline=before, holdout=metrics(test)), ROOT / 'checkpoints/recent-draft.pt')
    write(ROOT / 'draft-training.json', dict(examples=len(data), train_examples=int((~test).sum()),
          validation_examples=int(test.sum()), grouped_by='entire five-match group, temporal last 20% holdout',
          training_groups=[g for g in groups if g not in hold], validation_groups=sorted(hold),
          baseline=before, selected=metrics(test), epoch=best_epoch, matches=len({r[3] for r in data}),
          warning='Observational win prediction is confounded by team strength; engine evaluation is required.'))
    return best_epoch > 0

def summarize(results):
    return dict(games=len(results), wins=sum(r['win'] for r in results),
                win_rate=float(np.mean([r['win'] for r in results])) if results else 0,
                mean_gem_margin=float(np.mean([r['gems'] - r['opponent_gems'] for r in results])) if results else 0,
                faults=sum(r['faults'] for r in results), fuel=sum(r['fuel'] for r in results),
                collected=sum(r['collected'] for r in results), deaths=sum(r['deaths'] for r in results))

def evaluate_artifact(wasm, label, maps, opponents, workers):
    jobs = []
    for mi, m in enumerate(maps):
        for oi, opp in enumerate(opponents):
            for side in ('A', 'B'):
                a, b = (wasm, opp) if side == 'A' else (opp, wasm)
                jobs.append(dict(a=a, b=b, map_path=m, candidate_side=side,
                                 folder=ROOT / f'runs/{label}/m{mi:02d}-o{oi}-{side}'))
    results = run_jobs(jobs, workers)
    write(ROOT / f'evaluation/{label}.json', dict(summary=summarize(results),
          rows=[{k: v for k, v in r.items() if k != 'summary'} for r in results]))
    return summarize(results), wasm

def evaluate(policy, label, maps, opponents, workers):
    export_weights(policy, False, SEED)
    wasm = compile_bot(ROOT / 'candidate/src', ROOT / f'builds/{label}.wasm', workers)
    return evaluate_artifact(wasm, label, maps, opponents, workers)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--minutes', type=float, default=60)
    ap.add_argument('--workers', type=int, default=min(os.cpu_count() or 4, 20))
    ap.add_argument('--smoke', action='store_true'); args = ap.parse_args()
    for name in ('checkpoints', 'evaluation', 'data', 'release'): (ROOT / name).mkdir(exist_ok=True)
    policy = Policy().to(DEVICE); critic = Critic().to(DEVICE)
    optimizer = torch.optim.Adam(list(policy.parameters()) + list(critic.parameters()), lr=0.0004)
    event('initializing', device=DEVICE, gpu=torch.cuda.get_device_name() if DEVICE == 'cuda' else None,
          workers=args.workers, minutes=args.minutes, cli=command([CLI, '--version']).strip())
    rows = recent_data()
    event('recent_data', matches=len(rows), earliest=rows[0]['createdAt'] if rows else None,
          latest=rows[-1]['createdAt'] if rows else None, max_age_hours=24)
    maps = sorted((ARENA / 'maps').glob('*.map26a'))
    rng = random.Random(SEED); rng.shuffle(maps)
    final_maps, select_maps, train_maps = maps[:8], maps[8:14], maps[14:]
    write(ROOT / 'protocol.json', dict(seed=SEED, training_maps=[str(m) for m in train_maps],
          selection_maps=[str(m) for m in select_maps], final_holdout_maps=[str(m) for m in final_maps],
          holdout_rule='No optimization or model selection from final_holdout_maps. Final evaluation once.',
          recent_max_age_hours=24, opponent_scope='original bot plus explicitly labeled baseline-gameplay proxies',
          fuel='official release default, no fuel increase', requested_minutes=args.minutes,
          actor='18 inputs -> 16 tanh units -> bounded scalar residual over original camp ranking',
          optimizer='clipped PPO with critic, entropy bonus, gradient clipping, policy parity check'))
    export_weights(policy, True, SEED)
    initial = compile_bot(ROOT / 'candidate/src', ROOT / 'builds/training-initial.wasm', args.workers)
    jobs = [dict(a=initial, b=initial, map_path=m, folder=ROOT / f'runs/map-features/{m.stem}') for m in maps]
    results = run_jobs(jobs, args.workers)
    map_features = {}
    for r in results:
        for side in ('A', 'B'):
            _, feat = bundle_records(r['folder'], side)
            if feat: map_features[r['map'], side] = feat
    write(ROOT / 'data/map-features.json', {m + '/' + side: f for (m, side), f in map_features.items()})
    event('feature_collection', maps=len(results), features=len(map_features), **summarize(results))
    if args.smoke:
        samples, _ = training_samples(results)
        event('smoke_complete', **ppo_update(policy, critic, optimizer, samples))
        torch.save(policy.state_dict(), ROOT / 'checkpoints/smoke-policy.pt')
        return
    training_map_names = {m.stem for m in train_maps}
    fit_recent_draft(rows, {k: v for k, v in map_features.items() if k[0] in training_map_names})
    event('draft_fit_complete', report=str(ROOT / 'draft-training.json'))
    opponents = [ROOT / 'builds/baseline.wasm']
    if rows:
        leader_path = ROOT / 'data/recent/rank1.json'
        leaders = json.loads(leader_path.read_text(encoding='utf-8-sig')).get('matches', []) if leader_path.exists() and leader_path.stat().st_size else rows
        opponents += [make_proxy(leaders, 0, args.workers), make_proxy(rows, 1, args.workers)]
    # Freeze the map-only baseline's selection result before updating the gameplay actor.
    initial_score, _ = evaluate(policy, 'selection-initial', select_maps, opponents, args.workers)
    best_score = initial_score; best_state = copy.deepcopy(policy.state_dict()); best_label = 'selection-initial'
    trained_score = None; trained_state = None; trained_label = None
    torch.save(dict(policy=best_state, critic=critic.state_dict()), ROOT / 'checkpoints/best.pt')
    start = time.monotonic(); deadline = start + args.minutes * 60
    event('training_started', deadline_utc=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=args.minutes)).isoformat(),
          baseline_selection=initial_score)
    iteration = 0; games = 0; decisions = 0
    while time.monotonic() < deadline - 120:
        iteration += 1; seed = SEED + iteration * 7919
        export_weights(policy, True, seed)
        wasm = compile_bot(ROOT / 'candidate/src', ROOT / f'builds/train-{iteration:04d}.wasm', args.workers)
        chosen_maps = rng.sample(train_maps, min(12, len(train_maps)))
        jobs = []
        for mi, m in enumerate(chosen_maps):
            opp = opponents[(mi + iteration) % len(opponents)]
            for side in ('A', 'B'):
                a, b = (wasm, opp) if side == 'A' else (opp, wasm)
                jobs.append(dict(a=a, b=b, map_path=m, candidate_side=side,
                                 folder=ROOT / f'runs/train-{iteration:04d}/m{mi:02d}-{side}'))
        result = run_jobs(jobs, args.workers)
        samples, _ = training_samples(result)
        update = ppo_update(policy, critic, optimizer, samples)
        games += len(result); decisions += len(samples)
        checkpoint = dict(iteration=iteration, policy=policy.state_dict(), critic=critic.state_dict(),
                          optimizer=optimizer.state_dict(), games=games, decisions=decisions)
        torch.save(checkpoint, ROOT / 'checkpoints/latest.pt')
        write(ROOT / f'checkpoints/train-{iteration:04d}.json', dict(**update, **summarize(result)))
        event('training_update', iteration=iteration, games=games, decisions=decisions,
              elapsed_seconds=round(time.monotonic() - start), **update, rollout=summarize(result))
        if iteration % 4 == 0 or time.monotonic() >= deadline - 180:
            label = f'selection-{iteration:04d}'
            score, _ = evaluate(policy, label, select_maps, opponents, args.workers)
            rank = lambda v: (v['faults'] == 0, v['win_rate'], v['mean_gem_margin'])
            if score['games'] == initial_score['games'] and (trained_score is None or rank(score) > rank(trained_score)):
                trained_state = copy.deepcopy(policy.state_dict()); trained_score = score; trained_label = label
                torch.save(dict(policy=trained_state, selection=score, iteration=iteration), ROOT / 'checkpoints/best-trained.pt')
            if score['games'] == initial_score['games'] and rank(score) > rank(best_score):
                best_state = copy.deepcopy(policy.state_dict()); best_score = score; best_label = label
                torch.save(dict(policy=best_state, critic=critic.state_dict(), iteration=iteration,
                                selection=score), ROOT / 'checkpoints/best.pt')
            event('selection', iteration=iteration, score=score, best=best_label, best_score=best_score)
    # Always preserve a genuinely trained gameplay candidate, even if the unchanged
    # policy was stronger on the selection set. Promotion is a separate reported decision.
    if trained_state is not None:
        best_state, best_score, best_label = trained_state, trained_score, trained_label
    policy.load_state_dict(best_state)
    event('final_validation', iteration=iteration, games=games, decisions=decisions, selected=best_label)
    final, final_wasm = evaluate(policy, 'final-holdout', final_maps, opponents, args.workers)
    # Paired, same-map baseline comparison is separate from policy selection.
    base_final, _ = evaluate_artifact(ROOT / 'builds/baseline.wasm', 'original-holdout', final_maps, opponents, args.workers)
    export_weights(policy, False, SEED)
    release_src = ROOT / 'release/bot_neural/src'
    shutil.copytree(ROOT / 'candidate/src', release_src, dirs_exist_ok=True)
    shutil.copyfile(final_wasm, ROOT / 'release/bot_neural.wasm')
    with zipfile.ZipFile(ROOT / 'release/bot_neural.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(release_src.glob('*')): z.write(p, 'src/' + p.name)
    weights = export_weights(policy, False, SEED)
    report = dict(status='complete', duration_seconds=round(time.monotonic() - start), requested_minutes=args.minutes,
                  iterations=iteration, training_games=games, training_decisions=decisions,
                  selected_checkpoint=best_label, selection=best_score, final_holdout=final,
                  original_holdout=base_final, recent_matches=len(rows), gpu=torch.cuda.get_device_name() if DEVICE == 'cuda' else None,
                  local_improvement=bool(final['win_rate'] > base_final['win_rate'] and final['faults'] == 0),
                  nonzero_gameplay_weights=int(np.count_nonzero(weights)), workers=args.workers,
                  artifact=str(ROOT / 'release/bot_neural.zip'), source_sha256=sha(ROOT / 'release/bot_neural.zip'),
                  wasm_sha256=sha(ROOT / 'release/bot_neural.wasm'),
                  limitations=['Historical draft outcomes are observational, not causal labels.',
                               'Recent-meta opponents are local proxies, not downloaded top-team binaries.',
                               'Final holdout is local and does not establish a ladder rating.',
                               'Training happens offline; competition bot runs the fixed learned weights.'])
    write(ROOT / 'report.json', report); event('complete', **report)

if __name__ == '__main__':
    try: main()
    except Exception:
        event('failed', error=traceback.format_exc()); raise
