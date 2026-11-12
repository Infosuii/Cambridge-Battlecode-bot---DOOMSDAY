// Registered D1-D11 review flags from official engine-2 states and native events.
// Offline only. Native sources are authoritative for deaths, losses, purchases,
// wards and fuel. Hidden intentions / rejected SDK calls are never invented.
// --partition calibration-excluded|examined --out <local directory> [--workers 4] [--validate]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {engine,defaultAssets,verifyAssets,VERSION,PINNED} from './engine.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const STUDY=path.join(ROOT,'research/deep-2026-10-28');
const SPEC_PATH=path.join(STUDY,'DETECTOR_SPEC.json');
const SPEC=JSON.parse(fs.readFileSync(SPEC_PATH,'utf8')),T=SPEC.thresholds;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const SPEC_HASH=hash(fs.readFileSync(SPEC_PATH));
const CODE_HASH=hash(fs.readFileSync(fileURLToPath(import.meta.url)));
const PHASE=10,NONE=0xffffffff,IDS=Array.from({length:11},(_,i)=>'D'+(i+1));
const cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const pointKey=p=>p.x+','+p.y;
const same=(a,b)=>!!a&&!!b&&a.x===b.x&&a.y===b.y;
const equip=items=>items.reduce((s,n,i)=>s+n*(i%2?(Math.floor(i/6)===12?750:150):30),0);
const assert=(ok,message)=>{if(!ok)throw new Error(message);};
const nativeEvents=d=>d.events.flatMap(s=>s.entries.map(e=>({...e,kind:s.kind,owner:s.owner})));
const ownEvents=(events,id,kind)=>events.filter(e=>e.owner.kind==='champion'&&e.owner.id===id&&e.kind===kind);
const counter=rows=>{const out={};for(const row of rows){const k=JSON.stringify(row);out[k]=(out[k]??0)+1;}return Object.entries(out).sort();};
const equalCounts=(a,b)=>JSON.stringify(counter(a))===JSON.stringify(counter(b));
// Official PanelChrome.L: 4 Move,22 Teleport complete,23 Movement blocked.
const isMovementAction=a=>[4,22].includes(a.kind)&&!same(a.from,a.to);
const moving=r=>r.actions.some(isMovementAction);
const active=r=>r.actions.some(a=>[5,6].includes(a.kind))||moving(r);
const free=r=>r.complete&&r.alive&&r.end_alive&&r.p&&r.end_p&&!r.channel&&!r.end_channel&&!r.stun;
const idleEligible=r=>free(r)&&!r.capture&&!r.actions.some(a=>[11,12].includes(a.kind));
const isIdle=r=>idleEligible(r)&&!active(r)&&same(r.p,r.end_p);
const unionTurns=events=>{const rounds=new Set();for(const e of events)if(e.turns>0)for(let r=e.start;r<=e.end;r++)rounds.add(r);return rounds.size;};

function readBoard(E,w,h,stride,getter){
  E.check(getter(E.h,E.out));const p=E.dv().getUint32(E.out,true),d=E.dv(),b=new Uint8Array(w*h);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const word=d.getBigUint64(p+8*((y>>3)*stride+(x>>3)),true);
    b[y*w+x]=Number((word>>BigInt((y&7)*8+(x&7)))&1n);
  }return b;
}

