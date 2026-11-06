"""EXP282 archive/native proof recount, preserving original sources and results."""
from pathlib import Path
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,ENGINE,read
from freeze_engine3_discovery import write
from prove_varg_geometry import parse,audit

if __name__=='__main__':
    path=HERE/'VARG_GEOMETRY_PROOF.json';saved=read(path);plan=read(HERE/'VARG_GEOMETRY_PROOF_PLAN.json')
    assert saved['pass'] and bench.digest(HERE/'VARG_GEOMETRY_PROOF_PLAN.json')==saved['plan_sha256']
    for n,h in plan['sources'].items():assert bench.digest(HERE/n)==h
    b=saved['release'];assert bench.digest(Path(b['path']))==b['wasm']
    for n,h in b['sources'].items():assert bench.digest(Path(b['path']).parent/'src'/n)==h
    assert bench.digest(SDK_ROOT/'sdk/cpp/cambc.h')==plan['sdk']
    old={r['map']:r for r in read(HERE/'CAMP_GEOMETRY_RAW.json')['rows']};states=fuel=errors=crossed=maximum=0
    seen=set()
    for r in saved['rows']:
        assert (r['map'],r['side']) not in seen;seen.add((r['map'],r['side']))
        d=bench.ROOT/r['directory'];assert bench.digest(d/'native.json')==r['native_sha256']
        n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==plan['maps'][r['map']+'.map26a'] and n['diagnostics']['detailedCaptureComplete']
        f=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted');e=bool(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()))
        assert f==r['fuel'] and e==r['errors'];fuel+=f;errors+=e
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        assert stdout==r['stdout'];g=parse(stdout);assert g==r['groups']
        count,cr=audit(g,old[r['map']]['groups']);assert count==r['checked'] and cr==r['crossed']
        states+=count;crossed+=len(cr);maximum=max(maximum,max(x['fuel'] for x in g))
    assert len(seen)==plan['games']==saved['games']==180
    assert (states,fuel,errors,crossed,maximum)==tuple(saved[k] for k in ('states','fuel','errors','crossed','max_cold_group_fuel'))
    assert not(fuel or errors or crossed)
    report={'pass':True,'games':len(seen),'states':states,'fuel':fuel,'errors':errors,'crossed':crossed,'max_cold_group_fuel':maximum,
            'raw_sha256':bench.digest(path),'source_pin_checks':True,'all_archives_reopened':True,
            'scope':'SDK public-data pure kernel correctness/cost only; no complete-bot timing, arbitrary live float mechanics, strength or release claim.'}
    write(HERE/'VARG_GEOMETRY_PROOF_RECOUNT.json',report);print(report,flush=True)
