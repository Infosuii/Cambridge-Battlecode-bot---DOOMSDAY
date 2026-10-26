// Descriptive omniscient replay census, using the repository's pinned official
// engine/decoder. No bot execution, policy input generation or training.
// Usage: node --no-warnings tools/replay/scout_states.mjs --out <dir> <raw replays dir>
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {engine, defaultAssets, verifyAssets, PINNED} from './engine.mjs';

const argv = process.argv.slice(2), outIndex = argv.indexOf('--out');
if (outIndex < 0 || argv.length !== 3) throw Error('usage: --out <dir> <raw replays dir>');
const out = argv[outIndex + 1], input = argv[outIndex === 0 ? 2 : 0];
fs.mkdirSync(out, {recursive:true});
const assets = defaultAssets(); verifyAssets(assets); const E = await engine(assets);
const kinds = {4:'move',5:'attack',6:'cast',9:'priority',11:'recall',12:'submit_start',
  13:'buy',14:'ward',18:'submit_bank',20:'lock',23:'dash_move',25:'sell',26:'fuel_exhausted',27:'error'};
const sum = (a, f) => a.reduce((s,x)=>s+Number(f(x)??0),0);
const dist = (a,b) => Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const json = x => JSON.stringify(x,(_,v)=>typeof v==='bigint'?Number(v):v);
function state() {
  E.check(E.X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xffffffff),E.snap));
  return E.PC.F(E.dv(),E.snap);
}
function header() {
  E.check(E.X.Game_Visualiser_ReadTimelineState(E.h,E.tsnap));
  const d=E.dv(),t=E.tsnap,u=o=>d.getUint32(t+o,true);
  if(u(0)!==1||u(4)!==E.tsize) throw Error('unsupported snapshot ABI');
  return {round:u(8),awaiting:!!u(20),phase:u(24),outcome:u(28),score:[u(32),u(40)],
    input:u(56),kind:u(68),actorKind:u(72),actor:u(76),substep:u(104)};
}
const mini = c => ({id:c.entity.index,type:c.type,team:c.team,alive:c.alive,position:c.position,
  hp:c.health,max_hp:c.maxHealth,gems:c.gems,gold:c.gold,earned_gold:c.earnedGold,
  kda:c.kda,items:c.items});

