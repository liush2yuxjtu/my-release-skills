// Isolated codec fixtures only. These tests establish no product/model evidence.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createMediaServer } from '../scripts/verify_playback.mjs';

const script = fileURLToPath(new URL('../scripts/verify_playback.mjs', import.meta.url));
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function workspace(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-only-playback-'));
  try { return run(root); } finally { fs.rmSync(root, { recursive: true, force: true }); }
}
function cli(root, input, output = 'receipt', extra = [], environment = {}) {
  const result = spawnSync(process.execPath, [script, input, path.join(root, output), ...extra],
    { cwd: root, env: { ...process.env, PLAYWRIGHT_MODULE_PATH: path.join(root, 'absent-playwright'), ...environment },
      encoding: 'utf8', timeout: 45000, maxBuffer: 1024 ** 2 });
  assert.ifError(result.error);
  assert.equal(result.signal, null, result.stderr);
  return result;
}
function manifest(root, value) {
  const file = path.join(root, 'assets.json');
  fs.writeFileSync(file, JSON.stringify(value));
  return file;
}
function availableRuntime() {
  try {
    const require = createRequire(path.join(process.cwd(), 'package.json'));
    const entry = require.resolve(process.env.PLAYWRIGHT_MODULE_PATH ? path.resolve(process.env.PLAYWRIGHT_MODULE_PATH) : 'playwright');
    const executable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || require(entry).chromium.executablePath();
    if (!fs.existsSync(executable)) return null;
    return { entry, executable };
  } catch { return null; }
}
const runtime = availableRuntime();

test('missing input, malformed JSON and empty/object/oversized scopes fail with a new summary', () => workspace(root => {
  let result = cli(root, path.join(root, 'missing.json'), 'missing');
  assert.equal(result.status, 1);
  assert.equal(readJson(path.join(root, 'missing/summary.json')).pass, false);
  const malformed = path.join(root, 'malformed.json');
  fs.writeFileSync(malformed, '{');
  result = cli(root, malformed, 'malformed');
  assert.equal(result.status, 1);
  assert.equal(readJson(path.join(root, 'malformed/summary.json')).playback_verdict, 'FAIL');
  for (const [index, scope] of [[], {}, Array(33).fill({ path: 'fixture-only.mp4' })].entries()) {
    result = cli(root, manifest(root, scope), `scope-${index}`);
    assert.equal(result.status, 1);
    const summary = readJson(path.join(root, `scope-${index}/summary.json`));
    assert.equal(summary.pass, false);
    assert.equal(summary.assets.length, 0);
    assert.ok(summary.errors.length);
  }
}));

test('omitted CLI arguments fail promptly instead of bypassing scope validation', () => {
  const result = spawnSync(process.execPath, [script], { encoding: 'utf8', timeout: 5000 });
  assert.ifError(result.error);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /"playback_verdict":"FAIL"/);
});

test('existing output and source bytes are never clobbered', () => workspace(root => {
  const source = path.join(root, 'source.mp4');
  fs.writeFileSync(source, 'fixture-only source bytes');
  const output = path.join(root, 'existing');
  fs.mkdirSync(output);
  fs.writeFileSync(path.join(output, 'summary.json'), 'previous failure receipt\n');
  fs.writeFileSync(path.join(output, 'keep'), 'preserve this');
  const result = cli(root, manifest(root, [{ path: source }]), 'existing');
  assert.equal(result.status, 1);
  assert.equal(fs.readFileSync(path.join(output, 'summary.json'), 'utf8'), 'previous failure receipt\n');
  assert.deepEqual(fs.readdirSync(output).sort(), ['keep', 'summary.json']);
  assert.equal(fs.readFileSync(source, 'utf8'), 'fixture-only source bytes');
  assert.equal(cli(root, path.join(root, 'assets.json'), 'source.mp4').status, 1);
  assert.equal(fs.readFileSync(source, 'utf8'), 'fixture-only source bytes');
}));

