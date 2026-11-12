"""Frozen v76 with bounded home-resource diagnostics; no strategic change."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
out=root/'artifacts/tmp/v67/q84hometrace'
assert not out.exists()
shutil.copytree(root/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
p=out/'src/common.h'
p.write_bytes(b'#define V84_HOME_TRACE 1\n'+p.read_bytes())
p=out/'src/bot.cpp';s=p.read_text(encoding='utf8')
at='    drop_ward();'
assert s.count(at)==1
s=s.replace(at,'''#if V84_HOME_TRACE
    if(round<=350 && (round%10==0 || (target_group>=0 && w.groups[target_group].state==GroupState::reward))) {
        std::printf("HO R%d s%d t%d p%d,%d mode=%s job%d gold%d hp%.0f\\n",round,slot,static_cast<int>(type),pos.x,pos.y,mode,target_group,gold,hp);
        if(slot==0)for(std::size_t gi=0;gi<w.groups.size();++gi){const auto& g=w.groups[gi];
            std::printf("HG R%d g%zu gold%u gems%u harmless%d st%d hp%.0f/%0.f cap%d d%d seen%d margin%d\\n",round,gi,g.gold,g.gems,g.harmless,static_cast<int>(g.state),g.hp_left(w.camps),g.max_hp,group_capture_covered(g),w.group_distance(gi,pos),g.seen_round,w.enemy_ready?w.group_margin[gi]:999);
        }
    }
#endif
'''+at)
p.write_text(s,encoding='utf8')
plan={'note':'User MG18208504 home-cycle diagnostic, both sides, no strength claim','groups':[{'opponent':'pool','maps':['01yellow-brick-road']*2,'sides':['a','b']}]}
import json
(root/'research/v81/home_plan.json').write_text(json.dumps(plan,indent=1)+'\n')
print(out)
