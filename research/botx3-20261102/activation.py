"""Separate metered diagnostic builds; never count as competitive evidence."""
from pathlib import Path
import importlib.util,json
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
for label,flags in [('trace-end500',s.ARMS['end500']),('trace-cycle',['X3_BANKCYCLE=1']),('trace-planner',['APEX_PLAN=1','X3_BANKCYCLE=2'])]:
    bot=s.build(label,flags,trace=True)
    folder=s.OUT/'diagnostics'/label
    if not (folder/'receipt.json').exists():
        s.dz.match(bot,s.OUT/'opponents/v92.wasm',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a','A',folder,True,550)
    lines=[l for l in (folder/'candidate.stdout').read_text().splitlines() if l.startswith('X3_')]
    (folder/'activation.json').write_text(json.dumps(lines,indent=2)+'\n')
    print(label,len(lines),'trace records',lines[:4],lines[-4:],flush=True)