test('missing optional Playwright leaves per-asset SHA-bound failures and terminates', () => workspace(root => {
  const bytes = Buffer.from('fixture-only bytes; no claim of valid media');
  const source = path.join(root, 'fixture-only.mp4');
  fs.writeFileSync(source, bytes);
  const result = cli(root, manifest(root, [{ path: source }, { path: source }]));
  assert.equal(result.status, 1);
  const summary = readJson(path.join(root, 'receipt/summary.json'));
  assert.equal(summary.pass, false);
  assert.equal(summary.assets.length, 2);
  assert.equal(summary.errors[0].code, 'BROWSER_SETUP_FAILED');
  for (const id of ['asset-1', 'asset-2']) {
    const receipt = readJson(path.join(root, `receipt/${id}.json`));
    assert.equal(receipt.pass, false);
    assert.equal(receipt.source.sha256_before, sha(bytes));
    assert.equal(receipt.source.sha256_after, sha(bytes));
    assert.equal(receipt.source.unchanged, true);
    assert.equal(receipt.playback, null);
    assert.equal(receipt.visual_verdict, 'pending');
    assert.equal(receipt.audio_verdict, 'pending');
    assert.equal(receipt.model_verdict, 'not-evaluated');
    assert.equal(receipt.errors[0].code, 'BROWSER_SETUP_FAILED');
  }
  assert.deepEqual(fs.readFileSync(source), bytes);
}));

test('every malformed or missing selected entry gets a failure receipt', () => workspace(root => {
  const result = cli(root, manifest(root, [null, {}, { path: 'missing.mp4' }, { path: '', sha256: 42 }]));
  assert.equal(result.status, 1);
  const summary = readJson(path.join(root, 'receipt/summary.json'));
  assert.equal(summary.assets.length, 4);
  for (let index = 1; index <= 4; index++) {
    const receipt = readJson(path.join(root, `receipt/asset-${index}.json`));
    assert.equal(receipt.pass, false);
    assert.ok(receipt.errors.length);
  }
}));

test('a declared SHA mismatch remains a failure even when source bytes stay unchanged', () => workspace(root => {
  const source = path.join(root, 'fixture-only.mp4');
  fs.writeFileSync(source, 'fixture-only source bytes');
  const result = cli(root, manifest(root, [{ path: source, sha256: '0'.repeat(64) }]));
  assert.equal(result.status, 1);
  const receipt = readJson(path.join(root, 'receipt/asset-1.json'));
  assert.equal(receipt.pass, false);
  assert.equal(receipt.source.unchanged, true);
  assert.match(receipt.errors[0].message, /declared SHA-256/);
}));

test('selected-media server handles Range and HEAD and exposes no directory', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-only-ranges-'));
  const file = path.join(root, 'selected.mp4');
  fs.writeFileSync(file, '0123456789');
  fs.writeFileSync(path.join(root, 'unselected-secret.txt'), 'must not be served');
  const fd = fs.openSync(file, 'r');
  let server;
  try {
    server = await createMediaServer(fd, 10);
    const full = await fetch(server.mediaUrl);
    assert.equal(full.status, 200);
    assert.equal(await full.text(), '0123456789');
    for (const [range, body, contentRange] of [['bytes=2-5', '2345', 'bytes 2-5/10'],
      ['bytes=7-', '789', 'bytes 7-9/10'], ['bytes=-3', '789', 'bytes 7-9/10']]) {
      const response = await fetch(server.mediaUrl, { headers: { Range: range } });
      assert.equal(response.status, 206);
      assert.equal(response.headers.get('content-range'), contentRange);
      assert.equal(await response.text(), body);
    }
    const head = await fetch(server.mediaUrl, { method: 'HEAD', headers: { Range: 'bytes=2-5' } });
    assert.equal(head.status, 206);
    assert.equal(head.headers.get('content-length'), '4');
    assert.equal(await head.text(), '');
    for (const range of ['bytes=10-', 'bytes=5-2', 'bytes=-0', 'bytes=0-1,4-5', 'nonsense', 'bytes=9007199254740992-']) {
      const response = await fetch(server.mediaUrl, { headers: { Range: range } });
      assert.equal(response.status, 416, range);
      assert.equal(response.headers.get('content-range'), 'bytes */10');
      await response.arrayBuffer();
    }
    for (const target of ['/', '/unselected-secret.txt', '/%2e%2e/unselected-secret.txt', new URL(server.mediaUrl).pathname + '?other=1']) {
      const response = await fetch(new URL(target, server.mediaUrl));
      assert.equal(response.status, 404, target);
      await response.arrayBuffer();
    }
    const post = await fetch(server.mediaUrl, { method: 'POST' });
    assert.equal(post.status, 405);
    await post.arrayBuffer();
    const url = server.mediaUrl;
    await server.close();
    server = null;
    await assert.rejects(fetch(url));
    assert.equal(fs.readFileSync(fd, 'utf8'), '0123456789');
  } finally { if (server) await server.close(); fs.closeSync(fd); fs.rmSync(root, { recursive: true, force: true }); }
});

