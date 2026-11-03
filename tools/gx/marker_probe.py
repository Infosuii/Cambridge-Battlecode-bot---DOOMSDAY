"""Verify a diagnostic marker on both sides of complete local engine games."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('wasm',type=Path)
    p.add_argument('maps',type=Path)
    p.add_argument('scratch',type=Path)
    p.add_argument('layouts',nargs='+')
    p.add_argument('--expect',required=True)
    p.add_argument('--forbid',required=True)
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.scratch.mkdir(parents=True)
    cli = os.environ.get('DZ_CAMBC','cambc')
    wasm = a.wasm.resolve()
    expected, forbidden = (re.compile(x,re.M) for x in (a.expect,a.forbid))

    def run(name):
        layout = a.maps/(name+'.map26a')
        out = (a.scratch/name).resolve()
        out.mkdir()
        subprocess.run([cli,'run',str(wasm),str(wasm),'--map',str(layout.resolve()),
            '--out-dir',str(out),'--statistics',str(out/'summary.json'),'--json','--release'],
            capture_output=True,text=True,check=True,timeout=100)
        data=json.loads((out/'summary.json').read_text())
        faults=data['diagnostics']['botFaults']
        with zipfile.ZipFile(next(out.glob('*.repl26a'))) as z:
            logs=[z.read(f'team-{s}.stdout').replace(b'\0',b'').decode(errors='replace') for s in 'ab']
        counts=[len(expected.findall(log)) for log in logs]
        rejects=[forbidden.findall(log)[:20] for log in logs]
        if any(faults.values()) or not all(counts) or any(rejects):
            raise ValueError((name,counts,rejects,faults))
        return dict(layout=name,counts=counts,forbidden=rejects,faults=faults,
            map_sha256=sha256(layout.read_bytes()).hexdigest(),engine_sha256=data['match']['engineBuildHash'])

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows=list(pool.map(run,a.layouts))
    print(json.dumps(dict(wasm_sha256=sha256(wasm.read_bytes()).hexdigest(),
        expected=a.expect,forbidden=a.forbid,cells=rows),indent=2))


if __name__=='__main__':
    main()
