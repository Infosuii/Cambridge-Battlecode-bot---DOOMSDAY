#include <cambc.h>
#include <cstdio>
#include <algorithm>

// Diagnostic only. Deliberately logs and burns fuel; never a competition candidate.
template<class F> void measure(const char* name, F function) {
    const auto round = cambc::round_number();
    auto before = cambc::fuel_remaining();
    function();
    auto after = cambc::fuel_remaining();
    std::printf("CT1 %s round=%u stable=%d fuel=%llu samples=1\n", name, round,
        cambc::round_number() == round, static_cast<unsigned long long>(before >= after ? before - after : 0));
}
int main() {
    using namespace cambc;
    if (is_draft()) {
        unsigned turn = 0;
        const std::array picks{champion_draft::cassi_and_issac, champion_draft::heart_of_ruin, champion_draft::vendetta,
            champion_draft::marcella, champion_draft::vesper_vale};
        for (;;) {
            auto budget = fuel_remaining();
            try {
                auto chosen = draft::current_draft(team::ally);
                draft::pick(picks[std::min(chosen.size(), picks.size()-1)]);
                std::printf("CT20 draft_turn=%u fuel=%llu team_size=%u ours=%zu theirs=%zu\n", turn++,
                    static_cast<unsigned long long>(budget), draft::team_size(), chosen.size(), draft::current_draft(team::enemy).size());
            } catch (const std::exception& error) { std::printf("ERROR draft %s\n", error.what()); }
            end_turn();
        }
    }
    auto allies = champions(team::ally);
    std::sort(allies.begin(), allies.end(), [](auto& a, auto& b) {
        return static_cast<unsigned>(static_cast<handle_champion_t>(a)) < static_cast<unsigned>(static_cast<handle_champion_t>(b));
    });
    unsigned slot = 0;
    for (unsigned i = 0; i < allies.size(); ++i) if (allies[i] == self()) slot = i;
    unsigned turn = 0;
    bool burned = false;
    for (;;) {
        auto round = round_number(); auto budget = fuel_remaining();
        try {
            std::uint64_t word{};
            shared_memory.read(0, std::span<std::uint64_t>(&word, 1));
            if (turn < 3) std::printf("CT5 round=%u slot=%u observed_round=%u observed_mask=%u\n", round, slot,
                static_cast<unsigned>(word >> 32), static_cast<unsigned>(word));
            unsigned mask = static_cast<unsigned>(word >> 32) == round ? static_cast<unsigned>(word) : 0;
            word = (std::uint64_t{round} << 32) | mask | (1u << slot);
            shared_memory.write(0, std::span<const std::uint64_t>(&word, 1));
            if (turn < 2) std::printf("CT3 round=%u slot=%u play_turn=%u fuel=%llu bodies=%zu type=%d\n", round, slot, turn,
                static_cast<unsigned long long>(budget), allies.size(), static_cast<int>(self().champion_name()));
            if (turn == 0 && slot == 0) {
                bitboard blocked = map::walls() | map::holes() | map::altars() | map::spawn_region(team::enemy);
                bitboard visited, roots = map::spawn_region(team::ally);
                distance_field field;
                std::printf("CT1 dimensions=%dx%d\n", map::width(), map::height());
                measure("field.compute", [&] { field.compute(blocked, roots, visited); });
                measure("champions", [] { (void)champions(team::ally); });
                measure("visible.camps", [] { (void)vision::camps(); });
                measure("camp_groups", [] { (void)map::camp_groups(); });
                measure("champion.state", [] { (void)self().state(); });
                measure("shared.read", [&] { shared_memory.read(0, std::span<std::uint64_t>(&word, 1)); });
                measure("bitboard.union", [&] { visited = blocked | roots; });
                unsigned hash = 2166136261u;
                auto add = [&](unsigned value) { hash = (hash ^ value) * 16777619u; };
                add(constants::capture_time); add(constants::recall_time); add(constants::respawn_time);
                add(constants::winning_gems); add(constants::kill_gold);
                for (const auto& c : champion_designs) {
                    auto stats = c.base_stats();
                    add(static_cast<unsigned>(stats.base_health * 100)); add(static_cast<unsigned>(stats.base_strength * 100));
                    add(static_cast<unsigned>(stats.base_focus * 100)); add(stats.base_attack_range);
                }
                for (unsigned i = 0; i < static_cast<unsigned>(item_type::count); ++i) {
                    auto item = static_cast<item_type>(i).info();
                    add(item.cost); add(item.combine_count); add(item.strength_points); add(item.health_points); add(item.focus_points);
                    add(static_cast<unsigned>(item.passive_magnitude * 10000));
                }
                std::printf("CT27 partial_fingerprint=%08x capture=%d recall=%d respawn=%d winning=%u\n", hash,
                    constants::capture_time, constants::recall_time, constants::respawn_time, constants::winning_gems);
            }
            if (turn == 3 && slot == 0 && !burned) {
                burned = true;
                volatile unsigned sink = 1;
                while (round_number() == round) { for (unsigned n = 0; n < 100; ++n) sink = sink * 1664525u + 1013904223u; }
                // Only report a logical guard; no stale action is actually issued.
                std::printf("CT2 before=%u resumed=%u stale_refused=%d sink=%u\n", round, round_number(), round != round_number(), sink);
                ++turn;
                continue; // Keep the resumed turn rather than yielding it away.
            }
        } catch (const std::exception& error) { std::printf("ERROR round=%u slot=%u %s\n", round, slot, error.what()); }
        ++turn;
        if (round_number() != round) continue;
        end_turn();
    }
}
