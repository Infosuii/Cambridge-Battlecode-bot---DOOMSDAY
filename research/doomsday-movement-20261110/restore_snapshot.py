"""Restore the deduplicated source capsule without replacing different files."""
from pathlib import Path
import argparse,hashlib,json,zipfile

p=argparse.ArgumentParser(); p.add_argument('destination',type=Path); p.add_argument('--scope',default=''); a=p.parse_args()
dest=a.destination.resolve(); restored=0
archive=Path(__file__).with_name('workstream-source-and-research.zip')
if not archive.exists():
 info=json.loads(Path(__file__).with_name('ARCHIVE-PARTS.json').read_text(encoding='utf8'))
 temp=archive.with_suffix('.assembling')
 with temp.open('wb') as out:
  for part in info['parts']:
   data=archive.with_name(part['name']).read_bytes()
   if hashlib.sha256(data).hexdigest()!=part['sha256']:raise RuntimeError('Corrupt archive part: '+part['name'])
   out.write(data)
 if hashlib.sha256(temp.read_bytes()).hexdigest()!=info['sha256']:raise RuntimeError('Corrupt reassembled archive')
 temp.replace(archive)
with zipfile.ZipFile(archive) as z:
 for entry in json.loads(z.read('manifest.json')):
  if a.scope and not entry['path'].startswith(a.scope):continue
  target=(dest/entry['path']).resolve()
  if not target.is_relative_to(dest):raise RuntimeError('Unsafe archive path')
  data=z.read('blobs/'+entry['sha256'])
  if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise RuntimeError('Corrupt archive blob')
  if target.exists():
   if target.read_bytes()!=data:raise RuntimeError('Preserving different existing file: '+str(target))
   continue
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);restored+=1
print(f'Restored {restored} files to {dest}')
