"""EXP258: public terrain capacity only; no candidate or game-outcome selection."""
from concurrent.futures import ThreadPoolExecutor
from shutil import copyfile
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition

def varint(n):
    assert n>=0
    b=bytearray()
    while n>=128:b.append((n&127)|128);n>>=7
    b.append(n);return b

def encode(bits,w,h):
    labels=[-1]*(w*h);components=0;tiles=0
    for root in range(w*h):
        if labels[root]>=0 or not ((bits[root>>3]>>(root&7))&1):continue
        labels[root]=components;stack=[root]
        while stack:
            at=stack.pop();tiles+=1;x,y=at%w,at//w
            for yy in range(max(0,y-1),min(h,y+2)):
                for xx in range(max(0,x-1),min(w,x+2)):
                    q=yy*w+xx
                    if labels[q]<0 and (bits[q>>3]>>(q&7))&1:labels[q]=components;stack.append(q)
        components+=1
    data=bytearray();last=0;at=0;runs=[]
    while at<w*h:
        if labels[at]<0:at+=1;continue
        end=at+1
        while end<w*h and labels[end]==labels[at]:end+=1
        values=(at-last,end-at,labels[at]);runs.append(values)
        for n in values:data.extend(varint(n))
        last=end;at=end
    index=0
    def get():
        nonlocal index
        n=shift=0
        while True:
            b=data[index];index+=1;n|=(b&127)<<shift
            if not b&128:return n
            shift+=7;assert shift<=28
    rebuilt=[-1]*(w*h);last=0
    while index<len(data):
        gap,length,cid=get(),get(),get();start=last+gap;end=start+length
        assert length>0 and 0<=cid<components and end<=w*h and all(v==-1 for v in rebuilt[start:end])
        rebuilt[start:end]=[cid]*length;last=end
    assert rebuilt==labels
    return {'bush_tiles':tiles,'components':components,'runs':len(runs),'encoded_bytes':len(data),'encoding_hex':data.hex()}

if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'static-bush-cache-capacity-20261106';output.mkdir()
    project=SDK_ROOT/'bots/static-bush-cache-capacity-20261106';src=project/'src';src.mkdir(parents=True)
    copyfile(HERE/'static_bush_geometry_probe.cpp',src/'main.cpp');wasm=project/'bot.wasm'
    with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(ref)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    pins={'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),'source':bench.digest(src/'main.cpp'),'probe':bench.digest(wasm),'reference':bench.digest(ref),
          'maps':{p.name:bench.digest(p) for p in maps},'games':90,'fixed_metadata_bytes':48,'two_order_bytes_per_group':4,'capacity_bytes':496,'scope':'Static development-terrain capacity only; no candidate/table/policy/performance claim.'}
    write(HERE/'STATIC_BUSH_CACHE_CAPACITY_PLAN.json',pins)
    def run(mp):
        d=output/mp.stem;d.mkdir()
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',wasm,ref,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        native=read(d/'native.json');assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==bench.digest(mp) and native['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:text=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in text.splitlines() if l.startswith('STATIC_BUSH ')];_,w,h,g,mismatch,cost,hexbits=line.split()
        w,h,g,mismatch,cost=map(int,(w,h,g,mismatch,cost));assert mismatch==0
        bits=bytes.fromhex(hexbits);assert len(bits)==(w*h+7)//8
        data=encode(bits,w,h);total=48+4*g+data['encoded_bytes']
        errors=bool(native['diagnostics']['codes'] or any(native['diagnostics']['botFaults'].values()))
        fuel=sum(len(e['entries']) for e in native['events'] if e['kind']=='fuelExhausted')
        assert not errors and not fuel
        return {'map':mp.stem,'map_hash':bench.digest(mp),'width':w,'height':h,'groups':g,'packed_hex':hexbits,'export_and_tile_audit_cost':cost,
                **data,'combined_bytes':total,'fits':total<=496,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run,maps):
            rows.append(row)
            if len(rows)%15==0:print(f'{len(rows)}/90',flush=True)
    report={'pins':pins,'maps':len(rows),'fits':sum(r['fits'] for r in rows),'unsupported':sum(not r['fits'] for r in rows),'max_combined_bytes':max(r['combined_bytes'] for r in rows),'rows':rows}
    write(HERE/'STATIC_BUSH_CACHE_CAPACITY.json',report)
    print({k:v for k,v in report.items() if k not in ('pins','rows')},flush=True)
