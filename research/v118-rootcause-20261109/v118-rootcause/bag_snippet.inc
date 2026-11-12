    debug_block({
        if (gems >= 60 && round % 5 == 0) {
            const int bd = w.altar_ready ? static_cast<int>(fdist(w.altar_field, pos)) : -2;
            int en = 0;
            for (const auto& e : w.enemies) en += cheb(e.pos, pos) <= 8;
            std::printf("BAG %d %d %s %d %.0f %.0f %s f%d w%d nb%d d%d off%d nob%d ally%d enemy%d en%d hh%d st%d,%d\n", round, slot,
                bc::to_string(type).c_str(), gems, static_cast<float>(hp), static_cast<float>(max_hp), mode, fought ? 1 : 0,
                win_now() ? 1 : 0, nn_beh, bd, tribute_off_until - round, w.no_bank ? 1 : 0, ally_score, enemy_score, en,
                heading_home ? 1 : 0, tribute_stuck, tribute_last_dist);
        }
    });
