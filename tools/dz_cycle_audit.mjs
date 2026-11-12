// Offline full-game execution evidence. Never imported by a bot.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select engine 2.0.0');
const [file,output]=process.argv.slice(2);
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
const bytes=fs.readFileSync(file);E.load(bytes);const {X,dv,check,out,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const bodies=new Map(),events=[],checkpoints={};let previous,steps=0,lastRound=-1;
for(;steps<3000000;++steps) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>lastRound) {
    if(previous&&[100,250,500].includes(previous.round))checkpoints[previous.round]=previous.champions;
    lastRound=s.round;
  }
  for(const c of s.champions) {
    const id=c.entity.index;
    if(!bodies.has(id))bodies.set(id,{team:c.team,type:c.type,firstPosition:c.position,last:c,events:[],moves:0,stationaryTurns:0,turns:0,deaths:0,acquired:0,spent:0});
    const b=bodies.get(id),p=b.last;
    const add=(kind,extra)=>{const event={round:s.round,phase:s.phase,turn:s.turn,body:id,kind,position:c.position,native_step:s.step,...extra};b.events.push(event);events.push(event);};
    if(c.gold>p.gold||c.gems>p.gems){add('receipt',{gold:c.gold-p.gold,gems:c.gems-p.gems});b.acquired+=Math.max(0,c.gems-p.gems);}
    if(c.gold<p.gold){add('purchase',{spent:p.gold-c.gold,items:c.items});b.spent+=p.gold-c.gold;}
    if(c.gems<p.gems)add(c.alive?'bag-reduced':'death-bag',{before:p.gems,after:c.gems});
    if(p.alive&&!c.alive){++b.deaths;add('death',{});}
    if(c.position&&p.position&&(c.position.x!==p.position.x||c.position.y!==p.position.y))++b.moves;
    if(s.phase===14&&s.currentChampion===id&&(!previous||previous.phase!==14||previous.currentChampion!==id||previous.round!==s.round))++b.turns;
    b.last=c;
  }
  previous=s;
  if(s.phase===19)break;
  // The engine keeps the final state when no further events exist.
  const before=JSON.stringify([s.round,s.turn,s.phase,s.currentChampion,s.step]);
  const rc=X.Game_Visualiser_Timeline_ReplayNext(E.h,1);if(rc===18)break;check(rc);
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const after=E.PC.I(dv(),tsnap);
  if(before===JSON.stringify([after.round,after.turn,after.phase,after.currentChampion,after.step]))break;
}
if(steps>=3000000)throw new Error('Audit bound exceeded');
const result={replay_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),last_round:previous.round,steps,
  definitions:{receipt:'Observed gold or bag increase; distinct from predicted rewards',purchase:'Observed gold reduction; inspect item change for identity',bag_reduced:'Must reconcile with native submitted-gems timeline; not automatically banking',moves:'Position changes, including recall/respawn; not idle accounting'},
  checkpoints,bodies:[...bodies.entries()].map(([id,b])=>({id,team:b.team,type:b.type,moves:b.moves,turns:b.turns,deaths:b.deaths,acquired:b.acquired,spent:b.spent,first_events:b.events.slice(0,18),early_events:b.events.filter(x=>x.round<=250),last:b.last}))};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({last_round:result.last_round,steps,bodies:result.bodies.map(b=>({id:b.id,team:b.team,acquired:b.acquired,spent:b.spent,deaths:b.deaths,first_events:b.first_events.slice(0,5).map(({items,native_step,...e})=>e)}))}));E.destroy();
