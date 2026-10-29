#include <cambc.h>
#include <cstdio>
#include <stdexcept>
// Deliberately faulty diagnostic. Never use as a submission or strength candidate.
int main() {
    using namespace cambc;
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,champion_draft::vendetta,
            champion_draft::ryth,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto id=static_cast<unsigned>(static_cast<handle_champion_t>(self()));
    const bool subject=self().champion_name()==champion_type::vesper_vale;
    static unsigned local_boots=0; ++local_boots;
    std::uint64_t persisted{};
    if (subject) {
        shared_memory.read(0,std::span<std::uint64_t>(&persisted,1));
        auto boots=static_cast<unsigned>(persisted)+1;
        persisted=(persisted&0xffffffff00000000ULL)|boots;
        shared_memory.write(0,std::span<const std::uint64_t>(&persisted,1));
        std::printf("CT4_BOOT round=%u body=%u local=%u shared=%u flag=%u\n",round_number(),id,local_boots,boots,static_cast<unsigned>(persisted>>32));
    }
    std::optional<champion> faulted;
    for (auto& ally:champions(team::ally)) if (ally.champion_name()==champion_type::vesper_vale) faulted=ally;
    for (;;) {
        auto round=round_number();
        if (subject&&round>=50&&(persisted>>32)==0) {
            persisted|=std::uint64_t{1}<<32;
            shared_memory.write(0,std::span<const std::uint64_t>(&persisted,1));
            std::printf("CT4_THROW round=%u body=%u\n",round,id);
            std::fflush(stdout);
            throw std::runtime_error("controlled uncaught exception; diagnostic only");
        }
        if (round==1||round%100==0) {
            std::printf("CT4_HEARTBEAT round=%u body=%u\n",round,id);
            if (!subject&&round==100) std::printf("CT4_STATUS actor_alive=%d\n",faulted->is_alive());
        }
        end_turn();
    }
}
