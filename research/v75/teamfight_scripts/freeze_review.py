"""Freeze the local research candidate for review. Does not submit or select a version."""
import hashlib
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[3]
out = root / 'artifacts/tmp/v67/v80-review'
out.mkdir(exist_ok=True)
sources = sorted((root / 'bots/v80/src').rglob('*'))
manifest = {}
with zipfile.ZipFile(out / 'source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sources:
        if p.is_file():
            name = p.relative_to(root / 'bots/v80').as_posix()
            content = p.read_bytes()
            manifest[name] = dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
            z.writestr(name, content)
wasm = root / 'artifacts/tmp/v67/v80-candidate.wasm'
tested = root / 'artifacts/evaluations/v67/V80PKG-v65/build/bot-s1.wasm'
assert wasm.read_bytes() == tested.read_bytes(), 'final build differs from tested candidate'
proof = dict(note='Local research candidate only. No submission or activation. Margins do not establish a gain.',
             switches=dict(V80_RECALL=1, V80_SHARE=0, V79_TF=0, V80_TREASURE=1, V80_RESET_FLEE=1, V80_CAST_FLEE=0),
             sources=manifest, source_files=len(manifest), source_bytes=sum(v['bytes'] for v in manifest.values()),
             wasm=str(wasm.relative_to(root)), wasm_sha256=hashlib.sha256(wasm.read_bytes()).hexdigest(),
             identical_to_tested_wasm=str(tested.relative_to(root)),
             runs=[f'V80PKG-{o}' for o in ('v65', 'v61', 'v58', 'proxy')])
(out / 'manifest.json').write_text(json.dumps(proof, indent=1) + '\n')
print(json.dumps({k:v for k,v in proof.items() if k != 'sources'}, indent=1))
