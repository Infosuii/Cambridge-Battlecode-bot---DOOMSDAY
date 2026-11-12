"""Focused third attempt: bound optional planner work after measured fuel regression."""
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'bots/botx3/src/bot.cpp'
text=p.read_text(encoding='utf-8');a,rest=text.split('int Bot::plan_search(',1);b,c=rest.split('// Same identity as the draft',1)
b=b.replace('X3_BANKCYCLE == 2','X3_BANKCYCLE >= 2')
b=b.replace('const bool may = new_rows < 2;', '''const bool may = new_rows < 2
#if X3_BANKCYCLE >= 3
            && bc::fuel_remaining() >= 50000
#endif
            ;''')
b=b.replace('if (bc::fuel_remaining() < tune::kRouteFuel / 2) break;', '''if (bc::fuel_remaining() <
#if X3_BANKCYCLE >= 3
            45000
#else
            tune::kRouteFuel / 2
#endif
            ) break;''')
for index in [2,3]:
    needle=f'for (int g{index} = 0; g{index} < n; ++g{index}) {{'
    assert b.count(needle)==1
    b=b.replace(needle,needle+f'''
#if X3_BANKCYCLE >= 3
                if ((g{index} & 7) == 0 && bc::fuel_remaining() < 45000) break;
#endif''')
b=b.replace('if (tune::kPlanDepth >= 3) {','if (tune::kPlanDepth >= 3 && X3_BANKCYCLE < 3) {')
p.write_text(a+'int Bot::plan_search('+b+'// Same identity as the draft'+c,encoding='utf-8',newline='\n')
