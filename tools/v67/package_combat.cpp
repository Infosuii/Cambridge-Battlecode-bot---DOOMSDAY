// One contact controller: evaluate actual local HP and damage, regroup when
// outnumbered, and execute a burst together. Invisible allies guide the rally,
// never count as instant damage or invented health in the fight estimate.
#include "bot.h"
#include "fight.h"
#include "team_memory.h"

int Bot::v67_capture_owner(const GroupRec& g) const {
    if(g.state!=GroupState::reward) return -1;
    float invested=0,carry=0;
    int owner=-1;
    for(int s=0;s<std::min(team_size,6);++s) {
        const auto& a=team67_[s];
        if(!a.alive)continue;
        const float items=items_of(slot_type[s],a.max_hp,a.strength,a.focus);
        invested+=std::max(0.0f,items);
        if(slot_type[s]!=bc::champion_type::vesper_vale)continue;
        carry=items;
        if(!a.exact||a.hp<a.max_hp*0.5f)continue;
        int distance=99;for(int ci:g.camps)distance=std::min(distance,cheb(a.pos,w.camps[ci].pos));
        if(distance<=4&&(a.job==static_cast<int>(&g-w.groups.data())||bit(g.tiles,a.pos)))owner=s;
    }
    return owner>=0&&(invested<5||carry<invested*0.4f)?owner:-1;
}

int Bot::v67_buddy_job() const {
    if(battle_target67_<0 && round-contact67_>20) return -1;
    if(target_group>=0&&target_group<static_cast<int>(w.groups.size())) {
        const auto& g=w.groups[target_group];
        if(g.state==GroupState::reward&&v67_capture_owner(g)==slot) return -1;
        if(g.state==GroupState::alive&&g.hp_left(w.camps)<my_dps(&g)*3.0f) return -1;
    }
    const auto desired=(type==bc::champion_type::vesper_vale||type==bc::champion_type::vendetta)?
        bc::champion_type::heart_of_ruin:type==bc::champion_type::marcella?bc::champion_type::varg:type;
    if(desired==type)return -1;
    for(int s=0;s<std::min(team_size,6);++s) {
        const auto& a=team67_[s];const int g=a.job;
        if(!a.alive||slot_type[s]!=desired||round-a.job_seen>4||g<0||g>=static_cast<int>(w.groups.size()))continue;
        if(w.groups[g].state!=GroupState::alive)continue;
        const int distance=w.has_field(g)?w.group_distance(g,pos):cheb(pos,w.camps[w.groups[g].camps[0]].pos);
        if(distance<=16)return g;
    }
    return -1;
}

