"""Check the exported C++ decision tree against training-side inference on actual observation vectors."""
from pathlib import Path
import subprocess
import numpy as np

root=Path(__file__).resolve().parents[2];out=root/'artifacts/tmp/v67/intent83-check';out.mkdir(exist_ok=True)
source=out/'check.cpp';exe=out/'check.exe'
header=(root/'research/v81/intent_model.h').as_posix()
source.write_text(f'''#include <iostream>
#include "{header}"
int main(){{float f[33],p;while(std::cin>>f[0]){{for(int i=1;i<33;++i)std::cin>>f[i];int x=intent83::predict(f,p);std::cout<<x<<" "<<p<<"\\n";}}}}
''')
subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-O2','-static',str(source),'-o',str(exe)],check=True,capture_output=True)
d=np.load(root/'artifacts/tmp/v67/intent83_parity.npz');X=d['features']
text='\n'.join(' '.join(f'{float(x):.9g}' for x in row) for row in X)+'\n'
p=subprocess.run([str(exe)],input=text,text=True,capture_output=True,check=True)
result=np.loadtxt(p.stdout.splitlines());diff=int(np.count_nonzero(result[:,0]!=d['prediction']))
assert diff==0,(diff,len(X))
assert np.max(np.abs(result[:,1]-d['confidence']))<1e-5
print(len(X),'actual observation vectors: C++/NumPy class predictions identical; confidence error <1e-5')
