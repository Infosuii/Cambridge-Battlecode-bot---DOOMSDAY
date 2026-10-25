// Economy, objective and death diagnostics from pinned omniscient replay snapshots.
// Offline analysis only: never supplies hidden state to a bot.
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [input, output] = process.argv.slice(2);
const results = [];
for (const name of fs.readdirSync(input).filter(x => x.endsWith('.repl26a'))) {
  E.load(fs.readFileSync(path.join(input,name)));
  const {X,check,dv,out,args,tsnap}=E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h,out)); const main=dv().getBigUint64(out,true);
  check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16)); const size=dv().getUint32(args,true);
  check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  const full=()=>{check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));return E.PC.I(dv(),tsnap);};
  let lastRound=-1,previous=null,first=null,final=null;
  const teams=[0,1].map(()=>({banks:[],deaths:0,lost_on_death:0,camp_attacks:0,champion_attacks:0,
    first_targets:[],purchases:[],snapshots:[],gate_damage_rounds:[],fuel_exhausted:0,
    camp_attacks_by_type:{},early_camp_attacks:0,early_champion_attacks:0,
    dead_champion_rounds:0,alive_champion_rounds:0,unspent_gold_rounds:0}));
  const seenTargets=[new Set(),new Set()];
  let champs=new Map(), camps=new Map();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
    const d=dv(), round=d.getUint32(tsnap+8,true), kind=d.getUint32(tsnap+68,true), actor=d.getUint32(tsnap+76,true);
    const phase=d.getUint32(tsnap+24,true), outcome=d.getUint32(tsnap+28,true), pos=d.getUint32(tsnap+56,true);
    let s;
    if ((round!==lastRound && phase===10) || kind===18 || kind===13 || outcome) {
      s=full();
      if (!first && s.champions.length) first=s;
      champs=new Map(s.champions.map(c=>[c.entity.index,c]));
      camps=new Map(s.camps.filter(c=>c.position).map(c=>[`${c.position.x},${c.position.y}`,c]));
      if (round!==lastRound && phase===10) {
        for (const c of s.champions) {
          const p=previous?.champions.find(x=>x.entity.index===c.entity.index);
          if (p?.alive && !c.alive) {teams[c.team].deaths++;teams[c.team].lost_on_death+=p.gems??0;}
          if(c.alive) {teams[c.team].alive_champion_rounds++;teams[c.team].unspent_gold_rounds+=c.gold??0;}
          else teams[c.team].dead_champion_rounds++;
        }
        if (round===1 || round%100===0 || [25,50,75,150,250,750].includes(round))
          for (const t of [0,1]) teams[t].snapshots.push({round,banked:Number(s.submittedGems[t]),
            deaths:teams[t].deaths,dead_champion_rounds:teams[t].dead_champion_rounds,
            champions:s.champions.filter(c=>c.team===t).map(c=>({id:c.entity.index,type:c.type,alive:c.alive,
              position:c.position,hp:c.health,max_hp:c.maxHealth,gold:c.gold,gems:c.gems,
              items:c.items.map((n,i)=>n?[i,n]:null).filter(Boolean)}))});
        previous=s;lastRound=round;
      }
      if (kind===18 && champs.has(actor)) {
        const t=champs.get(actor).team, a=teams[t].banks;
        const total=Number(s.submittedGems[t]), prev=a.length?a.at(-1).total:0;
        a.push({round,actor,total,amount:total-prev});
      }
      if (kind===13 && champs.has(actor)) {
        const c=champs.get(actor);
        teams[c.team].purchases.push({round,type:c.type,items:c.items.map((n,i)=>n?[i,n]:null).filter(Boolean)});
      }
    }
    if (champs.has(actor)) {
      const t=champs.get(actor).team;
      if (kind===26) teams[t].fuel_exhausted++;
      if (kind===5) {
        const tx=dv().getInt32(tsnap+88,true),ty=dv().getInt32(tsnap+92,true),key=`${tx},${ty}`,c=camps.get(key);
        if (c) {
          teams[t].camp_attacks++;
          teams[t].camp_attacks_by_type[c.type]=(teams[t].camp_attacks_by_type[c.type]??0)+1;
          if(round<=250) teams[t].early_camp_attacks++;
          if (!seenTargets[t].has(key)) {seenTargets[t].add(key);teams[t].first_targets.push({round,type:c.type,x:tx,y:ty});}
        } else {teams[t].champion_attacks++;if(round<=250) teams[t].early_champion_attacks++;}
      }
    }
    if (outcome || (d.getUint32(tsnap+20,true)!==0 && pos>=size)) {final=s??full();break;}
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  results.push({id:name.replace('.repl26a',''),rounds:final.round,outcome:final.outcome,
    drafts:final.drafts,submitted_gems:final.submittedGems.map(Number),teams,
    champions:final.champions.map(c=>({id:c.entity.index,team:c.team,type:c.type,gems:c.gems,gold:c.gold,kills:c.kills}))});
  E.destroy();
}
fs.writeFileSync(output,JSON.stringify(results));
console.log(JSON.stringify({replays:results.length,out:output}));