bool Bot::v67_team_combat() {
    const EnemyRec* target=nullptr;
    int distance=99;
    for(const auto& e:w.enemies) {
        const int d=cheb(pos,e.pos);
        if(e.hp<=0||(bit(w.enemy_spawn,e.pos)&&d>e.range))continue;
        if(d<distance||(d==distance&&target&&e.hp<target->hp))target=&e,distance=d;
    }
    if(!target||distance>8)return false;
    const bool continuing=round-contact67_<=3;
    if(distance<=5)contact67_=round;
    float our_hp=hp,our_dps=my_dps(nullptr),their_hp=0,their_dps=0,immediate=0;
    int friends=1,foes=0;
    for(const auto& a:w.allies) if(a.hp>0&&cheb(a.pos,target->pos)<=5) {
        const int eta=std::max(0,cheb(a.pos,target->pos)-a.range);
        if(eta>2)continue;
        const float weight=eta==0?1.0f:eta==1?0.75f:0.5f;
        our_hp+=a.hp*weight;our_dps+=(a.strength+a.focus*0.25f)*weight;
        friends+=eta<=1&&a.hp>=a.max_hp*0.4f;
    }
    for(const auto& e:w.enemies) if(e.hp>0&&cheb(e.pos,pos)<=6) {
        const int d=cheb(e.pos,pos);const auto kit=spell_kit(e.type,e.focus);
        their_hp+=e.hp;their_dps+=e.strength+kit.nuke*(kit.two_spells?0.25f:0.125f);++foes;
        if(d<=e.range+(e.range==1?1:0))immediate+=e.strength;
        bool ready=false;
        for(unsigned i=0;i<2;++i) {std::int32_t cd=99;if(!cambc::detail::sdk_champion_cooldown(e.id,i,&cd)&&cd==0)ready=true;}
        if(ready&&d<=4)immediate+=kit.nuke;
    }
    if(bit(w.hot_zone,pos))for(const auto& c:w.camps) if(!c.dead&&c.strength>0&&cheb(pos,c.pos)<=c.range)
        immediate+=c.strength*camp_taken_mult;
    const float hp_ratio=our_hp/std::max(1.0f,their_hp);
    const float power_ratio=our_hp*our_dps/std::max(1.0f,their_hp*their_dps);
    const float fraction=hp/std::max(1.0f,max_hp);
    bool linked_low=false;
    if(type==bc::champion_type::cassi||type==bc::champion_type::issac)
        for(const auto& a:w.allies) if((type==bc::champion_type::cassi&&a.type==bc::champion_type::issac)||
            (type==bc::champion_type::issac&&a.type==bc::champion_type::cassi))linked_low|=a.hp<a.max_hp*0.4f;
    const bool finish=distance<=range&&target->hp<=strength*0.95f;
    const bool urgent=!finish&&(hp<immediate*1.5f||linked_low||(friends==1&&foes>=2&&power_ratio<2.0f));
    const bool winning=hp_ratio>=0.95f&&power_ratio>=1.1f;
    const bool engage=finish||(!urgent&&winning&&fraction>=(continuing?0.35f:0.7f));
    struct Restore {bool& ref;bool old;~Restore(){ref=old;}} restore{combat_move,combat_move};
    combat_move=true;
    auto& me=bc::self();
    if(!engage) {
        if(distance>5&&immediate<=0&&!urgent)return false;
        mode="package-regroup";
        if(melee&&distance<=range)attack_unit(target->unit,target->pos);
        if(fraction<0.45f||linked_low)heading_home=true;
        if(urgent&&distance<=target->range+2&&dash_away())return true;
        vec2 rally{-1,-1};int best=99;
        for(int s=0;s<std::min(team_size,6);++s) {
            const auto& a=team67_[s];if(s==slot||!a.alive||a.pos.x<0)continue;
            if(a.exact&&a.hp<a.max_hp*0.5f)continue;
            const int d=cheb(a.pos,pos);
            if(d<3||d>14||d>=best)continue;
            if(cheb(a.pos,target->pos)<=distance-1)continue;
            best=d;rally=a.pos;
        }
        if(rally.x>=0) {
            bc::bitboard goal,reach;goal.clear();reach.clear();goal.draw_chebyshev(rally,2.0f);
            for(const auto& e:w.enemies)reach.draw_chebyshev(e.pos,float(e.range+1));
            if(walk_toward(goal&~reach))return true;
        }
        if(urgent||distance<=target->range+2)return retreat_from(target->pos);
        return false;
    }
    if(distance>5)return false; // short chases preserve the economy
    contact67_=round;
    if(battle_target67_>=0&&battle_target67_<static_cast<int>(enemy_handles.size()))
        for(const auto& e:w.enemies) if(e.id==enemy_handles[battle_target67_]&&cheb(pos,e.pos)<=distance+1)target=&e;
    const auto it=std::find(enemy_handles.begin(),enemy_handles.end(),target->id);
    if(it!=enemy_handles.end()&&it-enemy_handles.begin()<6) {
        auto memory=team67::put_battle(read_shared(),int(it-enemy_handles.begin()),target->pos.x,target->pos.y,round);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});
    }
    mode="package-burst";
    // The bounded action search already models cooldowns, shields, stuns,
    // attack resets and the ranged move/attack allowance. It is an executor here.
    if(tune::kTSearch&&bc::fuel_remaining()>60000&&friends+foes<=8&&tactical_search())return true;
    cast_on_enemy(*target);
    if(!cast_done&&cheb(pos,target->pos)>range) {
        for(int i=0;i<2;++i) if(spell_ready(i)&&spells[i].kind==bc::ability_kind::dash&&type!=bc::champion_type::heart_of_ruin) {
            vec2 best=pos;int score=-1000000;
            const int reach=std::min(3,int(spells[i].range));
            for(int dx=-reach;dx<=reach;++dx)for(int dy=-reach;dy<=reach;++dy) {
                vec2 q{pos.x+dx,pos.y+dy};
                if(q.x<0||q.y<0||q.x>=w.width||q.y>=w.height||bit(w.static_blocked,q)||bit(w.unit_tiles,q)||bit(w.enemy_spawn,q))continue;
                const int d=cheb(q,target->pos);int value=-d*20;
                if(d<=range)value+=100;
                for(const auto& e:w.enemies)if(cheb(q,e.pos)<=e.range)value-=10;
                if(value>score)score=value,best=q;
            }
            if(best!=pos&&cheb(best,target->pos)<=range)try {
                if(me.abilities()[i].use(best)){pos=me.position();walked=cast_done=true;break;}
            }catch(...){}
        }
    }
    if(cheb(pos,target->pos)>range&&me.can_move()) {
        bc::bitboard goal;goal.clear();goal.draw_chebyshev(target->pos,float(range));walk_toward(goal);
    }
    if(cheb(pos,target->pos)<=range) {
        cast_on_enemy(*target);
        if(attack_unit(target->unit,target->pos))use_reset_and_attack(target->unit,target->pos);
    }
    return true;
}