function geometry(E){
  const {X,check,dv,out}=E;check(X.Game_GetBitboardMetadata(E.h,out));
  const w=dv().getInt32(out,true),h=dv().getInt32(out+4,true),stride=dv().getUint32(out+16,true);
  const wall=readBoard(E,w,h,stride,X.Game_GetWallBuffer),hole=readBoard(E,w,h,stride,X.Game_GetHoleBuffer);
  const altar=readBoard(E,w,h,stride,X.Game_GetAltarBuffer),spawn=[];
  for(let t=0;t<2;t++){
    check(X.Game_API_GetSpawnRegion(E.h,t,out));spawn.push([0,4,8,12].map(o=>dv().getInt32(out+o,true)));
  }
  const inSpawn=(p,t)=>p.x>=spawn[t][0]&&p.y>=spawn[t][1]&&p.x<spawn[t][2]&&p.y<spawn[t][3];
  const components=[0,1].map(t=>{
    const labels=new Int32Array(w*h).fill(-1),meta=[];
    const blocked=i=>wall[i]||hole[i]||altar[i]||inSpawn({x:i%w,y:(i/w)|0},1-t);
    for(let i=0;i<w*h;i++){
      if(labels[i]>=0||blocked(i))continue;
      const queue=[i],id=meta.length;labels[i]=id;let home=false,bank=false;
      for(let k=0;k<queue.length;k++){
        const cell=queue[k],x=cell%w,y=(cell/w)|0;home||=inSpawn({x,y},t);
        // Ordinary movement uses the eight neighbouring tiles. Abilities and
        // transient living-camp occupancy are deliberately outside this proxy.
        for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
          const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=w||ny>=h)continue;
          const j=ny*w+nx;bank||=!!altar[j];
          if((dx||dy)&&labels[j]<0&&!blocked(j)){labels[j]=id;queue.push(j);}
        }
      }meta.push({size:queue.length,home,bank});
    }return{labels,meta};
  });
  return{w,h,inSpawn,components};
}

function addEpisode(ch,id,subtype,start,end,context,turns=end-start+1){
  ch.detectors[id].events.push({subtype,start,end,fired_round:end,turns,context});
}

function episodes(ch,id,subtype,rows,predicate,minimum,context,key=()=>null){
  let run=[];
  const close=()=>{if(run.length>=minimum){addEpisode(ch,id,subtype,run[0].r,run.at(-1).r,context(run[0],run.at(-1)),run.length);ch.detectors[id].events.at(-1).fired_round=run[minimum-1].r;}run=[];};
  for(const row of rows){
    if(predicate(row)){
      if(run.length&&(row.r!==run.at(-1).r+1||key(row)!==key(run.at(-1))))close();
      run.push(row);
    }else close();
  }close();
}

