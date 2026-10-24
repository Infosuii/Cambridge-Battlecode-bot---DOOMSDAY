"""Read remote presence of committed recovery LFS objects without downloading data or printing signed URLs."""
import base64
import json
import os
from pathlib import Path
import subprocess
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
credentials=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=Infosuii\n\n',
                           capture_output=True,text=True,env=env,check=True)
c=dict(line.split('=',1) for line in credentials.stdout.splitlines() if '=' in line)
rows=json.loads(subprocess.check_output(['git','lfs','ls-files','--json'],cwd=ROOT,env=env,text=True))['files']
objects=[dict(oid=row['oid'],size=row['size']) for row in rows]
available=[];missing=[]
for start in range(0,len(objects),100):
    request=urllib.request.Request('https://github.com/Infosuii/neural-networkk-battlecode.git/info/lfs/objects/batch',
        data=json.dumps(dict(operation='download',transfers=['basic'],objects=objects[start:start+100])).encode(),
        headers={'Authorization':'Basic '+base64.b64encode((c.get('username','Infosuii')+':'+c['password']).encode()).decode(),
                 'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json',
                 'User-Agent':'battlecode-recovery'})
    with urllib.request.urlopen(request,timeout=60) as response:data=json.load(response)
    for item in data.get('objects',[]):
        (missing if item.get('error') or not item.get('actions',{}).get('download') else available).append(item['oid'])
print(json.dumps(dict(committed_lfs_objects=len(objects),remote_available=len(available),remote_missing=len(missing),
                      available_bytes=sum(x['size'] for x in objects if x['oid'] in available)),indent=2))
