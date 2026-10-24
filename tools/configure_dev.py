"""Configure this clone using installed development tools. Training data stays on the original laptop."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]

def configure(python=None,native_cxx=None,cli=None):
    paths=json.loads((ROOT/'config/paths.json').read_text(encoding='utf-8'))
    compiler=native_cxx or os.environ.get('NFS_GXX') or shutil.which('g++')
    if not compiler and Path('C:/msys64/ucrt64/bin/g++.exe').exists():compiler='C:/msys64/ucrt64/bin/g++.exe'
    if not compiler:raise RuntimeError('Install native g++ (MSYS2 UCRT64 on Windows) or pass --native-cxx')
    official=cli or str(ROOT/'tools/vendor/cambc.exe')
    if os.name!='nt' and not cli:official=shutil.which('cambc')
    if not official or not Path(official).is_file():raise RuntimeError('Official cambc CLI missing; pass --cli')
    paths.update(python=str(Path(python or sys.executable).resolve()),native_cxx=str(Path(compiler).resolve()),
                 cli=str(Path(official).resolve()),sdk_cpp=str(ROOT/'sdk/cpp'),maps=str(ROOT/'maps/local-benchmarks'),
                 _note='Configured for this clone. Existing training/history paths are original-laptop-only; never guess a replacement training dataset.')
    if os.name=='nt':paths['wasi_sdk']=str(Path(os.environ['LOCALAPPDATA'])/'cambc/wasi-sdk-33')
    (ROOT/'config/paths.json').write_text(json.dumps(paths,indent=2)+'\n',encoding='utf-8')
    temp=ROOT/'artifacts/tmp';temp.mkdir(parents=True,exist_ok=True)
    def q(value):return str(value).replace("'","''")
    script=(f"$env:PYTHONPATH='{q(ROOT/'python')}'\n$env:NFS_GXX='{q(paths['native_cxx'])}'\n"
            f"$env:PATH='{q(Path(paths['native_cxx']).parent)};'+$env:PATH\n"
            f"$env:TMP='{q(temp)}'\n$env:TEMP=$env:TMP\n$env:PYTHONDONTWRITEBYTECODE='1'\n")
    (temp/'dev-env.ps1').write_text(script,encoding='utf-8')
    print(json.dumps({k:paths[k] for k in ['python','native_cxx','cli','maps','sdk_cpp']},indent=2))
    print('PowerShell: . ./artifacts/tmp/dev-env.ps1')
    return paths

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--python');p.add_argument('--native-cxx');p.add_argument('--cli')
    a=p.parse_args();configure(a.python,a.native_cxx,a.cli)
