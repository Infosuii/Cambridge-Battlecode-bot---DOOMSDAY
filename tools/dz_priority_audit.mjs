// Scheduling audit through the pinned official native replay reader.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE!=='2.0.0') throw new Error('Select replay engine 2.0.0');
const [replay,candidate,opponent]=process.argv.slice(2);
const pattern=/CT6_TURN round=(\d+) body=(\d+) slot=(\d+) turn=(\d+) previous=(-?\d+) next_before=(-?\d+) next_after=(-?\d+) changed=([01]) desired=(-?\d+) opponent=([01])/g;
const views=[candidate,opponent].map(file=>[...fs.readFileSync(file,'utf8').matchAll(pattern)]
  .map(m=>({round:+m[1],body:+m[2],slot:+m[3],turn:+m[4],previous:+m[5],nextBefore:+m[6],nextAfter:+m[7],changed:+m[8],desired:+m[9],opponent:+m[10]})));
if (views.some(v=>!v.length)) throw new Error('Missing scheduling observations');
const assets=defaultAssets();verifyAssets(assets);
const E=await engine(assets);E.load(fs.readFileSync(replay));
const {X,check,dv,out,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const orders=new Map(),teams=new Map();let last='',ended=false;
for (let n=0;n<20000;++n) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
  const s=E.PC.I(dv(),tsnap);
  for (const c of s.champions) teams.set(c.entity.index,c.team);
  if (s.round>12) { ended=true;break; }
  // Measured on a native replay: awaitingInput is false at phase-14 champion
  // turns, so the first draft of this reader recorded nothing. Key by turn.
  const key=`${s.round}:${s.turn}`;
  if (s.phase===14&&s.currentChampion!==4294967295&&key!==last) {
    if (!orders.has(s.round)) orders.set(s.round,[]);
    orders.get(s.round).push(s.currentChampion);last=key;
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if (!ended) throw new Error('Scheduling audit exceeded step bound');
const mismatches=[],rounds=[];
const rosters=views.map(v=>[...new Set(v.map(x=>x.body))].sort((a,b)=>a-b));
let startingTeam;
for (let round=1;round<=12;++round) {
  const order=orders.get(round)??[],start=teams.get(order[0]);
  if (round===1) startingTeam=start;
  const alternating=order.length===rosters.flat().length&&order.every((body,i)=>teams.get(body)===(i%2?1-start:start));
  const startSwapped=start===(round%2?startingTeam:1-startingTeam);
  const expectedTeams=[];
  for (let team=0;team<2;++team) {
    const roster=rosters[team],observations=views[team].filter(v=>v.round===round);
    const native=order.filter(id=>roster.includes(id));
    const expected=[...observations].sort((a,b)=>b.previous-a.previous||a.body-b.body).map(v=>v.body);
    if (observations.length!==roster.length||new Set(observations.map(v=>v.body)).size!==roster.length||JSON.stringify(native)!==JSON.stringify(expected))
      mismatches.push({round,team,problem:'native team order versus current SDK priority',native,expected});
    for (const v of observations) {
      const prev=views[team].find(p=>p.body===v.body&&p.round===round-1);
      const shouldChange=[3,6,9].includes(round);
      const expectedNext=round<3?0:round<6?100+v.slot+team*1000:round<9?(v.slot===0?500:200+v.slot)+team*1000:-7+team*1000;
      if (v.opponent!==team||v.slot!==roster.indexOf(v.body)||v.turn!==round-1||v.previous!==(prev?.nextAfter??0)||v.nextBefore!==v.previous||v.nextAfter!==expectedNext||v.desired!==expectedNext||v.changed!==Number(shouldChange))
        mismatches.push({round,team,problem:'priority applied on wrong turn or persisted incorrectly',observation:v});
    }
    expectedTeams.push(expected);
  }
  if (!alternating||!startSwapped) mismatches.push({round,problem:'interleaving or starting team',order,start,alternating,startSwapped});
  rounds.push({round,order,starting_team:start,team_orders:expectedTeams,alternating,starting_team_swapped:startSwapped});
}
const result={passed:mismatches.length===0,sdk_observations:views.flat().length,rosters,mismatches,rounds,
  hypotheses:'Higher current priority first within each team; equal priority lower handle first; changes next round and persist; teams alternate and round starter swaps.'};
console.log(JSON.stringify(result));E.destroy();
