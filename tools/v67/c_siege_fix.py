"""Patch a bot folder in place with V68_SIEGE_FIX: the siege line-of-sight scan (NOVA_SIEGE_LOS in fight_camps) becomes
incremental. It resumes next turn where it stopped instead of suspending the turn, and its finished result is kept until
the group's live camps change.

Bug (2026-10-28, tools/v67/c_add_diag.py traces): on 00vault the siege target is a 49-camp group; the scan tests every
ring tile (~109) against every camp, overruns the 100k turn budget and suspends, and the next turn starts the same scan,
so the champion stands frozen (662 fuel-outs in one v65 mirror game, rounds 532-2000). Where the scan fits in a turn the
result is the same ring as before.

Usage: c_siege_fix.py bots/v68
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NEW = r'''            if (NOVA_SIEGE_LOS) {
#if V68_SIEGE_FIX
                const int siege_gi = static_cast<int>(&g - &w.groups[0]);
                int siege_alive = 0;
                for (int ci : g.camps) siege_alive += !w.camps[ci].dead;
                if (siege_los_group_ != siege_gi || siege_los_alive_ != siege_alive) {
                    siege_los_group_ = siege_gi, siege_los_alive_ = siege_alive, siege_los_next_ = 0;
                    siege_los_seeing_.clear();
                }
                const auto tiles = ring.positions();
                if (siege_los_next_ < tiles.size()) {
                    const bc::bitboard opaque = bc::map::walls() | w.bushes;
                    std::size_t k = siege_los_next_;
                    for (; k < tiles.size() && bc::fuel_remaining() > 15000; ++k) {
                        const vec2 q = tiles[k];
                        for (int ci : g.camps) {
                            const auto& c = w.camps[ci];
                            if (c.dead || cheb(c.pos, q) > 4) continue;
                            bool clear = true;
                            const int n = cheb(c.pos, q);
                            for (int s = 1; s < n && clear; ++s) {
                                const vec2 m{q.x + ((c.pos.x - q.x) * s * 2 + (c.pos.x >= q.x ? n : -n)) / (2 * n),
                                    q.y + ((c.pos.y - q.y) * s * 2 + (c.pos.y >= q.y ? n : -n)) / (2 * n)};
                                clear = !bit(opaque, m);
                            }
                            if (clear) {
                                siege_los_seeing_.set(q, true);
                                break;
                            }
                        }
                    }
                    siege_los_next_ = k;
                }
                if (!siege_los_seeing_.is_empty()) ring = siege_los_seeing_;
#else
'''


def main():
    src = ROOT / sys.argv[1] / 'src'
    h = (src / 'bot.h').read_bytes().decode()
    nl = '\r\n' if '\r\n' in h else '\n'
    assert 'siege_los_group_' not in h
    marker = 'class Bot {' + nl + 'public:' + nl
    assert h.count(marker) == 1
    at = h.index('private:', h.index(marker))
    fields = ('private:' + nl + '    // V68_SIEGE_FIX: incremental siege line-of-sight scan (group, live camps, next ring tile, tiles that see).' + nl +
              '    int siege_los_group_ = -1, siege_los_alive_ = -1;' + nl +
              '    std::size_t siege_los_next_ = 0;' + nl +
              '    bc::bitboard siege_los_seeing_;' + nl)
    h = h[:at] + fields + h[at + len('private:'):]
    (src / 'bot.h').write_bytes(h.encode())

    c = (src / 'bot.cpp').read_bytes().decode()
    nl = '\r\n' if '\r\n' in c else '\n'
    old = '            if (NOVA_SIEGE_LOS) {' + nl
    assert c.count(old) == 1
    start = c.index(old)
    end_marker = '                if (!seeing.is_empty()) ring = seeing;' + nl
    end = c.index(end_marker, start) + len(end_marker)
    original_body = c[start + len(old):end]
    c = c[:start] + NEW.replace('\n', nl) + original_body + '#endif' + nl + c[end:]
    (src / 'bot.cpp').write_bytes(c.encode())

    cm = (src / 'common.h').read_bytes().decode()
    nl = '\r\n' if '\r\n' in cm else '\n'
    assert 'V68_SIEGE_FIX' not in cm
    cm = ('#ifndef V68_SIEGE_FIX // 1: incremental siege line-of-sight scan (00vault froze champions on fuel every turn).' + nl +
          '#define V68_SIEGE_FIX 1' + nl + '#endif' + nl) + cm
    (src / 'common.h').write_bytes(cm.encode())
    print('patched', src)


if __name__ == '__main__':
    main()
