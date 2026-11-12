// Record the champion's view before its side's first actions, then label later events.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay_engine.mjs';
const dir=defaultAssets();
verifyAssets(dir);
const E=await engine(dir);
const jobs=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const horizon=8, interval=10;
const weights=[0.5910,0.6160,0.3645,0.3898,-0.2671,0.2456,0.2456,0.9425,0.2456,0.0850,0.5014,0.1200,0.3822];
const fields=['round','hp','hp_fraction','bag','nearest','allies','enemies','lanch_z','lanch_power_us',
    'lanch_power_enemy','basic_in','burst_in','ready_out','active_camp_dps','links_low_hp',
    'enemy_idle','enemy_area_pairs','shield','our_reach','enemy_bag','lane'];
const cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const strength=c=>c.strength?.effective??0;
const focus=c=>c.focus?.effective??0;
const power=c=>c.health/1000*((weights[c.type]??0)*strength(c)/70+0.7256*focus(c)/100);
const idle=c=>((c.roundFlags??0)&0x1006)!==0;
const atk=c=>c.attackRange??1;

function burstAt(c,target) {
    if (idle(c)) return 0;
    const d=cheb(c.position,target);
    let highest=0;
    for (let k=0;k<2;k++) {
        const a=c.abilityProps?.[k];
        if (!a || (c.cooldowns[k]??99)>1) continue;
        let n=0;
        if (a.type===1 && d<=atk(c)+1) n=strength(c);
        else if ([2,3,4,6].includes(a.type) && d<=(a.range??0)+(a.radius??0)+1)
            n=focus(c)*(a.modifier??0);
        highest=Math.max(highest,n);
    }
    return highest;
}

for (const {id,map,opponent,side,last,path,deaths} of jobs) {
    E.load(fs.readFileSync(path));
    const {X,check,dv,out,args,tsnap,snap}=E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
    const main=dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));
    const size=dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const lastSample=new Map(), rows=[];
    let lastRound=-1;
    for (;;) {
        check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
        const d=dv();
        const r=d.getUint32(tsnap+8,true), phase=d.getUint32(tsnap+24,true),
            done=d.getUint32(tsnap+28,true) || (d.getUint32(tsnap+20,true)!==0 && d.getUint32(tsnap+56,true)>=size);
        if (done || r>Math.min(last-horizon,900)) break;
        if (phase===10 && r!==lastRound) {
            lastRound=r;
            const full=E.PC.I(d,tsnap);
            const live=full.champions.filter(c=>c.alive && c.position);
            for (const visible of live) {
                const index=visible.entity.index;
                if (r-(lastSample.get(index)??-interval)<interval ||
                    !live.some(e=>e.team!==visible.team && cheb(e.position,visible.position)<=8)) continue;
                check(X.Game_Visualiser_ReadState(E.h,E.perspective(visible.team,index),snap));
                const view=E.PC.F(dv(),snap);
                const me=view.champions.find(c=>c.entity.index===index);
                if (!me?.position || me.position.x!==visible.position.x || me.position.y!==visible.position.y ||
                    Math.abs(me.health-visible.health)>0.05 || !Number.isFinite(strength(me))) throw Error('Perspective changed source');
                const nearby=view.champions.filter(c=>c.entity.index!==index && c.alive && c.position && c.health>0);
                const allies=nearby.filter(c=>c.team===me.team && cheb(c.position,me.position)<=7);
                const foes=nearby.filter(c=>c.team!==me.team && cheb(c.position,me.position)<=8);
                if (!foes.length) continue;
                lastSample.set(index,r);
                const near=foes.reduce((a,b)=>cheb(a.position,me.position)<=cheb(b.position,me.position)?a:b);
                const ours=power(me)+allies.reduce((s,c)=>s+power(c),0);
                const theirs=foes.reduce((s,c)=>s+power(c),0);
                const basic=foes.reduce((s,c)=>s+(!idle(c)&&cheb(c.position,me.position)<=atk(c)+1?strength(c):0),0);
                const burst=foes.reduce((s,c)=>s+burstAt(c,me.position),0);
                const camp=view.camps.reduce((s,c)=>s+(c.position&&c.health>0&&c.awake&&
                    cheb(c.position,me.position)<=atk(c)?strength(c):0),0);
                const partner=[3,4].includes(me.type)?allies.find(c=>c.type===(me.type===3?4:3)):null;
                let area=0;
                for (const e of foes) for (let k=0;k<2;k++) {
                    const a=e.abilityProps?.[k];
                    if (!a || ![3,6].includes(a.type) || !(a.radius>0) || idle(e) || (e.cooldowns[k]??99)>1) continue;
                    if (cheb(e.position,me.position)<=a.range+a.radius+1 &&
                        allies.some(c=>cheb(c.position,me.position)<=2*a.radius&&cheb(c.position,e.position)<=a.range+a.radius+1)) area++;
                }
                const shield=(me.buffs??[]).filter(b=>b.type===0).reduce((s,b)=>s+b.magnitude,0);
                const f=[r,me.health,me.health/me.maxHealth,me.gems??0,cheb(me.position,near.position),
                    allies.filter(c=>cheb(c.position,me.position)<=6&&c.health>=0.25*c.maxHealth).length,foes.length,
                    ours-theirs,ours,theirs,basic,burst,burstAt(me,near.position),camp,
                    partner?Math.min(me.health/me.maxHealth,partner.health/partner.maxHealth):me.health/me.maxHealth,
                    foes.filter(idle).length,area,shield,atk(me),Math.max(0,...foes.map(c=>c.gems??0)),
                    allies.filter(c=>cheb(c.position,near.position)<=atk(c)+1).length];
                if (f.length!==fields.length || f.some(x=>!Number.isFinite(x))) throw Error('Invalid feature');
                const ids=new Set(foes.map(c=>c.entity.index));
                const ownLoss=deaths.some(x=>r<=x[0]&&x[0]<r+horizon&&x[1]===index&&x[2]===1);
                const foeLoss=deaths.some(x=>r<=x[0]&&x[0]<r+horizon&&ids.has(x[1])&&x[2]===1);
                rows.push([me.team===side?0:1,index,me.type,ownLoss?1:0,foeLoss?1:0,
                    ...f.map(x=>Math.round(x*1000)/1000)]);
            }
        }
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    console.log(JSON.stringify({id,map,opponent,side,horizon,interval,fields,rows}));
    E.destroy();
}
