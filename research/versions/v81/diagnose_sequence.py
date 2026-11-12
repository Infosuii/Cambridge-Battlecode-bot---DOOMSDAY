import collections
import json
from pathlib import Path
import sys
import zipfile

root=Path(__file__).resolve().parents[2]
for run in sys.argv[1:]:
    C=collections.Counter();cost=[];types=collections.Counter()
    for g in json.loads((root/'artifacts/evaluations/v67'/run/'games.json').read_text())['games']:
        bundle=next((root/g['folder']).glob('*.repl26a'))
        with zipfile.ZipFile(bundle) as z: text=z.read(f'team-{g["side"]}.stdout').replace(b'\0',b'').decode('utf8','replace')
        for line in text.splitlines():
            if line.startswith('SQ '):
                p=line.split();C['executed']+=1;C['errors']+=int(p[8]);C['evaluated']+=int(p[4]);types[(p[5],p[6])]+=1
                if len(p)>10:cost.append(int(p[9]));C['crossed_round']+=int(p[10])!=0
    print(run,dict(C),'spell combinations',dict(types))
    if cost: print('fuel per executed plan: median',sorted(cost)[len(cost)//2],'max',max(cost))
