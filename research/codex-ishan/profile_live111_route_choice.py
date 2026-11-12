"""EXP219: distinguish original formula, route and NN choices in the matched fixture."""
from engine3_pool import HERE,read
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    anchor='        const int pick = tune::kPlan ? plan_search(top, n_top, bank) : route_search(top, n_top);'
    replacement='''        CODEX_FINE_MARK("route_before",static_cast<int>(type),round,best,n_top);
'''+anchor+'''
        CODEX_FINE_MARK("route_after",static_cast<int>(type),round,pick,pick>=0?top[pick].gi:-1);'''
    scoped(src/'bot.cpp','int Bot::score_groups_full','// Follow-up table',((anchor,replacement),))
    anchor='    nn_lazy_score();'
    # The call occurs in farm, after the formula reference has been selected.
    path=src/'bot.cpp';data=path.read_text(encoding='utf8');assert data.count(anchor)==1
    data=data.replace(anchor,'''    CODEX_FINE_MARK("route_teacher",static_cast<int>(type),round,best,nn_group);
'''+anchor)
    path.write_text(data,encoding='utf8',newline='\n')


if __name__=='__main__':
    main(label='routechoice111',cases=[read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']],prepare_fn=prepare,
         build_fn=exact_build,expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
