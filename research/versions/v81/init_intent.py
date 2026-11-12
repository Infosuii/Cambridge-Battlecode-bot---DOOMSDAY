from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2];out=root/'bots/v83'
if not out.exists():shutil.copytree(root/'bots/v76/src',out/'src',copy_function=shutil.copyfile)
else:assert b'V83_INTENT' in (out/'src/common.h').read_bytes()
p=out/'src/common.h'
if b'V83_INTENT' not in p.read_bytes():p.write_bytes(b'#ifndef V83_INTENT\n#define V83_INTENT 1\n#endif\n'+p.read_bytes())
p=out/'src/bot.h';code=p.read_text(encoding='utf8')
if 'learned_intent();' not in code:code=code.replace('    void init();','    int learned_intent();\n    void init();',1)
p.write_text(code,encoding='utf8')
p=out/'src/bot.cpp';code=p.read_text(encoding='utf8')
at='    const bool c1_acts = (in_danger && !winning) ||'
assert code.count(at)==1
if 'intent=learned_intent()' not in code:code=code.replace(at,'''#if V83_INTENT
    // A single learned stance arbitrates the engagement stage; existing legal fight/flee execution follows.
    if (const int intent=learned_intent(); intent>=0) {
        if(intent==0){winning=false;in_danger=true;if(threat_on_me<=0)threat_on_me=1.0f;}
        else if(intent==2 && target){winning=true;in_danger=false;}
    }
#endif
'''+at,1)
p.write_text(code,encoding='utf8')
for name in ('intent.cpp','intent_model.h'):shutil.copyfile(root/'research/v81'/name,out/'src'/name)
print('Prepared isolated v83 learned tactical policy')
