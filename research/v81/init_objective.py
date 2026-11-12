from pathlib import Path
import shutil,json
root=Path(__file__).resolve().parents[2];out=root/'bots/v85'
if not out.exists():shutil.copytree(root/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
else:assert b'V85_OBJECTIVE' in (out/'src/common.h').read_bytes()
p=out/'src/common.h'
if b'V85_OBJECTIVE' not in p.read_bytes():p.write_bytes(b'#ifndef V85_OBJECTIVE\n#define V85_OBJECTIVE 1\n#endif\n'+p.read_bytes())
p=out/'src/bot.h';s=p.read_text(encoding='utf8')
if 'bool resource_team_objective();' not in s:s=s.replace('    void init();','''    bool resource_team_objective();
#if V85_OBJECTIVE
    bool objective_checked=false;
    std::vector<int> objective_cluster;
    vec2 objective_center{-1,-1},objective_stage{-1,-1};
    int objective_until=-1;
#endif
    void init();''',1);p.write_text(s,encoding='utf8')
p=out/'src/bot.cpp';s=p.read_text(encoding='utf8');at='    } else if (tribute_if_needed()) {\n        mode = "tribute";\n    } else {';assert s.count(at)==1
if 'else if (resource_team_objective())' not in s:s=s.replace(at,'''    } else if (tribute_if_needed()) {
        mode = "tribute";
#if V85_OBJECTIVE
    } else if (resource_team_objective()) {
#endif
    } else {''',1);p.write_text(s,encoding='utf8')
shutil.copyfile(root/'research/v81/objective.cpp',out/'src/objective.cpp')
maps=['00ribs','02famine','00stampede','01concentrated-wealth','01boss-battle']
plan={'note':'Concentrated objective mechanism diagnostic, no holdout','groups':[{'opponent':'pool','maps':[m for m in maps for _ in range(2)],'sides':['a','b']*len(maps)}]}
(root/'research/v81/objective_plan.json').write_text(json.dumps(plan,indent=1)+'\n')
print('Prepared isolated concentrated-resource objective v85')
