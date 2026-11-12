from pathlib import Path
import sys,os,importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'large-camp-conformance'
sys.path[:0]=[os.environ['DZ_MAPGEN_DEPS'],str(s.ROOT/'tools/mapgen')]
from mapbuilder import Engine,MapBuilder,loads_in_game
os.environ['BC_ENGINE_WASM']=str(next((Path(os.environ['LOCALAPPDATA'])/'cambc/assets').rglob('mapeditor/assets/v2_0_0*.wasm')))
s.OUT.mkdir(exist_ok=True);m=s.OUT/'large-wolves.map26a'
if not m.exists():
 e=Engine();mb=MapBuilder(e,40,40,'rotational')
 try:
  mb.team_size(3);mb.spawn(1,1,4,4);mb.altar(3,19)
  for x in range(8,12):
   for y in range(8,11):mb.camp('wolf',x,y)
  mb.verify();data=mb.encode();assert loads_in_game(e,data);m.write_bytes(data)
 finally:mb.destroy()
f=json.loads((s.ROOT/'bots/botx3_10/features.json').read_text())['flags'];f['X1_FUEL_PROBE']='1'
for label,roster,chip,siege in [('chip','cd::vendetta,cd::varg,cd::heart_of_ruin',1,1),('siege','cd::tavi,cd::stellar,cd::varg',0,1)]:
 flags=dict(f,X3_CHIP_PLAN_USE=str(chip),X3_SIEGE_ADMIT_USE=str(siege),TOP_PICKS3=roster,TOP_PICKS4=roster+',cd::ren',TOP_PICKS5=roster+',cd::ren,cd::vesper_vale')
 b=s.build(label,[k+'='+v for k,v in flags.items()],trace=True);folder=s.OUT/label
 if not (folder/'candidate.stdout').exists():s.dz.match(b,BASE/'team-contract/opponents/x1.wasm',m,'A',folder,True,300)
 t=(folder/'candidate.stdout').read_text();signal='X3_CHIP_ADMIT' if label=='chip' else 'X3_SIEGE_ADMIT'
 assert 'bot error:' not in t and signal in t,(label,t[-3000:])
 records=[l for l in t.splitlines() if l.startswith(('X3_CHIP_ADMIT','X3_SIEGE_ADMIT','X3_CONFIG'))]
 s.write(s.OUT/(label+'.json'),dict(scope='Synthetic native large-camp activation only, not strength evidence',records=records))
 print(label,'native admissions',t.count(signal),flush=True)
