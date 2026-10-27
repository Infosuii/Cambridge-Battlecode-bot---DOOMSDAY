// One team controller. Legacy fight/farm policy chains do not run in this mode.
// Only the existing observation, pathfinding, shop and legal-action primitives are reused.
#include "bot.h"
#include "team_memory.h"
#include "strategy.h"
#include <cmath>

namespace {
float power67(float hp, float strength, float focus) {
    return std::max(0.0f, hp) * std::max(1.0f, strength + focus * 0.18f);
}
}

void Bot::v67_team_publish(bool alive) {
    namespace api = cambc::detail;
    api::champion_info self{};
    if (alive && api::sdk_champion(my_id, &self) == 0) {
        pos = {self.x, self.y};
        alive = (self.state & 1) && self.x >= 0;
    }
    auto memory = read_shared();
    if (!alive || (round & 1)) memory = team67::put_position(memory, slot, pos.x, pos.y, alive);
    else {
        const int job = !heading_home && !home67_ && !bank67_ && target_group >= 0 &&
            target_group < static_cast<int>(w.groups.size()) ? target_group : -1;
        memory = team67::put_job(memory, slot, job);
    }
    bc::shared_memory.write(0, std::span<std::uint64_t, 1>{&memory, 1});
    memory67_ = memory;
}

void Bot::v67_team_decode(std::uint64_t memory) {
    claim_cache.fill(static_cast<std::int16_t>(kClaimCodeIdle));
    onsite_bits = 0;
    for (int s = 0; s < std::min(team_size,6); ++s) {
        auto& a = team67_[s];
        const int message = static_cast<int>(team67::byte(memory,s));
        if (message != a.message) {
            a.message = message;
            if (team67::job_message(memory,s)) {
                a.job = team67::job(memory,s); a.job_seen = round;
            } else {
                int x,y;
                if (team67::position(memory,s,x,y)) {
                    a.pos = {std::min(x,w.width-1),std::min(y,w.height-1)};
                    a.position_seen = round;
                }
            }
        }
        if (s == slot && target_group >= 0 && target_group < static_cast<int>(w.groups.size()))
            a.job = target_group, a.job_seen = round;
        if (!a.alive && inited) { claim_cache[s] = kClaimCodeDead; continue; }
        if (a.job >= 0 && a.job < static_cast<int>(w.groups.size()) && round-a.job_seen <= 4) {
            claim_cache[s] = static_cast<std::int16_t>(a.job);
            if (a.exact) for (int ci : w.groups[a.job].camps)
                if (cheb(a.pos,w.camps[ci].pos) <= 5) onsite_bits |= 1u<<s;
        }
    }
}

void Bot::v67_team_sync() {
    memory67_ = read_shared();
    leader67_ = slot;
    for (int s = 0; s < std::min(team_size,6); ++s) {
        auto& a = team67_[s];
        std::int32_t live=0;
        cambc::detail::sdk_champion_is_alive(ally_handle[s], &live);
        a.alive = live != 0; a.exact = false;
        if (!a.alive) { a.pos={-1,-1}; a.job=-1; continue; }
        leader67_ = std::min(leader67_,s);
    }
    v67_team_decode(memory67_);
    // Exact visible states supersede the coarse mailbox location.
    for (int s = 0; s < std::min(team_size,6); ++s) {
        auto& a=team67_[s]; if(!a.alive) continue;
        if (s == slot) {
            a.pos=pos; a.hp=hp; a.max_hp=max_hp; a.strength=strength; a.focus=focus; a.exact=true;
        } else for (const auto& visible : w.allies) if(visible.id==ally_handle[s]) {
            a.pos=visible.pos; a.hp=visible.hp; a.max_hp=visible.max_hp;
            a.strength=visible.strength; a.focus=visible.focus; a.exact=true;
        }
        if(a.exact) a.seen=round, a.position_seen=round;
        else if(round-a.position_seen>4) a.pos={-1,-1};
        if (a.max_hp <= 1) {
            cambc::detail::champion_design design{};
            if (cambc::detail::sdk_champion_design(static_cast<int>(slot_type[s]), &design)==0) {
                a.max_hp=design.base_stats.base_health; a.hp=a.max_hp*0.75f;
                a.strength=design.base_stats.base_strength; a.focus=design.base_stats.base_focus;
            }
        }
        if (a.job >= 0 && a.job < static_cast<int>(w.groups.size()) && a.exact)
            for(int ci:w.groups[a.job].camps) if(cheb(a.pos,w.camps[ci].pos)<=5) onsite_bits|=1u<<s;
    }
    const int next=team67::rally(memory67_);
    if(next>=0 && next!=rally67_) { rally67_=next; rally_since67_=round; }
    int x,y;
    if(team67::battle(memory67_,round,battle_target67_,x,y)) {
        battle67_={std::min(x,w.width-1),std::min(y,w.height-1)};
        focus67_=battle_target67_; focus_seen67_=round-team67::age(memory67_,round);
    } else battle_target67_=-1, focus67_=-1;
    if(enemy_handles.empty()) for(const auto& e:bc::champions(team::enemy))
        enemy_handles.push_back(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(e)));
}

