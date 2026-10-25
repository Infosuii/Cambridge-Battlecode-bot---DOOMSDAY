// Shared loader for the official engine wasm and snapshot decoders shipped with the local cambc visualiser.
// Assets are used in place and pinned by SHA-256; nothing third-party is copied into this repository.
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const PINNED = {
  'v1_0_3-DRqNt1t2.wasm': '029ecd290dc400e75418178ec386d72cbd7d9f2fc2a2e451bf594ca23566df48',
  'PanelChrome-BXlTYAwV.js': '960affde6198366d2347bd21f43efec5bc06acc6cb0c53e5f7f96dbf87f027e6',
  'rolldown-runtime-hePW80VL.js': '580ad8c58061a4dde99bde0a56905e382f0568516ee2f5b84dbfb52085709021',
};

export function defaultAssets() {
  const root = path.join(os.homedir(), 'AppData/Local/cambc/assets');
  for (const d of fs.existsSync(root) ? fs.readdirSync(root) : []) {
    const p = path.join(root, d, 'visualiser/assets');
    if (fs.existsSync(path.join(p, 'v1_0_3-DRqNt1t2.wasm'))) return p;
  }
  throw new Error('cambc visualiser assets not found; pass --assets');
}

export function verifyAssets(dir) {
  for (const [name, digest] of Object.entries(PINNED)) {
    const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(dir, name))).digest('hex');
    if (actual !== digest) throw new Error(`pinned asset changed: ${name} ${actual}`);
  }
}

// One engine instance with scratch buffers and helpers for replay loading and perspective API calls.
export async function engine(dir) {
  const PC = await import(pathToFileURL(path.join(dir, 'PanelChrome-BXlTYAwV.js')).href);
  let X;
  const dv = () => new DataView(X.memory.buffer);
  const cstr = (p) => { if (!p) return ''; const b = new Uint8Array(X.memory.buffer); let e = p; while (b[e]) e++; return new TextDecoder().decode(b.subarray(p, e)); };
  // Minimal WASI matching the visualiser's own shim: no files, no environment, stdout/stderr discarded.
  const wasi = {
    random_get(p, n) { crypto.getRandomValues(new Uint8Array(X.memory.buffer, p, n)); return 0; },
    clock_time_get(id, prec, out) { dv().setBigUint64(out, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get(a, b) { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; }, environ_get() { return 0; },
    fd_close(fd) { return fd <= 2 ? 0 : 8; },
    fd_fdstat_get(fd, p) { if (fd > 2) return 8; const d = dv(); d.setUint8(p, 2); d.setUint16(p + 2, 0, true); d.setBigUint64(p + 8, 0n, true); d.setBigUint64(p + 16, 0n, true); return 0; },
    fd_prestat_get() { return 8; }, fd_prestat_dir_name() { return 8; },
    fd_read(fd, iov, n, out) { if (fd) return 8; dv().setUint32(out, 0, true); return 0; }, fd_seek(fd) { return fd <= 2 ? 70 : 8; },
    fd_write(fd, iov, n, out) { const d = dv(); let c = 0; for (let i = 0; i < n; i++) c += d.getUint32(iov + i * 8 + 4, true); d.setUint32(out, c, true); return 0; },
    proc_exit(c) { throw new Error('wasm exit ' + c); },
  };
  const { instance } = await WebAssembly.instantiate(fs.readFileSync(path.join(dir, 'v1_0_3-DRqNt1t2.wasm')),
    { wasi_snapshot_preview1: wasi, deep_wasm: { on_assert_fail_impl() { return 1; } } });
  X = instance.exports; X._initialize();
  const E = { X, PC, dv, cstr, h: undefined };
  E.check = (rc) => { if (rc !== 0) throw new Error(`engine error ${rc}: ${cstr(X.GetLastErrorMsg())}`); };
  E.out = X.Engine_Malloc(64); E.args = X.Engine_Malloc(256); E.buf = X.Engine_Malloc(4096);
  E.tsize = X.Game_Visualiser_TimelineSnapshotSize();
  E.snap = X.Engine_Malloc(X.Game_Visualiser_SnapshotSize()); E.tsnap = X.Engine_Malloc(E.tsize);
  E.perspective = (team, champion) => { const q = E.args + 48; dv().setUint32(q, team, true); dv().setUint32(q + 4, champion, true); return q; };
  E.load = (bytes) => {
    const p = X.Engine_Malloc(bytes.length);
    new Uint8Array(X.memory.buffer, p, bytes.length).set(bytes);
    try { E.check(X.Game_FromReplayFileBytes(p, bytes.length, E.out)); } finally { X.Engine_Free(p); }
    E.h = dv().getBigUint64(E.out, true);
  };
  E.destroy = () => { if (E.h !== undefined) X.Game_Destroy(E.h); E.h = undefined; };
  return E;
}
