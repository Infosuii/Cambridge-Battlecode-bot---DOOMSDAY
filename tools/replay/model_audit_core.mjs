// Pure event accounting shared by the pinned replay reader and synthetic tests.
export function memberHpHash(hp) {
  const bytes=new DataView(new ArrayBuffer(4));let h=2166136261;
  hp.forEach((value,index)=>{
    bytes.setFloat32(0,Math.max(0,value),true);
    h=Math.imul(h^index,16777619)>>>0;h=Math.imul(h^bytes.getUint32(0,true),16777619)>>>0;
  });return h;
}
export function parseQuotes(text) {
  const quotes=[];const seen=new Set();
  const required=['round','body','slot','kind','group','new','contact','x','y','state','seen','dist','field',
    'attacks','loss','hp','camp_hp','raw','quant','range','cluster','members','nearby','enemies','status'];
  for(const line of text.split('\n').filter(x=>x.startsWith('DZ_MODEL '))) {
    let q=Object.fromEntries([...line.matchAll(/(\w+)=(-?\d+(?:\.\d+)?)/g)].map(m=>[m[1],Number(m[2])]));
    if('v' in q) {
      if(q.v!==2)throw new Error('Unsupported model quote version');
      const aliases={r:'round',b:'body',s:'slot',k:'kind',g:'group',n:'new',c:'contact',x:'x',y:'y',st:'state',sn:'seen',
        d:'dist',f:'field',a:'attacks',l:'loss',h:'hp',ch:'camp_hp',rw:'raw',q:'quant',rg:'range',cl:'cluster',m:'members',
        na:'nearby',ne:'enemies',ok:'status',rc:'reset_cd',rm:'reset_max',t:'clock',ts:'clock_status',tl:'timed_loss',ss:'shield_sample',
        sk:'shield_skip',af:'shield_available',pm:'shield_mode',ph:'member_hp_hash',ps:'shield_status',pt:'shield_rounds',pl:'shield_loss',pc:'shield_casts',pn:'shield_live',pi:'shield_member',cd:'shield_cd',
        cp:'shield_period',ca:'shield_amount',ct:'shield_duration',ex:'shield_existing',ev:'shield_value',et:'shield_timer',
        inc:'shield_incoming',cast:'shield_can_cast',fuel:'shield_fuel'};
      const expanded={};
      for(const [key,value] of Object.entries(q))if(key!=='v') {
        if(!aliases[key])throw new Error('Unexpected compact model field');expanded[aliases[key]]=value;
      }
      q=expanded;
    }
    if(required.some(k=>!Number.isFinite(q[k])))throw new Error('Incomplete model quote');
    const key=`${q.round}:${q.body}`;
    if(seen.has(key))throw new Error('Duplicate model quote');
    seen.add(key);quotes.push(q);
  }
  if(!quotes.length)throw new Error('No model predictions; missing logs are not zero error');
  return quotes;
}

