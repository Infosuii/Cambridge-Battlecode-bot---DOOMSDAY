"""EXP224 real-turn snapshot/stage equality proof, never a production yield policy."""
import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    (src/'coherent_nn_frame.h').write_bytes((HERE/'coherent_nn_frame.h').read_bytes())
    apply(src/'nnrec.cpp',(('#include "bot.h"','#include "bot.h"\n#if CODEX_FINE\n#include "coherent_nn_frame.h"\n#endif'),))
    path=src/'nnrec.cpp';data=path.read_text(encoding='utf8')
    first=data.index('    if (nn_warm == 2 && f0 >= nn_est_camps')
    last=data.index('        const std::uint64_t f1 = bc::fuel_remaining();',first)
    body=data[first:last]
    anchor='        nn::live_camps(nn_lf, nn_lv, w.groups.size());\n        cmark(1);'
    assert body.count(anchor)==1
    body=body.replace(anchor,'''#if CODEX_FINE
        static codex_frame::Frame<kNF> frame;
        const bool frame_active=codex_trace::active;
        std::uint32_t frame_hash=0;
        if(frame_active) {
            CODEX_FINE_MARK("frame_copy_begin",static_cast<int>(type),round,sizeof(nn::Live),nn_lv.cache.size());
            frame.begin(nn_lf,nn_lv,w.groups.size(),round);
            CODEX_FINE_MARK("frame_copy_end",static_cast<int>(type),round,sizeof(frame),frame.groups);
            frame_hash=frame.input_hash();
        }
#endif
'''+anchor)
    body+='''#if CODEX_FINE
        if(frame_active) {
            const bool original_ready=nn_lv.z_ok;
            float original[nn::kNC+1];
            std::copy(nn_lo.target,nn_lo.target+nn::kNC+1,original);
            CODEX_FINE_MARK("frame_reference",static_cast<int>(type),round,original_ready,bc::round_number());
            for(int stage=0;stage<5;++stage) {
                // Diagnostic only: each subsequent pure stage gets one normal owner turn.
                if(stage) bc::end_turn();
                CODEX_FINE_MARK("frame_stage_begin",static_cast<int>(type),round,stage,0);
                frame.advance();
                CODEX_FINE_MARK("frame_stage_end",static_cast<int>(type),round,stage,0);
            }
            const bool equal=std::memcmp(original,frame.output.target,sizeof(original))==0;
            CODEX_FINE_MARK("frame_equal",static_cast<int>(type),round,equal,original_ready&&frame.ready());
            CODEX_FINE_MARK("frame_inputs",static_cast<int>(type),round,frame_hash,frame.input_hash());
            CODEX_FINE_MARK("frame_age",static_cast<int>(type),round,bc::round_number()-frame.captured_at,frame.fresh(bc::round_number(),A2_NN_LAZY_TTL));
            codex_trace::flush();
            bc::resign();
        }
#endif
'''
    path.write_text(data[:first]+body+data[last:],encoding='utf8',newline='\n')


if __name__=='__main__':
    main(label='coherentframe111r2',cases=[read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']],prepare_fn=prepare,
         build_fn=exact_build,expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
    raw=HERE/'LIVE109_RUNTIME_TARGET_COHERENTFRAME111R2.json';r=read(raw)['rows'][0]
    marks={s['mark']:s for s in r['samples'] if s['mark'] in ('frame_equal','frame_inputs','frame_age')}
    assert set(marks)=={'frame_equal','frame_inputs','frame_age'}
    native=read(bench.ROOT/r['directory']/'native.json')
    errors=bool(native['diagnostics']['codes'] or any(native['diagnostics']['botFaults'].values()))
    result={'scope':'Numerical/coherence proof with deliberately slow diagnostic normal-turn yields; no safety/progress/strength claim',
            'off_exact':read(raw)['off_matches_recorded_baseline'],'same_initial_own_view':r['same_own_view'],
            'all_target_logits_bit_equal':marks['frame_equal']['a']==1,'both_ready':marks['frame_equal']['b']==1,
            'input_immutable':marks['frame_inputs']['a']==marks['frame_inputs']['b'],
            'completion_age':marks['frame_age']['a'],'stale_rejected_at_ttl2':marks['frame_age']['a']>2 and marks['frame_age']['b']==0,
            'errors':errors,'native_actor_fuel_rounds':r['native_rounds'],'raw_sha256':bench.digest(raw),'marks':r['samples']}
    result['pass']=not errors and all(result[k] for k in ('off_exact','same_initial_own_view','all_target_logits_bit_equal','both_ready','input_immutable','stale_rejected_at_ttl2'))
    write(HERE/'COHERENT_NN_FRAME_FIXED_STATE.json',result)
    print({k:v for k,v in result.items() if k!='marks'},flush=True)
