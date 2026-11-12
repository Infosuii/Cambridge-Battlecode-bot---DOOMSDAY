"""Restore the published content-addressed research snapshot without executing it."""
from pathlib import Path
import argparse
import hashlib
from functools import lru_cache
import json
import zipfile

def restore(snapshot, output, verify_only=False):
    snapshot, output = Path(snapshot).resolve(), Path(output).resolve()
    manifest = json.loads((snapshot / 'index/artifacts.json').read_text(encoding='utf-8'))
    for part in manifest['archives']:
        path = (snapshot / part['file']).resolve()
        assert path.is_relative_to(snapshot)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == part['sha256'], str(path)
    handles = {}
    @lru_cache(maxsize=128)
    def object_bytes(digest):
        item = manifest['objects'][digest]
        archive = item['archive']
        archive_path = (snapshot / archive).resolve()
        assert archive_path.is_relative_to(snapshot), archive
        if archive not in handles: handles[archive] = zipfile.ZipFile(archive_path)
        data = handles[archive].read(item['entry'])
        assert hashlib.sha256(data).hexdigest() == digest
        return data
    try:
        for relative, spec in manifest['files'].items():
            target = (output / relative).resolve()
            assert target.is_relative_to(output), relative
            data = object_bytes(spec['sha256'])
            assert len(data) == spec['bytes'] and hashlib.sha256(data).hexdigest() == spec['sha256'], relative
            if not verify_only:
                if target.exists(): assert target.read_bytes() == data, f'Refusing to overwrite different file: {target}'
                else:
                    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    finally:
        for handle in handles.values(): handle.close()
    return len(manifest['files'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    print(restore(args.snapshot, args.output, args.verify_only), 'files verified')
