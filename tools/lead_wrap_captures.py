"""One-off lead edit: every nn_teacher_access::cap_* becomes noinline and opens with an nnb::CreditScope.

noinline keeps the surrounding teacher code's codegen (and therefore its own fuel cost) as close as possible to the
original; the scope credits the capture's fuel back to the teacher in the neutral_credit profile. Idempotent.
"""
import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'bot/src/nn_teacher.h'
s = p.read_text(encoding='utf-8')
if 'nnb::CreditScope' not in s:
    s = s.replace('#include "nn_config.h"', '#include "nn_config.h"\n#include "nn_budget.h"', 1)
    pat = re.compile(r'(    )((?:template <class C> )?static void (cap_\w+)\([^{]*?\)\s*)\{')
    n = 0

    def rep(m):
        global n
        n += 1
        return f'{m.group(1)}[[gnu::noinline]] {m.group(2)}{{\n        nnb::CreditScope nn_credit_scope_;\n       '

    s = pat.sub(rep, s)
    p.write_text(s, encoding='utf-8', newline='\n')
    print('wrapped', n)
else:
    print('already wrapped')
