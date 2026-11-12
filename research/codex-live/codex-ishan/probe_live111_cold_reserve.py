"""Controlled charged probes of the first NN reservation on one frozen acting view."""
from copy import deepcopy

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from live111_cold_reserve import patch
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument
from turn_prefix import action_prefix


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    patch(src,enabled and case['patched'],case)
    apply(src/'bot.cpp',(('    nn_v92best = best;','    nn_v92best = best;\n    CODEX_FINE_MARK("teacher_pick",static_cast<int>(type),round,nn_v92best,target_group);'),))
    scoped(src/'nnrec.cpp','void Bot::nn_lazy_score() {','#ifdef A2_NN_FCMP',(
        ('    std::uint64_t enemy_used = 0;','    std::uint64_t enemy_used = 0;\n    CODEX_FINE_MARK("cold_reserved",static_cast<int>(type),round,nn_sg_need,nn_c_camps);'),
        ('    if (round - nn_pub.at > A2_NN_LAZY_TTL) return;','    CODEX_FINE_MARK("cold_completed",static_cast<int>(type),round,nn_c_camps,nn_est_camps);\n    if (round - nn_pub.at > A2_NN_LAZY_TTL) return;'),))


if __name__=='__main__':
    original=read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']
    cases=[{**deepcopy(original),'stage':name,'patched':flag} for name,flag in (('coldcontrol111',False),('coldpatch111',True))]
    main(label='coldreserve111r2',cases=cases,prepare_fn=prepare,build_fn=exact_build,expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
    data=read(HERE/'LIVE109_RUNTIME_TARGET_COLDRESERVE111R2.json')
    control,proposal=data['rows']
    before=read(bench.ROOT/original['traces']['base']['path'])
    after=read(bench.ROOT/proposal['directory']/'turn.json')
    old,new=action_prefix(before),action_prefix(after)
    native=read(bench.ROOT/proposal['directory']/'native.json')
    control_native=read(bench.ROOT/control['directory']/'native.json')
    errors=any(bool(n['diagnostics']['codes']) or any(n['diagnostics']['botFaults'].values()) for n in (native,control_native))
    completes=[s for s in proposal['samples'] if s['mark']=='cold_completed']
    publishes=[s for s in proposal['samples'] if s['mark']=='lazy_pub']
    report={'control_matches_original':control['matched_view_and_prefix'] and control['same_native_actor_round'],
            'same_initial_own_view':proposal['same_own_view'],'original_pre_failure_prefix_preserved':new[:len(old)]==old,
            'actor70_removed':70 not in proposal['native_rounds'],'completed_full_call_in70':any(s['actual_round']==70 and s['a']>=1 for s in completes),
            'published_in70':any(s['actual_round']==70 for s in publishes),'errors':errors,
            'teacher_references':{r['case']['stage']:[s for s in r['samples'] if s['mark']=='teacher_pick'] for r in data['rows']},
            'raw_report_sha256':bench.digest(HERE/'LIVE109_RUNTIME_TARGET_COLDRESERVE111R2.json')}
    report['pass']=not errors and all(report[k] for k in ('control_matches_original','same_initial_own_view','original_pre_failure_prefix_preserved','actor70_removed','completed_full_call_in70','published_in70'))
    write(HERE/'LIVE111_COLD_RESERVE_FIXED_STATE.json',report)
    print(report,flush=True)
