"""EXP247 same-round immutable publication and ordinary gameplay fixture."""
from copy import deepcopy

import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_owned_executor import patch
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument
from turn_prefix import action_prefix


def old_eval():
    text=(SDK_ROOT/'bots/live111/src/nnrec.cpp').read_text(encoding='utf8')
    a=text.index('    if (nn_warm == 2 && f0 >= nn_est_camps')
    b=text.index('    nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;',a)
    return text[a:b]


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    header=src/'codex_trace.h';text=header.read_text(encoding='utf8')
    text=text.replace('inline Record records[96];','inline Record records[384];').replace('count >= 96','count >= 384').replace('inline char buffer[16384];','inline char buffer[65536];')
    text=text.replace('inline unsigned count = 0;','inline unsigned count = 0;\ninline bool frame_published=false;')
    text=text.replace('round==CODEX_TARGET_ROUND','round>=CODEX_TARGET_ROUND&&round<=CODEX_TARGET_ROUND+2')
    header.write_text(text,encoding='utf8',newline='\n')
    p=src/'main.cpp';text=p.read_text(encoding='utf8');anchor='if (codex_trace::count) {';assert text.count(anchor)==1
    text=text.replace(anchor,'if (codex_trace::count && (codex_trace::frame_published || bc::round_number()>=CODEX_TARGET_ROUND+3)) {')
    p.write_text(text,encoding='utf8',newline='\n')
    patch(src,enabled and case['patched'])
    # Production has no type/round scope. Only this controlled fixture preserves the old path before R70.
    p=src/'nnrec.cpp';text=p.read_text(encoding='utf8');body=(HERE/'owned_exec_body.inc').read_text(encoding='utf8');assert text.count(body)==1
    text=text.replace(body,'    if(codex_trace::active) {\n'+body+'    } else {\n'+old_eval()+'    }\n')
    text=text.replace('~RealCoreFuel(){nn_spent=0;}','~RealCoreFuel(){if(codex_trace::active)nn_spent=0;}')
    text=text.replace('if(cxowned_active)return;','if(codex_trace::active&&cxowned_active)return;')
    start='        cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);\n        nn_sg_need='
    a=text.index(start);b=text.index(';',a+len(start))+1;block=text[a:b]
    original='        nn_sg_need = nn_warm == 2 ? nn_est_camps + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;'
    text=text[:a]+'        if(codex_trace::active) {\n'+block+'\n        } else {\n'+original+'\n        }'+text[b:]
    anchor='    cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);\n    if(codex_trace::active&&cxowned_active)return; // preserve exclusive ownership'
    assert text.count(anchor)==1
    text=text.replace(anchor,'    if(codex_trace::active)cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);\n    if(codex_trace::active&&cxowned_active)return; // preserve exclusive ownership')
    p.write_text(text,encoding='utf8',newline='\n')
    p=src/'bot.cpp';text=p.read_text(encoding='utf8');assert text.count('        pick == target_group &&')==1
    p.write_text(text.replace('        pick == target_group &&','        (!codex_trace::active || pick == target_group) &&'),encoding='utf8',newline='\n')


if __name__=='__main__':
    original=read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']
    cases=[{**deepcopy(original),'stage':name,'patched':flag} for name,flag in (('ownedcontrol111',False),('ownedexec111',True))]
    main(label='ownedexec111',cases=cases,prepare_fn=prepare,build_fn=exact_build,
         expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-owned-target')
    raw=HERE/'LIVE109_RUNTIME_TARGET_OWNEDEXEC111.json';data=read(raw);control,proposal=data['rows']
    before=read(bench.ROOT/original['traces']['base']['path']);after=read(bench.ROOT/proposal['directory']/'turn.json')
    a,b=action_prefix(before),action_prefix(after)
    natives=[read(bench.ROOT/r['directory']/'native.json') for r in data['rows']]
    errors=any(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()) for n in natives)
    pubs=[s for s in proposal['samples'] if s['mark']=='owner_published']
    report={'control_matches_original':control['same_own_view'] and control['same_action_prefix'] and control['same_native_actor_round'],
            'same_initial_own_view':proposal['same_own_view'],'old_prefix_preserved':b[:len(a)]==a,
            'normal_extra_gameplay_in70':len(b)>len(a),'actor70to72_removed':not any(70<=r<=72 for r in proposal['native_rounds']),
            'immutable_same_round_publication':any(s['actual_round']==70 and s['a']==70 and s['b']==1 for s in pubs),
            'errors':bool(errors),'publication_marks':pubs,'native_actor_rounds':proposal['native_rounds'],'raw_sha256':bench.digest(raw)}
    report['pass']=not errors and all(report[k] for k in ('control_matches_original','same_initial_own_view','old_prefix_preserved','normal_extra_gameplay_in70','actor70to72_removed','immutable_same_round_publication'))
    write(HERE/'LIVE111_OWNED_EXECUTOR_MECHANISM.json',report);print(report,flush=True)
