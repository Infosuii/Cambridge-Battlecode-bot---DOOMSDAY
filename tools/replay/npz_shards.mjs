// Compact replay shards: standard NumPy .npz files (a zip of deflate-compressed .npy arrays, readable by numpy.load)
// plus a small JSON sidecar per shard and one run manifest. Format `replay-shard-v1`:
//
//   meta                 int64   (R, 11)  META_COLUMNS, one row per decoded replay (sidecar `replays[i]` names row i)
//   action_offsets       int64   (R+1,)   replay r's actions are actions[action_offsets[r]:action_offsets[r+1]]
//   actions              int16   (N, 8)   [round, champion, kind, fromX, fromY, toX, toY, abilitySlot]
//   champion_offsets     int64   (R+1,)
//   final_champions      int32   (C, 6)   [index, team, type, gold, gems, kills] at the end of the replay
// With --perspective (turn = the engine awaiting a champion's input; the view is that champion's own fog-limited view):
//   turn_offsets         int64   (R+1,)
//   turns                int32   (T, 3)   [round, champion, action_index]  (action_index is within the replay)
//   cooldowns            int32   (T, 2)   acting champion's ability cooldowns; -1 unknown, -2 champion absent from view
//   view_champion_offsets int64  (T+1,)   offsets into view_champions, shard-global
//   view_champions       float32 (V, 10)  [index, team, type, x, y, health, maxHealth, gems, gold, alive]; NaN = unknown
//   view_camp_offsets    int64   (T+1,)
//   view_camps           float32 (W, 5)   [index, type, x, y, health]; NaN = unknown
//
// Values are engine float32s or small integers, so this is lossless with respect to the JSONL rows. Replays are
// assigned to shards in sorted input order, so shard contents do not depend on the worker count or completion order.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

export const SHARD_FORMAT = 'replay-shard-v1';
export const META_COLUMNS = ['width', 'height', 'steps', 'inputs', 'timeline_size', 'rounds', 'outcome', 'submitted_gems_a',
                             'submitted_gems_b', 'fuel_exhausted_turns', 'error_turns'];
const ACTION_COLUMNS = 8, CHAMPION_COLUMNS = 6, TURN_COLUMNS = 3, VIEW_CHAMPION_COLUMNS = 10, VIEW_CAMP_COLUMNS = 5;
const DESCR = { Int16Array: '<i2', Int32Array: '<i4', Float32Array: '<f4', BigInt64Array: '<i8' };

function npy(array, shape) {
  let header = `{'descr': '${DESCR[array.constructor.name]}', 'fortran_order': False, 'shape': (${shape.join(', ')}${shape.length === 1 ? ',' : ''}), }`;
  header += ' '.repeat((64 - ((10 + header.length + 1) % 64)) % 64) + '\n';
  const prefix = Buffer.alloc(10);
  prefix.write('\x93NUMPY', 'latin1'); prefix[6] = 1; prefix[7] = 0; prefix.writeUInt16LE(header.length, 8);
  return Buffer.concat([prefix, Buffer.from(header, 'latin1'), Buffer.from(array.buffer, array.byteOffset, array.byteLength)]);
}

