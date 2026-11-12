"""EXP260: group identical public-data runs, never a per-map policy table."""
from census_static_bush_cache import encode,varint
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
import ablate_dev as bench

def decode_varints(data):
    values=[];n=shift=0
    for b in data:
        n|=(b&127)<<shift
        if b&128:shift+=7;assert shift<=28
        else:values.append(n);n=shift=0
    assert shift==0
    return values

def grouped(bits,w,h):
    original=encode(bits,w,h)
    old=decode_varints(bytes.fromhex(original['encoding_hex']));assert len(old)%3==0
    groups=[[] for _ in range(original['components'])];labels=[-1]*(w*h);last=0
    for i in range(0,len(old),3):
        gap,length,cid=old[i:i+3];start=last+gap;end=start+length
        groups[cid].append((start,length));labels[start:end]=[cid]*length;last=end
    data=bytearray()
    for runs in groups:
        assert runs;data.extend(varint(len(runs)));last=0
        for start,length in runs:data.extend(varint(start-last));data.extend(varint(length));last=start+length
    values=iter(decode_varints(data));rebuilt=[-1]*(w*h)
    for cid in range(len(groups)):
        count=next(values);assert count>0;last=0
        for _ in range(count):
            gap,length=next(values),next(values);start=last+gap;end=start+length
            assert length>0 and end<=w*h and all(v==-1 for v in rebuilt[start:end])
            rebuilt[start:end]=[cid]*length;last=end
    assert next(values,None) is None and rebuilt==labels
    assert all((label>=0)==bool(bits[i>>3]&(1<<(i&7))) for i,label in enumerate(rebuilt))
    return {'components':len(groups),'runs':original['runs'],'encoded_bytes':len(data),'encoding_hex':data.hex(),'bush_tiles':original['bush_tiles']}

if __name__=='__main__':
    assert read(HERE/'STATIC_BUSH_CACHE_CAPACITY_RECOUNT.json')['pass']
    path=HERE/'STATIC_BUSH_CACHE_CAPACITY.json';prior=read(path)
    plan={'source_raw_sha256':bench.digest(path),'source_recount_sha256':bench.digest(HERE/'STATIC_BUSH_CACHE_CAPACITY_RECOUNT.json'),
          'source_plan':prior['pins'],'maps':90,'encoding':'Per-component run count, then monotone unsigned-varint gap,length pairs; component id implicit.',
          'fixed_metadata_bytes':48,'two_order_bytes_per_group':4,'capacity_bytes':496,'scope':'Static development terrain only, no candidate or table.'}
    write(HERE/'GROUPED_BUSH_CACHE_CAPACITY_PLAN.json',plan)
    rows=[]
    for old in prior['rows']:
        new=grouped(bytes.fromhex(old['packed_hex']),old['width'],old['height']);size=48+4*old['groups']+new['encoded_bytes']
        rows.append({'map':old['map'],'map_hash':old['map_hash'],'old_combined_bytes':old['combined_bytes'],**new,'combined_bytes':size,'fits':size<=496})
    report={'pins':plan,'maps':len(rows),'fits':sum(r['fits'] for r in rows),'unsupported':sum(not r['fits'] for r in rows),'max_combined_bytes':max(r['combined_bytes'] for r in rows),'rows':rows}
    write(HERE/'GROUPED_BUSH_CACHE_CAPACITY.json',report)
    print({k:v for k,v in report.items() if k not in ('rows','pins')},flush=True)
