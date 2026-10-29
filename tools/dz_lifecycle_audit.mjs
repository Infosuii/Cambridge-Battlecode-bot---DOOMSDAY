// Cross-check SDK observations against the official replay timeline. Offline
// correctness analysis only; this does not provide hidden data to a bot.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE!=='2.0.0') throw new Error('Select replay engine 2.0.0');
const [replay,stdout]=process.argv.slice(2);
const text=fs.readFileSync(stdout,'utf8');
const linked=text.includes('CT19_VIEW');
const pattern=linked?/CT19_VIEW round=(\d+) observer=(\d+) first=(\d+) first_alive=(\d) second=(\d+) second_alive=(\d)/g:
  /CT_LIFEVIEW round=(\d+) observer=(\d+) enemy=(\d+) enemy_alive=(\d) ally=(\d+) ally_alive=(\d)/g;
const views=[...text.matchAll(pattern)]
  .map(m=>({round:+m[1],observer:+m[2],enemy:+m[3],enemyAlive:+m[4],ally:+m[5],allyAlive:+m[6]}));
if (!views.length) throw new Error('Missing SDK lifecycle observations');
const settings=[...text.matchAll(linked?/CT19_SETTING respawn=(\d+)/g:/CT_RESPAWN (?:enemy|ally)_ticks=\d+ base_setting=(\d+)/g)].map(m=>+m[1]);
if (settings.length!==(linked?1:2)||new Set(settings).size!==1) throw new Error('Missing/inconsistent respawn setting');
const assets=defaultAssets(); verifyAssets(assets);
const E=await engine(assets); E.load(fs.readFileSync(replay));
const {X,check,dv,out,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const old=new Map(),turns=new Map(),transitions=[];
const lastRound=Math.max(...views.map(v=>v.round));
for (let n=0;n<20000;++n) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
  const s=E.PC.I(dv(),tsnap);
  for (const c of s.champions) {
    const id=c.entity.index;
    if (old.has(id)&&old.get(id)!==c.alive) transitions.push({body:id,alive:c.alive,round:s.round,turn:s.turn,phase:s.phase,event:n});
    old.set(id,c.alive);
  }
  // snapshot.phase is the current phase; snapshot.step describes the previous
  // completed event. A kind-one step is a respawn, not every turn boundary.
  if (s.phase===14&&s.currentChampion!==4294967295) {
    turns.set(`${s.round}:${s.currentChampion}`,new Map(s.champions.map(c=>[c.entity.index,Number(c.alive)])));
  }
  if (s.round>lastRound) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  if (n===19999) throw new Error('Lifecycle audit exceeded step bound');
}
const mismatches=[];
for (const v of views) {
  const turn=turns.get(`${v.round}:${v.observer}`);
  if (!turn||turn.get(v.enemy)!==v.enemyAlive||turn.get(v.ally)!==v.allyAlive) mismatches.push(v);
}
const intervals=[];
for (const body of [views[0].enemy,views[0].ally]) {
  const events=transitions.filter(t=>t.body===body);
  if (events.length!==2||events[0].alive||!events[1].alive) throw new Error('Expected exactly one death/respawn per subject');
  intervals.push({body,death_round:events[0].round,death_phase:events[0].phase,death_turn:events[0].turn,death_event:events[0].event,respawn_event:events[1].event,respawn_round:events[1].round,elapsed:events[1].round-events[0].round,
    respawn_phase:events[1].phase,respawn_turn:events[1].turn});
}
const result={passed:mismatches.length===0&&intervals.every(i=>i.elapsed===settings[0]&&i.respawn_phase===14),
  sdk_observations_checked:views.length,mismatches,base_respawn_setting:settings[0],intervals,
  conclusion:'Respawn occurs at the champion turn. A different champion may observe it in that round or the next.'};
if (linked) {
  result.linked_death_same_native_event=intervals[0].death_round===intervals[1].death_round&&
    intervals[0].death_turn===intervals[1].death_turn&&intervals[0].death_phase===intervals[1].death_phase&&intervals[0].death_event===intervals[1].death_event;
  result.passed&&=result.linked_death_same_native_event;
  result.conclusion='Both linked bodies die in the same native event; each recorded SDK view matches native champion-turn state.';
}
console.log(JSON.stringify(result));
E.destroy();
