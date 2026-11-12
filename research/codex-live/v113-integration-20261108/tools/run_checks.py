from pathlib import Path
import concurrent.futures,hashlib,json
from project import ROOT,ARENA,save
from local_panel import run

def sections(path):
    data=Path(path).read_bytes();assert data[:8]==b'\0asm\x01\0\0\0'
    def leb(p):
        n=s=0
        while True:
            b=data[p];p+=1;n|=(b&127)<<s;s+=7
            if b<128:return n,p
    p=8;out={}
    while p<len(data):
        tag=data[p];size,start=leb(p+1);end=start+size
        out[str(tag)]=hashlib.sha256(data[start:end]).hexdigest();p=end
    return out

if __name__=='__main__':
    names=['n00','n01','n02','n04','n08','n15']
    ss={n:sections(ARENA/'bots'/n/'.cambc/build-release/bot-injected.wasm') for n in names}
    assert len({s['10'] for s in ss.values()})==1,'Mechanism arms differ in executable instructions'
    save(ROOT/'wasm-section-check.json',{'identical_code_sections':True,'sections':ss})
    pool=json.loads((ROOT/'published-maps.json').read_text())
    def maps(names):return [Path(next(r['file'] for r in pool if r['name']==n)) for n in names]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        jobs=[ex.submit(run,'mechanism-ablation-v2',names+['b113'],maps(['00the_line','01islands','03homonoliths','00happy_halloween','02guardians','00rows','00vault','04comb']),['b111','nnm4','ref_x1','teammate_max_gx'],10),
              ex.submit(run,'rl-recorder-qa-v1',['r15'],maps(['01islands','03homonoliths']),['b111'],2,True)]
        for f in jobs:f.result()
