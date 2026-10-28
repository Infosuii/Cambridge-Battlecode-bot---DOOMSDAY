"""Pack, verify, or restore the fixed offline evidence needed by DZ's next milestones.

Standard library only. No credentials, no network, no runtime edits. Restoration
never overwrites a different existing file. Contents are authenticated per-file.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'research/dz/supporting'
RUNS = ('SA-IDLE-v76', 'SA-P-base', 'SA-C-base')
def digest(data): return hashlib.sha256(data).hexdigest()
def allowed(name):
    p = PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name and (
        name.startswith('research/dz/supporting/deep-19109c4/') or
        any(name.startswith('artifacts/evaluations/v67/'+run+'/') for run in RUNS))

def pack():
    DEST.mkdir(parents=True, exist_ok=True)
    if (DEST/'manifest.json').exists(): raise ValueError('refuse to overwrite supporting checkpoint')
    rows = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        def add(name, data):
            if not allowed(name): raise ValueError('unexpected archive path: '+name)
            z.writestr(name, data); rows.append(dict(path=name, bytes=len(data), sha256=digest(data)))
        for run in RUNS:
            folder = ROOT/'artifacts/evaluations/v67'/run
            if not (folder/'games.json').is_file(): raise FileNotFoundError(folder/'games.json')
            for p in sorted(folder.rglob('*')):
                if not p.is_file() or '.cambc' in p.parts: continue
                # Preserve native summaries/replays, root manifests, source/Wasm
                # provenance and logs, excluding only rebuildable compiler files.
                relative = p.relative_to(folder)
                if ('build' in relative.parts or len(relative.parts) == 1 or
                    p.name in {'summary.json','runner.log','engine_identity.json'} or p.suffix == '.repl26a'):
                    if p.name == 'compile_commands.json': continue
                    add(p.relative_to(ROOT).as_posix(), p.read_bytes())
        deep = subprocess.check_output(['git','archive','--format=zip','19109c4','--',
            'research/deep-2026-10-28','docs/NEXT_BOT_BRIEF.md','tests/loss_cases'], cwd=ROOT)
        with zipfile.ZipFile(io.BytesIO(deep)) as source:
            for name in source.namelist():
                if not name.endswith('/'): add('research/dz/supporting/deep-19109c4/'+name, source.read(name))
    raw = buffer.getvalue(); parts = []
    for index, offset in enumerate(range(0, len(raw), 40*1024*1024)):
        data = raw[offset:offset+40*1024*1024]
        p = DEST/f'evidence.part{index:03d}'; p.write_bytes(data)
        parts.append(dict(name=p.name, bytes=len(data), sha256=digest(data)))
    manifest = dict(format=1, scope='Full SA-IDLE-v76, SA-P-base, SA-C-base replay/summary/build evidence; deep-study research and loss cases at 19109c4. No bot code used in DZ.',
        deep_commit=subprocess.check_output(['git','rev-parse','19109c4'],cwd=ROOT,text=True).strip(),
        files=rows, parts=parts, zip_sha256=digest(raw))
    (DEST/'manifest.json').write_text(json.dumps(manifest, indent=1)+'\n', encoding='utf-8', newline='\n')
    print(f'Packed {len(rows)} files, {len(raw):,} compressed bytes, {len(parts)} parts', flush=True)

def verify(restore=False, destination=None):
    target = (destination or ROOT).resolve()
    if not target.is_relative_to(ROOT): raise ValueError('restore destination must stay within this checkout')
    manifest = json.loads((DEST/'manifest.json').read_text())
    data = bytearray()
    for part in manifest['parts']:
        if PurePosixPath(part['name']).name != part['name']: raise ValueError('invalid part name')
        raw = (DEST/part['name']).read_bytes()
        if len(raw) != part['bytes'] or digest(raw) != part['sha256']: raise ValueError('part mismatch')
        data.extend(raw)
    if digest(data) != manifest['zip_sha256']: raise ValueError('archive mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for row in manifest['files']:
            name = row['path']
            if not allowed(name): raise ValueError('unsafe restore path')
            raw = z.read(name)
            if len(raw) != row['bytes'] or digest(raw) != row['sha256']: raise ValueError('file mismatch: '+name)
            if restore:
                dest = (target/name).resolve()
                if not dest.is_relative_to(target): raise ValueError('restore escapes workspace')
                if dest.exists():
                    if digest(dest.read_bytes()) != row['sha256']: raise ValueError('refuse to overwrite different file: '+name)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(raw)
    print(('Restored and verified' if restore else 'Verified')+f" {len(manifest['files'])} supporting files", flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('command',choices=['pack','verify','restore'])
    p.add_argument('--destination', type=Path, help='test restoration under a separate directory within this checkout')
    args = p.parse_args()
    if args.command == 'pack': pack()
    else: verify(args.command == 'restore', args.destination)
