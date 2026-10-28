// Engine-2 end-of-round timelines. Raw trajectories stay in ignored artifacts.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {engine,defaultAssets,verifyAssets,VERSION,PINNED} from './engine.mjs';
const equip=items=>items.reduce((s,n,i)=>s+n*(i%2?(Math.floor(i/6)===12?750:150):30),0);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const STUDY=path.join(ROOT,'research/deep-2026-10-28');
const LOCAL=path.join(ROOT,'artifacts/local-only/deep-2026-10-28');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const CODE_HASH=hash(fs.readFileSync(fileURLToPath(import.meta.url)));
const SCHEMA_HASH=hash(fs.readFileSync(path.join(STUDY,'TIMELINE_SCHEMA.json')));
const assert=(x,m)=>{if(!x)throw new Error(m);};
const cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const same=(a,b)=>a&&b&&a.x===b.x&&a.y===b.y;
const key=s=>[s.r,s.input,s.substep].join(':');
const side=t=>t==='teamA'?0:1;
function header(E,p){const d=E.dv();return{r:d.getInt32(p+8,true),phase:d.getUint32(p+24,true),outcome:d.getUint32(p+28,true),
  awaiting:!!d.getUint32(p+20,true),input:d.getUint32(p+56,true),current:d.getUint32(p+60,true),
  kind:d.getUint32(p+68,true),ak:d.getUint32(p+72,true),actor:d.getUint32(p+76,true),
  from:{x:d.getInt32(p+80,true),y:d.getInt32(p+84,true)},to:{x:d.getInt32(p+88,true),y:d.getInt32(p+92,true)},
  stepRound:d.getUint32(p+96,true),substep:d.getUint32(p+104,true),slot:d.getUint32(p+108,true)};}
