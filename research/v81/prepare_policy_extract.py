"""Derive a thin actual-observation policy extractor from the verified audit exporter."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
code=(root/'research/v75/teamfight_scripts/audit.mjs').read_text(encoding='utf8')
code=code.replace("'../../../tools/replay/engine.mjs'","'../../tools/replay/engine.mjs'")
code=code.replace('state=u(E.buf+40),type=i(E.buf+4);','state=u(E.buf+40),type=i(E.buf+4),str=dv().getFloat32(E.buf+24,true),focus=dv().getFloat32(E.buf+28,true),range=i(E.buf+36);')
old='foes:foes.map(e=>[e.entity.index,e.position.x,e.position.y]),'
new='''str,focus,range,gems:self.gems,
          foes:foes.map(e=>[e.entity.index,e.position.x,e.position.y,e.health,e.maxHealth,e.strength?.effective??0,e.focus?.effective??0,e.attackRange??1,e.type]),
          allies:view.champions.filter(e=>e.entity.index!==c && e.team===team && e.alive && e.position).map(e=>[e.entity.index,e.position.x,e.position.y,e.health,e.maxHealth,e.strength?.effective??0,e.focus?.effective??0,e.attackRange??1,e.type]),'''
assert old in code
code=code.replace(old,new)
code=code.replace('fs.writeFileSync(output,JSON.stringify({until,kits,groups,turns,frames}));','fs.writeFileSync(output,JSON.stringify({until,kits,turns}));')
(root/'research/v81/policy_extract.mjs').write_text(code,encoding='utf8')
code=(root/'research/v75/teamfight_scripts/audit_batch.py').read_text(encoding='utf8')
code=code.replace("'audit500.json'","'policy500.json'").replace("'research/v75/teamfight_scripts/audit.mjs'","'research/v81/policy_extract.mjs'")
(root/'research/v81/policy_batch.py').write_text(code,encoding='utf8')
print('Prepared actual-observation policy extractor')
