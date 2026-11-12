#if CODEX_OPENING_FINISH
    if (round <= 300 && !low_fuel && !in_role_pack && best_score > 0.0f &&
        target_group >= 0 && target_group != best && static_cast<std::size_t>(target_group) < w.groups.size() &&
        hp > max_hp * 0.65f && w.enemies.empty() && round >= avoid_until[target_group]) {
        auto& previous = w.groups[target_group];
        int remaining = 0;
        int finish = -1;
        if (previous.state == GroupState::alive) {
            for (int ci : previous.camps) {
                const auto& camp = w.camps[ci];
                if (camp.dead) continue;
                ++remaining;
                if (camp.hp > 0.0f && camp.hp <= strength && bit(w.visible, camp.pos) &&
                    cheb(camp.pos, pos) <= range)
                    finish = ci;
            }
        }
        if (remaining == 1 && finish >= 0 && bc::self().can_attack()) {
            // Keep the current claim for one turn; the normal camp combat still checks safety.
            const bool handled = fight_camps(previous, 1);
#if CODEX_OPENING_FINISH_DIAG
            const auto id = static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(w.camps[finish].camp));
            d::camp_state after{};
            const int code = d::sdk_camp(id, &after);
            std::printf("CODEX_FINISH_ACTION R%d S%d G%d I%u H%d\n", round, slot, target_group, id,
                code == 0 && after.health <= 0.0f ? 1 : 0);
#endif
            if (handled) return true;
        }
    }
#endif
