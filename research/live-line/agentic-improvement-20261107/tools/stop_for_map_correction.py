from pathlib import Path
import json
import psutil
import sys
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
sys.path.insert(0,str(BASE/'autonomy'))
from store import save, now
WD=BASE/'training/runs/bounded-delivery-retune-v1'
assert not (WD/'frozen-finalists.json').exists()
assert not any((BASE/'autonomy/data/benchmarks'/('bounded-delivery-retune-20261107-'+x)).exists() for x in ('final_a','final_b','published'))
runtime=json.loads((WD/'runtime.json').read_text(encoding='utf-8'))
assert runtime['status']=='running' and runtime['pid']==4928
owner=psutil.Process(runtime['pid']);assert any('bounded_delivery_retune.py' in s for s in owner.cmdline())
assert Path(owner.cwd()).resolve()==BASE.resolve()
folder=WD/'published-map-correction-20261108';folder.mkdir(exist_ok=True)
save(folder/'owner-before-stop.json',{'at':now(),'pid':owner.pid,'birth':owner.create_time(),'command':owner.cmdline(),'children':[{'pid':c.pid,'birth':c.create_time(),'command':c.cmdline()} for c in owner.children(recursive=True)]})
marker=BASE/'autonomy/STOP';assert not marker.exists()
marker.write_text('Internal maintenance: correct final published-map contamination before any final game. Not user pause.\n',encoding='utf-8')
print('Requested owned runner stop for prospective final-map correction; saved all completed games')
