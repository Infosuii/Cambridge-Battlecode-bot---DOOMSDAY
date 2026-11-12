"""Prepare a separate event-based coalition scheduler and an idle economy diagnostic opponent."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
out=root/'bots/v82'
assert not out.exists()
shutil.copytree(root/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
p=out/'src/common.h';p.write_bytes(b'#ifndef V82_SCHEDULE\n#define V82_SCHEDULE 1\n#endif\n#ifndef V82_DIAG\n#define V82_DIAG 0\n#endif\n'+p.read_bytes())
p=out/'src/bot.h';code=p.read_text(encoding='utf8')
code=code.replace('    void init();','''    int scheduled_farm();
    std::array<vec2,6> schedule_pos{};
    std::array<int,6> schedule_last{-1,-1,-1,-1,-1,-1};
    void init();''',1)
p.write_text(code,encoding='utf8')
p=out/'src/bot.cpp';code=p.read_text(encoding='utf8')
at='    if (avoid_until.size() != w.groups.size()) avoid_until.assign(w.groups.size(), 0);'
assert code.count(at)==1
code=code.replace(at,at+'''
#if V82_SCHEDULE
    if (const int result=scheduled_farm(); result>=0) return result!=0;
#endif
''',1)
p.write_text(code,encoding='utf8')
shutil.copyfile(root/'research/v81/scheduler.cpp',out/'src/scheduler.cpp')
idle=root/'bots/idle81'
assert not idle.exists()
shutil.copytree(root/'bots/v76/src',idle/'src',copy_function=shutil.copyfile)
(idle/'src/main.cpp').write_text('''#include "common.h"
#include "draft.h"
int main(){while(true){if(bc::is_draft())play_draft();bc::end_turn();}}
''',encoding='utf8')
print('Prepared v82 scheduler and idle81 diagnostic opponent')