function decode(file) {
  const started=performance.now(),bytes=fs.readFileSync(file);
  E.load(bytes);
  try {
    E.check(E.X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=E.dv().getBigUint64(E.out,true);
    E.check(E.X.Game_Visualiser_Timeline_Info(E.h,main,E.args,E.args+8,E.args+16));
    const size=E.dv().getUint32(E.args,true);
    E.check(E.X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    E.check(E.X.Game_API_Map_GetNumCampGroups(E.h,E.out));const ng=E.dv().getUint32(E.out,true);
    if(ng>256)throw Error('too many groups');
    E.check(E.X.Game_API_Map_GetCampGroups(E.h,E.buf+2048,256,E.out));
    const handles=[...new Uint32Array(E.X.memory.buffer,E.buf+2048,ng)];
    const groups=handles.map(handle=>{
      E.check(E.X.Game_API_Map_CampGroup_Get(E.h,handle,E.out));
      return {handle,gems:E.dv().getUint32(E.out,true),gold:E.dv().getUint32(E.out+4,true)};
    });
    const counts=[{},{}],banks=[[],[]],curve=[],checkpoints=[],teamOf=new Map(),
      peakBags=[0,0],carry100Rounds=[0,0],firsts=new Map();
    let prev=null,lastRound=-1,steps=0,unknownActor=0;
    const sample = s => {
      if(s.phase===12 || !s.champions.length)return;
      for(const c of s.champions)teamOf.set(c.entity.index,c.team);
      const perTeam=[0,1].map(t=>{
        const cs=s.champions.filter(c=>c.team===t);
        peakBags[t]=Math.max(peakBags[t],...cs.map(c=>Number(c.gems)));
        carry100Rounds[t]+=cs.some(c=>c.alive&&Number(c.gems)>=100)?1:0;
        return {score:Number(s.submittedGems[t]),carried:sum(cs,c=>c.gems),
          alive:cs.filter(c=>c.alive).length,deaths:sum(cs,c=>c.kda[1]),
          gold:sum(cs,c=>c.gold),earned_gold:sum(cs,c=>c.earnedGold)};
      });
      if(s.round%50===0||!curve.length)curve.push({round:s.round,teams:perTeam});
      if(s.round%250===0)checkpoints.push({round:s.round,champions:s.champions.map(mini)});
      for(const group of groups){
        const camps=s.camps.filter(c=>c.group===group.handle);
        if(!camps.length)continue;
        group.max_hp ??= sum(camps,c=>c.maxHealth);
        group.camps ??= camps.map(c=>({id:c.entity.index,type:c.type,position:c.position}));
        const hp=sum(camps,c=>Math.max(0,c.health));
        let rec=firsts.get(group.handle);
        if(!rec){rec={};firsts.set(group.handle,rec);}
        // A dead camp's live snapshot may omit its position. Its static seeded
        // position remains the objective anchor after the clear.
        const near=()=>s.champions.filter(c=>c.alive&&c.position&&
          group.camps.some(p=>p.position&&dist(c.position,p.position)<=8)).map(mini);
        if(hp<group.max_hp-0.01 && rec.first_damage_round===undefined){
          rec.first_damage_round=s.round;
          if(group.gems>=100)rec.near_first_damage=near();
        }
        if(hp<=0&&rec.first_clear_round===undefined){
          rec.first_clear_round=s.round;
          if(group.gems>=100)rec.near_first_clear=near();
        }
      }
    };
    for(;;){
      const h=header();
      if(prev&&h.input===prev.input&&h.substep===prev.substep)throw Error('timeline made no progress');
      if(h.round!==lastRound&&h.phase!==12){lastRound=h.round;sample(state());}
      if(h.actorKind===1&&kinds[h.kind]){
        const t=teamOf.get(h.actor);
        if(t===undefined)unknownActor++; else counts[t][kinds[h.kind]]=(counts[t][kinds[h.kind]]??0)+1;
      }
      if(prev)for(let t=0;t<2;t++){
        const delta=h.score[t]-prev.score[t];
        if(delta<0)throw Error('submitted score decreased');
        if(delta>0)banks[t].push({round:h.round,amount:delta,kind:h.kind,champion:h.actorKind===1?h.actor:null});
      }
      steps++;
      if(steps>1500000)throw Error('step cap reached');
      if(h.outcome||(h.awaiting&&h.input>=size))break;
      prev=h;E.check(E.X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    const s=state();
    if(!s.outcome)throw Error('incomplete replay');
    curve.push({round:s.round,final:true,teams:[0,1].map(t=>{
      const cs=s.champions.filter(c=>c.team===t);
      return {score:Number(s.submittedGems[t]),carried:sum(cs,c=>c.gems),
        alive:cs.filter(c=>c.alive).length,deaths:sum(cs,c=>c.kda[1]),
        gold:sum(cs,c=>c.gold),earned_gold:sum(cs,c=>c.earnedGold)};
    })});
    const teams=[0,1].map(t=>{
      const cs=s.champions.filter(c=>c.team===t);
      const amounts=banks[t].map(b=>b.amount).sort((a,b)=>a-b);
      const bankSum=sum(banks[t],b=>b.amount);
      if(bankSum!==Number(s.submittedGems[t]))throw Error('bank sum differs from final score');
      return {team:t,score:Number(s.submittedGems[t]),final_carried:sum(cs,c=>c.gems),
        peak_single_bag_round_sample:peakBags[t],rounds_with_100_bag:carry100Rounds[t],
        physical_body_deaths:sum(cs,c=>c.kda[1]),kills:sum(cs,c=>c.kda[0]),
        earned_gold:sum(cs,c=>c.earnedGold),unspent_gold:sum(cs,c=>c.gold),
        bank_events:banks[t].length,first_bank_round:banks[t][0]?.round??null,
        median_bank:amounts.length?amounts[Math.floor(amounts.length/2)]:null,
        actions:counts[t],champions:cs.map(mini),banks:banks[t]};
    });
    return {ok:true,replay:path.basename(file),replay_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
      engine:'1.0.3',pinned:PINNED,steps,rounds:s.round,outcome:s.outcome,
      drafts:s.drafts.map((d,t)=>d.slice(0,s.draftCounts[t])),unknown_actor_actions:unknownActor,
      teams,groups:groups.map(g=>({...g,...firsts.get(g.handle)})),curve,checkpoints,
      elapsed_seconds:(performance.now()-started)/1000};
  }finally{E.destroy();}
}
const results=[];
for(const name of fs.readdirSync(input).filter(n=>n.endsWith('.repl26a')).sort()){
  const dest=path.join(out,name.replace('.repl26a','.json'));
  try{
    const r=decode(path.join(input,name));fs.writeFileSync(dest,json(r)+'\n');
    results.push({replay:name,ok:true,seconds:r.elapsed_seconds});
    console.log(json(results.at(-1)));
  }catch(e){results.push({replay:name,ok:false,error:String(e.message??e)});console.log(json(results.at(-1)));}
}
fs.writeFileSync(path.join(out,'run.json'),json({assets,pinned:PINNED,results})+'\n');
if(results.some(r=>!r.ok))process.exitCode=1;
