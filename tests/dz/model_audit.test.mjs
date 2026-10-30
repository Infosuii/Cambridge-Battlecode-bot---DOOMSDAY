import test from 'node:test';
import assert from 'node:assert/strict';
import {ModelAudit,parseQuotes} from '../../tools/replay/model_audit_core.mjs';

const quote={round:10,body:0,slot:0,kind:0,group:0,new:1,contact:1,x:0,y:0,state:0,seen:10,
  dist:1,field:1,attacks:2,loss:10,hp:100,camp_hp:40,raw:20,quant:20,range:1,
  cluster:0,members:2,nearby:0,enemies:0,status:0};
const camp=(id,health)=>({entity:{index:id},position:{x:1,y:id-1},health});
function frame(round,hp,h1,h2,actor={kind:1,index:0},kind=5,inputPosition=round) {
  return {round,phase:10,currentChampion:0,step:{round,kind,actor,inputPosition},
    champions:[{entity:{index:0},position:{x:0,y:0},health:hp,alive:hp>0,team:0}],camps:[camp(1,h1),camp(2,h2)]};
}
function begin(a,hp=100) { const s=frame(10,hp,20,20);s.phase=14;a.consume(s,()=>true); }

test('parser rejects missing or partial observations',()=>{
  assert.throws(()=>parseQuotes(''),/No model predictions/);
  assert.throws(()=>parseQuotes('DZ_MODEL round=10 body=0'),/Incomplete/);
  const line='DZ_MODEL '+Object.entries(quote).map(([k,v])=>`${k}=${v}`).join(' ');
  assert.equal(parseQuotes(line)[0].group,0);
  assert.throws(()=>parseQuotes(line+'\n'+line),/Duplicate/);
});
test('isolated clear tracks future camp HP loss and accepted basic actions',()=>{
  const a=new ModelAudit([quote],[[1,2]],20);begin(a);
  a.consume(frame(10,100,0,20));
  a.consume(frame(11,90,0,20,{kind:2,index:2}));
  a.consume(frame(11,90,0,0));
  const r=a.finish().records[0];
  assert.equal(r.outcome,'cleared');assert.equal(r.clear_round,11);
  assert.equal(r.own_basic_attacks,2);assert.equal(r.target_camp_hp_loss,10);
  assert.equal(r.other_hp_loss,0);assert.equal(r.memory_hp_difference,0);
});
test('animation substeps do not multiply a single basic attack',()=>{
  const a=new ModelAudit([quote],[[1,2]],20);begin(a);
  a.consume(frame(10,100,0,20));a.consume(frame(10,100,0,0));
  assert.equal(a.finish().records[0].own_basic_attacks,1);
});
test('allied help remains explicit instead of validating a solo prediction',()=>{
  const a=new ModelAudit([quote],[[1,2]],20);begin(a);
  a.consume(frame(10,100,0,0,{kind:1,index:7}));const r=a.finish().records[0];
  assert.deepEqual(r.helpers,[7]);assert.equal(r.other_damage_events,1);assert.equal(r.own_basic_attacks,0);
});
test('death, missing input alignment, and unfinished episodes are not successful clears',()=>{
  const a=new ModelAudit([quote],[[1,2]],20);begin(a);a.consume(frame(11,0,20,20));
  assert.equal(a.finish().records[0].outcome,'death');
  const b=new ModelAudit([quote],[[1,2]],20);begin(b,99);b.consume(frame(11,99,20,20));
  assert.equal(b.finish().records[0].outcome,'unmatched_quote');
  const c=new ModelAudit([quote],[[1,2]],20);begin(c);
  assert.equal(c.finish().records[0].outcome,'right_censored');
});
test('respawn/HP increase and goal changes censor the current generation',()=>{
  const a=new ModelAudit([quote],[[1,2]],20);begin(a);a.consume(frame(11,100,120,20));
  assert.equal(a.finish().records[0].outcome,'camp_hp_increased');
  const b=new ModelAudit([quote,{...quote,round:11,kind:1,group:-1}],[[1,2]],20);begin(b);
  const s=frame(11,100,20,20);s.phase=14;b.consume(s);
  assert.equal(b.finish().records[0].outcome,'goal_changed');
});
test('physical group membership mismatch is a hard failure',()=>{
  assert.throws(()=>new ModelAudit([quote],[[1]]),/membership mismatch/);
});
test('a successful post-move attack proves arrival in the quote turn',()=>{
  const a=new ModelAudit([{...quote,contact:0,dist:2}],[[1,2]],20);
  const s=frame(10,100,20,20);s.phase=14;a.consume(s,()=>false);
  a.consume(frame(10,100,0,20));
  assert.equal(a.finish().records[0].arrival_round,10);
});

