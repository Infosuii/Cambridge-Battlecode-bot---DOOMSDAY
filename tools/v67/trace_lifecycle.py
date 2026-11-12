"""Trace a flat experimental controller without changing its benchmark source."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--bot',required=True)
ap.add_argument('--map',default='00quadrants')
ap.add_argument('--name',required=True)
a=ap.parse_args()
assert a.name.replace('-','').replace('_','').isalnum()
copy=ROOT/'artifacts/tmp/v67'/('trace-source-'+a.name)
assert not copy.exists()
shutil.copytree(ROOT/a.bot/'src',copy/'src')
p=copy/'src/bot.cpp';s=p.read_bytes().decode();e='\r\n' if '\r\n' in s else '\n'
old='    struct Publish67 { Bot* bot; ~Publish67() { bot->v67_team_after_turn(); } } publish67{this};'
assert s.count(old)==1
new='''    struct Publish67 {
        Bot* bot;
        ~Publish67() {
#if V67_TRACE
            if(bot->inited&&bot->round%25==0&&bc::self().is_alive()) {
                const int job=bot->target_group;
                std::printf("T67 r%d s%d %s p%d,%d hp%.0f/%.0f gold%d bag%d job%d state%d left%.0f allies%zu fields%d fuel%llu\\n",
                    bot->round,bot->slot,bot->mode,bot->pos.x,bot->pos.y,bot->hp,bot->max_hp,bot->gold,bot->gems,
                    job,job>=0&&job<int(bot->w.groups.size())?int(bot->w.groups[job].state):-1,
                    job>=0&&job<int(bot->w.groups.size())?bot->w.groups[job].hp_left(bot->w.camps):-1.0f,
                    bot->w.allies.size(),bot->field_calls,static_cast<unsigned long long>(bc::fuel_remaining()));
                if(bot->slot==0&&bot->round<=100&&job>=0&&job<int(bot->w.groups.size())) {
                    for(int ci:bot->w.groups[job].camps) {
                        const auto& c=bot->w.camps[ci];cambc::detail::camp_state state{};
                        const int code=cambc::detail::sdk_camp(static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c.camp)),&state);
                        std::printf("C67 r%d c%d p%d,%d remembered%.0f dead%d visible%d dist%d api%d live%.0f\\n",
                            bot->round,ci,c.pos.x,c.pos.y,c.hp,c.dead,bit(bot->w.visible,c.pos),cheb(bot->pos,c.pos),code,state.health);
                    }
                    std::printf("A67 r%d range%d move%d attack%d ward%d cast%d\\n",bot->round,bot->range,
                        bc::self().can_move(),bc::self().can_attack(),int(bc::self().ward_cooldown()),bot->cast_done);
                }
            }
#endif
            bot->v67_team_after_turn();
        }
    } publish67{this};'''
p.write_bytes(s.replace(old,new.replace('\n',e)).encode())
command=[sys.executable,'tools/v67/trace.py','--bot',str(copy.relative_to(ROOT)),'--map',a.map,
         '--out','artifacts/evaluations/v67/'+a.name]
raise SystemExit(subprocess.run(command,cwd=ROOT).returncode)
