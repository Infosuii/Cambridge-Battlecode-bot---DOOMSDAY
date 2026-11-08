from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
REPO=Path(__file__).resolve().parent
DEST=REPO/'research/agentic-improvement-20261107'
RELEASE=BASE/'release/delivery-20261108-auto_bank_arrive_learned'
sys.path.insert(0,str(BASE/'autonomy'))
from store import save, now
from campaign import record
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

def main():
    mainwd=BASE/'training/runs/bounded-delivery-retune-v1';parentwd=BASE/'training/runs/delivery-parent-comparison-20261108'
    assert read(mainwd/'runtime.json')['status']==read(parentwd/'runtime.json')['status']=='complete'
    outcome=read(parentwd/'outcomes.json');receipts=[];new_games=0
    for folder in sorted((BASE/'autonomy/data/benchmarks').iterdir()):
        if not folder.name.startswith(('bounded-delivery-retune-20261107-','delivery-parent-diagnostic-20261108-')):continue
        result=folder/'results.json'
        if not result.exists():continue
        receipt=read(folder/'both-team-audit.json')
        assert receipt['results_sha256']==sha(result) and receipt['complete_schedule'] and receipt['both_teams_zero_faults_and_codes'] and receipt['explicit_fuel_event_counts_match']
        receipts.append({'benchmark':folder.name,**receipt})
        if not folder.name.endswith('-repairs'):new_games+=receipt['cells']
    assert new_games==151272
    decision=read(RELEASE/'selection.json');manifest=read(RELEASE/'manifest.json');deployment=read(RELEASE/'ladder-receipt.json')
    for key in ('source_zip','wasm'):assert sha(RELEASE/manifest[key]['file'])==manifest[key]['sha256']
    delivery=DEST/'release';delivery.mkdir(exist_ok=True)
    for file in RELEASE.iterdir():
        if file.is_file():shutil.copy2(file,delivery/file.name)
    spot=BASE/'autonomy/data/experiments/bounded-delivery-retune-20261107-platform-spotcheck'
    checks={'plan':read(spot/'plan.json'),'baseline':read(spot/'baseline/report.json')}
    if (spot/'challenger/report.json').exists():checks['challenger']=read(spot/'challenger/report.json')
    dump(delivery/'platform-spotcheck.json',checks)
    for name in ['export_findings.py','restore_findings.py','package_delivery.py','ladder_delivery.py','platform_spotcheck.py',
                 'published_pool.py','test_published_pool.py','test_delivery_guards.py','test_restore_findings.py',
                 'compare_delivery_parents.py','correct_final_published_map.py','stop_for_map_correction.py',
                 'reconcile_map_rejection.py','review_retune_interactions.py','resume_delivery_check.py','delivery_inventory.py','finalize_findings.py','publish_findings.py']:
        shutil.copy2(REPO/name,DEST/'tools'/name)
    for name in ['decision.json','applied.json']:
        shutil.copy2(mainwd/'published-map-correction-20261108'/name,DEST/'findings'/('map-correction-'+name))
    summary={'at':now(),'selected':decision,'release_manifest':manifest,'deployment':deployment,
             'registered_retune':read(mainwd/'outcomes.json'),'same_map_comparison':outcome,
             'new_local_games_including_parent_diagnostic':new_games,'audit_receipts':receipts,
             'policy':'Experimental upload requested by user; no substantial or statistically established strength upgrade is claimed.'}
    dump(DEST/'findings/final-report.json',summary)
    table=['| Candidate | Final reference gain | Direct /328 | Published reference gain | Published direct /88 |','|---|---:|---:|---:|---:|']
    for n,r in outcome['candidates'].items():
        table.append(f"| {n} | {r['pooled']['gain']*100:+.2f} pp | {r['pooled']['direct_score']:g} | {r['panels']['published']['gain']*100:+.2f} pp | {r['panels']['published']['direct_score']:g} |")
    text='# Final validation and experimental delivery\n\n'+decision['rationale']+'\n\n'+decision['limitations']+'\n\n'+'\n'.join(table)
    text+='\n\nThe bounded retune plus unchanged-parent diagnostic played 151,272 local games. Every completed schedule has current-engine, frozen map/build, both-team fault/code and explicit fuel-count audit receipts. Merged repair panels include cached component/control rows and are excluded from the new-game total. A temporary maintenance stop reused completed games and corrected one generated map mistakenly labelled published before any final game.\n\n'
    text+='The two registered finalists failed the substantial gate. The unchanged-parent comparison was added after these results and selection among all four is adaptive; it is not another independent confirmation. The selected parent keeps the verified simulator/action/reset/runtime and banking-progress fixes with learned weights and deeper routing. Neither proposed threshold adjustment is silently merged into it. All variants remain in the archived sources.\n\n'
    text+='Future work should stop repeating broad scalar searches on the same small selection distribution. Use parent controls in final schedules, enforce catalog IDs plus official map bytes, trace direct-match farming/banking/coordination regressions at common horizons, and tie new interventions to verified execution evidence. Training or reference-only gains are insufficient evidence for a permanent upgrade.\n'
    (DEST/'findings/final-report.md').write_text(text,encoding='utf-8')
    status=f"**Delivery status: v{deployment.get('version',112)} {'active on DOOMSDAY' if deployment.get('phase')=='active' else 'uploaded; remote build/activation pending'}. Experimental release; a strength upgrade and ELO gain are unproven.**"
    path=DEST/'README.md';body=path.read_text(encoding='utf-8');body,count=re.subn(r'\*\*Delivery status:.*?\*\*',status,body,count=1,flags=re.S);assert count==1
    path.write_text(body,encoding='utf-8')
    record('bounded-delivery-retune-20261107-delivery',classification='Conditionally useful',
           phase='Experimental delivery selected; registered substantial target failed',candidate=decision['candidate'],
           evidence=outcome['candidates'][decision['candidate']],new_local_games=new_games,official_version=deployment.get('version'),
           uncertainty=decision['limitations'],next_action='Prioritize source-isolated direct-match regression mechanisms and official-map provenance; retain parents and failed retunes. No claim of verified major or incremental promotion.')
    print(json.dumps({'new_local_games':new_games,'checked_panels':len(receipts),'deployment_phase':deployment['phase'],'public_release':str(delivery)}))

if __name__=='__main__':main()