test('missing explicit browser leaves failure receipts without a listening server', { skip: !runtime }, () => workspace(root => {
  const source = path.join(root, 'fixture-only.mp4');
  fs.writeFileSync(source, 'fixture-only bytes');
  const result = cli(root, manifest(root, [{ path: source }]), 'receipt', [], {
    PLAYWRIGHT_MODULE_PATH: runtime.entry, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH: path.join(root, 'absent-chromium') });
  assert.equal(result.status, 1);
  assert.equal(readJson(path.join(root, 'receipt/summary.json')).errors[0].code, 'BROWSER_SETUP_FAILED');
  assert.equal(readJson(path.join(root, 'receipt/asset-1.json')).source.unchanged, true);
}));

test('an executable that cannot launch Chromium still leaves all failure receipts', { skip: !runtime }, () => workspace(root => {
  const source = path.join(root, 'fixture-only.mp4');
  fs.writeFileSync(source, 'fixture-only bytes');
  const result = cli(root, manifest(root, [{ path: source }]), 'receipt', [], {
    PLAYWRIGHT_MODULE_PATH: runtime.entry, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH: process.execPath });
  assert.equal(result.status, 1);
  assert.equal(readJson(path.join(root, 'receipt/summary.json')).errors[0].code, 'BROWSER_SETUP_FAILED');
  assert.equal(readJson(path.join(root, 'receipt/asset-1.json')).source.unchanged, true);
}));

test('actual Chromium plays a motion codec fixture at 1x through ended with separate pending verdicts',
  { skip: !runtime || spawnSync('ffmpeg', ['-version']).status !== 0 }, () => workspace(root => {
    const source = path.join(root, 'fixture-only.mp4');
    const generated = spawnSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=160x100:rate=30:duration=1.2',
      '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', source], { encoding: 'utf8', timeout: 15000 });
    assert.equal(generated.status, 0, generated.stderr);
    const before = fs.readFileSync(source);
    const result = cli(root, manifest(root, [{ path: source, sha256: sha(before) }]), 'receipt', ['--timeout-ms', '10000'], {
      PLAYWRIGHT_MODULE_PATH: runtime.entry, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH: runtime.executable });
    assert.equal(result.status, 0, result.stderr + '\n' + fs.readFileSync(path.join(root, 'receipt/summary.json'), 'utf8'));
    const summary = readJson(path.join(root, 'receipt/summary.json'));
    const receipt = readJson(path.join(root, 'receipt/asset-1.json'));
    assert.equal(summary.pass, true);
    assert.equal(summary.browser_closed, true);
    assert.equal(receipt.pass, true);
    assert.equal(receipt.playback.ended, true);
    assert.equal(receipt.playback.playback_rate, 1);
    assert.equal(receipt.playback.seeking_events, 0);
    assert.ok(receipt.playback.wall_ms >= 1080);
    assert.ok(receipt.playback.total_frames > 0);
    assert.ok(receipt.playback.decoded_frames > 0);
    assert.equal(typeof receipt.playback.dropped_frames, 'number');
    assert.equal(receipt.source.sha256_before, sha(before));
    assert.equal(receipt.source.sha256_after, sha(before));
    assert.equal(receipt.source.unchanged, true);
    assert.equal(receipt.visual_verdict, 'pending');
    assert.equal(receipt.audio_verdict, 'pending');
    assert.equal(receipt.model_verdict, 'not-evaluated');
    assert.equal(receipt.browser.version, summary.browser.version);
    assert.match(receipt.browser.actual_executable.sha256, /^[a-f0-9]{64}$/);
    assert.ok(fs.existsSync(receipt.browser.actual_executable.path));
    assert.ok(receipt.media_requests.some(request => request.status === 206));
    assert.deepEqual(fs.readFileSync(source), before);
  }));