function geometry(E,initial){
  E.check(E.X.Game_GetBitboardMetadata(E.h,E.out));const d=E.dv(),w=d.getInt32(E.out,true),h=d.getInt32(E.out+4,true),stride=d.getUint32(E.out+16,true);
  const spawns=[0,1].map(t=>initial.champions.filter(c=>c.team===t&&c.position).map(c=>c.position));
  assert(spawns.every(p=>p.length),'Missing initial spawn positions');
  const region=p=>{const a=Math.min(...spawns[0].map(s=>cheb(p,s))),b=Math.min(...spawns[1].map(s=>cheb(p,s)));return a<.8*b?0:b<.8*a?1:2;};
  const regions=Array.from({length:w*h},(_,i)=>region({x:i%w,y:(i/w)|0}));
  const campGroup=new Map(initial.camps.map(c=>[c.position.x+','+c.position.y,c.group]));
  const groupRegions=initial.groups.map((_,g)=>{
    const camps=initial.camps.filter(c=>c.group===g);
    const distances=spawns.map(sp=>Math.min(...camps.flatMap(c=>sp.map(s=>cheb(c.position,s)))));
    return distances[0]<.8*distances[1]?0:distances[1]<.8*distances[0]?1:2;
  });
  return{w,h,stride,regions,region,campGroup,groupRegions,spawns};
}
function vision(E,g,t,champions){
  const words=new BigUint64Array(g.stride*Math.ceil(g.h/8));
  for(const champion of champions){
    E.check(E.X.Game_Visualiser_GetVisionBuffer(E.h,E.perspective(t,champion),E.out));const d=E.dv(),p=d.getUint32(E.out,true);
    for(let i=0;i<words.length;i++)words[i]|=d.getBigUint64(p+8*i,true);
  }
  let all=0,mid=0,midN=0;
  for(let y=0;y<g.h;y++)for(let x=0;x<g.w;x++){
    const bit=Number((words[(y>>3)*g.stride+(x>>3)]>>BigInt((y&7)*8+(x&7)))&1n);
    all+=bit;if(g.regions[y*g.w+x]===2){mid+=bit;midN++;}
  }return[all/(g.w*g.h),midN?mid/midN:0];
}
function analyse(E,item){
  const start=performance.now(),file=item.file,native=JSON.parse(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'),'utf8'));
  const events=native.events.flatMap(s=>s.entries.map(e=>({...e,kind:s.kind,owner:s.owner}))).sort((a,b)=>a.timestamp.ordinal-b.timestamp.ordinal);
  const byKey=new Map();for(const e of events){const k=[e.timestamp.round,e.timestamp.input,e.timestamp.substep].join(':');if(!byKey.has(k))byKey.set(k,[]);byKey.get(k).push(e);}
  const eventRounds=new Set(events.map(e=>e.timestamp.round)),series=new Map(native.championTimelines.map(s=>[s.owner.id+':'+s.metric,s.runs.flatMap(r=>new Array(r.duration).fill(Number(r.value)))]));
  const ids=native.roster.champions.map(c=>c.id),teams=new Map(native.roster.champions.map(c=>[c.id,side(c.team)]));
  const nativeValue=(id,m,r)=>{const v=series.get(id+':'+m)?.[r];assert(v!==undefined,`Native series missing ${id}:${m}:${r}`);return v;};
  const sources=new Map(ids.map(id=>[id,{capture_gold:0,kill_gold:0,bank_bonus_gold:0,middle_capture_gold:0}]));
  const counters=[0,1].map(()=>({captures:0,clears:0,capture_rewards_taken_from_clearer:0,middle_gems:0,wards_placed:0,fuel_outs:0,
    round_actions:{},dead_rounds:0,travel_rounds:0,stationary_rounds:0,channel_rounds:0}));
  const rows=[],actions=[],credits=[],opening=Object.fromEntries(ids.map(id=>[id,[]]));
  let checks=0,identityChecks=0,eventIndex=0,started=false,g=null,prev=null,prevPtr=null,previousRound=null,lastClear=new Map(),matchedCreditKeys=new Set(),receipts=new Set();
  E.load(fs.readFileSync(file));const {X,check,dv}=E,second=X.Engine_Malloc(E.tsize);
  try{
    check(X.Game_API_GetSettings(E.buf));const maxRounds=dv().getUint32(E.buf+36,true);
    check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,E.args,E.args+8,E.args+16));const size=dv().getUint32(E.args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const view=(t,id=0xffffffff)=>{check(X.Game_Visualiser_ReadState(E.h,E.perspective(t,id),E.snap));return E.PC.F(dv(),E.snap);};
    const sample=(s,initial=false)=>{
      const r=initial?0:s.r,v=view(2);if(!g)g=geometry(E,v);
      assert(v.round===s.r&&v.inputPosition===s.input,'Snapshot clock differs');
      for(const c of v.champions)for(const m of ['gold','gems','earnedGold']){assert(c[m]===nativeValue(c.entity.index,m,r),`Resource clock mismatch ${r} ${c.entity.index} ${m}`);checks++;}
      // Native events are cumulative at the round end; no later event enters a row.
      if(!initial)while(eventIndex<events.length&&events[eventIndex].timestamp.round<=r){
        const e=events[eventIndex++],t=teams.get(e.owner.id),co=counters[t];if(!co)continue;
        if(e.kind==='campClear'){co.clears++;lastClear.set(e.target.id,e);}
        if(e.kind==='gemCollection'&&e.target?.kind==='campGroup'){
          if(g.groupRegions[e.target.id]===2)co.middle_gems+=Number(e.value);
          // A reward may be split among physical bodies: count group/input once.
          const receipt=e.timestamp.round+':'+e.target.id;
          if(!receipts.has(receipt)){receipts.add(receipt);co.captures++;const clear=lastClear.get(e.target.id);if(clear&&clear.owner.team!==e.owner.team)co.capture_rewards_taken_from_clearer++;lastClear.delete(e.target.id);}
        }
        if(e.kind==='wardPlacement')co.wards_placed+=Number(e.value);
        if(e.kind==='fuelExhausted')co.fuel_outs+=Number(e.value);
      }
      const states=[0,1].map(t=>{
        const cs=v.champions.filter(c=>c.team===t),live=cs.filter(c=>c.alive&&c.position),co=counters[t];
        const sum=f=>cs.reduce((a,c)=>a+f(c),0),metric=m=>sum(c=>nativeValue(c.entity.index,m,r));
        const earned=metric('earnedGold'),source=Object.fromEntries(['capture_gold','kill_gold','bank_bonus_gold','middle_capture_gold'].map(k=>[k,sum(c=>sources.get(c.entity.index)[k])]));
        const lost=events.filter(e=>e.kind==='gemLoss'&&teams.get(e.owner.id)===t&&e.timestamp.round<=r).reduce((a,e)=>a+Number(e.value),0);
        const banked=metric('submittedGems'),carried=metric('gems'),collected=metric('collectedGems');
        assert(banked===collected-lost-carried,'Gem race does not balance');identityChecks++;
        const residual=earned-source.capture_gold-source.kill_gold-source.bank_bonus_gold;assert(residual>=0,'Gold sources exceed native earned gold');
        const centroid=live.length?{x:live.reduce((a,c)=>a+c.position.x,0)/live.length,y:live.reduce((a,c)=>a+c.position.y,0)/live.length}:null;
        const enemies=v.champions.filter(c=>c.team!==t&&c.alive&&c.position);
        const vc=vision(E,g,t,cs.map(c=>c.entity.index)),visible=new Map();
        for(const c of cs)for(const e of view(t,c.entity.index).champions)if(e.team!==t&&e.position&&e.alive)visible.set(e.entity.index,e);
        const self=cs.map(c=>({id:c.entity.index,type:c.type,p:c.position??null,hp:c.health,max_hp:c.maxHealth,alive:c.alive,
          gold:c.gold,gems:c.gems,gear:equip(c.items),channel:c.channelType,timer:c.channelTimer,respawn:c.respawnTimer,items:c.items}));
        return{banked,carried,collected,lost,earned_gold:earned,gold:metric('gold'),...source,other_or_unclassified_gold:residual,
          equipment_cost:sum(c=>equip(c.items)),alive:live.length,health:live.reduce((a,c)=>a+c.health,0),max_health_alive:live.reduce((a,c)=>a+c.maxHealth,0),
          respawn_timer_sum:sum(c=>c.respawnTimer??0),...structuredClone(co),active_wards:v.wards.filter(w=>w.team===t).length,
          vision_fraction:vc[0],middle_vision_fraction:vc[1],centroid_x:centroid?.x??null,centroid_y:centroid?.y??null,
          spread:centroid&&live.length?live.reduce((a,c)=>a+cheb(c.position,centroid),0)/live.length:null,
          nearest_enemy_distance:live.length&&enemies.length?Math.min(...live.flatMap(c=>enemies.map(e=>cheb(c.position,e.position)))):null,
          self,visible_enemies:[...visible.values()].map(c=>({id:c.entity.index,p:c.position,hp:c.health,max_hp:c.maxHealth,bag:c.gems??null,known:c.known}))};
      });
      if(!initial&&previousRound){
        for(const c of v.champions){const co=counters[c.team],before=previousRound.get(c.entity.index);
          if(!c.alive)co.dead_rounds++;else if(c.channelType)co.channel_rounds++;else if(before?.position&&!same(before.position,c.position))co.travel_rounds++;else co.stationary_rounds++;
        }
        for(let t=0;t<2;t++)for(const k of ['dead_rounds','travel_rounds','stationary_rounds','channel_rounds'])states[t][k]=counters[t][k];
      }
      previousRound=new Map(v.champions.map(c=>[c.entity.index,c]));
      if(initial||r<=300||r%5===0||eventRounds.has(r)||s.outcome)rows.push({r,engine_round:s.r,input:s.input,substep:s.substep,phase:s.phase,terminal:!!s.outcome,initial,teams:states});
    };
    let p=E.tsnap;
    for(;;){
      check(X.Game_Visualiser_ReadTimelineState(E.h,p));const s=header(E,p);
      if(!started&&s.phase===10){started=true;sample(s,true);}
      if(started){
        const ne=byKey.get(key(s))??[],creditEvents=ne.filter(e=>['kill','gemSubmission'].includes(e.kind));
        if(prev&&prevPtr&&(s.phase===7||prev.phase===7||creditEvents.length)){
          const current=E.PC.I(dv(),p),prior=E.PC.I(dv(),prevPtr),pc=new Map(prior.champions.map(c=>[c.entity.index,c]));
          if(creditEvents.length)matchedCreditKeys.add(key(s));
          for(const c of current.champions){const before=pc.get(c.entity.index);if(!before)continue;const delta=c.gold-before.gold;if(delta<=0)continue;
            const ce=creditEvents.filter(e=>e.owner.id===c.entity.index),kinds=new Set(ce.map(e=>e.kind));
            let source=null;if(s.phase===7||prev.phase===7)source='capture_gold';else if(kinds.size===1)source=kinds.has('kill')?'kill_gold':'bank_bonus_gold';
            if(source){const acc=sources.get(c.entity.index);acc[source]+=delta;const group=c.position?g.campGroup.get(c.position.x+','+c.position.y):undefined;
              if(source==='capture_gold'&&group!==undefined&&g.groupRegions[group]===2)acc.middle_capture_gold+=delta;
              credits.push({r:s.r,input:s.input,substep:s.substep,owner:c.entity.index,gold:delta,source,group:group??null});}
          }
        }
        if(s.ak===1&&teams.has(s.actor)&&[4,5,6,11,12,13,14,18,22,23,25,26,27].includes(s.kind)){
          const a={r:s.stepRound,input:s.input,substep:s.substep,actor:s.actor,kind:s.kind,from:s.from,to:s.to,slot:s.slot};
          actions.push(a);const co=counters[teams.get(s.actor)];co.round_actions[s.kind]=(co.round_actions[s.kind]??0)+1;
          if([5,6].includes(s.kind)&&prevPtr&&opening[s.actor].length<3){
            const pv=E.PC.I(dv(),prevPtr),camp=pv.camps.find(c=>c.health>0&&same(c.position,s.to));
            const enemy=pv.champions.find(c=>c.team!==teams.get(s.actor)&&c.alive&&same(c.position,s.to));
            if(camp&&!enemy){const group=g.campGroup.get(s.to.x+','+s.to.y),last=opening[s.actor].at(-1);
              if(last?.group!==group)opening[s.actor].push({r:s.r,group,region:g.groupRegions[group],kind:s.kind});}
          }
        }
        if(s.phase===0||s.outcome)sample(s);
      }
      if(s.outcome||(s.awaiting&&s.input>=size))break;
      prev=s;prevPtr=p;p=p===E.tsnap?second:E.tsnap;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    assert(rows.at(-1).terminal,'Final state absent');
    const expectedCreditKeys=new Set(events.filter(e=>['kill','gemSubmission'].includes(e.kind)).map(e=>[e.timestamp.round,e.timestamp.input,e.timestamp.substep].join(':')));
    const coverage={native_credit_keys:expectedCreditKeys.size,matched_credit_keys:matchedCreditKeys.size,credit_key_coverage:[...expectedCreditKeys].every(k=>matchedCreditKeys.has(k)),
      classified_gold:credits.reduce((a,c)=>a+c.gold,0),unclassified_gold:rows.at(-1).teams.reduce((a,t)=>a+t.other_or_unclassified_gold,0)};
    return{match_id:item.entry.match_id,partition:item.entry.partition,engine:VERSION,code_sha256:CODE_HASH,schema_sha256:SCHEMA_HASH,
      replay_sha256:hash(fs.readFileSync(file)),summary_sha256:hash(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'))),
      max_rounds:maxRounds,rounds:native.match.roundsStarted,outcome:native.match.outcome,roster:native.roster.champions,
      geometry:{width:g.w,height:g.h,spawns:g.spawns,group_regions:g.groupRegions},
      validation:{native_resource_clock:checks>0,gem_identity:identityChecks>0,final_state:rows.at(-1).terminal,gold_sources_nonnegative:true,native_credit_key_coverage:coverage.credit_key_coverage},
      checks,identity_checks:identityChecks,coverage,opening,rows,events,actions,credits,ms:Math.round(performance.now()-start)};
  }finally{X.Engine_Free(second);E.destroy();}
}
if(!isMainThread){
  assert(VERSION==='2.0.0','Engine 2 required');const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
  parentPort.on('message',item=>{if(item===null){parentPort.close();return;}try{const r=analyse(E,item);fs.writeFileSync(path.join(workerData.out,r.match_id+'.json'),JSON.stringify(r)+'\n');
    parentPort.postMessage({match_id:r.match_id,passed:Object.values(r.validation).every(Boolean),validation:r.validation,checks:r.checks,coverage:r.coverage,rows:r.rows.length,ms:r.ms});
  }catch(e){parentPort.postMessage({match_id:item.entry.match_id,passed:false,error:String(e.stack??e)});}});parentPort.postMessage('ready');
}else if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  let partition=null,out=null,workers=4;for(let i=2;i<process.argv.length;i++){
    if(process.argv[i]==='--partition')partition=process.argv[++i];else if(process.argv[i]==='--out')out=path.resolve(process.argv[++i]);else if(process.argv[i]==='--workers')workers=Number(process.argv[++i]);else throw new Error('Unknown argument');}
  assert(VERSION==='2.0.0','Set NFS_REPLAY_ENGINE=2.0.0');assert(['calibration-excluded','examined'].includes(partition),'Only calibration and examined games allowed');
  assert(out&&out.startsWith(path.join(ROOT,'artifacts')+path.sep),'Output must be local artifacts');assert(workers>0&&workers<=8,'workers 1..8');
  if(partition==='examined'){const p=JSON.parse(fs.readFileSync(path.join(STUDY,'TIMELINE_VALIDATION.json'),'utf8'));
    assert(p.passed===5&&p.failed===0&&p.code_sha256===CODE_HASH&&p.schema_sha256===SCHEMA_HASH,'Five current-code calibration passes required');}
  fs.mkdirSync(out,{recursive:true});const manifest=JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8'));
  const inputs=manifest.rows.filter(e=>e.partition===partition).map(entry=>({entry,file:path.join(LOCAL,'replays',partition,entry.match_id+'.repl26a')}));
  const started=performance.now(),results=[];let next=0;
  await Promise.all(Array.from({length:Math.min(workers,inputs.length)},()=>new Promise((resolve,reject)=>{
    const w=new Worker(new URL(import.meta.url),{workerData:{out}}),feed=()=>w.postMessage(next<inputs.length?inputs[next++]:null);
    w.on('message',r=>{if(r==='ready'){feed();return;}results.push(r);if(results.length%25===0)console.log(JSON.stringify({processed:results.length,total:inputs.length}));feed();});w.on('error',reject);w.on('exit',c=>c?reject(new Error('Worker exit '+c)):resolve());
  })));
  const report={partition,engine:VERSION,code_sha256:CODE_HASH,schema_sha256:SCHEMA_HASH,pinned_assets:PINNED,processed:results.length,passed:results.filter(r=>r.passed).length,failed:results.filter(r=>!r.passed).length,seconds:Math.round((performance.now()-started)/1000),results};
  fs.writeFileSync(path.join(out,'run.json'),JSON.stringify(report,null,2)+'\n');if(partition==='calibration-excluded')fs.writeFileSync(path.join(STUDY,'TIMELINE_VALIDATION.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,results:results.filter(r=>!r.passed)}));if(report.failed)process.exitCode=1;
}
