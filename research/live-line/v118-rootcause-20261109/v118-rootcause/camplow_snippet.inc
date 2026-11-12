    debug_block({
        if (hp < 0.4f * max_hp) {
            int hits = 0, best_type = -1;
            float str = 0.0f, chp = 0.0f;
            for (const auto& c : w.camps) {
                if (c.dead || c.strength <= 0 || cheb(c.pos, pos) > c.range) continue;
                const int gi = w.camp_group[static_cast<std::size_t>(&c - &w.camps[0])];
                if (gi < 0 || w.groups[static_cast<std::size_t>(gi)].state != GroupState::alive) continue;
                ++hits, str += c.strength;
                if (best_type < 0) best_type = static_cast<int>(c.type), chp = c.hp;
            }
            int en = 0;
            for (const auto& e : w.enemies) en += cheb(e.pos, pos) <= 6;
            if (hits > 0)
                std::printf("CAMPLOW %d %d %s %s %.0f %.0f %d %d %.0f %d %.0f %d %d %d %d %d\n", round, slot, bc::to_string(type).c_str(), mode,
                    static_cast<float>(hp), static_cast<float>(max_hp), gems, hits, str, best_type, chp, en, target_group,
                    bit(w.ally_spawn, pos) ? 1 : 0, heading_home ? 1 : 0, walked ? 1 : 0);
        }
    });
