"""Check final delivery identities and research/candidate holdout boundaries."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save

S=ROOT/'research/deep-2026-10-28'
def read(name):return json.loads((S/name).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest=read('CANDIDATE_MANIFEST.json')['rows'];examined={r['match_id'] for r in manifest if r['partition']=='examined'};held={r['match_id'] for r in manifest if r['partition']=='hands-off'}
    assert len(examined)==385 and len(held)==165 and not examined&held
    for name in ('CARD_PREDICTIONS.json','MOMENT_SAMPLE.json','DETECTOR_SPEC.json','MODEL_SPLIT.json'):
        assert (S/name).read_bytes()==subprocess.check_output(['git','show','b490a1d:research/deep-2026-10-28/'+name],cwd=ROOT),name
    assert {r['match_id'] for r in read('MODEL_SPLIT.json')['rows']}==examined
    cards=read('CARD_DATA.json');assert len(cards['rows'])==105 and {r['match_id'] for r in cards['rows']}<=examined
    assert len({r['match_id'] for r in cards['rows'] if r['kind']=='loss'})==65
    assert len({r['match_id'] for r in cards['rows'] if r['kind']!='loss'})==15
    assert len([p for p in (S/'cards').glob('*.md') if len(p.read_text(encoding='utf-8').splitlines())<=25])==105
    source=read('LIVE_SOURCE.json');assert len(source['files'])==33
    for name,expected in source['files'].items():assert digest(ROOT/'bots/live-69'/name)==expected['sha256'],name
    subprocess.run(['git','diff','--exit-code','5114231','--','bots/live-69'],cwd=ROOT,check=True,capture_output=True)
    repro=read('REPRO_RESULTS.json');audit=read('REPRO_STATE_VALIDATION.json')
    assert repro['source_byte_exact']==repro['both_script_byte_exact']==12 and audit['passed']==24 and audit['state_samples_compared']==25184
    assert {r['match_id'] for r in repro['rows']}<=examined
    traces=read('TRACE_RESULTS_NUMERIC.json');tail=read('TRACE_RESULTS_TAIL.json');assert traces['complete_trusted_windows']==9 and traces['byte_exact_traces']==7 and tail['byte_exact_traces']==3
    complete={r['match_id'] for r in traces['rows'] if r['trace_window_complete_before_divergence']};complete|={r['match_id'] for r in tail['rows'] if r['trace_window_complete_before_divergence']}
    assert complete=={r['match_id'] for r in repro['rows']}
    for r in traces['rows']+tail['rows']:
        cutoff=r['first_input_divergence']['round'] if r['first_input_divergence'] else 100000
        for line in r['trusted_trace']:assert line['r']<cutoff and line['emitted_round']<cutoff
    takeover=read('TAKEOVER_RESULT.json');assert all(takeover[k] for k in ('warm_input_prefix_identical','warm_round_states_identical','baseline_fails_assertion','diagnostic_passes_assertion'))
    assert takeover['valid_horizon_end']==1678 and takeover['first_enemy_script_rejection_round']==1701
    mask=read('MASKING_RESULTS.json');assert len(mask['rows'])==2 and all(r['warm_prefix_valid'] for r in mask['rows'])
    assert next(r for r in mask['rows'] if r['card_id']=='C099')['byte_identical_full_replay']
    puppet=read('PUPPET_AUDIT.json');assert puppet['parser_fixtures']==17 and puppet['focus_team_comparisons']==10 and puppet['focus_equal']
    profiles=read('PROFILE_DATA.json');assert len(profiles['profiles'])==8 and len(profiles['matchups'])==78
    assert {r['match_id'] for r in profiles['rows']}<=examined
    assert read('M1_EXAMINED.json')['spec_sha256']==digest(S/'M1_SPEC.json')
    validation=read('FINAL_VALIDATION.json');assert validation['passed']==385 and validation['calibration_passed']==5 and validation['m1_equivalent'] and validation['d3_equivalent']
    assert validation['plan_sha256']==digest(S/'FINAL_CONFIRMATION_PLAN.json') and validation['action_code_sha256']==digest(ROOT/'tools/replay/final_actions.mjs') and validation['confirmation_code_sha256']==digest(ROOT/'tools/replay/deep_final_confirmation.py')
    assert (S/'FINAL_CONFIRMATION_PLAN.json').read_bytes()==subprocess.check_output(['git','show','590d106:research/deep-2026-10-28/FINAL_CONFIRMATION_PLAN.json'],cwd=ROOT)
    final=read('FINAL_CONFIRMATION.json');assert final['games_processed']==165 and final['own_games']==160 and final['no_retuning']
    assert len(final['rows'])==160 and {r['match_id'] for r in final['rows']}<held
    assert sum(r['result']=='loss' for r in final['rows'])==83 and sum(r['result']=='win' for r in final['rows'])==77
    for r in final['rows']:assert abs(r['final_margin']-r['income_margin']-r['preservation_margin']-r['carry_margin'])<1e-8
    catalogue=read('mistakes.json');assert len(catalogue['mistakes'])==5 and sum('causal (tested)' in m['confidence'] for m in catalogue['mistakes'])==1
    for m in catalogue['mistakes']:
        p=m['planning'];assert abs(p['score']-p['surrogate_coverage']*p['fixability_judgment']*p['transfer_judgment']/p['effort_hours_including_fuel_risk'])<1e-12
        assert m['cost']['causal_recoverable_gems'] is None
    files=[S/n for n in ('REPORT.md','DATA.json','MISTAKES.md','FINAL_CONFIRMATION.md','P5_OPPONENTS.md','P6_DEEP_TRACK.md','STATE.md')]+[ROOT/'docs'/n for n in ('NEXT_BOT_BRIEF.md','LOSS_KNOWLEDGE.md','handoff.md')]+[ROOT/'tests/loss_cases/README.md',ROOT/'tools/README.md']
    for p in files:
        assert p.exists() and p.stat().st_size>100,p
        if p.suffix!='.md':continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            assert (p.parent/target.split('#')[0]).exists(),(p,target)
    newpy=[p for p in (ROOT/'tools/replay/puppet').glob('*.py')]+[ROOT/'tools/replay'/n for n in ('deep_final_confirmation.py','deep_final_report.py','deep_profiles.py','deep_puppet_audit.py','audit_final_delivery.py')]+[ROOT/'tests/loss_cases/run_case.py']
    for p in newpy:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    assert all(not p.startswith(('artifacts/','bots/','config/','sources/')) for p in staged)
    for args in (['git','diff','--check'],['git','diff','--cached','--check']):subprocess.run(args,cwd=ROOT,check=True,capture_output=True)
    result={'passed':True,'examined_games':385,'final_reserved_games':165,'reserved_own_loss_win':[83,77],'cards':105,'distinct_examined_losses':65,'control_wins':15,'source_full_game_exact':12,'script_control_full_game_exact':12,'round_state_comparisons':24,'state_samples':25184,'faithful_detailed_windows':9,'faithful_sparse_windows':3,'parser_fixtures':17,'independent_focus_team_checks':10,'profile_games':385,'profiles':8,'matchup_strata':78,'one_confirmed_decision_bug':True,'frozen_source_unchanged':True,'predictions_specs_and_splits_unchanged':True,'final_plan_committed_before_access':'590d106','reserved_model_card_tuning':False,'future_candidate_holdout_needed':True,'production_candidate_tested':False,'limits':'One bounded decision fix; overall D3 frequency replicates, reserved Climb intervals include0. No match-win/rank improvement or new candidate release is established.'}
    save(S/'FINAL_DELIVERY_VALIDATION.json',result);print(json.dumps(result))


if __name__=='__main__':main()
