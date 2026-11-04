"""JNP3 carries consumed Q9 h0 followed by diagnostic Q8 h1.

Reject JNP2 rather than relabeling frozen-h1 training data as upper-trunk data.
"""
import numpy as np
from command_rows import read as read_query

def read(raw):
    converted=[]; h0s=[]
    for line in raw.replace(b'\0',b'').splitlines():
        q=line.split()
        if not q:continue
        if q[0]==b'JNP3':
            if len(q)!=21:raise ValueError('JNP3 token count')
            h0=np.frombuffer(bytes.fromhex(q[20].decode()),dtype='<i2').copy()
            if h0.shape!=(64,) or (h0<0).any():raise ValueError('JNP3 consumed h0')
            h0s.append(h0);converted.append(b'JNP2 '+b' '.join(q[1:20]))
        elif q[0] in (b'JND1',b'CNK'):converted.append(line)
        else:raise ValueError('unknown or incompatible upper-trunk row')
    rows,assoc=read_query(b'\n'.join(converted))
    if len(rows)!=len(h0s):raise ValueError('JNP3 association')
    for row,h0 in zip(rows,h0s):row['h0']=h0
    return rows,assoc
