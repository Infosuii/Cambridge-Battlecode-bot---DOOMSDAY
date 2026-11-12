"""Run the SDK-free core invariant suite using the pinned WASI compiler and Node.

This exercises Wasm C++ arithmetic/logic, not the host platform ABI. Native
tools/dz.py host remains available on devices with a C++20 native compiler.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
NODE="""import fs from 'node:fs';import{WASI}from'node:wasi';const wasi=new WASI({version:'preview1',args:[],env:{}});const{instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[1]),wasi.getImportObject());wasi.start(instance);"""


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',type=Path,default=Path(os.environ.get('LOCALAPPDATA',''))/'cambc/wasi-sdk-33')
    p.add_argument('--node',default=shutil.which('node'));p.add_argument('--name',required=True)
    a=p.parse_args()
    if not a.node or not a.name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in a.name):p.error('Node24 and a simple fresh name are required')
    out=ROOT/'artifacts/tmp/dz'/a.name;out.mkdir(parents=True,exist_ok=False)
    cxx=a.sdk/'bin/clang++.exe';sysroot=a.sdk/'share/wasi-sysroot'
    command=[str(cxx),'-std=c++20','-O2','-fwasm-exceptions','-mllvm','-wasm-use-legacy-eh=false','--no-wasm-opt',
             '-Wall','-Wextra','-Werror','-I',str(ROOT/'bots/dz/src'),'-isystem',str(sysroot/'include/wasm32-wasip1/eh/c++/v1'),
             '-L'+str(sysroot/'lib/wasm32-wasip1/eh'),'-lunwind',str(ROOT/'tests/dz/host/core_test.cpp'),'-o',str(out/'core_test.wasm')]
    compiled=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
    (out/'compile.log').write_text(compiled.stdout+compiled.stderr,newline='\n')
    compiled.check_returncode()
    tested=subprocess.run([a.node,'--no-warnings','--input-type=module','-e',NODE,str(out/'core_test.wasm')],capture_output=True,text=True,timeout=120)
    (out/'test.log').write_text(tested.stdout+tested.stderr,newline='\n');tested.check_returncode()
    report=dict(passed=True,scope='WASI core invariants; not native host ABI',command=command,
                compiler_sha256=hashlib.sha256(cxx.read_bytes()).hexdigest(),
                wasm_sha256=hashlib.sha256((out/'core_test.wasm').read_bytes()).hexdigest(),
                test_sha256=hashlib.sha256((ROOT/'tests/dz/host/core_test.cpp').read_bytes()).hexdigest(),stdout=tested.stdout)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');print(tested.stdout)


if __name__=='__main__':main()