function zip(entries) {
  // Plain (non-zip64) deflate archive; shards are kept far below 4 GiB.
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

const unknown = (v) => (v === null || v === undefined ? NaN : v);

// Runs in the worker: one decoded JSONL-shaped row -> typed arrays (transferable) plus its sidecar entry.
export function pack(row) {
  if (!row.ok) return { entry: { replay: row.replay, ok: false, error: row.error }, arrays: null };
  const actions = new Int16Array(row.actions.length * ACTION_COLUMNS);
  row.actions.forEach((a, i) => a.forEach((v, j) => {
    if (!Number.isInteger(v) || v < -32768 || v > 32767) throw new Error(`action field outside int16: ${row.replay} ${v}`);
    actions[i * ACTION_COLUMNS + j] = v;
  }));
  const meta = BigInt64Array.from([row.width, row.height, row.steps, row.inputs, row.timeline_size, row.rounds, row.outcome,
    row.submitted_gems[0], row.submitted_gems[1], row.fuel_exhausted_turns, row.error_turns].map(v => BigInt(v)));
  const champions = Int32Array.from(row.champions.flatMap(c => [c.index, c.team, c.type, c.gold, c.gems, c.kills]));
  const arrays = { meta, actions, champions };
  if (row.turns) {
    const T = row.turns.length;
    arrays.turns = Int32Array.from(row.turns.flatMap(t => [t.round, t.champion, t.action_index]));
    arrays.cooldowns = Int32Array.from(row.turns.flatMap(t => t.view.cooldowns === null ? [-2, -2] : t.view.cooldowns.map(c => c ?? -1)));
    arrays.view_champion_counts = Int32Array.from(row.turns.map(t => t.view.champions.length));
    arrays.view_champions = Float32Array.from(row.turns.flatMap(t => t.view.champions.flatMap(c => c.map(unknown))));
    arrays.view_camp_counts = Int32Array.from(row.turns.map(t => t.view.camps.length));
    arrays.view_camps = Float32Array.from(row.turns.flatMap(t => t.view.camps.flatMap(c => c.map(unknown))));
    if (arrays.turns.length !== T * TURN_COLUMNS) throw new Error('turn packing mismatch');
  }
  return { entry: { replay: row.replay, ok: true, ms: row.ms, summary_check: row.summary_check }, arrays };
}

export const transferables = (packed) => packed.arrays ? Object.values(packed.arrays).map(a => a.buffer) : [];

function concat(Type, parts) {
  const out = new Type(parts.reduce((n, p) => n + p.length, 0)); let at = 0;
  for (const p of parts) { out.set(p, at); at += p.length; }
  return out;
}

function offsets(counts) {
  const out = new BigInt64Array(counts.length + 1);
  counts.forEach((c, i) => { out[i + 1] = out[i] + BigInt(c); });
  return out;
}

function writeAtomic(file, data) {
  const temporary = file + '.partial';
  fs.writeFileSync(temporary, data); fs.renameSync(temporary, file);
}

export class ShardWriter {
  constructor(outDir, files, { shardSize, perspective, run }) {
    if (fs.existsSync(outDir)) throw new Error('fresh shard output directory required: ' + outDir);
    fs.mkdirSync(outDir, { recursive: true });
    Object.assign(this, { outDir, files, shardSize, perspective, run, pending: new Map(), shards: [], passed: 0, failed: 0 });
  }

  add(index, packed) {
    const shard = Math.floor(index / this.shardSize);
    if (!this.pending.has(shard)) this.pending.set(shard, new Map());
    const rows = this.pending.get(shard);
    rows.set(index, packed);
    if (packed.entry.ok && packed.entry.summary_check?.passed !== false) this.passed++; else this.failed++;
    const size = Math.min(this.shardSize, this.files.length - shard * this.shardSize);
    if (rows.size === size) { this.write(shard, rows); this.pending.delete(shard); }
  }

  write(shard, rows) {
    const ordered = [...rows.keys()].sort((a, b) => a - b).map(i => rows.get(i));
    const decoded = ordered.filter(p => p.arrays), A = decoded.map(p => p.arrays);
    const entries = [
      ['meta', concat(BigInt64Array, A.map(a => a.meta)), [A.length, META_COLUMNS.length]],
      ['action_offsets', offsets(A.map(a => a.actions.length / ACTION_COLUMNS)), [A.length + 1]],
      ['actions', concat(Int16Array, A.map(a => a.actions)), [A.reduce((n, a) => n + a.actions.length / ACTION_COLUMNS, 0), ACTION_COLUMNS]],
      ['champion_offsets', offsets(A.map(a => a.champions.length / CHAMPION_COLUMNS)), [A.length + 1]],
      ['final_champions', concat(Int32Array, A.map(a => a.champions)), [A.reduce((n, a) => n + a.champions.length / CHAMPION_COLUMNS, 0), CHAMPION_COLUMNS]],
    ];
    if (this.perspective) {
      const championCounts = concat(Int32Array, A.map(a => a.view_champion_counts)), campCounts = concat(Int32Array, A.map(a => a.view_camp_counts));
      const T = championCounts.length;
      entries.push(
        ['turn_offsets', offsets(A.map(a => a.turns.length / TURN_COLUMNS)), [A.length + 1]],
        ['turns', concat(Int32Array, A.map(a => a.turns)), [T, TURN_COLUMNS]],
        ['cooldowns', concat(Int32Array, A.map(a => a.cooldowns)), [T, 2]],
        ['view_champion_offsets', offsets([...championCounts]), [T + 1]],
        ['view_champions', concat(Float32Array, A.map(a => a.view_champions)), [championCounts.reduce((n, c) => n + c, 0), VIEW_CHAMPION_COLUMNS]],
        ['view_camp_offsets', offsets([...campCounts]), [T + 1]],
        ['view_camps', concat(Float32Array, A.map(a => a.view_camps)), [campCounts.reduce((n, c) => n + c, 0), VIEW_CAMP_COLUMNS]]);
    }
    const name = `shard-${String(shard).padStart(5, '0')}`;
    const archive = zip(entries.map(([key, array, shape]) => ({ name: key + '.npy', data: npy(array, shape) })));
    writeAtomic(path.join(this.outDir, name + '.npz'), archive);
    let row = 0;
    const sidecar = { format: SHARD_FORMAT, shard, meta_columns: META_COLUMNS, perspective: this.perspective,
      replays: ordered.filter(p => p.entry.ok).map(p => ({ ...p.entry, row: row++ })),
      failed: ordered.filter(p => !p.entry.ok).map(p => p.entry) };
    writeAtomic(path.join(this.outDir, name + '.json'), JSON.stringify(sidecar));
    this.shards.push({ npz: name + '.npz', json: name + '.json', replays: decoded.length, failed: ordered.length - decoded.length,
                       bytes: archive.length, sha256: crypto.createHash('sha256').update(archive).digest('hex') });
  }

  finish() {
    if (this.pending.size) throw new Error('incomplete shards: ' + [...this.pending.keys()].join(','));
    this.shards.sort((a, b) => a.npz.localeCompare(b.npz));
    const manifest = { format: SHARD_FORMAT, ...this.run, shard_size: this.shardSize, perspective: this.perspective,
      replays: this.files.length, passed: this.passed, failed: this.failed, bytes: this.shards.reduce((n, s) => n + s.bytes, 0),
      shards: this.shards };
    writeAtomic(path.join(this.outDir, 'manifest.json'), JSON.stringify(manifest, null, 1) + '\n');
    return manifest;
  }
}
