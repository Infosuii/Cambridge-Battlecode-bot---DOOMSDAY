// Whole-opponent-held-out tactical policy, isolated from the proven action executor.
#include "bot.h"
#if V83_INTENT
#include "intent_model.h"
int Bot::learned_intent() {
    if(round>500 || w.enemies.empty() || bc::fuel_remaining()<35000) return -1;
    float f[33]={};
    float ah=0,as=0,eh=0,es=0,an=0,en=0,ranged=0,weak=1;int nd=99;
    for(const auto& a:w.allies) if(cheb(pos,a.pos)<=6) ++an,ah+=a.hp,as+=a.strength;
    for(const auto& e:w.enemies) {
        const int dist=cheb(pos,e.pos);nd=std::min(nd,dist);
        if(dist<=6){++en;eh+=e.hp;es+=e.strength;ranged+=e.range>1;weak=std::min(weak,e.hp/std::max(1.0f,e.max_hp));}
    }
    if(nd>6 || en<=0) return -1;
    f[0]=hp/std::max(1.0f,max_hp);f[1]=hp/1000;f[2]=max_hp/1000;f[3]=strength/100;f[4]=focus/100;f[5]=range/3.0f;
    f[6]=gems/50.0f;f[7]=round/1000.0f;f[8]=cooldown[0]==0;f[9]=cooldown[1]==0;f[10]=nd/8.0f;
    f[11]=an;f[12]=ah/1000;f[13]=as/100;f[14]=en;f[15]=eh/1000;f[16]=es/100;f[17]=ranged;f[18]=weak;
    f[19]=std::min(5.0f,(hp+ah)/std::max(1.0f,eh));
    const int typ=static_cast<int>(type);if(typ>=0 && typ<13)f[20+typ]=1;
    float confidence=0;const int action=intent83::predict(f,confidence);
    return confidence>=0.65f?action:-1;
}
#else
int Bot::learned_intent(){return -1;}
#endif
