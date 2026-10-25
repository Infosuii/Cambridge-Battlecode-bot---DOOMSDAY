// Minimal NumPy .npy/.npz writer (deflate zip, non-zip64) and a deterministic row-shard writer.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const DESCR = { Int8Array: '|i1', Uint8Array: '|u1', Int16Array: '<i2', Int32Array: '<i4', Uint32Array: '<u4',
                Float32Array: '<f4', BigInt64Array: '<i8' };

export function npy(array, shape) {
  let header = `{'descr': '${DESCR[array.constructor.name]}', 'fortran_order': False, 'shape': (${shape.join(', ')}${shape.length === 1 ? ',' : ''}), }`;
  header += ' '.repeat((64 - ((10 + header.length + 1) % 64)) % 64) + '\n';
  const prefix = Buffer.alloc(10);
  prefix.write('\x93NUMPY', 'latin1'); prefix[6] = 1; prefix[7] = 0; prefix.writeUInt16LE(header.length, 8);
  return Buffer.concat([prefix, Buffer.from(header, 'latin1'), Buffer.from(array.buffer, array.byteOffset, array.byteLength)]);
}

export function zip(entries) {
  const parts = [], central = []; let offset = 0;
  for (const { name, data } of entries) {
    const packed = zlib.deflateRawSync(data, { level: 6 }), crc = zlib.crc32(data), nameBytes = Buffer.from(name);
    if (data.length >= 0xFFFFFFFF || offset >= 0xFFFFFFFF) throw new Error('shard too large for a non-zip64 archive');
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4); local.writeUInt16LE(8, 8); local.writeUInt16LE(0x21, 12);
    local.writeUInt32LE(crc, 14); local.writeUInt32LE(packed.length, 18); local.writeUInt32LE(data.length, 22); local.writeUInt16LE(nameBytes.length, 26);
    const entry = Buffer.alloc(46);
    entry.writeUInt32LE(0x02014b50, 0); entry.writeUInt16LE(20, 4); entry.writeUInt16LE(20, 6); entry.writeUInt16LE(8, 10); entry.writeUInt16LE(0x21, 14);
    entry.writeUInt32LE(crc, 16); entry.writeUInt32LE(packed.length, 20); entry.writeUInt32LE(data.length, 24); entry.writeUInt16LE(nameBytes.length, 28);
    entry.writeUInt32LE(offset, 42);
    parts.push(local, nameBytes, packed); central.push(entry, nameBytes);
    offset += local.length + nameBytes.length + packed.length;
  }
  const directory = Buffer.concat(central), end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(directory.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...parts, directory, end]);
}

function writeAtomic(file, data) { fs.writeFileSync(file + '.partial', data); fs.renameSync(file + '.partial', file); }

// Rows from several replays, concatenated per array in sorted input order. Each replay result is
// { entry: {...sidecar fields, ok}, rows: n, arrays: { key: TypedArray of n * width } } with fixed widths per key.
export class RowShardWriter {
  constructor(outDir, files, { shardSize, widths, format, run }) {
    if (fs.existsSync(outDir)) throw new Error('fresh shard output directory required: ' + outDir);
    fs.mkdirSync(outDir, { recursive: true });
    Object.assign(this, { outDir, files, shardSize, widths, format, run, pending: new Map(), shards: [], passed: 0, failed: 0, rows: 0 });
  }

  add(index, result) {
    const shard = Math.floor(index / this.shardSize);
    if (!this.pending.has(shard)) this.pending.set(shard, new Map());
    const items = this.pending.get(shard);
    items.set(index, result);
    if (result.entry.ok) this.passed++; else this.failed++;
    if (items.size === Math.min(this.shardSize, this.files.length - shard * this.shardSize)) { this.write(shard, items); this.pending.delete(shard); }
  }

  write(shard, items) {
    const ordered = [...items.keys()].sort((a, b) => a - b).map(i => items.get(i));
    const ok = ordered.filter(r => r.entry.ok && r.rows > 0);
    const n = ok.reduce((s, r) => s + r.rows, 0);
    const entries = [];
    for (const [key, { width, type }] of Object.entries(this.widths)) {
      const out = new type(n * width); let at = 0;
      for (const r of ok) { out.set(r.arrays[key], at); at += r.arrays[key].length; }
      if (at !== out.length) throw new Error(`row width mismatch for ${key}`);
      entries.push({ name: key + '.npy', data: npy(out, width === 1 ? [n] : [n, width]) });
    }
    const replayRow = new Int32Array(n); let at = 0;
    ok.forEach((r, i) => { replayRow.fill(i, at, at + r.rows); at += r.rows; });
    entries.push({ name: 'replay_row.npy', data: npy(replayRow, [n]) });
    const name = `shard-${String(shard).padStart(5, '0')}`, archive = zip(entries);
    writeAtomic(path.join(this.outDir, name + '.npz'), archive);
    writeAtomic(path.join(this.outDir, name + '.json'), JSON.stringify({ format: this.format, shard,
      replays: ok.map(r => r.entry), empty_or_failed: ordered.filter(r => !(r.entry.ok && r.rows > 0)).map(r => r.entry) }));
    this.rows += n;
    this.shards.push({ npz: name + '.npz', json: name + '.json', replays: ok.length, rows: n, bytes: archive.length,
                       sha256: crypto.createHash('sha256').update(archive).digest('hex') });
  }

  finish() {
    if (this.pending.size) throw new Error('incomplete shards: ' + [...this.pending.keys()].join(','));
    this.shards.sort((a, b) => a.npz.localeCompare(b.npz));
    const manifest = { format: this.format, ...this.run, shard_size: this.shardSize, replays: this.files.length, passed: this.passed,
      failed: this.failed, rows: this.rows, bytes: this.shards.reduce((s, x) => s + x.bytes, 0), shards: this.shards,
      widths: Object.fromEntries(Object.entries(this.widths).map(([k, v]) => [k, v.width])) };
    writeAtomic(path.join(this.outDir, 'manifest.json'), JSON.stringify(manifest, null, 1) + '\n');
    return manifest;
  }
}