void Bot::v67_team_after_turn() {
    if(!inited) return;
    const bool alive=bc::self().is_alive();
    v67_team_publish(alive);
    if(!alive) return;
    const EnemyRec* target=nullptr; int distance=99,foes=0,friends=1;
    for(const auto& e:w.enemies) if(e.hp>0 && !bit(w.enemy_spawn,e.pos)) {
        const int d=cheb(pos,e.pos); foes+=d<=6;
        if(d<distance) distance=d,target=&e;
    }
    for(const auto& a:w.allies) friends+=a.hp>=a.max_hp*0.5f&&cheb(a.pos,pos)<=5;
    auto memory=read_shared();
    if(target&&distance<=5&&hp>=max_hp*0.65f&&!heading_home&&friends>=foes) {
        const auto it=std::find(enemy_handles.begin(),enemy_handles.end(),target->id);
        if(it!=enemy_handles.end() && it-enemy_handles.begin()<6) {
            memory=team67::put_battle(memory,static_cast<int>(it-enemy_handles.begin()),target->pos.x,target->pos.y,round);
            bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});
        }
    } else if(slot==leader67_ && team67::focus(memory)>=0 && team67::age(memory,round)>3) {
        memory=team67::put_plan(memory,-1,rally67_,round);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});
    }
}

bool Bot::v67_team_join() {
    if (battle_target67_<0 || hp<max_hp*0.75f || gems>=30 || heading_home) return false;
    const int distance=cheb(pos,battle67_);
    if(distance<=4 || distance>11 || bit(w.enemy_spawn,battle67_)) return false;
    if(target_group>=0 && target_group<static_cast<int>(w.groups.size()) &&
       w.groups[target_group].state==GroupState::reward && bit(w.groups[target_group].tiles,pos)) return false;
    // Only a fresh, short reinforcement trip can interrupt the economy.
    mode="team-join";
    bc::bitboard goal; goal.clear(); goal.draw_chebyshev(battle67_,3.0f);
    return walk_toward(goal);
}

