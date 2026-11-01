"""Read immutable DZ capsules into a compact, attributable lifecycle scoreboard."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile
from dz import ROOT, sample_at


def report(name):
    folder = ROOT / 'research/dz/runs' / name
    provenance = json.loads((folder/'provenance.json').read_text())
    result = json.loads((folder/'results.json').read_text())
    rows = []
    with zipfile.ZipFile(folder/'evidence.zip') as z:
        for cell in result['per_game']:
            prefix = f"games/{cell['map']}-{cell['side']}/"
            summary = json.loads(z.read(prefix+'summary.json'))
            team = 'team'+cell['side']
            events = []
            for series in summary['events']:
                if series['owner'].get('team') != team:
                    continue
                for e in series['entries']:
                    events.append(dict(kind=series['kind'], body=series['owner']['id'],
                        champion=series['owner'].get('name'), **e))
            events.sort(key=lambda e: int(e['timestamp']['ordinal']))
            body_cycles = []
            for body in summary['champions']:
                if body['team'] != team:
                    continue
                own = [e for e in events if e['body'] == body['id']]
                captures = [e for e in own if e['kind']=='gemCollection' and e['context']=='campGroup']
                banks = [e for e in own if e['kind']=='gemSubmission']
                purchases = [e for e in own if e['kind']=='buyItem']
                bank_after_capture = next((e for e in banks if any(float(c['value'])>0 and
                    c['timestamp']['ordinal']<e['timestamp']['ordinal'] for c in captures)), None)
                next_purchase = next((e for e in purchases if bank_after_capture and
                    e['timestamp']['ordinal']>bank_after_capture['timestamp']['ordinal']), None)
                returned = next((e for e in captures if next_purchase and
                    e['timestamp']['ordinal']>next_purchase['timestamp']['ordinal']), None)
                gear = Counter()
                for e in purchases:
                    gear[e['target']['name']] += int(e['value'])
                body_cycles.append(dict(body=body['id'],champion=body['name'],
                    captures=len(captures),banks=len(banks),purchases=len(purchases),
                    first_capture=captures[0] if captures else None,first_bank=banks[0] if banks else None,
                    verified_bank_after_camp_receipt=bank_after_capture,gear_purchased=dict(gear),
                    purchase_after_bank=next_purchase,return_receipt=returned,
                    last_capture_round=captures[-1]['timestamp']['round'] if captures else None,
                    complete_collect_bank_purchase_return=returned is not None,
                    final=body['metrics']))
            checkpoints = {}
            for r in (100,250):
                metrics = {}
                for key in ('earnedGold','spentGold','collectedGems','submittedGems','deaths'):
                    values = [sample_at(t['runs'],r) for t in summary['championTimelines']
                              if t['owner']['team']==team and t['metric']==key]
                    metrics[key] = sum(values) if values and all(v is not None for v in values) else None
                checkpoint_events = [e for e in events if e['timestamp']['round']<=r]
                metrics['captures'] = len({(e['timestamp']['round'],e['target']['id']) for e in checkpoint_events
                    if e['kind']=='gemCollection' and e['context']=='campGroup'})
                metrics['clears'] = sum(e['kind']=='campClear' for e in checkpoint_events)
                checkpoints[r] = metrics
            try:
                stdout = z.read(prefix+'candidate.stdout').decode('utf8','replace')
            except KeyError:
                stdout = ''
            times = re.findall(r'DZ_TIME round=(\d+) slot=(\d+) ((?:\d+ ){10}\d+)',stdout)
            rows.append(dict(**cell,early=checkpoints,bodies=body_cycles,
                captures=len({(e['timestamp']['round'],e['target']['id']) for e in events
                    if e['kind']=='gemCollection' and e['context']=='campGroup'}),
                clears=sum(e['kind']=='campClear' for e in events),
                task_accounting=times[-len(body_cycles):] if times else None,
                task_accounting_note='Trace-only per-body cumulative categories; untraced Home/idle rounds unmeasured',
                lifecycle_events=[e for e in events if e['kind'] in ('gemCollection','gemSubmission','buyItem','campClear') and e['timestamp']['round']<=250]))
    return dict(name=name,candidate_sha256=provenance['candidate_sha256'],
        opponent_sha256=provenance['opponent_sha256'],trace=provenance['trace'],source=provenance['source'],
        provenance_sha256=hashlib.sha256((folder/'provenance.json').read_bytes()).hexdigest(),cells=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--names',nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+',n) for n in args.names):
        p.error('Invalid run identifier')
    rows=[report(n) for n in args.names]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
    for row in rows:
        for c in row['cells']:
            print(row['name'],c['map'],c['side'], 'bank',c['banked'],'capture',c['captures'],
                'cycles',sum(b['complete_collect_bank_purchase_return'] for b in c['bodies']),
                'R250',c['early'][250])


if __name__=='__main__':
    main()
