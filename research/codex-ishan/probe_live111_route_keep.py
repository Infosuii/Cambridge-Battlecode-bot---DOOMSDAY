"""EXP221 scoped scorer keep contract, with original-view and post-failure-prefix checks."""
from copy import deepcopy

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument
from turn_prefix import action_prefix


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    path=src/'common.h';path.write_bytes(f'#define CODEX_KEEP_ONE {int(enabled and case["patched"])}\n'.encode()+path.read_bytes())
    old='    const int keep = tune::kRouteDepth >= 2 ? std::clamp(tune::kRouteK, 1, 8) : 1;'
    new='''#if CODEX_FINE && CODEX_KEEP_ONE
    const int keep = codex_trace::active ? 1 : (tune::kRouteDepth >= 2 ? std::clamp(tune::kRouteK, 1, 8) : 1);
#else
'''+old+'''
#endif
    CODEX_FINE_MARK("route_keep",static_cast<int>(type),round,keep,0);'''
    apply(src/'bot.cpp',((old,new),('    nn_v92best = best;','    nn_v92best = best;\n    CODEX_FINE_MARK("keep_teacher",static_cast<int>(type),round,nn_v92best,target_group);')))
    scoped(src/'nnrec.cpp','void Bot::nn_lazy_score() {','#ifdef A2_NN_FCMP',(
        ('    if (round - nn_pub.at > A2_NN_LAZY_TTL) return;','    CODEX_FINE_MARK("keep_completed",static_cast<int>(type),round,nn_c_camps,nn_est_camps);\n    if (round - nn_pub.at > A2_NN_LAZY_TTL) return;'),))


if __name__=='__main__':
    original=read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']
    cases=[{**deepcopy(original),'stage':name,'patched':flag} for name,flag in (('keepcontrol111',False),('keeppatch111',True))]
    main(label='routekeep111',cases=cases,prepare_fn=prepare,build_fn=exact_build,
         expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
    data=read(HERE/'LIVE109_RUNTIME_TARGET_ROUTEKEEP111.json');control,proposal=data['rows']
    before=read(bench.ROOT/original['traces']['base']['path']);after=read(bench.ROOT/proposal['directory']/'turn.json')
    old,new=action_prefix(before),action_prefix(after)
    natives=[read(bench.ROOT/r['directory']/'native.json') for r in data['rows']]
    errors=any(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()) for n in natives)
    report={'control_matches_original':control['matched_view_and_prefix'] and control['same_native_actor_round'],
            'same_initial_own_view':proposal['same_own_view'],'original_pre_failure_prefix_preserved':new[:len(old)]==old,
            'actor70_removed':70 not in proposal['native_rounds'],
            'full_call_completes70':any(s['mark']=='keep_completed' and s['actual_round']==70 and s['a']>=1 for s in proposal['samples']),
            'published_in70':any(s['mark']=='lazy_pub' and s['actual_round']==70 for s in proposal['samples']),
            'errors':bool(errors),'teacher_marks':{r['case']['stage']:[s for s in r['samples'] if s['mark']=='keep_teacher'] for r in data['rows']},
            'keep_marks':{r['case']['stage']:[s for s in r['samples'] if s['mark']=='route_keep'] for r in data['rows']},
            'raw_sha256':bench.digest(HERE/'LIVE109_RUNTIME_TARGET_ROUTEKEEP111.json')}
    report['pass']=not errors and all(report[k] for k in ('control_matches_original','same_initial_own_view','original_pre_failure_prefix_preserved','actor70_removed','full_call_completes70','published_in70'))
    write(HERE/'LIVE111_ROUTE_KEEP_FIXED_STATE.json',report)
    print(report,flush=True)
