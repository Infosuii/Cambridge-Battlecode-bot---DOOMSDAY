"""Pinned Agent2 export with lossless float32 literals and explicit lineage."""
import argparse,hashlib,json,os,sys
from pathlib import Path
LAB=Path(r'C:\projects\cambridge battlecode\battlecode part 2\jd-eval\a2\research\agent2-neural\rl_workspace\agent2\lab')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkpoint',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 if a.output.exists():raise SystemExit('Refusing to overwrite an export')
 source=LAB/'nn_export.py';raw=source.read_bytes()
 blob=hashlib.sha1(b'blob %d\0'%len(raw)+raw).hexdigest()
 if blob!='21bb3bd6ed049778b4bf4eb10084cd0fc380c1d1':raise SystemExit('Upstream exporter version mismatch')
 text=raw.decode();assert text.count('{x:.7e}f')==1
 text=text.replace('{x:.7e}f','{x:.9e}f')
 original='f = lambda t: ", ".join(f"{x:.9e}f" for x in t.detach().flatten().tolist())'
 assert original in text
 text=text.replace(original,'''EXPECTED=[]
def f(t):
    values=t.detach().flatten().tolist()
    EXPECTED.append(values)
    return ", ".join(f"{x:.9e}f" for x in values)
''')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 os.environ['NN_LAYOUT']='2';sys.path.insert(0,str(LAB));sys.argv=[str(source),str(a.checkpoint),'student',str(a.output)]
 # The original source is never modified; only the numeric literal format changes.
 namespace={'__file__':str(source),'__name__':'__main__'}
 exec(compile(text,str(source),'exec'),namespace)
 import numpy as np,re
 arrays=re.findall(r'inline constexpr float \w+\[\] = \{([^}]*)\};',a.output.read_text())
 expected=namespace['EXPECTED'];assert len(arrays)==len(expected)
 total=old_lossy=0
 for array,values in zip(arrays,expected):
    actual=np.array([float(x.strip().removesuffix('f')) for x in array.split(',')],np.float32)
    want=np.array(values,np.float32)
    assert np.array_equal(actual.view(np.uint32),want.view(np.uint32)), 'Header changed float32 bits'
    old=np.array([float(f'{x:.7e}') for x in values],np.float32)
    old_lossy+=int(np.count_nonzero(old.view(np.uint32)!=want.view(np.uint32)));total+=len(values)
 print(f'Verified {total} float32 literals exactly; old exporter altered {old_lossy}')
 a.output.with_suffix('.manifest.json').write_text(json.dumps(dict(checkpoint_sha256=sha(a.checkpoint),header_sha256=sha(a.output),upstream_blob=blob,layout=2,kind='student',float_format='.9e',exact_float32_literals=total,old_format_changed_literals=old_lossy,status='exported; requires golden and official-fuel evaluation'),indent=2))
if __name__=='__main__':main()
