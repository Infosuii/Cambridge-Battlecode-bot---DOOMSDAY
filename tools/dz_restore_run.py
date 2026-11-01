"""Restore committed DZ evidence on a fresh clone; no runtime or account needed."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TRANSFER = ROOT / 'research/dz/legacy-transfer-2026-11-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def restore(archive: Path, destination: Path, expected_archive=None, files=None):
    destination = destination.resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError('Restore inside this checkout; destination is outside the repository')
    if expected_archive and sha(archive) != expected_archive:
        raise ValueError('Archive hash does not match the committed manifest')
    with zipfile.ZipFile(archive) as z:
        entries = []
        names = set()
        for entry in z.infolist():
            relative = PurePosixPath(entry.filename)
            if relative.is_absolute() or '..' in relative.parts or '\\' in entry.filename or any(':' in p for p in relative.parts):
                raise ValueError('Unsafe archive path: ' + entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Archive symlinks are not supported')
            target = (destination / Path(*relative.parts)).resolve()
            if not target.is_relative_to(destination):
                raise ValueError('Archive entry escapes the destination')
            if entry.is_dir():
                continue
            if entry.filename in names:
                raise ValueError('Duplicate archive entry: ' + entry.filename)
            names.add(entry.filename)
            data = z.read(entry)
            if files is not None:
                expected = files.get(entry.filename)
                if expected is None or len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
                    raise ValueError('Reference hash mismatch: ' + entry.filename)
            if target.exists() and (not target.is_file() or sha(target) != hashlib.sha256(data).hexdigest()):
                raise FileExistsError('Existing file differs; choose a new destination: ' + str(target))
            entries.append((target, entry))
        if files is not None and names != set(files):
            raise ValueError('Reference archive is missing expected files')
        # Validate the entire archive before writing; never overwrite a different file.
        for target, entry in entries:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(z.read(entry))
    return destination, len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', help='Committed research/dz/runs capsule name')
    mode.add_argument('--references', action='store_true', help='Restore all retained elite reference replays and traces')
    parser.add_argument('--destination', type=Path, help='Optional destination inside this checkout')
    args = parser.parse_args()
    if args.references:
        manifest = json.loads((TRANSFER / 'reference-replays.manifest.json').read_text())
        destination = args.destination or ROOT / 'artifacts/local-only/dz-cycle-reference-2026-11-01'
        result, count = restore(TRANSFER / manifest['archive'], destination, manifest['archive_sha256'],
                                {row['file']: row for row in manifest['files']})
    else:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run):
            parser.error('Use a simple committed run name')
        capsule = ROOT / 'research/dz/runs' / args.run
        expected = None
        for row in json.loads((TRANSFER / 'RUNS.json').read_text())['runs']:
            if row['name'] == args.run:
                expected = row['evidence_sha256']
                break
        destination = args.destination or ROOT / 'artifacts/tmp/dz' / args.run
        result, count = restore(capsule / 'evidence.zip', destination, expected)
        provenance = json.loads((capsule / 'provenance.json').read_text())
        for key, relative in [('candidate_sha256', 'candidate.wasm'), ('opponent_sha256', 'opponent.wasm')]:
            if sha(result / relative) != provenance[key]:
                raise ValueError('Restored binary hash mismatch: ' + relative)
        for relative, digest in provenance['source'].items():
            if sha(result / 'build/candidate' / relative) != digest:
                raise ValueError('Restored candidate source mismatch: ' + relative)
    print(json.dumps({'restored_files': count, 'destination': str(result)}))


if __name__ == '__main__':
    main()
