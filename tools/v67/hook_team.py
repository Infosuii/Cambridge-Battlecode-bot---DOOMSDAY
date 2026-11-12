"""Integrate tagged mailboxes into the established execution pipeline (one-use edit)."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'bots/v67/src/bot.cpp'
s=p.read_bytes().decode(); end='\r\n' if '\r\n' in s else '\n'
def change(old,new):
    global s
    old=old.replace('\n',end); new=new.replace('\n',end)
    assert old in s,old[:100]
    s=s.replace(old,new,1)
change('#include "v67_meta.h"','#include "v67_meta.h"\n#include "team_memory.h"')
change('''void Bot::write_claim(int group, bool onsite) {
    if (V67_TEAMPLAY) return;''','''void Bot::write_claim(int group, bool onsite) {
    if (V67_TEAMPLAY) {
        auto memory = team67::put_job(read_shared(),slot,group);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});
        if(slot>=0 && slot<6) {
            team67_[slot].job=group; team67_[slot].job_seen=round;
            claim_cache[slot]=static_cast<std::int16_t>(group<0 ? kClaimCodeIdle : group);
            if(onsite) onsite_bits |= 1u<<slot;
        }
        return;
    }''')
change('    if (V67_TEAMPLAY) { claim_cache.fill(static_cast<std::int16_t>(kClaimCodeIdle)); onsite_bits = 0; return; }',
       '    if (V67_TEAMPLAY) { v67_team_decode(shared); return; }')
change('void Bot::read_sighting() {','void Bot::read_sighting() {\n    if (V67_TEAMPLAY) return;')
change('''void Bot::play_turn() {
#if V67_TEAMPLAY''','''void Bot::play_turn() {
#if V67_TEAMPLAY == 3
    struct Publish67 { Bot* bot; ~Publish67() { bot->v67_team_after_turn(); } } publish67{this};
#endif
#if V67_TEAMPLAY == 1 || V67_TEAMPLAY == 2''')
change('''        w.update(round);
        PROF_CHECK("w_update");''','''        w.update(round);
#if V67_TEAMPLAY == 3
        v67_team_sync();
#endif
        PROF_CHECK("w_update");''')
change('''#if APEX_EVENTS
    // No enemy in view: publish''','''#if APEX_EVENTS && !V67_TEAMPLAY
    // No enemy in view: publish''')
change('''    } else if (hunt()) {
    } else if (tribute_if_needed())''','''#if V67_TEAMPLAY == 3 && V67_COORD
    } else if (v67_team_join()) {
#endif
    } else if (hunt()) {
    } else if (tribute_if_needed())''')
change('''        const float key = ttk / worth;''','''#if V67_TEAMPLAY == 3 && V67_COORD
        if(battle_target67_>=0 && battle_target67_<static_cast<int>(enemy_handles.size()) &&
           e.id==enemy_handles[battle_target67_] && dist<=nearest_d+2) worth*=2.0f;
#endif
        const float key = ttk / worth;''')
p.write_bytes(s.encode())
