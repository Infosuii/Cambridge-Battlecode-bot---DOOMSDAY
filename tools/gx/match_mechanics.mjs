// Offline replay measurements. No state from this decoder is read by any bot.
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from './replay_engine.mjs';
const dir = defaultAssets();
verifyAssets(dir);
const E = await engine(dir);
const newTeam = () => ({contact: 0, alone: 0, nearAllies: 0, nearEnemies: 0,
    first210Locks: 0, locks: 0, tributeStarts: 0, bankEvents: 0, tributeRestarts: 0,
    bankGems: 0, snapshots: 0, carriedGems: 0, equipment: 0});
const cheb = (a,b) => Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const paths = process.argv.slice(2);
for (const path of paths) {
    E.load(fs.readFileSync(path));
    const {X, check, dv, out, args, tsnap} = E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
    const main = dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));
    const size = dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const t = [newTeam(),newTeam()];
    const pending = new Set();
    let actors = null, last = -1, score = null, finalRound = null;
    for (;;) {
        check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
        const d = dv();
        const r = d.getUint32(tsnap+8,true), phase = d.getUint32(tsnap+24,true),
            input = d.getUint32(tsnap+56,true), outcome = d.getUint32(tsnap+28,true);
        const kind = d.getUint32(tsnap+68,true), actorKind = d.getUint32(tsnap+72,true),
            actor = d.getUint32(tsnap+76,true);
        if (phase === 10 && last !== r) {
            const s = E.PC.I(d,tsnap);
            last = r;
            if (!actors) actors = new Map(s.champions.map(c => [c.entity.index,c.team]));
            if (r <= 450) {
                const live = s.champions.filter(c => c.alive && c.position);
                for (const c of live) {
                    const own = t[c.team], enemies = live.filter(o => o.team !== c.team && cheb(o.position,c.position) <= 6).length;
                    if (r % 25 === 0) {
                        own.snapshots++;
                        own.carriedGems += c.gems;
                        // Index pairs are shard and emblem for a shared stat and item family.
                        own.equipment += c.items.reduce((sum,n,i) => sum + n * (i % 2 ? 5 : 1),0);
                    }
                    if (enemies === 0) continue;
                    const allies = live.filter(o => o.team === c.team && o.entity.index !== c.entity.index && cheb(o.position,c.position) <= 4).length;
                    own.contact++;
                    own.alone += allies === 0;
                    own.nearAllies += allies;
                    own.nearEnemies += enemies;
                }
            }
        }
        if (actorKind === 1 && actors?.has(actor)) {
            const own = t[actors.get(actor)];
            if (kind === 20) own.locks++, own.first210Locks += r <= 210;
            if (kind === 12) {
                own.tributeStarts++;
                if (pending.has(actor)) own.tributeRestarts++;
                pending.add(actor);
            }
            if (kind === 18) own.bankEvents++, pending.delete(actor);
        }
        if (outcome || (d.getUint32(tsnap+20,true) !== 0 && input >= size)) {
            const s = E.PC.I(d,tsnap);
            score = s.submittedGems.map(Number);
            finalRound = r;
            break;
        }
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    score.forEach((value,side) => { t[side].bankGems = value; });
    console.log(JSON.stringify({path,teams:t,round:finalRound}));
    E.destroy();
}
