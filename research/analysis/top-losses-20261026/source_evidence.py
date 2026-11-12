"""Capture reviewed source excerpts without modifying the development bots."""
import hashlib
from collect import ROOT,OUT
specs=[('bots/v62c/src/bot.cpp',58,88),('bots/v62c/src/bot.cpp',1341,1369),
 ('bots/v62c/src/bot.cpp',1783,1809),('bots/v62c/src/bot.cpp',3301,3320),
 ('bots/v62c/src/bot.cpp',5212,5240),('bots/v62c/src/bot.cpp',5394,5440),
 ('bots/v62c/src/common.h',1346,1352),('bots/v62c/src/common.h',1657,1679),
 ('bots/v62c/src/common.h',1039,1051)]
lines=['# Source evidence snapshots','','Exact excerpts from the local v62c source inspected during the audit. These explain code paths; they are not a causal attribution for every game. The duel arm maps to platform63 by recorded group IDs. This review did not rebuild to prove binary-to-source equivalence. Earlier unconditional definitions can override later defaults; use effective-macros.txt for the preprocessed values.','']
for name,a,b in specs:
    p=ROOT/name;src=p.read_text(encoding='utf8').splitlines()
    lines += ['## '+name+':'+str(a),'','SHA256: '+hashlib.sha256(p.read_bytes()).hexdigest(),'','```cpp']
    lines += [f'{i}: {src[i-1]}' for i in range(a,b+1)]
    lines += ['```','']
(OUT/'SOURCE_EVIDENCE.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf8',newline='\n')
