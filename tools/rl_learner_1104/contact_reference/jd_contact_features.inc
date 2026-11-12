// Shadow only. Final verdict after existing contact heuristics, before its
// downstream executor. Earlier burst/ambush/capture returns are outside scope.
{
    ++jd_contact::hooks;
    if(nearest && nearest_d<=6){
        ++jd_contact::opportunities;
        if(bc::fuel_remaining()<25000)++jd_contact::low_fuel;
        else if(jd_contact::records<8 && bc::round_number()==static_cast<unsigned>(round)){
            const auto f0=bc::fuel_remaining();
            float f[48]={};int na=0,ne=0;float ah=hp,eh=0;
            for(const auto& a:w.allies)if(a.id!=my_id && a.hp>0 && cheb(a.pos,pos)<=6){++na;ah+=a.hp;}
            for(const auto& e:w.enemies)if(e.hp>0 && cheb(e.pos,pos)<=6){++ne;eh+=e.hp;}
            f[0]=hp/std::max(1.0f,max_hp);f[1]=gems/100.0f;f[2]=gold/1000.0f;f[3]=strength/100.0f;f[4]=focus/100.0f;
            f[5]=range/8.0f;f[6]=nearest_d/8.0f;f[7]=target?target->hp/std::max(1.0f,target->max_hp):0;
            f[8]=std::min(target_ttk,20.0f)/20.0f;f[9]=std::min(ttd,20.0f)/20.0f;f[10]=std::min(threat_on_me/std::max(1.0f,hp),4.0f)/4.0f;f[11]=mine/100.0f;
            f[12]=na/5.0f;f[13]=ne/8.0f;f[14]=ah/4000.0f;f[15]=eh/4000.0f;f[16]=ally_score/1000.0f;f[17]=enemy_score/1000.0f;
            f[18]=(ally_score-enemy_score)/1000.0f;f[19]=round/2000.0f;f[20]=risk/2.0f;f[21]=nearest->hp/std::max(1.0f,nearest->max_hp);
            f[22]=target?cheb(target->pos,pos)/8.0f:1.0f;f[23]=target?target->gems/100.0f:0;f[24]=nearest->gems/100.0f;
            f[25]=winning;f[26]=in_danger;f[27]=target!=nullptr;f[28]=std::min(threat_on_me,2000.0f)/2000.0f;
            f[29]=std::min(ttd/std::max(target_ttk,.1f),8.0f)/8.0f;f[30]=gems/std::max(1.0f,static_cast<float>(bc::constants::winning_gems-ally_score));f[31]=1;
            const int ti=static_cast<int>(type);if(ti>=0 && ti<16)f[32+ti]=1;
            std::int16_t q[48],z[8];bool finite=true;
            for(int i=0;i<48;++i){if(!std::isfinite(f[i])){finite=false;q[i]=0;}else q[i]=static_cast<std::int16_t>(std::clamp(f[i]*2048.0f,-16000.0f,16000.0f));}
            if(finite){
                const auto f1=bc::fuel_remaining();jd_contact::score(q,z);const auto f2=bc::fuel_remaining();
                const bool valid[3]={true,target && !(winning && !in_danger),!(!winning && in_danger && threat_on_me>0)};
                ++jd_contact::records;jd_contact::record(round,static_cast<int>(my_id),jd_contact::records,winning,in_danger,valid,q,z,f0,f1,f2);
            }
        }
    }
}