function analyse(E,file,entry,validate){
  const started=performance.now(),native=JSON.parse(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'),'utf8'));
  const events=nativeEvents(native),roster=new Map(native.roster.champions.map(c=>[c.id,c]));
  const all=new Map([...roster].map(([id,c])=>[id,{id,team:c.team==='teamA'?0:1,name:c.name,turns:[],
    detectors:Object.fromEntries(IDS.map(k=>[k,{events:[]}]))}]));
  E.load(fs.readFileSync(file));
  try{
    const {X,check,dv,out,args,tsnap,snap}=E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const main=dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));const size=dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const geo=geometry(E),turnMap=new Map(),actions=[],groupFrames=[];
    let currentTurn=null,lastRound=-1,previous=null,groupTiles=null,campGroups=null;
    let selfChecks=0,clockChecks=0,hiddenEnemySamples=0,visibleEnemySamples=0,completeTurns=0;
    const view=(team,champion)=>{check(X.Game_Visualiser_ReadState(E.h,E.perspective(team,champion),snap));return E.PC.F(dv(),snap);};
    for(;;){
      check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv();
      const round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true);
      const input=d.getUint32(tsnap+56,true),kind=d.getUint32(tsnap+68,true),ak=d.getUint32(tsnap+72,true),actor=d.getUint32(tsnap+76,true);
      const stepRound=d.getUint32(tsnap+96,true),substep=d.getUint32(tsnap+104,true);
      const current=d.getUint32(tsnap+60,true),awaiting=!!d.getUint32(tsnap+20,true);
      if(previous)assert(input!==previous.input||substep!==previous.substep,'Timeline made no progress');
      previous={input,substep};
      if((round!==lastRound&&phase===PHASE)||outcome){
        const omni=view(2,NONE);assert(omni.round===round&&omni.inputPosition===input,'Omniscient snapshot clock mismatch');clockChecks++;
        if(!groupTiles){
          groupTiles=Array.from({length:omni.groups.length},()=>new Set());campGroups=new Map();
          for(const c of omni.camps)if(c.position){assert(Number.isInteger(c.group)&&c.group>=0&&c.group<groupTiles.length,'Official camp group identity missing');groupTiles[c.group].add(pointKey(c.position));campGroups.set(pointKey(c.position),c.group);}
          assert(groupTiles.every(g=>g.size>0),'Empty official group geometry');
        }
        groupFrames.push({r:round,groups:omni.groups.map((g,i)=>({state:g.state,team:g.captureTeam,timer:g.captureTimer,duration:g.captureDuration,
          on:omni.champions.filter(c=>c.alive&&c.position&&groupTiles[i].has(pointKey(c.position))).map(c=>c.entity.index)}))});
        lastRound=round;
      }
      if(phase===PHASE&&awaiting&&current!==NONE&&roster.has(current)){
        const key=current+':'+round;
        if(!turnMap.has(key)){
          if(currentTurn){
            const prior=all.get(currentTurn.id),endView=view(prior.team,prior.id),end=endView.champions.find(c=>c.entity.index===prior.id);
            currentTurn.end_alive=end.alive;currentTurn.end_p=end.position??null;currentTurn.end_channel=end.channelType??0;
            const eg=end.position?campGroups.get(pointKey(end.position)):undefined;
            currentTurn.end_spawn_block=eg!==undefined&&eg===currentTurn.group&&endView.groups[eg].state===3&&endView.groups[eg].respawnRounds===0;
            currentTurn.complete=true;completeTurns++;
          }
          const ch=all.get(current),v=view(ch.team,current),c=v.champions.find(c=>c.entity.index===current);
          assert(v.round===round&&v.inputPosition===input,'Own-perspective clock mismatch');clockChecks++;
          assert(c&&c.team===ch.team&&c.gold!==undefined&&c.gems!==undefined,'Own champion state missing');
          if(validate){
            const omni=E.PC.I(dv(),tsnap),self=omni.champions.find(x=>x.entity.index===current);
            assert(self&&self.team===c.team&&self.type===c.type&&self.gold===c.gold&&self.gems===c.gems&&self.alive===c.alive&&
              ((!self.position&&!c.position)||same(self.position,c.position)),'Own state differs from timeline');selfChecks++;
          }
          const enemies=v.champions.filter(e=>e.team!==ch.team&&e.position&&e.alive);
          hiddenEnemySamples+=v.champions.filter(e=>e.team!==ch.team&&!e.position).length;visibleEnemySamples+=enemies.length;
          const allies=v.champions.filter(a=>a.team===ch.team&&a.entity.index!==current&&a.position&&a.alive);
          const tile=c.position?pointKey(c.position):null,group=tile===null?undefined:campGroups.get(tile);
          let emptyNear=null;
          if(c.position)for(let gi=0;gi<groupTiles.length;gi++)if(v.groups[gi].state===3){
            for(const t of groupTiles[gi]){const [x,y]=t.split(',').map(Number);if(cheb(c.position,{x,y})<=1){emptyNear=gi;break;}}
            if(emptyNear!==null)break;
          }
          const label=c.position?geo.components[ch.team].labels[c.position.y*geo.w+c.position.x]:-1;
          const component=label>=0?geo.components[ch.team].meta[label]:null;
          const row={r:round,input,id:current,alive:c.alive,p:c.position??null,hp:c.health,max_hp:c.maxHealth,bag:c.gems,gold:c.gold,
            gear:equip(c.items),channel:c.channelType??0,channel_timer:c.channelTimer??0,stun:c.buffs.some(b=>b.type===1&&b.timer>0),
            visible:enemies.map(e=>e.entity.index),enemies6:c.position?enemies.filter(e=>cheb(c.position,e.position)<=T.isolated_radius).length:0,
            allies6:c.position?allies.filter(a=>cheb(c.position,a.position)<=T.isolated_radius).length:0,
            capture:group!==undefined&&v.groups[group].state===2,
            group:group??null,empty_near:emptyNear,spawn_block:group!==undefined&&v.groups[group].state===3&&v.groups[group].respawnRounds===0,
            ground_disconnected:!!component&&!component.home&&!component.bank,component_size:component?.size??null,
            visible_enemy_locks:(v.altarLocks??[]).filter(l=>l.team!==ch.team).map(l=>l.position??null),
            complete:false,actions:[]};
          ch.turns.push(row);turnMap.set(key,row);currentTurn=row;
        }
      }
      if(ak===1&&roster.has(actor)&&[4,5,6,11,12,13,14,18,22,23,25,26,27].includes(kind)){
        const action={r:stepRound,actor,kind,input,substep,from:{x:d.getInt32(tsnap+80,true),y:d.getInt32(tsnap+84,true)},
          to:{x:d.getInt32(tsnap+88,true),y:d.getInt32(tsnap+92,true)}};
        if(kind===12){const v=view(all.get(actor).team,actor),c=v.champions.find(c=>c.entity.index===actor);action.channel_type=c.channelType;}
        actions.push(action);turnMap.get(actor+':'+stepRound)?.actions.push(action);
      }
      if(outcome||(awaiting&&input>=size))break;
      check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    const validations={snapshot_clocks:clockChecks>0,own_state_matches_timeline:!validate||selfChecks>0,
      native_fuel_events:equalCounts(actions.filter(a=>a.kind===26).map(a=>[a.actor,a.r]),events.filter(e=>e.kind==='fuelExhausted').map(e=>[e.owner.id,e.timestamp.round])),
      native_ward_events:equalCounts(actions.filter(a=>a.kind===14).map(a=>[a.actor,a.r]),events.filter(e=>e.kind==='wardPlacement').map(e=>[e.owner.id,e.timestamp.round])),
      native_buy_events:equalCounts(actions.filter(a=>a.kind===13).map(a=>[a.actor,a.r]),events.filter(e=>['buyItem','buyConsumable'].includes(e.kind)).map(e=>[e.owner.id,e.timestamp.round])),
      native_bank_events:equalCounts(actions.filter(a=>a.kind===18).map(a=>[a.actor,a.r]),events.filter(e=>e.kind==='gemSubmission').map(e=>[e.owner.id,e.timestamp.round])),
      native_fault_totals:[0,1].every(t=>actions.filter(a=>a.kind===27&&all.get(a.actor).team===t).length===native.diagnostics.botFaults[t===0?'teamA':'teamB']),
      native_capture_group_positions:events.filter(e=>e.kind==='gemCollection'&&e.target?.kind==='campGroup').every(e=>groupTiles[e.target.id]?.has(e.x+','+e.y))};
    for(const ch of all.values()){
      const rows=ch.turns,whole=rows.filter(r=>r.complete),alive=whole.filter(r=>r.alive&&r.p);
      ch.denominators={observed_turns:rows.length,complete_turns:whole.length,alive_complete_turns:alive.length,
        alive_observed_turns:rows.filter(r=>r.alive&&r.p).length,
        high_bag_observed_turns:rows.filter(r=>r.alive&&r.p&&r.bag>=T.bag_gems).length,
        idle_eligible_turns:whole.filter(idleEligible).length,native_deaths:ownEvents(events,ch.id,'death').length,
        moves:actions.filter(a=>a.actor===ch.id&&isMovementAction(a)).length};
      episodes(ch,'D1','stationary',whole,isIdle,T.idle_turns,r=>({x:r.p.x,y:r.p.y,bag:r.bag,gold:r.gold}),r=>pointKey(r.p));
      episodes(ch,'D2','high_bag',rows,r=>r.alive&&r.p&&r.bag>=T.bag_gems&&!r.channel&&!r.actions.some(a=>[12,18].includes(a.kind)),T.bag_turns,(a,b)=>({bag_start:a.bag,bag_end:b.bag}));
      const deaths=ownEvents(events,ch.id,'death').sort((a,b)=>a.timestamp.ordinal-b.timestamp.ordinal);
      for(let i=0;i<deaths.length;i++){
        const death=deaths[i],r=death.timestamp.round;
        const losses=ownEvents(events,ch.id,'gemLoss').filter(e=>e.timestamp.input===death.timestamp.input&&e.timestamp.round===r);
        const lost=losses.reduce((s,e)=>s+Number(e.value),0);
        if(lost>=T.bag_gems)addEpisode(ch,'D2','high_bag_death',r,r,{gems_lost:lost,x:death.x,y:death.y},0);
        const prior=deaths.slice(0,i).filter(e=>r-e.timestamp.round<=T.repeat_death_window);
        const spatial=prior.find(e=>cheb(e,death)<=T.repeat_death_radius),killer=death.target?.kind==='champion'&&death.target.team!==death.owner.team?death.target.id:null;
        const repeatedKiller=killer!==null&&prior.find(e=>e.target?.kind==='champion'&&e.target.id===killer);
        if(spatial||repeatedKiller)addEpisode(ch,'D3','repeat_death',r,r,{x:death.x,y:death.y,prior_round:(spatial??repeatedKiller).timestamp.round,same_area:!!spatial,same_killer:!!repeatedKiller},0);
        if(killer!==null){
          const before=rows.filter(row=>row.r>=r-T.vision_history_rounds&&row.r<r&&row.alive&&row.p);
          if(before.length===T.vision_history_rounds&&new Set(before.map(x=>x.r)).size===T.vision_history_rounds){
            ch.denominators.vision_eligible_deaths=(ch.denominators.vision_eligible_deaths??0)+1;
            if(before.every(row=>!row.visible.includes(killer)))addEpisode(ch,'D11','turn_sampled_unseen_killer',r,r,{killer,prior_rounds:before.map(x=>x.r),limitation:'Visibility between samples and in death round is unmeasured'},0);
          }
        }
      }
      let movement=[],oscillation=null;
      for(const a of actions.filter(a=>a.actor===ch.id&&isMovementAction(a))){
        if(!movement.length||!same(movement.at(-1).p,a.from)){movement=[{p:a.from,r:a.r}];oscillation=null;}
        movement.push({p:a.to,r:a.r});if(movement.length>5)movement.shift();
        const yes=movement.length===5&&same(movement[0].p,movement[2].p)&&same(movement[2].p,movement[4].p)&&same(movement[1].p,movement[3].p)&&
          !same(movement[0].p,movement[1].p)&&a.r-movement[0].r<=T.oscillation_window;
        if(yes){
          if(oscillation&&a.r-oscillation.end<=T.oscillation_window){oscillation.end=a.r;oscillation.turns++;}
          else{addEpisode(ch,'D4','tile_oscillation_proxy',movement[0].r,a.r,{a:movement[0].p,b:movement[1].p},0);oscillation=ch.detectors.D4.events.at(-1);}
        }else oscillation=null;
      }
      episodes(ch,'D6','empty_camp_wait',whole,r=>free(r)&&same(r.p,r.end_p)&&r.empty_near!==null&&!active(r),T.empty_camp_wait_turns,r=>({group:r.empty_near,x:r.p.x,y:r.p.y}),r=>r.empty_near);
      episodes(ch,'D6','spawn_block',whole,r=>r.alive&&r.end_alive&&r.p&&r.spawn_block&&r.end_spawn_block,T.spawn_block_turns,r=>({group:r.group,x:r.p.x,y:r.p.y}),r=>r.group);
      for(const e of ownEvents(events,ch.id,'fuelExhausted'))addEpisode(ch,'D7','fuel_exhausted',e.timestamp.round,e.timestamp.round,{input:e.timestamp.input},0);
      for(const a of actions.filter(a=>a.actor===ch.id&&a.kind===27))addEpisode(ch,'D7','native_fault',a.r,a.r,{input:a.input},0);
      const starts=actions.filter(a=>a.actor===ch.id&&a.kind===12),banks=ownEvents(events,ch.id,'gemSubmission');
      ch.denominators.bank_attempts=starts.length;ch.descriptors={bank_attempts_censored:0};
      for(let i=0;i<starts.length;i++){
        const a=starts[i],next=starts[i+1];
        const ending=rows.find(row=>row.r>a.r&&row.channel!==a.channel_type);
        const death=deaths.find(e=>e.timestamp.round>=a.r&&(!next||e.timestamp.round<next.r));
        const completed=banks.find(e=>e.timestamp.round>a.r&&(!next||e.timestamp.round<=next.r)&&(!ending||e.timestamp.round<=ending.r)&&(!death||e.timestamp.ordinal<death.timestamp.ordinal));
        if(completed)continue;
        if(!ending&&!next&&!death){ch.descriptors.bank_attempts_censored++;continue;}
        const end=Math.min(ending?.r??Infinity,next?.r??Infinity,death?.timestamp.round??Infinity);
        addEpisode(ch,'D8','bank_channel_interrupted',a.r,end,{channel_type:a.channel_type,death:!!death&&death.timestamp.round===end},0);
      }
      episodes(ch,'D9','visible_isolation',rows,r=>r.alive&&r.p&&r.enemies6>=T.isolated_enemies&&r.allies6===0,T.isolated_turns,r=>({visible_enemies:r.enemies6,allies:r.allies6,x:r.p.x,y:r.p.y}));
      episodes(ch,'D9','ground_island_proxy',whole,r=>free(r)&&same(r.p,r.end_p)&&r.ground_disconnected&&!moving(r),T.ground_island_turns,r=>({component_size:r.component_size,x:r.p.x,y:r.p.y,limitation:'Ability/teleport routes are not tested'}),r=>pointKey(r.p));
      episodes(ch,'D10','high_gold',rows,r=>r.gold>=T.gold,T.gold_turns,(a,b)=>({gold_start:a.gold,gold_end:b.gold,alive_start:a.alive}));
      const buys=events.filter(e=>e.owner.kind==='champion'&&e.owner.id===ch.id&&['buyItem','buyConsumable'].includes(e.kind));
      ch.descriptors.first_native_buy=buys.length?Math.min(...buys.map(e=>e.timestamp.round)):null;
      ch.descriptors.equipment_at=Object.fromEntries(T.equipment_rounds.map(r=>[r,rows.find(x=>x.r===r)?.gear??null]));
      ch.descriptors.wards_by_250=native.match.roundsStarted>=250?ownEvents(events,ch.id,'wardPlacement').filter(e=>e.timestamp.round<=250).reduce((s,e)=>s+Number(e.value),0):null;
      ch.descriptors.death_gems_lost=ownEvents(events,ch.id,'gemLoss').reduce((s,e)=>s+Number(e.value),0);
      ch.descriptors.end_gems=Number(native.champions.find(c=>c.id===ch.id).metrics.gems);
      ch.descriptors.native_deaths=deaths.length;
      ch.descriptors.visible_enemy_lock_high_bag_samples=rows.filter(r=>r.alive&&r.bag>=T.bag_gems&&r.visible_enemy_locks.length).length;
    }
    // Native clear/receipt identities avoid the older gold-gain capture heuristic.
    const receiptMap=new Map();
    for(const e of events.filter(e=>e.kind==='gemCollection'&&e.target?.kind==='campGroup')){
      const key=[e.timestamp.round,e.timestamp.input,e.target.id,e.owner.team].join(':');
      if(!receiptMap.has(key))receiptMap.set(key,{...e,value:0});receiptMap.get(key).value+=Number(e.value);
    }
    const race=[...events.filter(e=>e.kind==='campClear'&&e.target?.kind==='campGroup'),...receiptMap.values()].sort((a,b)=>a.timestamp.ordinal-b.timestamp.ordinal);
    const lastClear=new Map();let nativeReceipts=0;
    for(const e of race){
      if(e.kind==='campClear')lastClear.set(e.target.id,e);
      else{
        nativeReceipts++;const clear=lastClear.get(e.target.id);
        if(clear&&all.has(clear.owner.id)){
          const denom=all.get(clear.owner.id).denominators;
          denom.gem_reward_clear_episodes=(denom.gem_reward_clear_episodes??0)+1;
        }
        if(clear&&clear.owner.team!==e.owner.team&&all.has(clear.owner.id))addEpisode(all.get(clear.owner.id),'D5','reward_to_enemy_after_native_clear',e.timestamp.round,e.timestamp.round,
          {group:e.target.id,clear_round:clear.timestamp.round,enemy_gems:e.value,recipient_team:e.owner.team},0);
        lastClear.delete(e.target.id);
      }
    }
    let progressTransitions=0;
    for(let fi=1;fi<groupFrames.length;fi++){
      const prior=groupFrames[fi-1],now=groupFrames[fi];if(now.r!==prior.r+1)continue;
      for(let gi=0;gi<prior.groups.length;gi++){
        const a=prior.groups[gi],b=now.groups[gi];
        if(a.state!==2||a.team>1||a.duration<=0||a.timer>=a.duration)continue;progressTransitions++;
        for(const id of a.on.filter(id=>all.get(id)?.team===a.team)){
          const denom=all.get(id).denominators;denom.capture_progress_transitions=(denom.capture_progress_transitions??0)+1;
        }
        if(b.state===2&&(b.team!==a.team||b.timer>a.timer))for(const id of a.on.filter(id=>all.get(id)?.team===a.team))
          addEpisode(all.get(id),'D5','observed_capture_progress_lost',now.r,now.r,{group:gi,previous_timer:a.timer,current_timer:b.timer,previous_duration:a.duration,current_duration:b.duration,previous_owner:a.team,current_owner:b.team},0);
      }
    }
    const actors=[...all.values()].map(({turns,...ch})=>({...ch,detectors:Object.fromEntries(Object.entries(ch.detectors).map(([id,d])=>{
      // Overlapping D6/D9 subtypes must not count the same physical turn twice.
      const timed=['D1','D2','D6','D9','D10'].includes(id),flaggedTurns=timed?unionTurns(d.events):0;
      const ratio=(numerator,denominator,unit)=>({numerator,denominator,rate:denominator?numerator/denominator:null,unit});
      const count=subtype=>d.events.filter(e=>e.subtype===subtype).length;
      const denominators={D1:'idle_eligible_turns',D2:'alive_observed_turns',D6:'alive_complete_turns',D9:'alive_observed_turns',D10:'observed_turns'};
      const rates={};
      if(timed)rates.flagged_turn_fraction=ratio(flaggedTurns,ch.denominators[denominators[id]],'champion-turn fraction');
      if(id==='D2')rates.high_bag_death_fraction=ratio(count('high_bag_death'),ch.denominators.native_deaths,'native-death fraction');
      if(id==='D3')rates.repeat_death_fraction=ratio(d.events.length,ch.denominators.native_deaths,'native-death fraction');
      if(id==='D4')rates.episodes_per_move=ratio(d.events.length,ch.denominators.moves,'episode per recorded movement step');
      if(id==='D5'){
        rates.progress_losses=ratio(count('observed_capture_progress_lost'),ch.denominators.capture_progress_transitions??0,'loss per observed progress transition');
        rates.enemy_reward_after_clear=ratio(count('reward_to_enemy_after_native_clear'),ch.denominators.gem_reward_clear_episodes??0,'enemy gem reward per matched native-clear episode');
      }
      if(id==='D7')rates.events_per_turn=ratio(d.events.length,ch.denominators.complete_turns,'native fuel/fault event per fully observed turn');
      if(id==='D8')rates.interrupted_attempt_fraction=ratio(d.events.length,ch.denominators.bank_attempts-ch.descriptors.bank_attempts_censored,'completed-observation bank-attempt fraction');
      if(id==='D11')rates.sampled_vision_gap_death_fraction=ratio(d.events.length,ch.denominators.vision_eligible_deaths??0,'eligible-death fraction');
      return[id,{...d,flagged:d.events.length>0,event_count:d.events.length,flagged_turns:flaggedTurns,rates}];
    }))}));
    return{match_id:entry.match_id,partition:entry.partition,engine:VERSION,spec_sha256:SPEC_HASH,code_sha256:CODE_HASH,
      replay_sha256:hash(fs.readFileSync(file)),summary_sha256:hash(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'))),
      rounds:native.match.roundsStarted,validation:validations,validation_samples:{selfChecks,clockChecks,hiddenEnemySamples,visibleEnemySamples,completeTurns},
      coverage:{native_gem_reward_captures:nativeReceipts,observed_capture_progress_transitions:progressTransitions,
        rejected_sdk_calls:'unobservable',vision:'victim turn-start samples',group_progress:'round-boundary samples'},
      actors,ms:Math.round(performance.now()-started)};
  }finally{E.destroy();}
}

