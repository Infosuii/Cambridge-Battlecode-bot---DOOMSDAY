"""Create an isolated structural experiment from frozen v76. Never changes v76/v80."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'bots/v81'
if not out.exists(): shutil.copytree(ROOT/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
else: assert b'V81_SEQ' in (out/'src/common.h').read_bytes(), 'refuse unknown existing tree'
p=out/'src/common.h'
if b'#ifndef V81_SEQ' not in p.read_bytes():
    p.write_bytes(b'#ifndef V81_SEQ\n#define V81_SEQ 1\n#endif\n#ifndef V81_SEQ_DIAG\n#define V81_SEQ_DIAG 0\n#endif\n'+p.read_bytes())
p=out/'src/bot.h';code=p.read_text(encoding='utf8')
if 'bool sequence_combat();' not in code: code=code.replace('    void init();','    bool sequence_combat();\n    void init();',1)
p.write_text(code,encoding='utf8')
p=out/'src/bot.cpp';code=p.read_text(encoding='utf8')
at='    if (tune::kTSearch && c1_acts && nearest_d <= tune::kTsRange && tactical_search()) {'
assert code.count(at)==1
code=code.replace(at,'''#if V81_SEQ
    // Strategic verdict remains the frozen control's. One planner owns the complete engagement action sequence.
    if (target && !(in_danger && !winning) && c1_acts && nearest_d <= 5 && sequence_combat()) {
        mode = "sequence";
        return true;
    }
#endif
'''+at)
p.write_text(code,encoding='utf8')
shutil.copyfile(ROOT/'research/v81/sequence.cpp',out/'src/sequence.cpp')
print('Prepared isolated bots/v81 from frozen bots/v76')
