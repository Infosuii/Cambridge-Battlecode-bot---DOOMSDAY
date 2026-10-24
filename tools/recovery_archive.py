"""Lossless deduplicated local snapshot, verification and safe restore. Standard Python3.12; no packages required.

Packs are ordinary ZIP files (deflate1) stored through Git LFS. Every file has a SHA256 and ordered SHA256 blocks.
No credentials are included; all exclusions and source read errors are explicit. Original sources are never changed.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery'
CHUNK=4*1024*1024
PACK_LIMIT=256*1024*1024
SECRET=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
SECRET_NAMES={'.env','.netrc','_netrc','.git-credentials','credentials','credentials.json','auth.json','hosts.yml','id_rsa','id_ed25519'}

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');temporary.replace(path)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def safe_relative(text):
    p=PurePosixPath(text)
    if p.is_absolute() or '..' in p.parts or not p.parts or ':' in text:raise ValueError('unsafe archive member')
    return p

def snapshot():
    if (OUT/'snapshot.json').exists():raise RuntimeError('Snapshot already finalized; never overwrite a saved snapshot')
    OUT.mkdir(exist_ok=True);(OUT/'packs').mkdir(exist_ok=True);(OUT/'histories').mkdir(exist_ok=True)
    config=json.loads((ROOT/'config/recovery_sources.json').read_text())
    progress=dict(status='building',pid=os.getpid(),started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=0,logical_bytes=0,
                  unique_bytes=0,packs=0,excluded=0,errors=0,current='',roots=config['roots'])
    objects={};identities={};pack=None;pack_name=None;pack_bytes=0;pack_index=0;packs=[];last=time.monotonic()
    errors=[];histories=[];exclusions=[]
    # Explicit --resume rebuilds manifests by rereading sources, reusing already closed ZIP content blocks.
    # Never invoke two snapshot processes concurrently. Preserve a truncated final ZIP instead of deleting it.
    if getattr(globals().get('ARGS'),'resume',False):
        for existing in sorted((OUT/'packs').glob('pack-*.zip')):
            pack_index=max(pack_index,int(existing.stem.split('-')[1]))
            try:
                with zipfile.ZipFile(existing) as z:
                    for item in z.infolist():objects[item.filename]=existing.name;progress['unique_bytes']+=item.file_size
                packs.append(dict(file=existing.name,bytes=existing.stat().st_size,sha256=sha(existing)))
            except zipfile.BadZipFile:
                incomplete=OUT/'incomplete';incomplete.mkdir(exist_ok=True)
                existing.replace(incomplete/existing.name)
        print(f'Reusing {len(packs)} closed packs / {len(objects)} content blocks',flush=True)
    manifest=gzip.open(OUT/'files.jsonl.gz.partial','wt',encoding='utf-8',newline='\n')
    object_stream=gzip.open(OUT/'objects.jsonl.gz.partial','wt',encoding='utf-8',newline='\n')
    def tick(force=False):
        nonlocal last
        if force or time.monotonic()-last>5:
            progress['packs']=pack_index;progress['errors']=len(errors);progress['excluded']=len(exclusions)
            dump(OUT/'progress.json',progress);print(json.dumps({k:progress[k] for k in ['status','files','logical_bytes','unique_bytes','packs','excluded','errors','current']}),flush=True);last=time.monotonic()
    def close_pack():
        nonlocal pack
        if pack:
            pack.close();p=OUT/'packs'/pack_name
            packs.append(dict(file=pack_name,bytes=p.stat().st_size,sha256=sha(p)));pack=None
    def store(data,already_compressed=False):
        nonlocal pack,pack_name,pack_bytes,pack_index
        digest=hashlib.sha256(data).hexdigest()
        if digest in objects:return digest
        if pack is None or pack_bytes+len(data)>PACK_LIMIT:
            close_pack();pack_index+=1;pack_name=f'pack-{pack_index:05d}.zip';pack_bytes=0
            path=OUT/'packs'/pack_name
            if path.exists():raise RuntimeError('Unfinished snapshot exists; preserve it and choose explicit recovery before retry')
            pack=zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True)
        pack.writestr(digest,data,compress_type=zipfile.ZIP_STORED if already_compressed else zipfile.ZIP_DEFLATED)
        pack_bytes+=len(data);objects[digest]=pack_name;progress['unique_bytes']+=len(data)
        object_stream.write(json.dumps(dict(sha256=digest,pack=pack_name,bytes=len(data)),separators=(',',':'))+'\n')
        return digest
    try:
        for label,root_text in config['roots'].items():
            root=Path(root_text).resolve()
            if not root.exists():errors.append(dict(root=label,error='root missing'));continue
            def walk_error(error):errors.append(dict(root=label,path=str(error.filename),error=str(error)))
            for directory,dirs,files in os.walk(root,onerror=walk_error,followlinks=False):
                directory=Path(directory)
                if (directory/'.git').exists():
                    relative=directory.relative_to(root).as_posix();key=hashlib.sha256((label+'/'+relative).encode()).hexdigest()[:20]
                    target=OUT/'histories'/f'{key}.bundle'
                    if target.exists():histories.append(dict(root=label,path=relative,file=target.name,sha256=sha(target)))
                    else:
                        result=subprocess.run(['git','-C',str(directory),'bundle','create',str(target),'--all'],capture_output=True,text=True)
                        if result.returncode:errors.append(dict(root=label,path=relative,error='git bundle failed: '+result.stderr[-500:]))
                        else:histories.append(dict(root=label,path=relative,file=target.name,sha256=sha(target)))
                kept=[]
                for name in sorted(dirs):
                    child=directory/name
                    if name=='.git':continue
                    if child.resolve()==OUT.resolve():continue
                    if child.is_symlink():
                        exclusions.append(dict(root=label,path=child.relative_to(root).as_posix(),reason='directory symlink; target recorded separately',target=os.readlink(child)));continue
                    kept.append(name)
                dirs[:]=kept
                for name in sorted(files):
                    path=directory/name;relative=path.relative_to(root).as_posix();progress['current']=label+'/'+relative
                    if name=='.git':
                        exclusions.append(dict(root=label,path=relative,reason='worktree git pointer; history preserved in bundle'));continue
                    if name.casefold() in SECRET_NAMES or name.casefold().endswith(('.pfx','.p12','.key')):
                        exclusions.append(dict(root=label,path=relative,reason='authentication filename'));continue
                    if path.is_symlink():
                        exclusions.append(dict(root=label,path=relative,reason='file symlink',target=os.readlink(path)));continue
                    try:
                        stat=path.stat();key=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
                        if key in identities:
                            digest,blocks=identities[key]
                        else:
                            h=hashlib.sha256();blocks=[];unsafe=False
                            with path.open('rb') as stream:
                                for data in iter(lambda:stream.read(CHUNK),b''):
                                    if stat.st_size<=2*1024*1024 and SECRET.search(data):unsafe=True;break
                                    h.update(data);blocks.append(store(data,path.suffix.lower() in {'.zip','.7z','.gz','.zst','.xz','.bz2','.png','.jpg','.mp4'}))
                            if unsafe:
                                exclusions.append(dict(root=label,path=relative,reason='recognizable secret content'));continue
                            digest=h.hexdigest();after=path.stat()
                            if (after.st_size,after.st_mtime_ns)!=(stat.st_size,stat.st_mtime_ns):raise RuntimeError('source changed while reading')
                            identities[key]=(digest,blocks)
                        manifest.write(json.dumps(dict(root=label,path=relative,bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,
                                                       mode=stat.st_mode,sha256=digest,blocks=blocks),separators=(',',':'))+'\n')
                        progress['files']+=1;progress['logical_bytes']+=stat.st_size
                    except Exception as error:errors.append(dict(root=label,path=relative,error=str(error)))
                    tick()
        close_pack();manifest.close();object_stream.close()
        if getattr(globals().get('ARGS'),'resume',False):
            # Rebuild a complete object map: the new stream otherwise contains only newly added blocks.
            with gzip.open(OUT/'objects.jsonl.gz.partial','wt',encoding='utf-8',newline='\n') as stream:
                for name in sorted(set(objects.values())):
                    with zipfile.ZipFile(OUT/'packs'/name) as z:
                        for item in z.infolist():stream.write(json.dumps(dict(sha256=item.filename,pack=name,bytes=item.file_size),separators=(',',':'))+'\n')
        (OUT/'files.jsonl.gz.partial').replace(OUT/'files.jsonl.gz')
        (OUT/'objects.jsonl.gz.partial').replace(OUT/'objects.jsonl.gz')
        dump(OUT/'exclusions.json',exclusions);dump(OUT/'source_errors.json',errors);dump(OUT/'histories.json',histories)
        progress.update(status='complete' if not errors else 'complete_with_errors',current='',packs=len(packs),
                        excluded=len(exclusions),errors=len(errors),packed_bytes=sum(p['bytes'] for p in packs))
        receipt=dict(progress,format='nfs.recovery.v1',chunk_bytes=CHUNK,project_prefix=config['project_prefix'],packs=packs,
                     manifests={n:sha(OUT/n) for n in ['files.jsonl.gz','objects.jsonl.gz','exclusions.json','source_errors.json','histories.json']})
        dump(OUT/'snapshot.json',receipt);tick(True)
    finally:
        if pack:pack.close()
        manifest.close();object_stream.close()

def verify(full=False):
    receipt=json.loads((OUT/'snapshot.json').read_text())
    for name,digest in receipt['manifests'].items():
        if sha(OUT/name)!=digest:raise RuntimeError('manifest checksum mismatch: '+name)
    count=0
    for spec in receipt['packs']:
        path=OUT/'packs'/spec['file']
        if path.stat().st_size!=spec['bytes'] or sha(path)!=spec['sha256']:raise RuntimeError('pack checksum mismatch: '+path.name)
        if full:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if hashlib.sha256(archive.read(name)).hexdigest()!=name:raise RuntimeError('block checksum mismatch')
                    count+=1
        print('verified '+path.name,flush=True)
    for item in json.loads((OUT/'histories.json').read_text()):
        if sha(OUT/'histories'/item['file'])!=item['sha256']:raise RuntimeError('history bundle checksum mismatch')
    print(json.dumps(dict(verified=True,packs=len(receipt['packs']),blocks_checked=count,files=receipt['files'],source_errors=receipt['errors'])),flush=True)

def restore(destination,scope):
    dest=Path(destination).resolve()
    if dest.exists() and any(dest.iterdir()):raise RuntimeError('Restore destination must be empty; existing data is never overwritten')
    dest.mkdir(parents=True,exist_ok=True)
    receipt=json.loads((OUT/'snapshot.json').read_text())
    lookup={}
    with gzip.open(OUT/'objects.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            item=json.loads(line);lookup[item['sha256']]=item['pack']
    archives={};count=0
    try:
        with gzip.open(OUT/'files.jsonl.gz','rt',encoding='utf-8') as stream:
            for line in stream:
                item=json.loads(line);virtual=item['root']+'/'+item['path']
                if scope=='project':
                    prefix=receipt['project_prefix']+'/'
                    if not virtual.startswith(prefix):continue
                    relative=virtual[len(prefix):]
                elif scope=='all':relative=virtual
                else:
                    if item['root']!=scope:continue
                    relative=item['path']
                out=dest/Path(safe_relative(relative));out.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256()
                with out.open('xb') as output:
                    for digest in item['blocks']:
                        name=lookup[digest]
                        if name not in archives:
                            if len(archives)>16:archives.pop(next(iter(archives))).close()
                            archives[name]=zipfile.ZipFile(OUT/'packs'/name)
                        data=archives[name].read(digest)
                        if hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('corrupt block')
                        output.write(data);h.update(data)
                if h.hexdigest()!=item['sha256'] or out.stat().st_size!=item['bytes']:raise RuntimeError('restored file checksum mismatch')
                os.utime(out,ns=(item['mtime_ns'],item['mtime_ns']));count+=1
                if count%5000==0:print(f'restored {count} files',flush=True)
    finally:
        for archive in archives.values():archive.close()
    dump(dest/'RESTORE_RECEIPT.json',dict(files=count,scope=scope,verified_sha256=True,snapshot_started=receipt['started_utc']))
    print(f'Restored and SHA256-verified {count} files',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    s=sub.add_parser('snapshot');s.add_argument('--resume',action='store_true',help='Only after previous snapshot process stopped; reuse closed packs')
    v=sub.add_parser('verify');v.add_argument('--full',action='store_true')
    r=sub.add_parser('restore');r.add_argument('--dest',required=True);r.add_argument('--scope',default='all')
    args=parser.parse_args();ARGS=args
    if args.action=='snapshot':snapshot()
    elif args.action=='verify':verify(args.full)
    else:restore(args.dest,args.scope)
