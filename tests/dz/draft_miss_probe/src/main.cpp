#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
int main() {
    if (is_draft()) {
        unsigned turn=0;
        const std::array choices{champion_draft::cassi_and_issac,champion_draft::vendetta,champion_draft::ryth,
            champion_draft::vesper_vale,champion_draft::marcella,champion_draft::heart_of_ruin,
            champion_draft::stellar,champion_draft::prism,champion_draft::willow,champion_draft::ren,
            champion_draft::varg,champion_draft::tavi};
        for (;;) {
            try {
                if (turn==static_cast<unsigned>(DZ_SKIP_SECOND)) {
                    auto before=draft::current_draft(team::ally);
                    std::uint64_t word=(std::uint64_t{3}<<62)|(static_cast<std::uint64_t>(turn)<<48)|(static_cast<std::uint64_t>(before.size())<<32);
                    for (unsigned i=0;i<before.size();++i) word|=static_cast<std::uint64_t>(before[i])<<(4*i);
                    shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
                    std::printf("CT20_SKIP turn=%u picks=%u before=%zu\n",turn,draft::team_size(),before.size());
                } else {
                    auto before=draft::current_draft(team::ally);
                    if (turn>static_cast<unsigned>(DZ_SKIP_SECOND)) std::printf("CT20_AFTER_SKIP count=%zu\n",before.size());
                    auto chosen=choices[0];
                    for (auto c:choices) if (std::find(before.begin(),before.end(),c)==before.end()) { chosen=c; break; }
                    draft::pick(chosen);
                    auto after=draft::current_draft(team::ally);
                    std::uint64_t word=(std::uint64_t{1}<<63)|(static_cast<std::uint64_t>(after.size())<<32);
                    for (unsigned i=0;i<after.size();++i) word|=static_cast<std::uint64_t>(after[i])<<(4*i);
                    shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
                    std::printf("CT20_PICK turn=%u before=%zu after=%zu choice=%d\n",turn,before.size(),after.size(),static_cast<int>(chosen));
                }
            } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
            ++turn; end_turn();
        }
    }
    std::uint64_t word{};shared_memory.read(0,std::span<std::uint64_t>(&word,1));
    std::printf("CT20_PLAY body=%u type=%d picks=%u word=%016llx\n",static_cast<unsigned>(static_cast<handle_champion_t>(self())),
        static_cast<int>(self().champion_name()),draft::team_size(),static_cast<unsigned long long>(word));
    for (;;) end_turn();
}
