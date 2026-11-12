"""Generate the repository's self-contained, GitHub-compatible SVG figures."""
from pathlib import Path
from html import escape

OUT=Path(__file__).resolve().parent
BG='#0b111b'; PANEL='#121e2d'; LINE='#26384d'; TEXT='#edf3fa'; MUTED='#a8bbcf'; ORANGE='#f38a60'; CYAN='#64ddc5'; BLUE='#9abaff'
FONT='Segoe UI,Arial,Helvetica,sans-serif'

def start(w,h,title):
 return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">',f'<title>{escape(title)}</title>', '<defs><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#9abaff" stroke-opacity=".045"/></pattern><linearGradient id="accent"><stop stop-color="#f38a60"/><stop offset="1" stop-color="#64ddc5"/></linearGradient></defs>',f'<rect width="{w}" height="{h}" rx="20" fill="{BG}"/>',f'<rect width="{w}" height="{h}" rx="20" fill="url(#grid)"/>']
def rect(s,x,y,w,h,fill=PANEL,stroke=LINE,r=12):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
def text(s,x,y,t,size=20,color=TEXT,weight=400,spacing=None):
 a=f' letter-spacing="{spacing}"' if spacing else ''
 s.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}"{a}>{escape(t)}</text>')
def line(s,x1,y1,x2,y2,color=LINE,width=2,dash=False):s.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="6 7"' if dash else '')+'/>')
def dot(s,x,y,color,r=5):s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
def write(name,s):(OUT/name).write_text('\n'.join(s+['</svg>'])+'\n',encoding='utf8')

s=start(1280,620,'DOOMSDAY — autonomous strategy under constraint. Historical peaks: fifth UK lobby, forty-first international. Final recommended local build: v306.')
s.append('<rect x="48" y="48" width="72" height="4" rx="2" fill="url(#accent)"/>')
text(s,48,89,'CAMBRIDGE BATTLECODE  /  2026',17,MUTED,600,3)
text(s,42,199,'DOOMSDAY',102,TEXT,800,1)
text(s,48,254,'AUTONOMOUS STRATEGY. EVERY TURN.',23,ORANGE,700,1)
text(s,48,301,'C++20 → WebAssembly',23,TEXT,500)
text(s,48,338,'Rules · neural ranking · short combat simulation',20,MUTED)
rect(s,48,372,309,38,fill='#172a2b',stroke='#2d5b53',r=19)
text(s,67,397,'FINAL LOCAL RELEASE  /  v306',15,CYAN,700,1)
rect(s,844,48,388,362,stroke='#334962')
text(s,866,80,'TACTICAL SCHEMATIC',13,MUTED,600,2)
for i in range(8):
 for j in range(6):
  if (i,j) in {(2,1),(2,2),(2,3),(5,2),(5,3),(5,4)}:rect(s,872+i*40,103+j*40,31,31,fill='#293647',stroke='#34465c',r=4)
line(s,892,321,972,321,CYAN,3);line(s,972,321,1052,241,CYAN,3);line(s,1052,241,1132,241,CYAN,3);line(s,1132,241,1172,161,CYAN,3)
for x,y in [(892,321),(932,361),(892,281)]:dot(s,x,y,CYAN,7)
for x,y in [(1132,161),(1172,121)]:dot(s,x,y,ORANGE,7)
s.append(f'<path d="M1052 215l12 12-12 12-12-12z" fill="{BLUE}"/>')
text(s,1013,381,'OBSERVE → DECIDE → ACT',12,MUTED,600,1)
for x,value,label,note,c in [(48,'#5','UK LOBBY PEAK','Historical competition record',ORANGE),(448,'#41','INTERNATIONAL PEAK','v112 · 8 November 2026',BLUE),(848,'44','SOURCE FILES','Final v306 · C++ headers + sources',CYAN)]:
 rect(s,x,453,384,119);text(s,x+23,503,value,43,c,750);text(s,x+121,490,label,14,TEXT,700,1);text(s,x+23,545,note,16,MUTED)
write('hero.svg',s)

s=start(1280,850,'v306 decision architecture: persistent perception, ordered priorities, bounded decision support, legal actions and deferred computation.')
text(s,40,57,'ONE CHAMPION. ONE CONTROLLER.',27,TEXT,750)
text(s,40,90,'Persistent state, local teamwork and a budget for every decision.',18,MUTED)
for x,w,label,c in [(40,300,'01  PERCEIVE',BLUE),(370,500,'02  PRIORITISE',ORANGE),(900,340,'03  ASSIST',CYAN)]:
 text(s,x,139,label,15,c,700,2)
