"""Strict staged-actor records: no malformed, missing, or duplicate rows discarded."""
import base64,zipfile
from pathlib import Path
import numpy as np

def stdout(path,side):
    path=Path(path)
    if path.is_dir():
        paths=list(path.glob('*.repl26a'));assert len(paths)==1;path=paths[0]
    with zipfile.ZipFile(path) as z:raw=z.read('team-'+side.lower()+'.stdout')
    assert len(raw)<67108864-8192,'Possible truncated policy records'
    return raw.replace(b'\0',b'\n').decode('utf-8','strict')

def parse_rows(txt):
    zs,qs,rows,seen={}, {}, [],set()
    counts={'NRZ':0,'NRQ':0,'NRL':0}
    for line in txt.splitlines():
        tag=line.split(' ',1)[0]
        if tag not in counts:continue
        counts[tag]+=1;q=line.split()
        if tag=='NRQ':
            assert len(q)==4,'Malformed NRQ'
            key=int(q[2]),int(q[1]);assert key not in qs and key not in seen,'Duplicate native decision'
            v=np.frombuffer(base64.b64decode(q[3],validate=True),dtype='<f4').copy()
            assert v.shape==(11,) and np.isfinite(v).all();qs[key]=v
        elif tag=='NRZ':
            assert len(q)==3,'Malformed NRZ'
            x=np.frombuffer(base64.b64decode(q[2],validate=True),dtype='<i2').copy();assert x.shape==(500,)
            key=int(x[47]),int(q[1]);assert key not in zs,'Repeated publication identity'
            zs[key]=x
        else:
            assert len(q)==9,'Malformed NRL'
            x=np.frombuffer(base64.b64decode(q[8],validate=True),dtype='<i2').copy();assert x.shape==(500,)
            me,r=int(x[47]),int(q[1]);key=me,r;zkey=me,int(q[6])
            assert key not in seen and key in qs,'Missing native probabilities / repeated decision'
            assert zkey in zs,'Missing published features'
            assert np.array_equal(x,zs[zkey]),'Staged input drift between published and sampled features'
            action=int(q[3]);bs=int(q[7]);assert 0<=action<=10 and 0<=bs<=10
            if action<10:assert x[248+action*22]==1,'Sampled an absent camp'
            assert not rows or all(old['r']<r for old in rows[-12:] if old['me']==me),'Decision order'
            rows.append(dict(r=r,sl=int(q[2]),ta=action,tlp=float(q[4]),chg=int(q[5]),x=x,xz=zs[zkey],me=me,bs=bs,q=qs.pop(key),zid=zkey[1]))
            seen.add(key)
    assert not qs and len(rows)==counts['NRQ']==counts['NRL'],'Unmatched or lost decisions'
    assert rows and counts['NRZ']>0,'No usable policy records'
    return rows
