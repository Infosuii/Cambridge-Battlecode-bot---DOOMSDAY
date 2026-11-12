"""Freeze the user-provided live-source ZIP without modifying any source bytes."""
import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from deep_preflight import input_provenance, save

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--platform-version', type=int, required=True)
    parser.add_argument('--submission-id', required=True)
    parser.add_argument('--study', default='deep-2026-10-28')
    args = parser.parse_args()
    work = ROOT / 'artifacts/local-only' / args.study
    manifest = json.loads((work / 'repository-tree.json').read_text())
    result = input_provenance(manifest, [args.archive])
    row = result['inputs'][0]
    row.update(evidence_label='measured', provided_as_platform_version=args.platform_version,
               submission_id=args.submission_id, provenance='user attachment supplied after request for live v69 archive',
               independent_server_archive_comparison=False,
               attribution_caveat='Platform identity is user-provided and consistent with observed UI; server archive hash unavailable')
    identity = hashlib.sha256()
    for name, meta in sorted(row['files'].items()):
        identity.update(name.encode() + b'\0' + bytes.fromhex(meta['sha256']))
    row['source_tree_sha256'] = identity.hexdigest()
    row['source_tree_hash_definition'] = 'SHA256(sorted UTF8 path + NUL + raw 32-byte file SHA256, concatenated)'
    frozen = ROOT / 'bots' / ('live-' + str(args.platform_version))
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP paths')
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if info.is_dir() or path.is_absolute() or '..' in path.parts or path.parts[0] != 'src':
                raise ValueError('Archive must contain source files under src only')
            if info.file_size > 8 * 1024 * 1024 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unexpected archive entry')
            payload = archive.read(info)
            target = frozen / str(path)
            if target.exists():
                if target.read_bytes() != payload:
                    raise ValueError('Refusing to overwrite different frozen source: ' + str(target))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
    local = ROOT / 'artifacts/local-only/live-src/bot.zip'
    local.parent.mkdir(parents=True, exist_ok=True)
    if local.exists() and local.read_bytes() != args.archive.read_bytes():
        raise ValueError('A different live-src/bot.zip already exists')
    if args.archive.resolve() != local.resolve():
        shutil.copyfile(args.archive, local)
    source_note = f'''# Frozen user-provided live-source reference

Platform version: {args.platform_version}; submission ID: `{args.submission_id}`.
Provided by the user in this analysis session after a request for the live ZIP.
Recorded {datetime.now(timezone.utc).isoformat()}.

Archive SHA-256: `{row['archive_sha256']}`.
Source-tree SHA-256: `{row['source_tree_sha256']}`.
Definition: {row['source_tree_hash_definition']}.
All {row['file_count']} source files are extracted byte-for-byte; no gameplay edits.
Per-file hashes and comparisons: `research/{args.study}/LIVE_SOURCE.json`.

The website showed platform v69 Active/Verified, note "v75 ladder duel candidate",
uploaded by Om. This reference is supplied by the user; its archive hash has not
been independently compared with the server archive because that download was
blocked. Absolute activation time remains separately unverified. Do not equate
repository version labels with platform numbering. Preserve this directory.
'''
    note = frozen / 'SOURCE.md'
    if not note.exists():
        note.write_text(source_note)
    save(ROOT / 'research' / args.study / 'LIVE_SOURCE.json', row)
    best = row['comparisons'][0]
    print(json.dumps({'files':row['file_count'], 'archive_sha256':row['archive_sha256'],
                      'source_tree_sha256':row['source_tree_sha256'], 'best_comparison':best,
                      'frozen':str(frozen.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
