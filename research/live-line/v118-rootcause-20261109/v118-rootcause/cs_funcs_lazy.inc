// CS (camp safety, v118): camps killed our champions 1.0-1.6 times per ladder game (1.4 per local game). Debug
// attribution of 712 local camp deaths: 43% in "flee" (retreat_from scored steps by enemy distance, spawn distance and
// ally pull only, so fleeing champions walked into awake wolves, elks and golems) and 26% in "home-escape" (walk to the
// nearest tile outside the hot zone, ignoring how much the camps on the way hit). camp_hit(q) is the damage the awake
// camps around us deal on tile q next round.
void Bot::cs_build() {
    if (cs_round == round) return;
    cs_round = round;
    n_csc = 0;
    // Lazy (flee / escape turns only): constant per-turn work in the world update cost games at the fuel limit.
    // A camp is hot when it is damaged or any member of its alive group is damaged or dead (World's hot_zone rule).
    for (std::size_t ci = 0; ci < w.camps.size() && n_csc < static_cast<int>(csc.size()); ++ci) {
        const auto& c = w.camps[ci];
        if (c.dead || c.strength <= 0 || cheb(c.pos, pos) > c.range + 3) continue;
        const int gi = w.camp_group[ci];
        if (gi < 0 || w.groups[static_cast<std::size_t>(gi)].state != GroupState::alive) continue;
        bool hot = c.hp < c.max_hp;
        if (!hot)
            for (int o : w.groups[static_cast<std::size_t>(gi)].camps) {
                const auto& m = w.camps[static_cast<std::size_t>(o)];
                if (m.dead || m.hp < m.max_hp) {
                    hot = true;
                    break;
                }
            }
        if (hot) csc[static_cast<std::size_t>(n_csc++)] = {c.pos, c.strength, c.range};
    }
}

float Bot::camp_hit(vec2 q) {
    cs_build();
    float s = 0.0f;
    for (int i = 0; i < n_csc; ++i)
        if (cheb(csc[static_cast<std::size_t>(i)].p, q) <= csc[static_cast<std::size_t>(i)].r) s += csc[static_cast<std::size_t>(i)].s;
    return s * camp_taken_mult;
}

int Bot::camp_penalty(vec2 q) {
    const float h = camp_hit(q);
    if (h <= 0.0f) return 0;
    if (h >= hp) return 100000; // this step dies to the camps alone
    return static_cast<int>(CS_FLEE_W * h / std::max(hp, 1.0f));
}

// Leave the awake camps' reach with the least camp damage on the way: a ready dash first (two tiles toward the exit),
// otherwise the neighbour that minimises next-round camp damage plus exit distance. Lethal tiles only as a last resort.
bool Bot::cs_escape() {
    auto& me = bc::self();
    if (!me.can_move()) return false;
    bc::bitboard blocked = w.static_blocked | w.unit_tiles;
    blocked.set(pos, false);
    const bc::bitboard goals = ~w.hot_zone & ~blocked;
    if (goals.is_empty()) return false;
    bc::distance_field f;
    bc::bitboard visited;
    f.compute_to(blocked, goals, single(pos), visited);
    const int here = fdist(f, pos);
    if (here == kUnreach || here == 0) return false;
    auto score = [&](vec2 q) {
        const int d = fdist(f, q);
        if (d == kUnreach) return 1 << 28;
        const float h = camp_hit(q);
        return (h >= hp ? 100000 : 0) + static_cast<int>(h) + 40 * d;
    };
    // The dash is worth more in fights: spend it on camps only when staying two rounds would kill us.
    if (!cast_done && here >= 2 && camp_hit(pos) * 2.0f >= hp)
        for (int s = 0; s < 2; ++s) {
            if (!spell_ready(s) || spells[s].kind != bc::ability_kind::dash) continue;
            const int reach = std::max(1, static_cast<int>(spells[s].range));
            vec2 best = pos;
            int best_sc = score(pos);
            for (int dy = -reach; dy <= reach; ++dy)
                for (int dx = -reach; dx <= reach; ++dx) {
                    const vec2 q{pos.x + dx, pos.y + dy};
                    if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;
                    const int sc = score(q);
                    if (sc + 60 < best_sc) best_sc = sc, best = q;
                }
            if (best == pos) break;
            try {
                if (me.abilities()[s].use(best)) {
                    pos = best;
                    cast_done = true;
                    break;
                }
            } catch (...) {
            }
            break;
        }
    struct Cand {
        vec2 p;
        int s;
    };
    std::array<Cand, 8> cands{};
    int n = 0;
    const int stay = score(pos) + 1;
    for (vec2 dir : kDirs) {
        const vec2 q = pos + dir;
        if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;
        const int sc = score(q);
        if (sc >= stay) continue;
        int i = n++;
        for (; i > 0 && cands[static_cast<std::size_t>(i - 1)].s > sc; --i) cands[static_cast<std::size_t>(i)] = cands[static_cast<std::size_t>(i - 1)];
        cands[static_cast<std::size_t>(i)] = {q, sc};
    }
    for (int i = 0; i < n; ++i) {
        try {
            if (me.move_absolute(cands[static_cast<std::size_t>(i)].p)) {
                pos = cands[static_cast<std::size_t>(i)].p;
                walked = true;
                return true;
            }
        } catch (...) {
        }
    }
    return cast_done;
}

