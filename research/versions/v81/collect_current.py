"""Read current top-12 match listings and download one recent ranked replay per team. Never queues or activates."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
CLI=ROOT/'tools/vendor/cambc.exe'
teams=json.loads((ROOT/'research/v75/current_ladder_20261028.json').read_text())['teams'][:12]
out=ROOT/'artifacts/local-only/v81-current'; out.mkdir(exist_ok=True)

def one(t):
    listing=out/f'{t["teamId"]}-listing.json'
    if listing.exists(): d=json.loads(listing.read_text())
    else:
        for attempt in range(3):
            p=subprocess.run([str(CLI),'matches','list','--team',t['teamId'],'--kind','ranked','--limit','4','--json'],
                             capture_output=True,text=True,encoding='utf8',timeout=120)
            if p.returncode==0: break
            if attempt==2: raise RuntimeError(p.stdout+' '+p.stderr)
            time.sleep(5)
        d=json.loads(p.stdout)
        listing.write_text(json.dumps(d,indent=1)+'\n')
    m=d['matches'][0]
    folder=out/m['matchId']; folder.mkdir(exist_ok=True)
    for kind,name in [('download','replay.repl26a'),('summary','summary.json')]:
        dest=folder/name
        if not dest.exists():
            cmd=[str(CLI),'matches',kind,m['matchId'],'--output',str(dest)]
            if kind=='summary': cmd.append('--json')
            for attempt in range(3):
                result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=120)
                if result.returncode==0 and dest.exists(): break
                if attempt==2: raise RuntimeError(f'{m["matchId"]}: {result.stdout} {result.stderr}')
                time.sleep(3)
    return dict(team=t['name'],rank=t['rank'],match=m)

with ThreadPoolExecutor(1) as ex:
    rows=list(ex.map(one,teams))
(ROOT/'research/v81/current_top_matches.json').write_text(json.dumps(rows,indent=1)+'\n')
print('Read-only collection complete:',len(rows),'team selections;',len({r['match']['matchId'] for r in rows}),'distinct games')