if(!isMainThread){
  assert(VERSION==='2.0.0','Explicit engine 2.0.0 required');const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
  parentPort.on('message',item=>{
    if(item===null){parentPort.close();return;}
    try{
      const row=analyse(E,item.file,item.entry,workerData.validate);
      fs.writeFileSync(path.join(workerData.out,item.entry.match_id+'.json'),JSON.stringify(row)+'\n');
      parentPort.postMessage({match_id:row.match_id,passed:Object.values(row.validation).every(Boolean),failed:Object.entries(row.validation).filter(([,v])=>!v).map(([k])=>k),ms:row.ms});
    }catch(e){parentPort.postMessage({match_id:item.entry.match_id,passed:false,error:String(e.stack??e)});}
  });parentPort.postMessage('ready');
}else if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  let partition=null,out=null,workers=4,validate=true;
  for(let i=2;i<process.argv.length;i++){
    if(process.argv[i]==='--partition')partition=process.argv[++i];else if(process.argv[i]==='--out')out=path.resolve(process.argv[++i]);
    else if(process.argv[i]==='--workers')workers=Number(process.argv[++i]);else if(process.argv[i]==='--validate')validate=true;
    else throw new Error('Unknown argument '+process.argv[i]);
  }
  assert(VERSION==='2.0.0','Set NFS_REPLAY_ENGINE=2.0.0');
  assert(['calibration-excluded','examined'].includes(partition),'Only calibration/examined partitions are allowed');
  assert(out&&out.startsWith(path.join(ROOT,'artifacts')+path.sep),'Output must be local artifacts');
  assert(Number.isInteger(workers)&&workers>0&&workers<=8,'workers must be 1..8');
  fs.mkdirSync(out,{recursive:true});
  const manifest=JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8'));
  const inputs=manifest.rows.filter(r=>r.partition===partition).map(entry=>({entry,file:path.join(ROOT,'artifacts/local-only/deep-2026-10-28/replays',partition,entry.match_id+'.repl26a')}));
  if(partition==='examined'){
    const proofPath=path.join(STUDY,'DETECTOR_VALIDATION.json');assert(fs.existsSync(proofPath),'Calibration validation receipt required');
    const proof=JSON.parse(fs.readFileSync(proofPath,'utf8'));
    assert(proof.passed===5&&proof.failed===0&&proof.spec_sha256===SPEC_HASH&&proof.code_sha256===CODE_HASH,'Five current-code calibration games must pass before examined processing');
  }
  let next=0,done=0;const results=[],started=performance.now();
  await Promise.all(Array.from({length:Math.min(workers,inputs.length)},()=>new Promise((resolve,reject)=>{
    const worker=new Worker(new URL(import.meta.url),{workerData:{out,validate}});
    const feed=()=>worker.postMessage(next<inputs.length?inputs[next++]:null);
    worker.on('message',result=>{if(result==='ready'){feed();return;}results.push(result);done++;if(done%25===0)console.log(JSON.stringify({partition,processed:done,total:inputs.length}));feed();});
    worker.on('error',reject);worker.on('exit',code=>code?reject(new Error('Worker exit '+code)):resolve());
  })));
  const report={engine:VERSION,partition,spec_sha256:SPEC_HASH,code_sha256:CODE_HASH,pinned_assets:PINNED,processed:results.length,
    passed:results.filter(r=>r.passed).length,failed:results.filter(r=>!r.passed).length,seconds:Math.round((performance.now()-started)/1000),results};
  fs.writeFileSync(path.join(out,'run.json'),JSON.stringify(report,null,2)+'\n');
  if(partition==='calibration-excluded')fs.writeFileSync(path.join(STUDY,'DETECTOR_VALIDATION.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,results:results.filter(r=>!r.passed)}));if(report.failed)process.exitCode=1;
}
export {episodes,isIdle,idleEligible,unionTurns,equip,isMovementAction};