test('a non-damaging tank is separated from a fully isolated clear',()=>{
  const a=new ModelAudit([quote],[[1,2]],20,new Map([[0,{range:3,strength:10}]]));
  const withTank=(s,hp,x=2)=>{
    s.camps.forEach(c=>c.type=0);
    s.champions.push({entity:{index:7},position:{x,y:0},health:hp,alive:true,team:1});return s;
  };
  const s=withTank(frame(10,100,20,20),100);s.phase=14;a.consume(s,()=>true);
  a.consume(withTank(frame(11,100,20,20,{kind:2,index:1}),90));
  a.consume(withTank(frame(11,100,0,0),90));
  const r=a.finish().records[0];
  assert.equal(r.other_damage_events,0);assert.equal(r.target_camp_other_hp_loss,10);
  assert.deepEqual(r.other_camp_targets,[7]);assert.deepEqual(r.potential_tank_bystanders,[7]);
  assert.equal(r.bystander_context_known,true);
});

test('spatial context excludes distant or harmless bystanders and rejects missing designs',()=>{
  const a=new ModelAudit([quote],[[1,2]],20,new Map([[0,{range:3,strength:0}],[1,{range:3,strength:10}]]));
  const s=frame(10,100,20,20);s.phase=14;s.camps[0].type=0;s.camps[1].type=1;
  s.champions.push({entity:{index:7},position:{x:4,y:-3},health:100,alive:true,team:0});
  a.consume(s,()=>true);assert.deepEqual(a.finish().records[0].potential_tank_bystanders,[]);
  const b=new ModelAudit([quote],[[1,2]],20,new Map());
  assert.throws(()=>b.consume(s,()=>true),/Missing camp design/);
});

test('shield casts deduplicate by input and single-live memory matches physical identity',()=>{
  const a=new ModelAudit([{...quote,shield_member:1}],[[1,2]],20);
  const s=frame(10,100,0,40);s.phase=14;a.consume(s,()=>true);
  const cast=frame(10,100,0,40,{kind:1,index:0},6,9);cast.step.abilityType=7;
  a.consume(cast);a.consume(cast);a.consume(frame(11,100,0,0));
  const r=a.finish().records[0];
  assert.equal(r.native_initial_live_members,1);assert.equal(r.shield_member_matches,true);
  assert.deepEqual(r.shield_actions,['10:9']);
  const b=new ModelAudit([{...quote,shield_member:0}],[[1,2]],20);b.consume(s,()=>true);
  assert.equal(b.finish().records[0].shield_member_matches,false);
});

test('compact atomic quotes preserve fields and reject unknown versions',()=>{
  const line='DZ_MODEL v=2 r=10 b=0 s=0 k=0 g=0 n=1 c=1 x=0 y=0 st=0 sn=10 d=1 f=1 a=2 l=10 h=100 ch=40 rw=20 q=20 rg=1 cl=0 m=2 na=0 ne=0 ok=0 ss=1 ps=0 pt=2 pl=10 pc=1 pn=1 pi=0 cd=0 cp=8 ca=250 ct=5 ex=0 ev=0 et=0 inc=20 cast=1 fuel=2000';
  const q=parseQuotes(line)[0];assert.equal(q.shield_loss,10);assert.equal(q.shield_sample,1);
  assert.equal(q.round,10);assert.equal(q.members,2);assert.equal(q.state,0);
  assert.throws(()=>parseQuotes(line.replace('v=2','v=3')),/Unsupported/);
  assert.throws(()=>parseQuotes(line+' zz=1'),/Unexpected compact/);
  assert.throws(()=>parseQuotes(line.replace('r=10 ','')),/Incomplete model/);
});
