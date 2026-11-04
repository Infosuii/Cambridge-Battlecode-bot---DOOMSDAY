from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'runs/prepatch-design-audit05'
s=json.loads(p.with_suffix('.json').read_text());assert s['diagnostics']['detailedCaptureComplete'] and not any(s['diagnostics']['botFaults'].values())
ch={};items={};names=['ryth','vesper_vale','vendetta','cassi','issac','stellar','prism','marcella','willow','ren','varg','tavi','heart_of_ruin']
for line in (p/'team-a.stdout').read_bytes().replace(b'\0',b'').splitlines():
 t=line.decode().split()
 if t[0]=='JDS1':
  i=int(t[1]);v=dict(zip(['base_health','base_strength','base_focus','health_growth','strength_growth','focus_growth'],map(float,t[2:])));assert i not in ch or ch[i]==v;ch[i]=v
 elif t[0]=='JDI1':
  i=int(t[1]);v=dict(zip(['health_points','strength_points','focus_points','passive_magnitude','cost','combine_count'],map(float,t[2:])));assert i not in items or items[i]==v;items[i]=v
assert len(ch)==13 and len(items)==2
exp=json.loads((r/'patch4_transition/expected_designs.json').read_text());changes=[]
for name,fields in exp['new_patch_expected'].items():
 for key,target in fields.items():changes.append({'champion':name,'field':key,'current_local':ch[names.index(name)][key],'patch4_expected_from_user':target,'matches_expected':ch[names.index(name)][key]==target})
d={'scope':'Current immutable runtime designs vs user-provided future patch4 expectations, no strength claim','match_engine_version':s['match']['engineVersion'],'match_engine_build_hash':s['match']['engineBuildHash'],'sdk_version':'4.0.0','actual_designs':{names[i]:v for i,v in ch.items()},'actual_item_metadata':items,'target_design_comparison':changes,'target_engine_released':False,'target_release_source':'User says tomorrow, time unknown','source_audit':{'V58_PATCH':1,'champion_stats':'Dynamic SDK champion_design reads in Bot::init; disabled old constexpr tables preserved but not active.','skirmish_multiplier':'Dynamic item passive_magnitude in refresh_emblems.','shopping':'Runtime cost/combine_count/result used by active shopping path.','strategy_caveat':'Draft priorities, shop plan and learned weights remain trained/selected on old balance; dynamic reads do not validate decision quality.'},'diagnostics':s['diagnostics'],'audit_log_sha256':hashlib.sha256((p/'team-a.stdout').read_bytes()).hexdigest()}
(r.parent.parent/'outputs/rl-execution/PATCH4_TRANSITION_AUDIT.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'engine':d['match_engine_version'],'items':items,'comparison':changes},indent=2))
