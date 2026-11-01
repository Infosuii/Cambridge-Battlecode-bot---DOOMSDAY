"""Build x1 once per switch (as dz.py --set would) and record the Wasm hash, so a sweep only plays switches that
change the binary. Flags whose build equals the base build are dead code in this tree (identical play by
construction); flags that share a hash with each other are played once.

usage: python tools/x1_flag_hashes.py SNAPSHOT_SRC SPEC.json OUT.json
"""
import hashlib, importlib.util, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('dz', ROOT/'tools/dz.py'); dz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dz)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build_with(src, flag, work):
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(src, work/'src')
    if flag:
        name, value = flag
        config = work/'src/x1_config.h'; text = config.read_text()
        text, count = re.subn(r'^#define '+name+r'\s+[^\n]+', '#define '+name+' '+value, text, flags=re.MULTILINE)
        if count == 0: text += '\n#define '+name+' '+value+'\n'
        config.write_text(text, encoding='utf-8', newline='\n')
    wasm = dz.build(work, work/'out.wasm')
    return sha(wasm)

def main():
    src, spec_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    flags = json.load(open(spec_path))['flags']
    result = json.load(open(out_path)) if out_path.exists() else {}
    work = ROOT/'artifacts/tmp/x1-flaghash'
    if 'BASE' not in result:
        result['BASE'] = build_with(src, None, work); out_path.write_text(json.dumps(result, indent=1))
    for f in flags:
        if f in result: continue
        result[f] = build_with(src, (f, '1'), work)
        print(f, result[f][:12], 'same-as-base' if result[f] == result['BASE'] else '', flush=True)
        out_path.write_text(json.dumps(result, indent=1))

if __name__ == '__main__': main()
