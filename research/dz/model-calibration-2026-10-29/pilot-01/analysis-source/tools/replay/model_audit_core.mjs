// Pure event accounting shared by the pinned replay reader and synthetic tests.
export function parseQuotes(text) {
  const quotes=[];const seen=new Set();
  const required=['round','body','slot','kind','group','new','contact','x','y','state','seen','dist','field',
    'attacks','loss','hp','camp_hp','raw','quant','range','cluster','members','nearby','enemies','status'];
  for(const line of text.split('\n').filter(x=>x.startsWith('DZ_MODEL '))) {
    const q=Object.fromEntries([...line.matchAll(/(\w+)=(-?\d+(?:\.\d+)?)/g)].map(m=>[m[1],Number(m[2])]));
    if(required.some(k=>!Number.isFinite(q[k])))throw new Error('Incomplete model quote');
    const key=`${q.round}:${q.body}`;
    if(seen.has(key))throw new Error('Duplicate model quote');
    seen.add(key);quotes.push(q);
  }
  if(!quotes.length)throw new Error('No model predictions; missing logs are not zero error');
  return quotes;
}

export class ModelAudit {
  constructor(quotes,groups,lastRound=500) {
    this.groups=groups;this.lastRound=lastRound;this.previous=null;this.frames=0;
    this.records=quotes.filter(q=>q.kind===0).map(q=>{
      if(!groups[q.group]||groups[q.group].length!==q.members)throw new Error('Quote/native group membership mismatch');
      const next=quotes.find(n=>n.body===q.body&&n.round>q.round&&n.new===1);
      return {quote:q,end_round:next?.round??lastRound+1,started:false,outcome:null,
        arrival_round:null,first_attack_round:null,clear_round:null,own_basic_attacks:0,
        own_damage_events:0,own_nonbasic_damage_events:0,other_damage_events:0,unknown_damage_events:0,helpers:[],
        hp_loss:0,target_camp_hp_loss:0,other_hp_loss:0,healing:0,basic_actions:[]};
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
          r.memory_hp_difference=q.camp_hp-r.native_initial_camp_hp;
        } else if(s.round>q.round)r.outcome='unmatched_quote';
        if(!r.started)continue;
      }
      if(s.round>this.lastRound) { r.outcome='right_censored';continue; }
      if(s.round>=r.end_round&&ownTurn) { r.outcome='goal_changed';continue; }
      if(this.frames!==r.start_frame&&previous) {
        const prev=prevChamps.get(q.body);
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
