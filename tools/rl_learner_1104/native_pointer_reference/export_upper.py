"""Export both existing upper trunk and query, with quantized no-op preservation."""
from pathlib import Path
import hashlib,re,tempfile
import numpy as np,torch
from export_query import export as export_query,pattern,values,NAMES as QUERY_NAMES
TRUNK_NAMES=('kT_W1','kT_b1','kT_W1_T','kT_W1_TQ','kT_b1Q')
def export(source,model,destination):
 destination=Path(destination)
 if destination.exists():raise ValueError('refuse existing export')
 before=Path(source).read_text()
 W=torch.round(model.trunk_w.detach()*16384).clamp(-32768,32767).cpu().numpy().astype(np.int64)
 b=torch.round(model.trunk_bias.detach()*256).clamp(-32768,32767).cpu().numpy().astype(np.int64)
 if W.shape!=(64,64) or b.shape!=(64,):raise ValueError('upper trunk shape')
 noop=np.array_equal(W,values(before,'kT_W1_TQ',True).reshape(64,64)) and np.array_equal(b,values(before,'kT_b1Q',True))
 with tempfile.TemporaryDirectory() as folder:
  tmp=Path(folder)/'query.h';qr=export_query(source,model,tmp);text=tmp.read_text()
 if not noop:
  repl={'kT_W1':(W.T/16384).flatten(),'kT_b1':b/256,'kT_W1_T':(W/16384).flatten(),'kT_W1_TQ':W.flatten(),'kT_b1Q':b}
  for name,v in repl.items():
   body=', '.join(str(int(x)) if name in ('kT_W1_TQ','kT_b1Q') else float(x).hex()+'f' for x in v)
   text,n=re.subn(pattern(name),lambda m:m.group(1)+body+m.group(3),text)
   if n!=1:raise ValueError('ambiguous upper array '+name)
 def stripped(s):
  for name in TRUNK_NAMES+QUERY_NAMES:s=re.sub(pattern(name),lambda m:m.group(1)+'<TRAINED>'+m.group(3),s)
  return s
 assert stripped(before)==stripped(text)
 assert np.array_equal(values(text,'kT_W1_TQ',True).reshape(64,64),W)
 assert np.array_equal(values(text,'kT_b1Q',True),b)
 if not noop:
  assert np.array_equal(values(text,'kT_W1').reshape(64,64).T,np.asarray(W/16384,np.float32))
  assert np.array_equal(values(text,'kT_W1_T').reshape(64,64),np.asarray(W/16384,np.float32))
 destination.write_text(text)
 return dict(noop=noop and qr['noop'],source_sha256=hashlib.sha256(before.encode()).hexdigest(),export_sha256=hashlib.sha256(text.encode()).hexdigest(),only_changed_arrays=([] if noop else list(TRUNK_NAMES))+qr['only_changed_arrays'])