int Bot::v67_team_local_job(vec2 origin, int exclude) {
    float ex = 0, ey = 0, count = 0;
    for (const auto p : w.enemy_spawn.positions()) { ex += p.x; ey += p.y; count += 1; }
    if (count) { ex /= count; ey /= count; }
    float dps = 0, healthy = 0;
    int bodies = 0;
    for (int s = 0; s < std::min(team_size, 6); ++s) {
        const auto& a = team67_[s];
        if (!a.alive || a.pos.x < 0 || cheb(a.pos, origin) > 14) continue;
        dps += a.strength * (slot_type[s] == bc::champion_type::varg ? 1.5f : 1.1f) + a.focus * 0.12f;
        healthy += a.exact ? a.hp : a.max_hp * 0.65f;
        ++bodies;
    }
    dps = std::max(dps, strength + focus * 0.15f);
    healthy = std::max(healthy, hp);
    bodies = std::max(1, bodies);
    int best = -1;
    float score = 0;
    for (int gi = 0; gi < static_cast<int>(w.groups.size()); ++gi) {
        const auto& g = w.groups[gi];
        if (gi == exclude || g.camps.empty() || (!g.gold && !g.gems)) continue;
        const vec2 at = w.camps[g.camps[0]].pos;
        int distance = w.has_field(gi) ? w.group_distance(gi, origin) : cheb(origin, at);
        if (distance == kUnreach) continue;
        int wait = g.state == GroupState::respawning ? std::max(0, g.respawn_round - round - distance) : 0;
        if (wait > 8) continue;
        const float hp_left = g.state == GroupState::reward ? 0 : g.hp_left(w.camps);
        const float clear = hp_left / dps;
        const float loss = g.strength * clear;
        if (loss > healthy * 1.2f && !g.harmless) continue;
        const int home = fdist(w.spawn_field, at);
        const float enemy = std::max(std::fabs(at.x - ex), std::fabs(at.y - ey));
        float value = (g.gems + g.gold * (round < 400 ? 0.6f : 0.25f)) /
                      (distance + clear + wait + 7);
        if (home != kUnreach && home > enemy * 1.1f) value *= 0.65f;
        value /= 1 + loss / std::max(1.0f, healthy) * 0.35f;
        if (g.state == GroupState::reward) value *= 1.5f;
        if (gi == rally67_) value *= 1.18f;
        if (value > score) { score = value; best = gi; }
    }
    return best;
}

void Bot::v67_team_plan() {
    if (slot != leader67_) return;
    if (focus67_ >= 0 && round - focus_seen67_ <= 5) return;
    bool replan = rally67_ < 0 || rally67_ >= static_cast<int>(w.groups.size());
    if (!replan) {
        const auto& g = w.groups[rally67_];
        replan = (g.state == GroupState::respawning && g.respawn_round - round > 3) ||
                 round - rally_since67_ > 80;
    }
    if (!replan && round - last_plan67_ < 10) return;
    vec2 origin = pos;
    int x = 0, y = 0, n = 0;
    for (const auto& a : team67_) if (a.alive && a.pos.x >= 0) { x += a.pos.x; y += a.pos.y; ++n; }
    if (n) origin = {x / n, y / n};
    const int next = v67_team_local_job(origin);
    if (next >= 0 && (replan || next == rally67_)) {
        if (next != rally67_) rally_since67_ = round;
        rally67_ = next;
    }
    // Bank gates are real economic objectives: open them after the crew has gear and a valuable bag.
    if (w.altar_gated && !w.gate_camps.empty() && (gems >= 60 || round > 500)) {
        const int camp = w.gate_camps[0];
        if (camp >= 0 && camp < static_cast<int>(w.camp_group.size())) rally67_ = w.camp_group[camp];
    }
    auto memory = team67::put_plan(read_shared(), -1, rally67_);
    bc::shared_memory.write(0, std::span<std::uint64_t, 1>{&memory, 1});
    memory67_ = memory;
    last_plan67_ = round;
}

