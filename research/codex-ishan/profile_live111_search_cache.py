"""Read the real existing SGAUTO cache state in the already matched cold overrun."""
from engine3_pool import HERE,read
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument


def cache(src,enabled,case):
    instrument(src,enabled,case)
    anchor='    const std::uint64_t left = (bc::fuel_remaining() + nn_spent);'
    addition=anchor+'''
#if CODEX_FINE
    if(codex_trace::active){
        CODEX_FINE_MARK("sg_budget",0,0,nn_sg_need,est);
        CODEX_FINE_MARK("sg_cache",0,0,hint,pick);
        const bool valid=pick>=0&&pick<static_cast<int>(w.groups.size());
        CODEX_FINE_MARK("sg_state",0,0,valid?static_cast<int>(w.groups[pick].state):-1,valid?avoid_until[pick]:-1);
        CODEX_FINE_MARK("sg_hint",0,0,participants_hint,round);
    }
#endif'''
    scoped(src/'bot.cpp','#elif defined(A2_NN_SGAUTO)','\n#else\nint Bot::score_groups',((anchor,addition),))


if __name__=='__main__':
    main(label='searchcache111',cases=[read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']],prepare_fn=cache,
         build_fn=exact_build,expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
