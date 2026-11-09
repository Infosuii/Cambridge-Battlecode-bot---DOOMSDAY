        debug_block({
            if (dx_still == 31) {
                std::printf("TDG %d %d pos%d,%d range%.1f\n", round, slot, pos.x, pos.y, static_cast<float>(spells[s].range));
                for (int dy = -3; dy <= 3; ++dy) {
                    std::printf("TDG ");
                    for (int dx = -3; dx <= 3; ++dx) {
                        const vec2 q{pos.x + dx, pos.y + dy};
                        if (!in_bounds(q, w.width, w.height)) { std::printf("  ."); continue; }
                        const bool hole = bit(bc::map::holes(), q), br = w.bridges_on && bit(w.bridges, q);
                        const bool un = bit(w.unit_tiles, q), sb = bit(w.static_blocked, q), bl = bit(blocked, q);
                        const int dq = std::min(99, static_cast<int>(fdist(field, q)));
                        if (dx == 0 && dy == 0) std::printf("  @");
                        else if (br) std::printf(" B%d", dq);
                        else if (hole) std::printf("  H");
                        else if (sb) std::printf("  #");
                        else if (un) std::printf(" U%d", dq);
                        else if (bl) std::printf(" X%d", dq);
                        else std::printf(" %2d", dq);
                    }
                    std::printf("\n");
                }
            }
        });
