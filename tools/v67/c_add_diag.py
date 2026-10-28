"""Copy a bot folder and add fuel-overrun diagnostics: whenever a turn's play_turn() is still running when the round
advances (it ran out of fuel and resumed), print the round it started, the round it finished, the champion, its
position and the last mode string, plus a PROF trail of the named checkpoints it passed (APEX_PROFILE marks).

Usage: c_add_diag.py --base bots/v65 --out artifacts/tmp/v67/NAME
"""
import argparse
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = ROOT / a.out
    assert not out.exists()
    shutil.copytree(ROOT / a.base / 'src', out / 'src', copy_function=shutil.copyfile)
    src = out / 'src'
    h = (src / 'bot.h').read_bytes().decode()
    assert h.count('    void play_turn();') == 1
    h = h.replace('    void play_turn();', '    void play_turn();\n    void diag_overrun(unsigned r0, unsigned r1);', 1)
    (src / 'bot.h').write_bytes(h.encode())
    c = (src / 'bot.cpp').read_bytes().decode()
    c += '''
void Bot::diag_overrun(unsigned r0, unsigned r1) {
    if (r1 != r0)
        std::printf("OVR %u->%u %s pos(%d,%d) hp%.0f gems%d mode=%s target=%d\\n", r0, r1, bc::to_string(type).c_str(), pos.x,
            pos.y, hp, gems, mode, target_group);
    // Status every 50 rounds: what each champion is doing (idle audits).
    if (r0 % 50 == 0)
        std::printf("ST %u %s pos(%d,%d) hp%.0f/%.0f gems%d gold%d mode=%s target=%d\\n", r0, bc::to_string(type).c_str(), pos.x,
            pos.y, hp, max_hp, gems, gold, mode, target_group);
}
'''
    (src / 'bot.cpp').write_bytes(c.encode())
    m = (src / 'main.cpp').read_bytes().decode()
    new, n = re.subn(r'(            else\r?\n)(                bot\.play_turn\(\);)',
                     r'\1                { const unsigned r0 = bc::round_number(); bot.play_turn(); '
                     r'const unsigned r1 = bc::round_number(); bot.diag_overrun(r0, r1); }', m)
    assert n == 1
    (src / 'main.cpp').write_bytes(new.encode())
    print('prepared', out)


if __name__ == '__main__':
    main()
