"""Configure this clone from the byte-preserved recovery tree. Does not train, run games or submit anything.

Windows x64 is the exact saved environment. Use a standard Python3.12+ to run the archive restorer first.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def configure(restored,install_cli_cache=False):
    restored=Path(restored).resolve();workspace=restored/'battlecode_workspace'
    python=restored/'python_runtime/python.exe';native=restored/'native_compiler/bin/g++.exe'
    cli=restored/'official_cli_workspace/cambc.exe';cache=restored/'official_cli_runtime'
    original_env=workspace/'work/neural-gameplay/.venv/Lib/site-packages'
    for path in [python,native,cli,original_env]:
        if not path.exists():raise RuntimeError('Restore is incomplete: '+str(path))
    venv=ROOT/'.venv'
    if not (venv/'Scripts/python.exe').exists():
        subprocess.run([str(python),'-m','venv','--without-pip',str(venv)],check=True)
    # Preserve the exact installed packages offline, including CUDA Torch and its DLLs. No fitting or pip upgrade.
    site=venv/'Lib/site-packages';site.mkdir(parents=True,exist_ok=True)
    (site/'battlecode_recovered_packages.pth').write_text(str(original_env)+'\n',encoding='utf-8')
    paths=json.loads((ROOT/'config/paths.json').read_text())
    paths.update(cli=str(cli),arena=str(restored/'official_cli_workspace/arena'),
                 maps=str(restored/'official_cli_workspace/arena/maps'),sdk_cpp=str(ROOT/'sdk/cpp'),
                 wasi_sdk=str(cache/'wasi-sdk-33'),python=str(venv/'Scripts/python.exe'),native_cxx=str(native),
                 previous_experiment=str(workspace/'work/neural-gameplay'),
                 historical=dict(part1_zip=str(workspace/'summaries-2026-10-21-part1.zip'),
                                 parts_dir=str(workspace/'23102026')),
                 _note='Generated for this clone by tools/configure_recovery.py. Original machine paths remain in Git history/recovery snapshot.')
    (ROOT/'config/paths.json').write_text(json.dumps(paths,indent=2)+'\n',encoding='utf-8')
    if install_cli_cache:
        target=Path(os.environ['LOCALAPPDATA'])/'cambc'
        shutil.copytree(cache,target,dirs_exist_ok=True)
        paths['wasi_sdk']=str(target/'wasi-sdk-33')
        (ROOT/'config/paths.json').write_text(json.dumps(paths,indent=2)+'\n',encoding='utf-8')
    environment=(
        f"$env:PYTHONPATH='{str(ROOT/'python').replace(chr(39),chr(39)*2)}'\n"
        f"$env:NFS_GXX='{str(native).replace(chr(39),chr(39)*2)}'\n"
        f"$env:PATH='{str(native.parent).replace(chr(39),chr(39)*2)};'+$env:PATH\n"
        f"$env:TMP='{str(ROOT/'artifacts/tmp').replace(chr(39),chr(39)*2)}'\n"
        "$env:TEMP=$env:TMP\n")
    (ROOT/'artifacts/tmp').mkdir(parents=True,exist_ok=True)
    (venv/'recovery-env.ps1').write_text(environment,encoding='utf-8')
    print('Configured clone. In PowerShell run: . ./.venv/recovery-env.ps1')
    print('Python: '+paths['python'])
    if not install_cli_cache:print('Official CLI cache not installed; pass --install-cli-cache on the new laptop before official builds.')
    return paths

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--restored',default=str(ROOT/'recovery/restored'))
    ap.add_argument('--install-cli-cache',action='store_true')
    args=ap.parse_args();configure(args.restored,args.install_cli_cache)
