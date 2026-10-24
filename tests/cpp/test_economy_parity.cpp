// Synthetic fixtures only. Native driver for Python/C++ economy candidate parity.
#include "nn_economy.h"
#include <iostream>
#include <iomanip>
#include <string>

int main() {
    std::cout << std::setprecision(9);
    std::string kind;
    while (std::cin >> kind) {
        nne::State s;
        std::cin >> s.hp >> s.max_hp >> s.gems >> s.gold >> s.round >> s.ally_score >> s.enemy_score;
        nnh::Decision d{};
        if (kind == "bank") {
            nne::BankTerms t;
            std::cin >> t.go >> t.safe >> t.force >> t.wins >> t.late >> t.end_bank >> t.rhythm >> t.edge >>
                t.threatened >> t.dist >> t.raw_dist;
            nne::BankChoice choices[3];
            nne::build_bank(s, t, d, choices);
        } else {
            auto read = [](nne::Buy& b) {
                int k;
                std::cin >> k >> b.item >> b.count >> b.cost >> b.owned >> b.legal;
                b.kind = static_cast<nne::BuyKind>(k);
            };
            nne::Buy teacher, options[32], choices[16];
            int n; read(teacher); std::cin >> n;
            if (n < 0 || n > 32) return 2;
            for (int i = 0; i < n; ++i) read(options[i]);
            nne::build_shop(s, teacher, options, n, d, choices);
        }
        if (!std::cin) return 3;
        std::cout << d.K << ' ' << d.F << ' ' << int(d.context);
        for (int i = 0; i < d.K; ++i) std::cout << ' ' << d.id[i] << ' ' << int(d.legal[i]) << ' ' << d.prior[i];
        for (int i = 0; i < d.K*d.F; ++i) std::cout << ' ' << d.feat[i];
        std::cout << '\n';
    }
}
