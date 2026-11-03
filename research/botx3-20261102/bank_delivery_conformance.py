from pathlib import Path
import importlib.util,json,re
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'bank-delivery-conformance';f=json.loads((s.ROOT/'bots/botx3_6/features.json').read_text())['flags'];flags=[k+'='+v for k,v in f.items()]+['X3_BANK_PROBE=1']
b=s.build('delivery-probe',flags,trace=True);folder=s.OUT/'perimeter'
if not (folder/'candidate.stdout').exists():s.dz.match(b,BASE/'team-contract/opponents/x2.wasm',BASE/'team-unseen-maps/perimeter-banking-2.map26a','A',folder,True,800)
t=(folder/'candidate.stdout').read_text();lines=[l for l in t.splitlines() if l.startswith(('X3_BANK_PROBE','X3_BANK_STATE','X3_BANK_END'))]
assert 'bot error:' not in t and 'X3_BANK_PROBE' in t and 'X3_BANK_STATE' in t
assert all('marker125' in l for l in lines if l.startswith('X3_BANK_STATE'))
completed=[l for l in lines if l.startswith('X3_BANK_END') and 'gems0 ' in l];assert completed,lines[:30]
s.write(s.OUT/'conformance.json',dict(scope='Synthetic delivery order only, no resource/visibility changes; not competitive strength evidence',probes=t.count('X3_BANK_PROBE'),steps=t.count('X3_BANK_STATE'),completed_empty_bag=len(completed),records=lines))
print('Probes',t.count('X3_BANK_PROBE'),'continued delivery steps',t.count('X3_BANK_STATE'),'completed',len(completed),flush=True)