bool Bot::v67_team_combat() {
    const EnemyRec* target = nullptr;
    int distance = 99;
    for (const auto& e : w.enemies) {
        const int d = cheb(pos, e.pos);
        if (e.hp <= 0 || (bit(w.enemy_spawn, e.pos) && d > range)) continue;
        if (d < distance || (d == distance && target && e.hp < target->hp)) distance = d, target = &e;
    }
    if (!target || distance > 7) return false;
    float friendly = power67(hp, strength, focus), hostile = 0;
    int friends = 1, foes = 0;
    for (int s = 0; s < std::min(team_size, 6); ++s) {
        if (s == slot) continue;
        const auto& a = team67_[s];
        if (!a.alive || a.pos.x < 0) continue;
        const int d = cheb(a.pos, target->pos);
        if (d > 7) continue;
        // Coarse positions guide arrival; they are not exact health or instant attack coverage.
        const float arrival = a.exact ? std::max(0.25f, 1 - std::max(0, d - 2) * 0.15f) : 0.25f;
        friendly += arrival * power67(a.exact ? a.hp : a.max_hp * 0.6f, a.strength, a.focus);
        friends += a.exact && d <= 5;
    }
    float incoming = 0;
    for (const auto& e : w.enemies) if (cheb(e.pos, pos) <= 6 && e.hp > 0) {
        hostile += power67(e.hp, e.strength, e.focus);
        ++foes;
        if (cheb(e.pos, pos) <= e.range + 2) incoming += e.strength + e.focus * 0.20f;
    }
    const float ratio = friendly / std::max(1.0f, hostile), frac = hp / std::max(1.0f, max_hp);
    const bool finish = distance <= range && target->hp <= strength * 0.9f;
    const bool retreat = !finish && !bit(w.ally_spawn, pos) &&
        (hp < incoming * 3 || (frac < 0.55f && ratio < 1.5f) || (friends == 1 && foes >= 2 && ratio < 1.1f));
    const bool engage = finish || (frac >= 0.68f && ratio >= 0.9f) || bit(w.ally_spawn, pos);
    if (retreat && distance > target->range + 2) return false; // keep doing useful work outside immediate contact
    if (!retreat && !engage && distance > 3) return false;
    struct Restore { bool& ref; bool old; ~Restore() { ref = old; } } restore{combat_move, combat_move};
    combat_move = true;
    auto& me = bc::self();
    if (retreat || !engage) {
        mode = "team-retreat";
        if (melee)
            for (const auto& e : w.enemies) if (cheb(pos, e.pos) <= range && attack_unit(e.unit, e.pos)) break;
        const bool dash = dash_away();
        const bool step = me.can_move() && retreat_from(target->pos);
        if (!dash && !step && distance <= range) {
            cast_on_enemy(*target);
            if (attack_unit(target->unit, target->pos)) use_reset_and_attack(target->unit, target->pos);
        }
        if (frac < 0.5f) home67_ = true;
        return true;
    }
    const int encoded = team67::focus(read_shared());
    if (encoded >= 0 && encoded < static_cast<int>(enemy_handles.size()))
        for (const auto& e : w.enemies)
            if (e.id == enemy_handles[encoded] && cheb(pos, e.pos) <= distance + 2) target = &e;
    const auto found = std::find(enemy_handles.begin(), enemy_handles.end(), target->id);
    if (found != enemy_handles.end() && found - enemy_handles.begin() < 6) {
        focus67_ = static_cast<int>(found - enemy_handles.begin());
        focus_seen67_ = round;
        auto memory = team67::put_battle(read_shared(), focus67_, target->pos.x, target->pos.y, round);
        bc::shared_memory.write(0, std::span<std::uint64_t, 1>{&memory, 1});
    }
    mode = "team-focus";
    cast_on_enemy(*target);
    if (cheb(pos, target->pos) > range && me.can_move()) {
        bc::bitboard goals;
        goals.clear();
        goals.draw_chebyshev(target->pos, static_cast<float>(range));
        walk_toward(goals);
    }
    if (cheb(pos, target->pos) <= range) {
        cast_on_enemy(*target);
        if (attack_unit(target->unit, target->pos)) use_reset_and_attack(target->unit, target->pos);
    }
    return true;
}

bool Bot::v67_team_home() {
    const bool on_spawn = bit(w.ally_spawn, pos);
    if (on_spawn) {
        home67_ = false;
        heading_home = false;
        return hp < max_hp * 0.98f;
    }
    const int distance = fdist(w.spawn_field, pos);
    home67_ |= hp < max_hp * 0.38f || gold >= (distance <= 10 ? 150 : 300);
    if (!home67_) return false;
    heading_home = true;
    mode = "team-reset";
    if (distance > 6 && w.enemies.empty() && !bit(w.hot_zone, pos)) {
        try { bc::self().recall(); return true; } catch (...) {}
    }
    return walk_toward(w.ally_spawn);
}

bool Bot::v67_team_bank() {
    if (!gems || w.no_bank) { bank67_ = false; return false; }
    if (!w.altar_ready && bc::fuel_remaining() > 40000) w.ensure_altar_field();
    const int distance = w.altar_ready ? fdist(w.altar_field, pos) : kUnreach;
    const bool finishes = ally_score + gems >= static_cast<int>(bc::constants::winning_gems);
    bank67_ |= finishes || gems >= 65 || (gems >= 30 && distance <= 24) ||
               (gems >= 8 && distance <= 4) || (type == bc::champion_type::marcella && gems >= 20);
    if (!bank67_ || distance == kUnreach) return false;
    mode = "team-bank";
    for (const auto altar : w.altars) if (cheb(pos, altar) <= 1) {
        try { bc::self().submit_gems(altar); return true; } catch (...) {}
    }
    return walk_toward(w.altar_ring);
}

