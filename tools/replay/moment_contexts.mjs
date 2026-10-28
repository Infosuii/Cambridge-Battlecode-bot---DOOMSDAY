// Separate prediction observations from subsequent action-window exposure.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from './engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const STUDY=path.join(ROOT,'research/deep-2026-10-28'),LOCAL=path.join(ROOT,'artifacts/local-only/deep-2026-10-28');
const cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const assert=(x,m)=>{if(!x)throw new Error(m);};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const [mode,runDir]=process.argv.slice(2);assert(['before','after'].includes(mode)&&runDir,'before|after timeline-run');
assert(VERSION==='2.0.0','Engine2 required');
const samplePath=path.join(STUDY,'MOMENT_SAMPLE.json'),sample=JSON.parse(fs.readFileSync(samplePath,'utf8'));
const accepted=new Set(JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8')).rows.filter(r=>r.partition==='examined').map(r=>r.match_id));
assert(sample.rows.every(r=>accepted.has(r.match_id)),'Non-examined card rejected');
const predPath=path.join(STUDY,'CARD_PREDICTIONS.json');
if(mode==='after')assert(fs.existsSync(predPath),'Write and freeze predictions before exposing actions');
const predictions=mode==='after'?JSON.parse(fs.readFileSync(predPath,'utf8')):null;
if(predictions)assert(predictions.sample_sha256===hash(fs.readFileSync(samplePath)),'Sample changed after predictions');
const output=path.join(LOCAL,'card-contexts');fs.mkdirSync(output,{recursive:true});
const groups=new Map();for(const c of sample.rows){if(!groups.has(c.match_id))groups.set(c.match_id,[]);groups.get(c.match_id).push(c);}
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv,tsnap,snap}=E;
const read=(t,id)=>{check(X.Game_Visualiser_ReadState(E.h,E.perspective(t,id),snap));return E.PC.F(dv(),snap);};
const brief=c=>({id:c.entity.index,type:c.type,p:c.position??null,hp:c.health,max_hp:c.maxHealth,alive:c.alive,
  bag:c.gems??null,gold:c.gold??null,range:c.range??null,channel:c.channelType??null,timer:c.channelTimer??null,
  buffs:c.buffs,known:c.known});