export class ModelAudit {
  constructor(quotes,groups,lastRound=500,campDesigns=null,campSpawns=null) {
    this.groups=groups;this.lastRound=lastRound;this.previous=null;this.frames=0;this.campDesigns=campDesigns;this.campSpawns=campSpawns;
    this.records=quotes.filter(q=>q.kind===0).map(q=>{
      if(!groups[q.group]||groups[q.group].length!==q.members)throw new Error('Quote/native group membership mismatch');
      const next=quotes.find(n=>n.body===q.body&&n.round>q.round&&n.new===1);
      return {quote:q,end_round:next?.round??lastRound+1,started:false,outcome:null,
        arrival_round:null,first_attack_round:null,clear_round:null,own_basic_attacks:0,
        own_damage_events:0,own_nonbasic_damage_events:0,other_damage_events:0,unknown_damage_events:0,helpers:[],
        hp_loss:0,target_camp_hp_loss:0,other_hp_loss:0,healing:0,basic_actions:[],reset_actions:[],shield_actions:[],
        bystander_context_known:campDesigns!==null,potential_tank_bystanders:[],
        target_camp_other_hp_loss:0,other_camp_targets:[],own_movement_events:0,camp_movement_events:0};
    });
  }
  consume(s,visibleCamp=()=>false) {
    ++this.frames;
    const champs=new Map(s.champions.map(c=>[c.entity.index,c]));
    const camps=new Map(s.camps.map(c=>[c.entity.index,c]));
    const previous=this.previous;
    const prevChamps=new Map((previous?.champions??[]).map(c=>[c.entity.index,c]));
    const prevCamps=new Map((previous?.camps??[]).map(c=>[c.entity.index,c]));
    for(const r of this.records) {
      if(r.outcome)continue;
      const q=r.quote,c=champs.get(q.body),memberIds=this.groups[q.group];
      const ownTurn=s.phase===14&&s.currentChampion===q.body;
      if(!r.started) {
        // A quote follows observation/shopping, before execution. Match its
        // physical position/HP on its own turn, without borrowing future HP.
        const ownAction=s.phase===10&&s.step?.actor.kind===1&&s.step.actor.index===q.body;
        if(s.round===q.round&&(ownTurn||ownAction)&&c?.alive&&c.position?.x===q.x&&c.position?.y===q.y&&Math.abs(c.health-q.hp)<.021) {
          r.started=true;r.start_frame=this.frames;
          r.champion_type=c.type;
          r.native_initial_camp_hp=memberIds.reduce((n,id)=>n+(camps.get(id)?.health??0),0);
          const live=memberIds.filter(id=>(camps.get(id)?.health??0)>0);
          r.native_initial_live_members=live.length;
          if(live.length>1)r.native_initial_members=live.map(id=>{
            const m=camps.get(id);return {id,hp:m.health,type:m.type,x:m.position.x,y:m.position.y};
          });
          if(this.campDesigns!==null) {
            const damaging=live.filter(id=>this.campDesigns.get(camps.get(id).type)?.strength>0);
            r.native_damaging_live_members=damaging.length;
            r.shield_target_matches=damaging.length===1&&memberIds[q.shield_member]===damaging[0];
          }
          r.native_member_hp_hash=memberHpHash(memberIds.map(id=>camps.get(id)?.health??0));
          if('member_hp_hash' in q)r.member_hp_hash_matches=q.member_hp_hash===r.native_member_hp_hash;
          r.native_static_positions=this.campSpawns!==null&&live.every(id=>{
            const p=this.campSpawns.get(id),c=camps.get(id);return p&&c.position.x===p.x&&c.position.y===p.y;
          });
          if('shield_member' in q)r.shield_member_matches=live.length===1&&memberIds[q.shield_member]===live[0];
          r.memory_hp_difference=q.camp_hp-r.native_initial_camp_hp;
        } else if(s.round>q.round)r.outcome='unmatched_quote';
        if(!r.started)continue;
      }
      if(s.round>this.lastRound) { r.outcome='right_censored';continue; }
      if(s.round>=r.end_round&&ownTurn) { r.outcome='goal_changed';continue; }
      // A non-damaging ally/enemy can still absorb a camp's attacks. Outcome
      // context only: native positions never become inputs to bot predictions.
      if(this.campDesigns)for(const id of memberIds) {
        const camp=camps.get(id);if(!camp||camp.health<=0)continue;
        const design=this.campDesigns.get(camp.type);
        if(!design)throw new Error('Missing camp design for bystander classification');
        if(design.strength<=0)continue;
        for(const other of s.champions)if(other.entity.index!==q.body&&other.alive&&
            Math.max(Math.abs(other.position.x-camp.position.x),Math.abs(other.position.y-camp.position.y))<=design.range&&
            !r.potential_tank_bystanders.includes(other.entity.index))r.potential_tank_bystanders.push(other.entity.index);
      }
      if(this.frames!==r.start_frame&&previous) {
        if(s.step?.kind===6&&s.step.actor.kind===1&&s.step.actor.index===q.body&&s.step.abilityType===1) {
          const action=`${s.step.round}:${s.step.inputPosition}`;
          if(!r.reset_actions.includes(action))r.reset_actions.push(action);
        }
        if(s.step?.kind===6&&s.step.actor.kind===1&&s.step.actor.index===q.body&&s.step.abilityType===7) {
          const action=`${s.step.round}:${s.step.inputPosition}`;
          if(!r.shield_actions.includes(action))r.shield_actions.push(action);
        }
        const prev=prevChamps.get(q.body);
        if(prev?.alive&&c?.alive&&(prev.position.x!==c.position.x||prev.position.y!==c.position.y))++r.own_movement_events;
        for(const id of memberIds) {
          const p=prevCamps.get(id),camp=camps.get(id);
          if(p?.health>0&&camp?.health>0&&(p.position.x!==camp.position.x||p.position.y!==camp.position.y))++r.camp_movement_events;
        }
        if(s.step?.actor.kind===2&&memberIds.includes(s.step.actor.index))for(const other of s.champions) {
          if(other.entity.index===q.body)continue;
          const loss=Math.max(0,(prevChamps.get(other.entity.index)?.health??other.health)-other.health);
          r.target_camp_other_hp_loss+=loss;
          if(loss>0&&!r.other_camp_targets.includes(other.entity.index))r.other_camp_targets.push(other.entity.index);
        }
        if(prev&&c) {
          const loss=Math.max(0,prev.health-c.health);r.hp_loss+=loss;r.healing+=Math.max(0,c.health-prev.health);
          if(s.step?.actor.kind===2&&memberIds.includes(s.step.actor.index))r.target_camp_hp_loss+=loss;
          else r.other_hp_loss+=loss;
        }
        const changes=memberIds.map(id=>({id,before:prevCamps.get(id)?.health??0,after:camps.get(id)?.health??0}));
        if(changes.some(x=>x.after>x.before+.01)) { r.outcome='camp_hp_increased';continue; }
        if(changes.some(x=>x.before>x.after+.01)) {
          const actor=s.step?.actor;
          if(actor?.kind===1&&actor.index===q.body) {
            ++r.own_damage_events;
            if(s.step.kind!==5)++r.own_nonbasic_damage_events;
            if(s.step.kind===5) {
              const action=`${s.step.round}:${s.step.inputPosition}`;
              if(!r.basic_actions.includes(action)) { r.basic_actions.push(action);++r.own_basic_attacks; }
              r.first_attack_round??=s.round;
              // A successful basic against this group proves legal contact,
              // including a melee attack after moving in this very turn.
              r.arrival_round??=s.round;
            }
          } else if(actor?.kind===1) {
            ++r.other_damage_events;if(!r.helpers.includes(actor.index))r.helpers.push(actor.index);
          } else ++r.unknown_damage_events;
        }
      }
      if(!c?.alive) { r.outcome='death';continue; }
      if(ownTurn&&r.arrival_round===null) {
        const inRange=memberIds.filter(id=>{
          const camp=camps.get(id);return camp?.health>0&&Math.max(Math.abs(c.position.x-camp.position.x),Math.abs(c.position.y-camp.position.y))<=q.range;
        });
        if(inRange.some(id=>visibleCamp(id,c)))r.arrival_round=s.round;
      }
      if(memberIds.every(id=>(camps.get(id)?.health??0)<=0)) {
        r.clear_round=s.round;r.outcome=r.native_initial_camp_hp>0?'cleared':'already_clear';
      }
    }
    this.previous=s;
  }
  finish() {
    for(const r of this.records)if(!r.outcome)r.outcome=r.started?'right_censored':'unmatched_quote';
    return {frames:this.frames,records:this.records};
  }
}
