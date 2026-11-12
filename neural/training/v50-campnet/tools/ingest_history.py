"""Sample completed 21 October summary archives and fit a separate draft model.

Does not alter the running PPO trainer, its source, checkpoints or frozen tests.
Only the authorized date is admitted. Historical training and validation use
the already-frozen training/selection maps; final holdout maps are excluded.
"""
import argparse, concurrent.futures as cf, copy, hashlib, json, os, re, subprocess, tempfile, time, zipfile
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from torch import nn
import train

ROOT = train.ROOT
DEST = ROOT / 'historical-training'
NAMES = {'Ryth':0, 'Vesper Vale':1, 'Vendetta':2, 'Cassi & Issac':3,
         'Cassi+Issac':3, 'Cassi and Issac':3, 'Stellar':4, 'Prism':5, 'Marcella':6,
         'Willow':7, 'Ren':8, 'Varg':9, 'Tavi':10, 'Heart of Ruin':11}

def completed_archives():
    found = {}
    dirs = [ROOT / 'data/bulk-2026-10-21', ROOT.parents[1],
            ROOT.parents[1] / '21 october matches', Path('C:/Users/omdha/Downloads')]
    for folder in dirs:
        if not folder.exists(): continue
        for p in folder.glob('summaries-2026-10-21-part*.zip'):
            m = re.fullmatch(r'summaries-2026-10-21-part(\d+)(?: \(\d+\))?\.zip', p.name)
            if m and zipfile.is_zipfile(p): found[int(m[1])] = p
    return sorted(found.items())

def decode(task):
    name, raw, archive = task
    match_id = re.search(r'[0-9a-f]{8}-[0-9a-f-]{27}', name)
    if not match_id: return None
    with tempfile.TemporaryDirectory(prefix='summary-', dir=DEST / 'tmp') as td:
        source = Path(td) / 'input.camstat'; source.write_bytes(raw)
        r = subprocess.run([str(train.CLI), 'summary', str(source)], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=30)
        if r.returncode: return dict(rejected='conversion_error', match_id=match_id[0])
        try: d = json.loads(r.stdout)
        except ValueError: return dict(rejected='invalid_json', match_id=match_id[0])
    match = d['match']
    # 1.0.2 is the 21 October balance patch. Its outcomes may pretrain
    # draft preferences, but never substitute for current-engine gameplay rewards.
    if match.get('engineVersion') not in ('1.0.2', '1.0.3'):
        return dict(rejected='engine_version_' + str(match.get('engineVersion')), match_id=match_id[0])
    if match['outcome'] not in ('teamA','teamB') or match['roundsStarted'] < 50:
        return dict(rejected='unfinished_or_forfeit', match_id=match_id[0])
    picks = {'teamA':[], 'teamB':[]}
    for row in d.get('roster', {}).get('draft', []):
        if row['champion'] not in NAMES: return dict(rejected='unknown_champion_' + row['champion'], match_id=match_id[0])
        picks[row['team']].append(NAMES[row['champion']])
    if len(picks['teamA']) not in (3,4,5) or len(picks['teamA']) != len(picks['teamB']):
        return dict(rejected='draft_size', match_id=match_id[0])
    return dict(match_id=match_id[0], source_day='2026-10-21', source_archive=archive,
                engine_version=match['engineVersion'], map_hash=match['mapHash'],
                outcome=match['outcome'], picks=picks,
                first=d['roster']['draft'][0]['team'], rounds=match['roundsStarted'])