rect(s,40,160,300,225)
text(s,62,197,'World & memory',23,TEXT,700)
for y,t in [(237,'Terrain + distance fields'),(271,'Camps + capture state'),(305,'Enemies + dated sightings'),(339,'Our HP, bag and cooldowns')]:text(s,62,y,t,18,MUTED)
rect(s,40,409,300,191)
text(s,62,446,'Team radio',23,TEXT,700)
for y,t in [(485,'Compact camp claims'),(519,'Sightings + respawn events'),(553,'Local crews + capture owner')]:text(s,62,y,t,18,MUTED)
line(s,340,266,370,266,BLUE,2);line(s,340,502,370,502,BLUE,2)
rect(s,370,160,500,440)
rows=[('Refresh / shop / support','Prepare observations and legal support'),('Safe deposit window','An available short channel can win priority'),('Enemy contact','Protect captures · fight · pressure · retreat'),('Urgent banking / home','Winning bags, healing and spending'),('Team support / hunt / bank','Use nearby opportunities when eligible'),('Farm','Score jobs, select a target and act')]
for i,(title,note) in enumerate(rows):
 y=191+i*68;dot(s,394,y-5,ORANGE,4);text(s,410,y,title,20,TEXT,600);text(s,410,y+24,note,15,MUTED)
 if i<5:line(s,394,y+5,394,y+54,LINE,1)
rect(s,900,160,340,154)
text(s,921,196,'Neural camp ranking',22,TEXT,700)
text(s,921,232,'500 feature slots · fixed weights',17,MUTED)
text(s,921,264,'Cached + quantised inference',17,MUTED)
text(s,921,292,'Blended with the hand scorer',17,CYAN)
rect(s,900,336,340,146)
text(s,921,372,'Short combat simulation',21,TEXT,700)
text(s,921,408,'Compare fight versus retreat',17,MUTED)
text(s,921,440,'Budget and modelling safeguards',17,MUTED)
rect(s,900,504,340,96)
text(s,921,541,'Draft before gameplay',20,TEXT,700)
text(s,921,575,'Map rules + eligible neural picks',17,MUTED)
line(s,870,237,900,237,CYAN,2,dash=True);line(s,870,410,900,410,CYAN,2,dash=True)
rect(s,40,638,1200,91,fill='#162a2a',stroke='#31564f')
text(s,62,675,'04  EXECUTE',15,CYAN,700,2)
text(s,247,675,'Walk / dash / attack / cast / capture / submit / recall',23,TEXT,600)
text(s,247,706,'Legal action ordering and champion-specific movement restrictions apply.',17,MUTED)
rect(s,40,751,1200,59,fill='#17202d')
text(s,62,788,'FUEL GOVERNOR',14,BLUE,700,2)
text(s,268,788,'Bound searches · reserve action time · defer fields and neural refresh',19,MUTED)
write('architecture.svg',s)

s=start(1280,460,'Frozen local evaluation: 240 fresh maps, 1920 conditions per bot, 1398 v306 wins. A separate supplied-opponent random-map test was inconclusive.')
text(s,40,56,'MEASURED. FROZEN. REPRODUCIBLE.',27,TEXT,750)
text(s,40,91,'Extended local panel · paired conditions · map-clustered comparison',18,MUTED)
rect(s,40,120,470,241,stroke='#31564f')
text(s,66,157,'v306  /  RECOMMENDED',16,CYAN,700,2)
text(s,61,248,'72.8%',79,TEXT,750)
text(s,66,290,'1,398 wins / 1,920 conditions',23,CYAN,600)
text(s,66,329,'Against four frozen local reference bots',17,MUTED)
for x,y,value,label in [(536,120,'240','FRESH RANDOM MAPS'),(899,120,'4','REFERENCE OPPONENTS'),(536,251,'3 / 4 / 5','DRAFT PICKS'),(899,251,'2','SIDES PER MAP')]:
 rect(s,x,y,341,110);text(s,x+22,y+48,value,35,BLUE,700);text(s,x+22,y+84,label,13,MUTED,650,1)
text(s,40,407,'SEPARATE MATCHUP',13,ORANGE,700,1)
text(s,248,407,'Supplied opponent: 104 / 200 random games · 95% interval 44.0–60.5%',19,TEXT,500)
text(s,248,436,'Inconclusive advantage. Local results are separate from historical ladder ranks.',15,MUTED)
write('evaluation.svg',s)
print('Generated hero.svg, architecture.svg and evaluation.svg')
