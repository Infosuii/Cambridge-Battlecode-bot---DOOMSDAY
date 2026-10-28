"""Copy the frozen source into a local-only diagnostic build, preserving bytes."""
import hashlib
import json
import shutil
from pathlib import Path
from deep_preflight import ROOT


def main():
    source = ROOT / 'bots/live-69/src'
    dest = ROOT / 'artifacts/tmp/deep-repro/live69-plain/src'
    files = [p for p in source.rglob('*') if p.is_file()]
    assert len(files) == 33
    for p in files:
        q = dest / p.relative_to(source)
        if q.exists():
            assert q.read_bytes() == p.read_bytes(), 'Diagnostic source changed; use another directory'
        else:
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, q)
    result = {'source': 'bots/live-69/src', 'files': len(files), 'exact_copy': True,
              'file_sha256': {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (dest.parent / 'source-identity.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({'files': len(files), 'exact_copy': True, 'destination': str(dest.parent)}))


if __name__ == '__main__':
    main()
