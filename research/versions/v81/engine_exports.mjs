import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
console.log(Object.keys(E.X).filter(k=>/Champion.*(Ability|Attack|Move|Damage)|Ability_|Visualiser.*Design|CampGroup.*(State|Cooldown|Capture)/.test(k)).join('\n'));
E.destroy();
