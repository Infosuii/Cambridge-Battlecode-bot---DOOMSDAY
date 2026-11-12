"""Source provenance and native replay extraction for failed-game inspection."""
from pathlib import Path
import hashlib,json,zipfile
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[1]
expected=json.loads((OUT/'v92-source-blobs.json').read_text());checks={}
for name,digest in expected.items():
    data=(ROOT/'bots/v92/src'/name).read_bytes()
    lf=data.replace(b'\r\n',b'\n')
    candidates=[data,lf,lf.rstrip(b'\n')+b'\n',lf[:-1]]
    candidates += [x.replace(b'\n',b'\r\n') for x in candidates if b'\r' not in x]
    matches=[x for x in candidates if hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()==digest]
    assert matches,name
    checks[name]=dict(remote_blob=digest,local_sha256=hashlib.sha256(data).hexdigest(),
                      exact_bytes=data==matches[0],difference='none' if data==matches[0] else 'line endings / trailing newline only')
(OUT/'v92-verified.json').write_text(json.dumps(checks,indent=2)+'\n')
folder=OUT/'replay-audit';folder.mkdir(exist_ok=True)
for arm in ['off','parent','end500','cycle']:
    p=OUT/'games'/arm/'v92/01gold-rush-A'
    bundle=next(p.glob('*.repl26a'))
    with zipfile.ZipFile(bundle) as z:
        (folder/(arm+'.repl26a')).write_bytes(z.read('replay.repl26a'))
print('Verified all v92 source blobs; extracted four native replays.')
