"""Public camp group state queries, including the engine's out-of-vision cooldown reports."""
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'bots/v67/src/world.cpp'
s=p.read_bytes().decode(); e='\r\n' if '\r\n' in s else '\n'
old='''        if (!group_visible[gi]) {
            // Not in view: advance predictions.'''.replace('\n',e)
new='''        if (!group_visible[gi]) {
#if V67_CAMP_STATE
            // These public calls may report a cooldown outside vision. Failure
            // means unknown, and preserves the existing observation prediction.
            std::uint32_t state = 0;
            if (d::sdk_camp_group_state(g.handle, &state) == 0) {
                if (state == 3) {
                    std::int32_t timer = 0;
                    if (d::sdk_camp_group_cooldown(g.handle, &timer) == 0) {
                        g.state = GroupState::respawning;
                        g.respawn_round = round + timer;
                        continue;
                    }
                } else if (state == 2) {
                    g.state = GroupState::reward;
                    g.reward_seen = round;
                    continue;
                } else if (state == 1 && g.state == GroupState::respawning) {
                    g.state = GroupState::alive;
                    for (int ci : g.camps) { camps[ci].hp = camps[ci].max_hp; camps[ci].dead = false; }
                }
            }
#endif
            // Not in view: advance predictions.'''.replace('\n',e)
assert old in s
p.write_bytes(s.replace(old,new,1).encode())
