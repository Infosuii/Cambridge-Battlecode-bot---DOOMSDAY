"""Audit every recorded passing assertion cell without rerunning engine games."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',default='research/dz/ASSERTION_AUDIT.json')
    args=parser.parse_args()
    cells=[]; failures=[]
    for folder in sorted((ROOT/'research/dz/runs').iterdir()):
        report=folder/'results.json'
        if not report.exists(): continue
        passing=[r for r in json.loads(report.read_text())['per_game'] if r.get('diagnostic_checks',{}).get('passed') is True]
        if not passing: continue
        with zipfile.ZipFile(folder/'evidence.zip') as archive:
            for row in passing:
                raw=archive.read(f"games/{row['map']}-{row['side']}/candidate.stdout")
                assertions=re.findall(r'CT_CHECK name=(\w+) pass=(\d+)\b',raw.decode('utf-8','replace'))
                if not assertions: continue
                cell=dict(run=folder.name,map=row['map'],side=row['side'],assertions=len(assertions),stdout_sha256=hashlib.sha256(raw).hexdigest())
                cells.append(cell)
                failed=[name for name,value in assertions if value!='1']
                if failed: failures.append(dict(**cell,failed=failed))
    result=dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        purpose='Check that a reported pass never masks an earlier failed assertion of the same name',
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        checked_passing_cells=len(cells),masked_failures=len(failures),failures=failures,cells=cells)
    (ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'{len(cells)} passing assertion cells audited; {len(failures)} masked failures')
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
