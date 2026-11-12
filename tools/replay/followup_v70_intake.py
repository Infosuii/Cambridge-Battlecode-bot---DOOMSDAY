"""Read-only website source/metadata intake for the separate v70 follow-up."""
import argparse
import difflib
import hashlib
import io
import json
import re
import subprocess
import zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
from deep_preflight import ROOT,OURS
from deep_detector_report import save
from scout_public import Public
STUDY='followup-v70-2026-10-29';S=ROOT/'research'/STUDY;L=ROOT/'artifacts/local-only'/STUDY
def sha(b):return hashlib.sha256(b).hexdigest()
def preserve(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==b,'Existing evidence differs: '+str(p)
    else:p.write_bytes(b)


def source(p):
    archive=p.read_bytes();preserve(L/'source/archive.zip',archive);files=[];patches=[]
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        for i in z.infolist():
            name=PurePosixPath(i.filename)
            assert not i.is_dir() and name.parts[0]=='src' and not name.is_absolute() and '..' not in name.parts and i.file_size<8*1024*1024
            assert (i.external_attr>>16)&0o170000!=0o120000
            b=z.read(i);preserve(L/'source'/str(name),b);base=ROOT/'bots/live-69'/str(name);old=base.read_bytes() if base.exists() else b''
            diff=list(difflib.unified_diff(old.decode('utf-8').splitlines(),b.decode('utf-8').splitlines(),fromfile='v69/'+str(name),tofile='v70/'+str(name),lineterm=''))
            patches+=diff;files.append({'path':str(name),'bytes':len(b),'sha256':sha(b),'v69_sha256':sha(old),'identical_to_v69':old==b,'added_lines':sum(l.startswith('+') and not l.startswith('+++') for l in diff),'removed_lines':sum(l.startswith('-') and not l.startswith('---') for l in diff)})
    preserve(L/'source/v69-to-v70.patch',('\n'.join(patches)+'\n').encode())
    out={'evidence':'official signed-in Submissions page Download v70; Active/Verified, note home side','submission_id':'78116168-a5b6-42f3-bb19-1f7d1b17c45d','archive_url':'https://2026a.battlecode.co.uk/api/v1/submissions/78116168-a5b6-42f3-bb19-1f7d1b17c45d/archive','download_name':p.name,'archive_sha256':sha(archive),'files':files,'file_count':len(files),'changed_files':[f['path'] for f in files if not f['identical_to_v69']],'frozen_sources_edited':False}
    save(S/'SOURCE_COMPARISON.json',out);print(json.dumps({k:v for k,v in out.items() if k!='files'}))


def metadata():
    plan=json.loads((S/'PLAN.json').read_text(encoding='utf-8'));api=Public(L/'public');ladder=api.json('/api/v1/ladder?page=1&pageSize=100&category=all','ladder.json');save(S/'LADDER_SNAPSHOT.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'source':'official public ladder API',**ladder});rows=[]
    for gid in plan['group_ids']:
        d=api.json('/api/v1/match-groups/'+gid,'groups/'+gid+'.json')
        for m in d['matches']:
            sides=sorted(m['sides'],key=lambda x:x['side']);own=next(s for s in sides if s['teamId']==OURS);enemy=next(s for s in sides if s['teamId']!=OURS)
            assert own.get('version') in (None,70) and m['status']=='finished' and m['patchId'].startswith('2.0.0:')
            rows.append({'match_id':m['id'],'group_id':gid,'map':m['map'],'map_id':m['mapId'],'created_at':m['createdAt'],'kind':m['kind'],'patch_id':m['patchId'],'rounds':m['rounds'],'our_side':own['side'],'result':own['result'],'our_score':own['score'],'opponent_score':enemy['score'],'opponent':enemy['teamName'],'opponent_id':enemy['teamId'],'platform_version':70,'version_basis':'authenticated UI group-version=70; no time-only attribution'})
    assert len(rows)==85 and len({r['match_id'] for r in rows})==85
    save(S/'MANIFEST.json',{'created_at':datetime.now(timezone.utc).isoformat(),'games':len(rows),'groups':17,'rows':rows});print(json.dumps({'games':len(rows),'groups':17}))


def ingest(downloads):
    manifest=json.loads((S/'MANIFEST.json').read_text(encoding='utf-8'));lookup={r['match_id']:r for r in manifest['rows']};rows=[];bundles=[]
    for gid in sorted({r['group_id'] for r in lookup.values()}):
        p=downloads/('match-group-'+gid+'.zip')
        if not p.exists():continue
        raw=p.read_bytes();assert len(raw)<32*1024*1024;preserve(L/'bundles'/p.name,raw);seen=set()
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            assert outer.testzip() is None
            for info in outer.infolist():
                match=re.fullmatch(r'\d+-([0-9a-f-]{36})\.zip',info.filename);assert match and info.file_size<16*1024*1024;mid=match[1];assert mid in lookup and lookup[mid]['group_id']==gid and mid not in seen;seen.add(mid)
                with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                    assert inner.testzip() is None
                    ri=inner.getinfo('replay.repl26a');assert ri.file_size<16*1024*1024;b=inner.read(ri);preserve(L/'replays'/(mid+'.repl26a'),b)
                np=downloads/('match-'+mid+'.json');binary=downloads/('match-'+mid+'.camstat');target=L/'replays'/(mid+'.summary.json')
                if not np.exists() and binary.exists() and not target.exists():
                    preserve(L/'summaries'/(mid+'.camstat'),binary.read_bytes())
                    p=subprocess.run([str(ROOT/'tools/vendor/cambc.exe'),'summary',str(binary),'--output',str(target)],cwd=ROOT,capture_output=True,timeout=30)
                    assert p.returncode==0,p.stderr.decode('utf-8','replace')
                if not np.exists() and target.exists():np=target
                has=np.exists()
                if has:
                    nraw=np.read_bytes();n=json.loads(nraw);assert n['match']['engineVersion']=='2.0.0';preserve(L/'replays'/(mid+'.summary.json'),nraw)
                rows.append({'match_id':mid,'replay_sha256':sha(b),'native_present':has,'summary_sha256':sha(nraw) if has else None})
        assert seen=={r['match_id'] for r in lookup.values() if r['group_id']==gid}
        bundles.append({'group_id':gid,'sha256':sha(raw),'games':5})
    save(S/'DOWNLOADS.json',{'groups':len(bundles),'replays':len(rows),'native_summaries':sum(r['native_present'] for r in rows),'bundles':bundles,'rows':rows});print(json.dumps({'groups':len(bundles),'replays':len(rows),'native_summaries':sum(r['native_present'] for r in rows)}))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['source','metadata','ingest']);ap.add_argument('--archive',type=Path);ap.add_argument('--downloads',type=Path,default=Path.home()/'Downloads');a=ap.parse_args();L.mkdir(parents=True,exist_ok=True)
    if a.mode=='source':source(a.archive)
    elif a.mode=='metadata':metadata()
    else:ingest(a.downloads)
if __name__=='__main__':main()
