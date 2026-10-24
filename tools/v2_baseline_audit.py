"""Official release reproducibility diagnosis before v2 integration; no games/training."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from nfs import engine

def main():
    candidate=ROOT/'artifacts/tmp/teacher_exact_check/b99089fada190a97/teacher_exact.wasm'
    original=ROOT/'references/builds/original.wasm'
    copied=engine.make_bot_dir(ROOT/'references/original-src',ROOT/'artifacts/tmp/v2_original_rebuild')
    rebuilt=engine.official_build(copied,copied/'original.wasm')
    rows={}
    for name,p in [('original',original),('root_off',candidate),('original_rebuild',rebuilt)]:
        rows[name]=dict(sha256=engine.sha256(p),size=p.stat().st_size,sections=engine.wasm_sections(p))
    engine.write_json(ROOT/'evaluation/evidence/v2_baseline_audit.json',rows)
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
