"""Generate an exact accepted-action puppet from an independently validated input script."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT

HEADER = r'''// Generated accepted-input replay puppet. Local diagnostic only.
#include <cambc.h>
#include <cstdio>
#include <cstdint>
namespace bc=cambc;
struct Action { int kind; std::int32_t p[5]; };
struct Turn { std::uint32_t round, actor, first, count; };
'''
FOOTER = r'''
int main() {
    std::uint32_t misses=0;
    for (;;) {
        if (bc::is_draft()) {
            const auto i=bc::draft::current_draft(bc::team::ally).size();
            if(i < sizeof(draft)/sizeof(draft[0])) bc::detail::check(bc::detail::sdk_draft_champion(draft[i]));
            bc::end_turn(); continue;
        }
        const auto r=bc::round_number(), id=static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self()));
        std::uint32_t lo=0,hi=sizeof(turns)/sizeof(turns[0]);
        const std::uint64_t key=(std::uint64_t(r)<<32)|id;
        while(lo<hi){auto m=(lo+hi)/2;auto mk=(std::uint64_t(turns[m].round)<<32)|turns[m].actor;if(mk<key)lo=m+1;else hi=m;}
        if(lo==sizeof(turns)/sizeof(turns[0])||turns[lo].round!=r||turns[lo].actor!=id){
            if(misses++<8)std::printf("puppet missing r=%u actor=%u\n",r,id);bc::end_turn();continue;
        }
        const Turn t=turns[lo]; bool exhausted=false;
        for(std::uint32_t j=t.first;j<t.first+t.count;++j){const auto &a=actions[j];const auto *p=a.p;int rc=0,result=0;
            switch(a.kind){
            case 0:rc=bc::detail::sdk_set_priority(p[0]);break;
            case 1:rc=bc::detail::sdk_move_to(p[0],p[1],&result);break;
            case 2:rc=bc::detail::sdk_attack(p[0],p[1]);break;
            case 3:rc=bc::detail::sdk_cast(p[0],p[1],p[2],p[3],p[4],&result);break;
            case 4:rc=bc::detail::sdk_recall();break;
            case 5:rc=bc::detail::sdk_submit_gems(p[0],p[1]);break;
            case 6:rc=bc::detail::sdk_buy_item(p[0],p[1]);break;
            case 7:rc=bc::detail::sdk_cancel_channel();break;
            case 8:rc=bc::detail::sdk_buy_consumable(p[0]);break;
            case 9:rc=bc::detail::sdk_use_consumable(p[0],p[1],p[2],&result);break;
            case 10:rc=bc::detail::sdk_place_ward(p[0],p[1],&result);break;
            case 11:rc=bc::detail::sdk_sell(p[0]);break;
            case 100:
                if(p[0]==1){
                    // The official fuel pause resumes this VM in a later round.
                    // Do not yield the new turn when this old frame resumes.
                    while(bc::round_number()==r){volatile std::uint32_t busy=0;for(int k=0;k<100;++k)busy=busy+1;}
                    exhausted=true;
                } else if(p[0]==2){__builtin_trap();}
                break;
            default:__builtin_trap();
            }
            if(rc){if(misses++<8)std::printf("puppet rejected r=%u actor=%u index=%u kind=%d rc=%d\n",r,id,j,a.kind,rc);break;}
            if(bc::round_number()!=r){exhausted=true;break;}
        }
        if(!exhausted)bc::end_turn();
    }
}
'''


def generate(script, side, destination):
    assert script['partition'] in ('calibration-excluded', 'examined')
    assert script['validation']['replay_bytes_identical']
    selected = [r for r in script['inputs'] if r['team'] == side]
    draft = [r['args'][1] for r in selected if r['tag'] == 4]
    assert draft
    groups = {}
    for row in selected:
        if row['phase'] == 12:
            continue
        assert row['actor'] is not None
        groups.setdefault((row['r'], row['actor']), []).append(row)
    code = [HEADER, 'static constexpr int draft[]={' + ','.join(map(str, draft)) + '};', 'static constexpr Action actions[]={']
    turns, index = [], 0
    for (r, actor), rows in sorted(groups.items()):
        first = index
        assert rows[-1]['tag'] == 3 or rows[-1]['input'] == script['inputs'][-1]['input'], 'Unterminated nonfinal turn'
        for row in rows:
            kind = row['action'] if row['tag'] == 0 else 100 if row['tag'] == 3 else None
            assert kind is not None
            args = row['args'][:]
            if kind == 2:
                assert args.pop() == 65535
            if kind == 8:
                assert args[1] == 1
            args += [0] * (5 - len(args))
            # Preserve uint32 handle bit patterns in a fixed int32 literal array.
            args = [v if v < 2**31 else v - 2**32 for v in args]
            code.append('{' + str(kind) + ',{' + ','.join(map(str, args)) + '}},')
            index += 1
        turns.append((r, actor, first, index - first))
    code += ['};', 'static constexpr Turn turns[]={']
    code += ['{' + ','.join(map(str, t)) + '},' for t in turns]
    code += ['};', FOOTER]
    raw = ('\n'.join(code) + '\n').encode()
    destination = Path(destination).resolve()
    assert destination.is_relative_to(ROOT / 'artifacts')
    target = destination / 'src/main.cpp'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, 'Use a fresh directory after puppet-generator changes'
    target.write_bytes(raw)
    result = {'match_id': script['match_id'], 'side': side, 'turns': len(turns), 'actions': index,
              'replay_sha256': script['replay_sha256'], 'map_sha256': script['map_sha256'],
              'source_sha256': hashlib.sha256(raw).hexdigest(), 'draft': draft,
              'fuel': 'recorded exhaustion induced using default official fuel; validate resulting state trajectory',
              'server_wasm_identity': 'unavailable; exact source reproduction is tested independently'}
    (destination / 'puppet-identity.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script', type=Path)
    ap.add_argument('--side', type=int, choices=[0, 1], required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(generate(json.loads(a.script.read_text(encoding='utf-8')), a.side, a.out)))


if __name__ == '__main__':
    main()