bool Bot::v67_team_farm() {
    int job = rally67_;
    if (job < 0 || job >= static_cast<int>(w.groups.size())) job = v67_team_local_job(pos);
    if (job < 0) return false;
    int spare = 0;
    for (int s = 0; s < std::min(team_size, 6); ++s)
        spare += team67_[s].alive && s < slot;
    if (spare >= 3 && w.groups[job].max_hp < 7000) {
        const int local = v67_team_local_job(pos, job);
        if (local >= 0 && cheb(pos, w.camps[w.groups[local].camps[0]].pos) <= 8) job = local;
    }
    auto& g = w.groups[job];
    target_group = job;
    const vec2 anchor = w.camps[g.camps[0]].pos;
    if (g.state == GroupState::respawning) {
        if (bit(g.tiles, pos) || g.respawn_round - round > 3) {
            const int other = v67_team_local_job(pos, job);
            if (other >= 0) {
                target_group = other;
                bc::bitboard goals;
                goals.clear();
                for (int ci : w.groups[other].camps) goals.draw_chebyshev(w.camps[ci].pos, static_cast<float>(range));
                return walk_toward(goals);
            }
        }
        return false;
    }
    if (g.state == GroupState::reward) {
        int owner = slot;
        int mine = w.has_field(job) ? w.group_distance(job, pos) : cheb(pos, anchor);
        float best = static_cast<float>(mine) - (type == bc::champion_type::vesper_vale ? 2 : 0);
        for (int s = 0; s < std::min(team_size, 6); ++s) {
            const auto& a = team67_[s];
            if (s == slot || !a.alive || a.pos.x < 0) continue;
            int distance = w.has_field(job) ? w.group_distance(job, a.pos) : cheb(a.pos, anchor);
            if (a.exact && bit(g.tiles, a.pos)) distance = -5;
            const float key = static_cast<float>(distance) - (slot_type[s] == bc::champion_type::vesper_vale ? 2 : 0);
            if (key < best || (key == best && s < owner)) { best = key; owner = s; }
        }
        if (owner == slot) {
            mode = "team-capture";
            if (bit(g.tiles, pos)) return true;
            return walk_toward(g.tiles);
        }
        const int next = v67_team_local_job(pos, job);
        if (next >= 0) {
            mode = "team-next-clear";
            bc::bitboard goals;
            goals.clear();
            for (int ci : w.groups[next].camps) goals.draw_chebyshev(w.camps[ci].pos, static_cast<float>(range));
            return walk_toward(goals);
        }
        return false;
    }
    // The team policy chooses the job. The proven camp execution handles bush
    // reveal, splash targeting, tank rotation and range-aware approach.
    return fight_camps(g, 1);
#if 0
    int present = 0;
    float crew_dps = 0, crew_hp = 0;
    for (const auto& a : team67_) if (a.alive && a.pos.x >= 0 && cheb(a.pos, anchor) <= 9) {
        ++present;
        crew_dps += a.strength * 1.1f + a.focus * 0.15f;
        crew_hp += a.exact ? a.hp : a.max_hp * 0.6f;
    }
    const float clear = g.hp_left(w.camps) / std::max(1.0f, crew_dps);
    const bool unsafe = !g.harmless && g.strength * clear > std::max(1.0f, crew_hp) * 1.1f;
    if (unsafe && cheb(pos, anchor) <= 6) {
        mode = "team-stage";
        bc::bitboard outer, inner;
        outer.clear(); inner.clear();
        outer.draw_chebyshev(anchor, 5);
        inner.draw_chebyshev(anchor, 3);
        if (cheb(pos, anchor) <= 3) return retreat_from(anchor);
        if (present < 3) return walk_toward(outer & ~inner);
        return false;
    }
    int pick = -1;
    float key = 1e30f;
    for (int ci : g.camps) {
        const auto& c = w.camps[ci];
        if (c.dead || !bit(w.visible, c.pos)) continue;
        const int d = cheb(pos, c.pos);
        const float score = c.hp / std::max(1.0f, strength) + std::max(0, d - range) * 12 - c.strength * 0.1f;
        if (score < key) { key = score; pick = ci; }
    }
    mode = "team-clear";
    if (pick >= 0) {
        auto& c = w.camps[pick];
        if (cheb(pos, c.pos) <= range) {
            cast_on_camp(pick);
            if (attack_unit(c.camp, c.pos)) use_reset_and_attack(c.camp, c.pos);
            return true;
        }
        if (!unsafe && cheb(pos, c.pos) <= 4) {
#if V55_HEART_CAMP
            if (cast_camp_strike(pick) && cheb(pos, c.pos) <= range) {
                attack_unit(c.camp, c.pos);
                return true;
            }
#endif
            bool reach = false;
            for (int s = 0; s < 2; ++s)
                reach |= spell_ready(s) && spells[s].camps && spells[s].excludes_walk && cheb(pos, c.pos) <= spells[s].range;
            if (reach && cast_on_camp(pick)) return true;
        }
    }
    bc::bitboard goals;
    goals.clear();
    for (int ci : g.camps) if (!w.camps[ci].dead)
        goals.draw_chebyshev(w.camps[ci].pos, static_cast<float>(range));
    const bool moved = walk_toward(goals);
    if (moved && melee)
        for (int ci : g.camps) {
            const auto& c = w.camps[ci];
            if (!c.dead && bit(w.visible, c.pos) && cheb(pos, c.pos) <= range) {
                cast_on_camp(ci);
                if (attack_unit(c.camp, c.pos)) use_reset_and_attack(c.camp, c.pos);
                break;
            }
        }
    return moved;
#endif
}

