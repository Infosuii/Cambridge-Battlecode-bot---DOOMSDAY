"""Preserve incomplete EXP284 and demonstrate zero-group setup before R2 repair."""
from pathlib import Path
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,ENGINE,read
from freeze_engine3_discovery import write

if __name__=='__main__':
    plan=read(HERE/'VARG_WRAPPER_PROOF_PLAN.json');project=SDK_ROOT/'bots/varg-wrapper-proof-20261106'
    assert {p.name:bench.digest(p) for p in (project/'src').iterdir() if p.is_file()}==plan['sources']
    out=bench.CACHE/'varg-wrapper-proof-20261106';rows=[]
    for name in plan['maps']:
        for side in 'AB':
            d=out/(Path(name).stem+'-'+side)
            if not (d/'native.json').exists():rows.append({'map':name,'side':side,'available':False,'reason':'cancelled after first assertion'});continue
            n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==plan['maps'][name]
            archive,=d.glob('*.repl26a')
            with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
            assert stdout=='VARG_WRAPPER_DONE\n' and not n['diagnostics']['codes'] and not any(n['diagnostics']['botFaults'].values())
            assert not sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted')
            rows.append({'map':name,'side':side,'available':True,'emitted_groups':0,'stdout':stdout,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive)})
    report={'pass':False,'planned_games':6,'completed_empty':sum(r['available'] for r in rows),'rows':rows,
            'wasm':bench.digest(project/'bot.wasm'),'plan_sha256':bench.digest(HERE/'VARG_WRAPPER_PROOF_PLAN.json'),
            'demonstration':'Private World initialized only in separate draft instance; champion-control instance has zero groups. No candidate/model control evaluated.'}
    write(HERE/'VARG_WRAPPER_PROOF_ATTEMPT_RECOUNT.json',report);print({k:v for k,v in report.items() if k!='rows'},flush=True)