const predRows=[];let count=0;
for(const [mid,cards] of groups){
  const game=JSON.parse(fs.readFileSync(path.resolve(runDir,mid+'.json'),'utf8'));
  assert(game.partition==='examined','Held-out context rejected');
  const states=new Map(cards.map(c=>[c.card_id,{card:c,observations:[],actions:[]}]));
  for(const s of states.values()){
    const pre=game.rows.find(r=>r.r===s.card.start),alive=pre.teams[s.card.own_side].self.filter(c=>c.alive&&c.p);
    alive.sort((a,b)=>b.gems-a.gems||a.hp/a.max_hp-b.hp/b.max_hp||a.id-b.id);
    s.actor=mode==='before'?alive[0]?.id:predictions.rows.find(p=>p.card_id===s.card.card_id).actor_id;
    assert(Number.isInteger(s.actor),'No alive focus actor before window');
  }
  E.load(fs.readFileSync(path.join(LOCAL,'replays/examined',mid+'.repl26a')));
  try{
    check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));let started=false;
    const end=Math.max(...cards.map(c=>c.end+20));
    for(;;){
      check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv(),r=d.getInt32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),
        input=d.getUint32(tsnap+56,true),substep=d.getUint32(tsnap+104,true),current=d.getUint32(tsnap+60,true),awaiting=!!d.getUint32(tsnap+20,true);
      if(phase===10)started=true;
      if(started&&phase===10&&awaiting){
        for(const s of states.values()){
          if(current!==s.actor)continue;
          const needed=mode==='before'?!s.observation&&r>=s.card.start+1:r>=s.card.start-20&&r<=s.card.end+20;
          if(!needed)continue;
          const v=read(s.card.own_side,s.actor),me=v.champions.find(c=>c.entity.index===s.actor),near=v.champions.filter(c=>c.team!==me.team&&c.position&&c.alive&&me.position&&cheb(c.position,me.position)<=8);
          const row={r,input,substep,self:brief(me),allies:v.champions.filter(c=>c.team===me.team&&c.entity.index!==s.actor).map(brief),enemies:near.map(brief)};
          if(mode==='before')s.observation=row;else if(!s.observations.some(o=>o.r===r))s.observations.push(row);
        }
      }
      if(started&&mode==='after'){
        const actor=d.getUint32(tsnap+76,true),ak=d.getUint32(tsnap+72,true),kind=d.getUint32(tsnap+68,true);
        if(ak===1&&[4,5,6,11,12,13,14,18,22,23,25,26,27].includes(kind))for(const s of states.values())if(actor===s.actor&&r>=s.card.start-20&&r<=s.card.end+20)
          s.actions.push({r,input,substep,kind,slot:d.getUint32(tsnap+108,true),from:{x:d.getInt32(tsnap+80,true),y:d.getInt32(tsnap+84,true)},to:{x:d.getInt32(tsnap+88,true),y:d.getInt32(tsnap+92,true)}});
      }
      if(outcome||(started&&r>end)||(mode==='before'&&[...states.values()].every(s=>s.observation)))break;
      check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    for(const s of states.values()){
      if(mode==='before'){
        assert(s.observation,'Pre-window actor observation absent');const o=s.observation,me=o.self;
        const friends=me.p?o.allies.filter(a=>a.alive&&a.p&&a.hp>=.4*a.max_hp&&cheb(a.p,me.p)<=4):[];
        const enemyHP=me.p?o.enemies.filter(e=>e.p&&cheb(e.p,me.p)<=6).reduce((a,e)=>a+e.hp,0):0;
        const lonePrerequisites=me.alive&&friends.length===0&&enemyHP>=2*me.hp&&enemyHP>0;
        let expectation;
        if(!me.alive)expectation='No living action is expected at this turn; check when death occurred before judging movement.';
        else if(lonePrerequisites)expectation='V75_LONE=2 and LONE_ALL=1 should veto sustained engagement if the one-turn-kill exception is false; escape also requires nearest distance <= enemy range+2. A cast/attack alone cannot establish a violation.';
        else if(me.channel)expectation='An active bank/recall channel may hold position; assess channel safety and completion before treating stationary actions as an error.';
        else if(me.bag>=40)expectation='A large bag is a review flag. V75_BAG is disabled: this source does not promise automatic retreat. Banking depends on effective per-map carry threshold, gates and immediate combat rules.';
        else expectation='Continue a legal farm/route/engage decision using this actor’s visible state. No unconditional inactivity, banking or retreat obligation follows from this observation; trace target selection if the outcome surprises.';
        predRows.push({card_id:s.card.card_id,match_id:mid,actor_id:s.actor,pre_window_observation:o,
          lone_guard_prerequisites:lonePrerequisites,healthy_friends4:friends.length,visible_enemy_hp6:enemyHP,
          expectation,source:'bots/live-69/src/bot.cpp:3988; common.h:1332; effective map/lab knobs require trace',
          unknowns:['target_ttk and one-turn-kill exception','full effective map/lab thresholds','memory and tactical-search branch']});
      }else{
        const row={card_id:s.card.card_id,match_id:mid,actor_id:s.actor,predictions_sha256:hash(fs.readFileSync(predPath)),
          observations:s.observations,actions:s.actions,events:game.events.filter(e=>e.timestamp.round>=s.card.start-20&&e.timestamp.round<=s.card.end+20)};
        fs.writeFileSync(path.join(output,s.card.card_id+'.json'),JSON.stringify(row)+'\n');
      }
    }
  }finally{E.destroy();}
  if(++count%10===0)console.log(JSON.stringify({mode,games:count,total:groups.size}));
}
if(mode==='before'){
  const value={stage:'expectations frozen before subsequent action-window extraction',sample_sha256:hash(fs.readFileSync(samplePath)),
    cards:predRows.length,hands_off_used:0,method:'largest pre-window bag among alive bodies, then lower HP fraction, then physical ID; exact actor-own turn-start view',rows:predRows};
  const raw=JSON.stringify(value,null,2)+'\n';if(fs.existsSync(predPath))assert(fs.readFileSync(predPath,'utf8')===raw,'Predictions immutable after action exposure');fs.writeFileSync(predPath,raw);
}
console.log(JSON.stringify({mode,games:groups.size,cards:sample.rows.length,hands_off_used:0}));
