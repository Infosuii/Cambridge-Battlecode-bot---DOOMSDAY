"""EXP285 independent raw archive/source/native rerun controls after setup repair."""
from pathlib import Path
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,ENGINE,read
from freeze_engine3_discovery import write
from prove_varg_wrapper import parse,audit

if __name__=='__main__':
    path=HERE/'VARG_WRAPPER_PROOF_R2.json';saved=read(path);plan=read(HERE/'VARG_WRAPPER_PROOF_R2_PLAN.json')
    assert saved['pass'] and bench.digest(HERE/'VARG_WRAPPER_PROOF_R2_PLAN.json')==saved['plan_sha256']
    project=SDK_ROOT/'bots/varg-wrapper-proof-r2-20261106'
    assert bench.digest(project/'bot.wasm')==saved['wasm']
    assert {p.name:bench.digest(p) for p in (project/'src').iterdir() if p.is_file()}==plan['sources']
    assert bench.digest(HERE/'live111_varg_capability.py')==plan['prepare_sha256'] and bench.digest(HERE/'varg_wrapper_probe_r2.cpp')==plan['probe_sha256']
    assert read(HERE/'VARG_WRAPPER_PROOF_ATTEMPT_RECOUNT.json')['pass'] is False
    old={r['map']:r for r in read(HERE/'CAMP_GEOMETRY_RAW.json')['rows']};seen=set();checked=fuel=errors=crossed=maximum=0
    for r in saved['rows']:
        assert (r['map'],r['side']) not in seen;seen.add((r['map'],r['side']))
        d=bench.ROOT/r['directory'];assert bench.digest(d/'native.json')==r['native_sha256']
        n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==plan['maps'][r['map']+'.map26a'] and n['diagnostics']['detailedCaptureComplete']
        f=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted');e=bool(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()))
        assert f==r['fuel'] and e==r['errors'];fuel+=f;errors+=e
        archive,=d.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:stdout=z.read('team-'+r['side'].lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        assert stdout==r['stdout'];assert len([l for l in stdout.splitlines() if l.startswith('VARG_WRAPPER_SETUP ')])==1
        groups=parse(stdout);assert groups==r['groups'];count=audit(groups,old[r['map']]['groups']);assert count==r['checked'];checked+=count
        crossed+=sum(v[-1] for g in groups for v in g['rows']);maximum=max(maximum,max(v[9] for g in groups for v in g['rows']))
    assert seen=={(Path(n).stem,s) for n in plan['maps'] for s in 'AB'} and len(seen)==saved['games']==6
    assert checked==saved['cases'] and (fuel,errors,crossed,maximum)==tuple(saved[k] for k in ('fuel','errors','crossed','max_cold_case_fuel'))
    assert not(fuel or errors or crossed)
    report={'pass':True,'games':len(seen),'cases':checked,'fuel':fuel,'errors':errors,'crossed':crossed,'max_cold_case_fuel':maximum,
            'raw_sha256':bench.digest(path),'failed_attempt_sha256':bench.digest(HERE/'VARG_WRAPPER_PROOF_ATTEMPT_RECOUNT.json'),
            'production_helper_source_sha256':plan['sources']['bot.cpp'],'all_original_fixed_controls_rerun':True,
            'scope':'Actual cache/factor/my_dps/target methods on private mathematical arrays; no production timing/strength claim.'}
    write(HERE/'VARG_WRAPPER_PROOF_R2_RECOUNT.json',report);print(report,flush=True)