def ingest(max_per_part, workers):
    DEST.mkdir(exist_ok=True); (DEST / 'tmp').mkdir(exist_ok=True)
    parts = completed_archives(); reports = []
    for number, path in parts:
        cache = DEST / f'part-{number:02d}-v2.jsonl'
        if cache.exists():
            reports.append(dict(part=number, source=str(path), cached=True)); continue
        with zipfile.ZipFile(path) as z:
            members = [i for i in z.infolist() if not i.is_dir() and re.search(r'[0-9a-f]{8}-[0-9a-f-]{27}', i.filename)]
            # UUID hashing gives a reproducible, distributed sample within each part.
            members.sort(key=lambda i: hashlib.sha256(i.filename.encode()).digest())
            chosen = members[:max_per_part]
            tasks = [(i.filename, z.read(i), path.name) for i in chosen]
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            rows = [r for r in ex.map(decode, tasks) if r]
        with cache.open('w', encoding='utf-8') as f:
            for r in rows: f.write(json.dumps(r) + '\n')
        report = dict(part=number, source=str(path), source_bytes=path.stat().st_size,
                      archive_entries=len(members), sampled=len(chosen), decoded=len(rows),
                      accepted=sum('rejected' not in r for r in rows),
                      rejections=dict(Counter(r['rejected'] for r in rows if 'rejected' in r)))
        train.write(DEST / f'part-{number:02d}-v2-receipt.json', report)
        reports.append(report); print(json.dumps(report), flush=True)
    train.write(DEST / 'ingestion.json', dict(allowed_date='2026-10-21', parts=reports,
                  sampling='fixed SHA-256 order of match UUID filenames, capped per part',
                  max_per_part=max_per_part, no_old_archives=True,
                  accepted_engines=['1.0.2','1.0.3'], scope='draft pretraining only; current-engine testing required'))
    rows = {}
    for p in DEST.glob('part-*-v2.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():
            r = json.loads(line)
            if 'rejected' not in r: rows[r['match_id']] = r
    return list(rows.values())

def fit(rows):
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    train_maps = {Path(p).stem for p in protocol['training_maps']}
    valid_maps = {Path(p).stem for p in protocol['selection_maps']}
    map_hash = {train.sha(p):Path(p).stem for p in map(Path, protocol['training_maps'] + protocol['selection_maps'])}
    feats = json.loads((ROOT / 'data/map-features.json').read_text())
    data = []; ids = set()
    def add(match_id, name, side, ours, theirs, first, outcome, weight):
        feature = feats.get(name + '/' + ('A' if side=='teamA' else 'B'))
        size = len(ours)
        if feature is None or size not in (3,4,5) or name not in train_maps | valid_maps: return
        label = float(outcome == side)
        for j in range(1, size + 1):
            x = np.zeros(53, np.float32); x[:16] = feature
            for c in ours[:j]: x[16+c] = 1
            seen = j-1 if first==side else j
            for c in theirs[:seen]: x[28+c] = 1
            x[40+size-3] = 1; x[43] = float(first==side); x[44] = j/size
            data.append((x,label,name in valid_maps,weight,match_id))
        ids.add(match_id)
    for r in rows:
        name = map_hash.get(r['map_hash'])
        if not name: continue
        for side, other in [('teamA','teamB'),('teamB','teamA')]:
            add(r['match_id'],name,side,r['picks'][side],r['picks'][other],r['first'],r['outcome'],0.5)
    # Today's higher-weight examples keep the 21 October archive from dominating
    # the smaller, more recent snapshot. No fabricated historical timestamps.
    recent = json.loads((ROOT / 'data/recent-filtered.json').read_text())
    for r in recent:
        name = r['map'].replace('_','-')
        for t in r['teams']:
            other = next(o for o in r['teams'] if o['side'] != t['side'])
            side = 'team' + t['side'].upper()
            outcome = side if t['result']=='win' else 'team' + other['side'].upper()
            add(r['matchId'],name,side,t.get('draftPicks',[]),other.get('draftPicks',[]),'teamA',outcome,2.0)
    if not rows or len(ids) < 200:
        train.write(DEST / 'fit.json',dict(status='waiting_for_more_compatible_21_october_data', accepted_historical_matches=len(rows),usable_matches=len(ids)))
        return
    x = torch.tensor(np.stack([r[0] for r in data]),device=train.DEVICE)
    y = torch.tensor([r[1] for r in data],device=train.DEVICE)
    valid = torch.tensor([r[2] for r in data],device=train.DEVICE,dtype=torch.bool)
    weight = torch.tensor([r[3] for r in data],device=train.DEVICE)
    model = train.load_draft(ROOT / 'baseline/src/draft_net.h')
    anchor = [p.detach().clone() for p in model.parameters()]
    opt = torch.optim.AdamW(model.parameters(),lr=0.0002,weight_decay=0.01)
    def metric():
        with torch.no_grad():
            z=model(x[valid]); loss=nn.functional.binary_cross_entropy_with_logits(z,y[valid],reduction='none')
            return dict(loss=float((loss*weight[valid]).sum()/weight[valid].sum()),accuracy=float(((z>0)==(y[valid]>0)).float().mean()))
    before=metric(); best=copy.deepcopy(model.state_dict()); best_loss=before['loss']; best_epoch=0
    indices=torch.where(~valid)[0]
    for epoch in range(100):
        for idx in indices[torch.randperm(len(indices),device=train.DEVICE)].split(2048):
            loss=nn.functional.binary_cross_entropy_with_logits(model(x[idx]),y[idx],reduction='none')
            loss=(loss*weight[idx]).sum()/weight[idx].sum()
            loss=loss+2*sum((p-p0).square().mean() for p,p0 in zip(model.parameters(),anchor))
            opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);opt.step()
        score=metric()
        if score['loss']<best_loss:
            best_loss=score['loss'];best_epoch=epoch+1;best=copy.deepcopy(model.state_dict())
    model.load_state_dict(best)
    train.export_draft(model, DEST / 'draft_net.h')
    torch.save(dict(model=best,optimizer=opt.state_dict(),epoch=best_epoch),DEST / 'draft.pt')
    train.write(DEST / 'fit.json',dict(status='trained' if best_epoch else 'original_retained',
         historical_matches=len(rows),usable_matches=len(ids),examples=len(data),
         training_examples=int((~valid).sum()),validation_examples=int(valid.sum()),
         split='frozen whole-map training / selection partition; final holdout maps excluded',
         baseline=before,selected=metric(),epoch=best_epoch,gpu=train.DEVICE,
         source_dates=['2026-10-21','2026-10-23'],historical_weight=0.5,today_weight=2,
         caveat='Observed win prediction includes team-skill confounding. Engine tests must precede promotion.'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--max-per-part',type=int,default=1000)
    parser.add_argument('--workers',type=int,default=8);parser.add_argument('--fit',action='store_true')
    args=parser.parse_args();DEST.mkdir(exist_ok=True);lock=DEST/'ingestion.lock'
    try:
        with lock.open('x',encoding='utf-8') as f: json.dump(dict(pid=os.getpid(),started=time.time()),f)
    except FileExistsError:
        print('Historical ingestion already running; lock retained.');raise SystemExit(0)
    try:
        rows=ingest(args.max_per_part,args.workers)
        print(json.dumps(dict(accepted_matches=len(rows),completed_parts=len(completed_archives()))),flush=True)
        if args.fit: fit(rows)
    finally:
        lock.unlink(missing_ok=True)
