"""Create immutable restart experiment snapshots; never edits frozen bots."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / 'artifacts/tmp/v55-r7-heart'
variants = {
    'v55-r7-no-retarget': ('V55_CAST_RETARGET',),
    'v55-r7-no-model': ('V55_HEART_MODEL',),
    'v55-r7-no-strike': ('V55_HEART_CAMP',),
    'v55-r8-heart-completion': (),
    'v55-r9-heart-only': ('V55_CAST_RETARGET', 'V55_HEART_MODEL'),
    'v55-r10-heart-completion': ('V55_CAST_RETARGET', 'V55_HEART_MODEL'),
}
for name, flags in variants.items():
    dst = ROOT / 'artifacts/tmp' / name
    if dst.exists():
        print(f'preserved existing {name}')
        continue
    shutil.copytree(src / 'src', dst / 'src')
    common = dst / 'src/common.h'
    data = common.read_bytes()
    for flag in flags:
        old = f'#define {flag} 1'.encode()
        assert data.count(old) == 1
        data = data.replace(old, f'#define {flag} 0'.encode())
    if name in ('v55-r8-heart-completion', 'v55-r10-heart-completion'):
        data = b'#ifndef V55_COMMIT_EVENT\n#define V55_COMMIT_EVENT 1\n#endif\n' + data
        bot = dst / 'src/bot.cpp'
        text = bot.read_bytes()
        baseline = (ROOT / 'artifacts/tmp/v55-r2-completion/src/bot.cpp').read_bytes()
        start = baseline.index(b'#if V55_COMMIT_EVENT')
        end = baseline.index(b'#endif', start) + len(b'#endif\r\n')
        anchor = b'    // A committed pick (an earlier sample) stands while it is still a candidate and fresh: no resampling every turn.'
        assert text.count(anchor) == 1
        bot.write_bytes(text.replace(anchor, baseline[start:end] + anchor))
    common.write_bytes(data)
    if name in ('v55-r9-heart-only', 'v55-r10-heart-completion'):
        # Necessary rules correction, independently neutral in the R1 full suite.
        common.write_bytes(b'#ifndef V55_DRAFT_LEGAL\n#define V55_DRAFT_LEGAL 1\n#endif\n' + common.read_bytes())
        shutil.copyfile(ROOT / 'artifacts/tmp/v55-r1-legal/src/draft.cpp', dst / 'src/draft.cpp')
    print(name)
