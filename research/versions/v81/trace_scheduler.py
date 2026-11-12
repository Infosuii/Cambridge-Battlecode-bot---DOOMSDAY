import collections
import json
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[2]
run='SCHED82D-auction'
for g in json.loads((root/'artifacts/evaluations/v67'/run/'games.json').read_text())['games']:
    if g['side']!='a':continue
    bundle=next((root/g['folder']).glob('*.repl26a'))
    with zipfile.ZipFile(bundle) as z:text=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8','replace')
    print(g['map'],g['folder'])
    lines=[x for x in text.splitlines() if x.startswith('SC ')]
    print('\n'.join(lines[:12]))
    print('at R50/100/150/200:', '\n'.join(x for x in lines if x.split()[1] in ('50','100','150','200')))
