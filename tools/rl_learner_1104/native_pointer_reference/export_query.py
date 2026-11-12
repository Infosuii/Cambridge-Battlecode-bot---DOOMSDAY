"""Export existing native target-query weights without changing inference code.
Updates float/out-major, float/input-major and Q16 arrays together. All other
header bytes must stay unchanged. Quantized-equivalent no-op preserves header.
"""
import hashlib,re
from pathlib import Path
import numpy as np,torch
NAMES=('kP_target_qW','kP_target_qb','kP_target_qW_T','kP_target_qW_TQ','kP_target_qbQ')
def pattern(name):return r'(inline constexpr (?:float|short) '+re.escape(name)+r'\[\] = \{)([^}]*)(\})'
def values(text,name,integer=False):
 m=re.search(pattern(name),text)
 if m is None:raise ValueError('missing native array '+name)
 return np.array([int(v.strip()) if integer else float.fromhex(v.strip().rstrip('f')) if '0x' in v else float(v.strip().rstrip('f')) for v in m.group(2).split(',')],dtype=np.int64 if integer else np.float32)
def export(source,model,destination):
 destination=Path(destination)
 if destination.exists():raise ValueError('refuse existing export')
 original=Path(source).read_text();before=original
 W=torch.round(model.query_w.detach()*16384).clamp(-32768,32767).cpu().numpy().astype(np.int64)
 b=torch.round(model.query_bias.detach()*128).clamp(-32768,32767).cpu().numpy().astype(np.int64)
 if W.shape!=(64,16) or b.shape!=(16,):raise ValueError('query shape')
 oldW=values(original,'kP_target_qW_TQ',True).reshape(64,16);oldb=values(original,'kP_target_qbQ',True)
 noop=np.array_equal(W,oldW) and np.array_equal(b,oldb)
 if not noop:
  repl={'kP_target_qW':(W.T/16384).flatten(),'kP_target_qb':b/128,
        'kP_target_qW_T':(W/16384).flatten(),'kP_target_qW_TQ':W.flatten(),'kP_target_qbQ':b}
  for name,v in repl.items():
   body=', '.join(str(int(x)) if name.endswith(('TQ','bQ')) else float(x).hex()+'f' for x in v)
   original,n=re.subn(pattern(name),lambda m:m.group(1)+body+m.group(3),original)
   if n!=1:raise ValueError('ambiguous array '+name)
 # Prove source changes are confined to the declared arrays.
 def stripped(s):
  for name in NAMES:s=re.sub(pattern(name),lambda m:m.group(1)+'<QUERY>'+m.group(3),s)
  return s
 if stripped(before)!=stripped(original):raise ValueError('unrelated header change')
 assert np.array_equal(values(original,'kP_target_qW_TQ',True).reshape(64,16),W)
 assert np.array_equal(values(original,'kP_target_qbQ',True),b)
 if not noop:
  assert np.array_equal(values(original,'kP_target_qW').reshape(16,64).T,np.asarray(W/16384,np.float32))
  assert np.array_equal(values(original,'kP_target_qW_T').reshape(64,16),np.asarray(W/16384,np.float32))
 destination.write_text(original)
 return dict(noop=noop,source_sha256=hashlib.sha256(before.encode()).hexdigest(),export_sha256=hashlib.sha256(original.encode()).hexdigest(),only_changed_arrays=list(NAMES) if not noop else [])
