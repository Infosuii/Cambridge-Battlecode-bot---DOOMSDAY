"""Patch a bot folder in place with a C67_CARRY_FOCUS hook in the enemy target choice: the enemy Vendetta's worth is
multiplied by 1 + C67_CARRY_FOCUS (off unless the macro is defined). In our runs Vendetta decides mirror games: 6.8 kills
in our wins against 3.2 in losses.

Usage: c_carry_focus.py artifacts/tmp/v67/NAME
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = ROOT / sys.argv[1] / 'src/bot.cpp'
    s = p.read_bytes().decode()
    nl = '\r\n' if '\r\n' in s else '\n'
    old = '        if (e.recalling()) worth += 0.5f;' + nl
    assert s.count(old) == 1 and 'C67_CARRY_FOCUS' not in s
    s = s.replace(old, old + '#ifdef C67_CARRY_FOCUS' + nl +
                  '        if (e.type == bc::champion_type::vendetta) worth *= 1.0f + C67_CARRY_FOCUS; // the enemy carry first' + nl +
                  '#endif' + nl)
    p.write_bytes(s.encode())
    print('patched', p)


if __name__ == '__main__':
    main()
