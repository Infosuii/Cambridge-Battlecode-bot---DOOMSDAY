"""Isolate economic capture-region denial from frozen v76."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2];out=root/'bots/v84'
assert not out.exists()
shutil.copytree(root/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
p=out/'src/common.h';p.write_bytes(b'#ifndef V84_DENIAL\n#define V84_DENIAL 1\n#endif\n'+p.read_bytes())
p=out/'src/bot.h';s=p.read_text(encoding='utf8');s=s.replace('    void init();','''    bool deny_income_region();
#if V84_DENIAL
    int denial_group=-2;
    vec2 denial_anchor{-1,-1};
#endif
    void init();''',1);p.write_text(s,encoding='utf8')
p=out/'src/bot.cpp';s=p.read_text(encoding='utf8');at='    } else if (hunt()) {';assert s.count(at)==1
s=s.replace(at,'''#if V84_DENIAL
    } else if (deny_income_region()) {
#endif
'''+at,1);p.write_text(s,encoding='utf8')
shutil.copyfile(root/'research/v81/denial.cpp',out/'src/denial.cpp')
print('Prepared isolated denial experiment v84')