void Bot::v67_team_turn() {
    auto& me = bc::self();
    round = static_cast<int>(bc::round_number());
    if (!inited) init();
    if (APEX_BRAIN) {
        brain::load(team_size);
        brain::adapt(static_cast<int>(bc::global_submitted_gems(team::ally)),
                     static_cast<int>(bc::global_submitted_gems(team::enemy)));
    }
    if (!me.is_alive()) {
        gold = static_cast<int>(me.gold_count());
        shop();
        home67_ = bank67_ = heading_home = false;
        v67_team_publish(false);
        build_fields();
        return;
    }
    refresh_self();
    cast_done = walked = keep_channel = false;
    if (bit(w.ally_spawn, pos) || type == bc::champion_type::tavi) {
        shop();
        refresh_emblems();
        refresh_self();
    }
    w.update(round);
    v67_team_sync();
    struct Publish {
        Bot* bot;
        ~Publish() {
#if V67_TRACE
            if (bot->round % 25 == 0) {
                const int g = bot->target_group;
                std::printf("T67 r%d s%d %s p%d,%d hp%.0f/%.0f gold%d bag%d rally%d job%d state%d left%.0f allies%zu fields%d fuel%llu\n",
                    bot->round, bot->slot, bot->mode, bot->pos.x, bot->pos.y, bot->hp, bot->max_hp, bot->gold, bot->gems,
                    bot->rally67_, g, g >= 0 ? static_cast<int>(bot->w.groups[g].state) : -1,
                    g >= 0 ? bot->w.groups[g].hp_left(bot->w.camps) : -1.0f, bot->w.allies.size(), bot->field_calls,
                    static_cast<unsigned long long>(bc::fuel_remaining()));
            }
#endif
            bot->v67_team_publish(true);
        }
    } publish{this};
    const auto state = me.state();
    if (state.contains(bc::champion_state::recalling) || state.contains(bc::champion_state::submitting_gems) ||
        state.contains(bc::champion_state::teleporting)) return;
    v67_team_plan();
    support_casts();
    if (!v67_team_combat()) {
        if (!v67_team_home() && !v67_team_bank()) {
#if V67_TEAMPLAY == 2
            farm();
#else
            v67_team_farm();
#endif
        }
    }
#if A2_SHIELDLATE
    shield_late_pass = true;
    support_casts();
    shield_late_pass = false;
#endif
    // This also advances field_calls when there is not room for a field yet.
    // farm() deliberately refuses its first job until that startup pass ran.
    build_fields();
}
