// File-only Chromium playback. Receipts are private QA, never visual/model evidence.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { execFile } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const SCHEMA = 'delivered-playback/v2';
const MAX_ASSETS = 32;
const MAX_MEDIA_BYTES = 2 * 1024 ** 3;
const SETUP_TIMEOUT_MS = 15000;
const USAGE = 'node verify_playback.mjs assets.json NEW_OUTPUT_DIRECTORY [--playwright-module PATH] [--timeout-ms 180000]';
const pending = { visual_verdict: 'pending', audio_verdict: 'pending', model_verdict: 'not-evaluated' };

function failure(code, message) { return { code, message: String(message).slice(0, 2000) }; }
function writeJson(file, value) {
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
}
function deadline(promise, milliseconds, label) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => {
    timer = setTimeout(() => reject(Error(`${label} exceeded ${milliseconds} ms`)), milliseconds);
  })]).finally(() => clearTimeout(timer));
}
function command(file, args, timeout = SETUP_TIMEOUT_MS) {
  return new Promise((resolve, reject) => execFile(file, args, { timeout, maxBuffer: 1024 ** 2 },
    (error, stdout, stderr) => error ? reject(Error(`${path.basename(file)} failed: ${stderr || error.message}`)) : resolve(stdout.trim())));
}
function metadata(stat) {
  return Object.fromEntries(['dev', 'ino', 'size', 'mode', 'mtimeNs', 'ctimeNs'].map(key => [key, stat[key].toString()]));
}
function sameMetadata(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function streamFd(fd, start, end) {
  // destroy() can close a supplied fd even with autoClose:false. This stream has
  // no ownership of the immutable source descriptor; its caller closes it once.
  return fs.createReadStream(null, { fd, autoClose: false, start, ...(end === undefined ? {} : { end }),
    fs: { read: fs.read, close: (_fd, callback) => callback(null) } });
}
async function digestFd(fd) {
  const hash = crypto.createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 ** 2);
  const limit = Date.now() + 30000;
  const size = fs.fstatSync(fd).size;
  if (size > MAX_MEDIA_BYTES) throw Error('Hash input exceeds 2 GiB bound');
  let position = 0;
  while (position < size) {
    if (Date.now() > limit) throw Error('Hashing exceeded 30000 ms');
    const count = fs.readSync(fd, buffer, 0, Math.min(buffer.length, size - position), position);
    if (!count) throw Error('Source truncated while hashing');
    hash.update(buffer.subarray(0, count));
    position += count;
    if (position % (16 * 1024 ** 2) === 0) await new Promise(resolve => setImmediate(resolve));
  }
  return hash.digest('hex');
}
async function executableIdentity(file) {
  const actualPath = fs.realpathSync(file);
  fs.accessSync(actualPath, fs.constants.X_OK);
  const fd = fs.openSync(actualPath, fs.constants.O_RDONLY);
  try {
    const before = metadata(fs.fstatSync(fd, { bigint: true }));
    const sha256 = await digestFd(fd);
    if (!sameMetadata(before, metadata(fs.fstatSync(fd, { bigint: true })))) throw Error('Browser executable changed while hashing');
    return { path: actualPath, sha256, metadata: before };
  } finally { fs.closeSync(fd); }
}

// Reject malformed/multiple ranges rather than silently serving different bytes.
export function parseByteRange(header, size) {
  if (header === undefined) return { start: 0, end: size - 1, partial: false };
  if (typeof header !== 'string') return null;
  const match = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!match || (!match[1] && !match[2])) return null;
  const first = match[1] ? Number(match[1]) : null;
  const last = match[2] ? Number(match[2]) : null;
  if ((first !== null && !Number.isSafeInteger(first)) || (last !== null && !Number.isSafeInteger(last))) return null;
  const start = first === null ? Math.max(0, size - last) : first;
  const end = first === null || last === null ? size - 1 : Math.min(last, size - 1);
  if (size <= 0 || last === 0 && first === null || start > end || start >= size) return null;
  return { start, end, partial: true };
}

// One already-opened selected file; no path decoding, directory root or external URL.
export async function createMediaServer(fd, size) {
  const token = crypto.randomBytes(18).toString('hex');
  const mediaPath = `/${token}/media.mp4`;
  const playerPath = `/${token}/player.html`;
  const requests = [];
  const sockets = new Set();
  const streams = new Set();
  const server = http.createServer((req, res) => {
    if (req.url !== mediaPath && req.url !== playerPath) { res.writeHead(404).end(); return; }
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405, { Allow: 'GET, HEAD' }).end(); return; }
    if (req.url === playerPath) {
      const html = '<!doctype html><meta charset="utf-8"><title>Media playback</title><video id="media" muted controls playsinline preload="metadata"></video>';
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': Buffer.byteLength(html),
        'Cache-Control': 'no-store', 'Content-Security-Policy': "default-src 'none'; media-src 'self'" });
      res.end(req.method === 'HEAD' ? undefined : html);
      return;
    }
    const range = parseByteRange(req.headers.range, size);
    if (!range) { res.writeHead(416, { 'Content-Range': `bytes */${size}` }).end(); return; }
    const { start, end, partial } = range;
    if (requests.length < 256) requests.push({ method: req.method, status: partial ? 206 : 200, start, end });
    res.writeHead(partial ? 206 : 200, { 'Content-Type': 'video/mp4', 'Content-Length': end - start + 1,
      'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
      ...(partial ? { 'Content-Range': `bytes ${start}-${end}/${size}` } : {}) });
    if (req.method === 'HEAD') { res.end(); return; }
    const stream = streamFd(fd, start, end);
    streams.add(stream);
    stream.once('close', () => streams.delete(stream));
    stream.on('error', () => res.destroy());
    res.on('close', () => stream.destroy());
    stream.pipe(res);
  });
  server.requestTimeout = 15000;
  server.headersTimeout = 10000;
  server.keepAliveTimeout = 1000;
  server.on('connection', socket => { sockets.add(socket); socket.on('close', () => sockets.delete(socket)); });
  try {
    await deadline(new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    }), 5000, 'Loopback server startup');
  } catch (error) { server.close(); for (const socket of sockets) socket.destroy(); throw error; }
  const base = `http://127.0.0.1:${server.address().port}`;
  return { mediaUrl: base + mediaPath, playerUrl: base + playerPath, requests,
    async close() {
      const closed = new Promise(resolve => server.close(resolve));
      const drained = Array.from(streams, stream => new Promise(resolve => {
        stream.once('close', resolve);
        stream.destroy();
      }));
      for (const socket of sockets) socket.destroy();
      await deadline(Promise.all([closed, ...drained]), 3000, 'Loopback server close');
    } };
}

function parseArgs(argv, environment) {
  const options = { input: argv[0], output: argv[1], timeoutMs: 180000,
    modulePath: environment.PLAYWRIGHT_MODULE_PATH || null,
    executablePath: environment.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || null };
  if (!options.input || !options.output || options.input.startsWith('--') || options.output.startsWith('--')) throw Error(USAGE);
  for (let i = 2; i < argv.length; i += 2) {
    if (!argv[i + 1]) throw Error(`Missing value for ${argv[i]}`);
    if (argv[i] === '--playwright-module') options.modulePath = argv[i + 1];
    else if (argv[i] === '--timeout-ms') options.timeoutMs = Number(argv[i + 1]);
    else throw Error(`Unknown option ${argv[i]}`);
  }
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1000 || options.timeoutMs > 600000) {
    throw Error('--timeout-ms must be an integer from 1000 to 600000');
  }
  return options;
}
function packageIdentity(entry) {
  let directory = path.dirname(entry);
  while (true) {
    const candidate = path.join(directory, 'package.json');
    if (fs.existsSync(candidate)) {
      const info = JSON.parse(fs.readFileSync(candidate, 'utf8'));
      if (['playwright', 'playwright-core'].includes(info.name) && typeof info.version === 'string') {
        return { name: info.name, version: info.version, entry };
      }
    }
    const parent = path.dirname(directory);
    if (parent === directory) throw Error('Resolved module is not an identifiable Playwright package');
    directory = parent;
  }
}
async function launchBrowser(options, summary) {
  const require = createRequire(path.join(process.cwd(), 'package.json'));
  const entry = require.resolve(options.modulePath ? path.resolve(options.modulePath) : 'playwright');
  summary.playwright = packageIdentity(entry);
  const { chromium } = require(entry);
  if (!chromium?.launch || !chromium?.executablePath) throw Error('Playwright Chromium API unavailable');
  summary.browser = { headless: true, isolated_contexts: true, custom_launch_arguments: [],
    executable_selection: options.executablePath ? 'explicit' : 'playwright-default',
    launcher: await executableIdentity(options.executablePath || chromium.executablePath()) };
  const browser = await chromium.launch({ headless: true, timeout: SETUP_TIMEOUT_MS,
    ...(options.executablePath ? { executablePath: options.executablePath } : {}) });
  try {
    const session = await deadline(browser.newBrowserCDPSession(), SETUP_TIMEOUT_MS, 'Browser identity session');
    try {
      const version = await deadline(session.send('Browser.getVersion'), SETUP_TIMEOUT_MS, 'Browser version');
      let actualExecutable;
      try {
        const { arguments: arguments_ } = await deadline(session.send('Browser.getBrowserCommandLine'), SETUP_TIMEOUT_MS, 'Browser executable identity');
        if (arguments_?.[0] && path.isAbsolute(arguments_[0])) actualExecutable = arguments_[0];
        summary.browser.executable_identity_method = 'cdp-browser-command-line';
      } catch { /* Some Chromium builds omit --enable-automation. Do not add it just for this check. */ }
      if (!actualExecutable) {
        const info = await deadline(session.send('SystemInfo.getProcessInfo'), SETUP_TIMEOUT_MS, 'Browser process identity');
        const processId = info.processInfo?.find(item => item.type === 'browser')?.id;
        if (!Number.isSafeInteger(processId) || processId <= 0) throw Error('Chromium did not report its browser process');
        if (process.platform === 'linux') actualExecutable = fs.readlinkSync(`/proc/${processId}/exe`);
        else if (process.platform === 'darwin') actualExecutable = await command('ps', ['-p', String(processId), '-o', 'comm='], 5000);
        else throw Error('Actual browser executable identity is unavailable on this platform');
        summary.browser.executable_identity_method = process.platform === 'linux' ? 'cdp-process-id/proc-exe' : 'cdp-process-id/ps-comm';
      }
      if (!path.isAbsolute(actualExecutable)) throw Error('Browser did not report an absolute actual executable path');
      summary.browser.actual_executable = await executableIdentity(actualExecutable);
      summary.browser.executable_version = await command(summary.browser.actual_executable.path, ['--version'], 5000);
      summary.browser.version = browser.version();
      summary.browser.runtime = version;
      const binaryVersion = summary.browser.executable_version.match(/\d+(?:\.\d+){1,3}/)?.[0];
      if (binaryVersion !== browser.version() || !version.product.endsWith('/' + binaryVersion)) throw Error('Running browser version does not match executable version');
    } finally { await deadline(session.detach(), 5000, 'Browser identity session cleanup'); }
    return browser;
  } catch (error) { await deadline(browser.close(), 10000, 'Browser cleanup'); throw error; }
}

async function probe(file) {
  const result = JSON.parse(await command('ffprobe', ['-v', 'error', '-show_format', '-show_streams', '-of', 'json', file]));
  const video = result.streams?.find(stream => stream.codec_type === 'video');
  const duration = Number(result.format?.duration);
  if (!result.format?.format_name?.split(',').includes('mp4') || !video ||
      !Number.isFinite(duration) || duration <= 0 || !Number.isInteger(video.width) || !Number.isInteger(video.height)) {
    throw Error('ffprobe did not identify a finite MP4 video');
  }
  const rotation = Number(video.side_data_list?.find(item => item.rotation !== undefined)?.rotation || 0);
  const rotated = Math.abs(rotation % 180) === 90;
  return { duration_s: duration, width: rotated ? video.height : video.width, height: rotated ? video.width : video.height,
    size_bytes: Number(result.format.size), codec: video.codec_name, rotation_degrees: rotation,
    sample_aspect_ratio: video.sample_aspect_ratio || null };
}

async function play(page, mediaUrl, timeoutMs) {
  return deadline(page.evaluate(({ mediaUrl, timeoutMs }) => new Promise(resolve => {
    const video = document.getElementById('media');
    if (!video) { resolve({ error: 'Player element missing' }); return; }
    const started = performance.now();
    const checkpoints = [{ time_s: video.currentTime, wall_ms: 0 }];
    const rateChanges = [];
    let seekingEvents = 0;
    let presentedFrames = 0;
    let firstPlayingTime = null;
    let finished = false;
    const timer = setTimeout(() => finish('Playback exceeded bounded timeout'), timeoutMs);
    function checkpoint() {
      if (checkpoints.length < 4096) checkpoints.push({ time_s: video.currentTime, wall_ms: performance.now() - started });
    }
    function finish(error = null) {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      checkpoint();
      const quality = video.getVideoPlaybackQuality?.();
      const total = quality?.totalVideoFrames ?? null;
      const dropped = quality?.droppedVideoFrames ?? null;
      resolve({ error, ended: video.ended, current_time_s: video.currentTime,
        duration_s: Number.isFinite(video.duration) ? video.duration : null,
        width: video.videoWidth, height: video.videoHeight, wall_ms: performance.now() - started,
        first_playing_time_s: firstPlayingTime, playback_rate: video.playbackRate,
        rate_changes: rateChanges, seeking_events: seekingEvents, media_error: video.error?.code ?? null,
        muted: video.muted, total_frames: total, dropped_frames: dropped,
        dropped_frame_fraction: total ? dropped / total : null,
        decoded_frames: video.webkitDecodedFrameCount ?? null,
        displayed_frames_estimate: total === null || dropped === null ? null : total - dropped,
        presented_frame_callbacks: presentedFrames, checkpoints });
      video.pause();
    }
    video.muted = true;
    video.playbackRate = 1;
    video.addEventListener('timeupdate', checkpoint);
    video.addEventListener('playing', () => { firstPlayingTime ??= video.currentTime; checkpoint(); });
    video.addEventListener('ratechange', () => rateChanges.push(video.playbackRate));
    video.addEventListener('seeking', () => { seekingEvents++; });
    video.addEventListener('ended', () => finish(), { once: true });
    video.addEventListener('error', () => finish('Media error ' + (video.error?.code ?? 'unknown')), { once: true });
    if (video.requestVideoFrameCallback) {
      const frame = () => { if (!finished) { presentedFrames++; video.requestVideoFrameCallback(frame); } };
      video.requestVideoFrameCallback(frame);
    }
    video.src = mediaUrl;
    video.load();
    video.play().catch(error => finish('play() rejected: ' + error.name));
  }), { mediaUrl, timeoutMs }), timeoutMs + 3000, 'Browser playback evaluation');
}

function playerChecks(playback, file) {
  return { ended: playback.ended === true, no_media_error: playback.media_error === null && !playback.error,
    normal_speed: playback.playback_rate === 1 && playback.rate_changes.every(rate => rate === 1),
    no_seeking: playback.seeking_events === 0, started_at_beginning: playback.first_playing_time_s !== null && playback.first_playing_time_s <= 0.1,
    decoded_frames: playback.total_frames > 0 && playback.decoded_frames > 0,
    reached_duration: Number.isFinite(playback.duration_s) && Math.abs(playback.current_time_s - playback.duration_s) <= 0.1,
    elapsed_at_normal_speed: playback.wall_ms >= playback.duration_s * 900,
    file_duration_match: Math.abs(playback.duration_s - file.duration_s) <= 0.15,
    file_dimensions_match: playback.width === file.width && playback.height === file.height };
}

async function verifyAsset(asset, index, options, browser, runtimeError, summary) {
  const receipt = { schema: SCHEMA, id: `asset-${index + 1}`, asset_index: index, pass: false,
    playback_verdict: 'FAIL', ...pending, source: { sha256_before: null, sha256_after: null, unchanged: false }, file_metadata: null, playback: null, errors: [],
    browser: summary.browser || null, playwright: summary.playwright || null };
  let fd;
  let sourcePath;
  let realPath;
  let server;
  let context;
  try {
    if (!asset || Array.isArray(asset) || typeof asset !== 'object' || typeof asset.path !== 'string' || !asset.path.trim() || asset.path.includes('\0')) {
      throw Error('Each asset must be an object with a nonempty local path');
    }
    if (asset.sha256 !== undefined && (typeof asset.sha256 !== 'string' || !/^[a-fA-F0-9]{64}$/.test(asset.sha256))) throw Error('Optional sha256 must have 64 hexadecimal characters');
    sourcePath = path.resolve(asset.path);
    realPath = fs.realpathSync(sourcePath);
    const pathStat = fs.statSync(realPath, { bigint: true });
    if (!pathStat.isFile() || pathStat.size <= 0 || pathStat.size > BigInt(MAX_MEDIA_BYTES)) throw Error('Selected source must be a nonempty regular file no larger than 2 GiB');
    fd = fs.openSync(realPath, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    const stat = fs.fstatSync(fd, { bigint: true });
    if (!stat.isFile() || stat.size <= 0 || stat.size > BigInt(MAX_MEDIA_BYTES)) throw Error('Selected source must be a nonempty regular file no larger than 2 GiB');
    receipt.source.metadata_before = metadata(stat);
    receipt.source.sha256_before = await digestFd(fd);
    receipt.sha256 = receipt.source.sha256_before; // v1 receipt compatibility.
    receipt.source.declared_sha256 = asset.sha256?.toLowerCase() ?? null;
    if (asset.sha256 && receipt.sha256 !== asset.sha256.toLowerCase()) throw Error('Selected source does not match its declared SHA-256');
    if (runtimeError) { receipt.errors.push(runtimeError); return receipt; }
    receipt.file_metadata = await probe(realPath);
    if (receipt.file_metadata.size_bytes !== Number(stat.size)) throw Error('ffprobe source size differs from the opened source');
    if (receipt.file_metadata.duration_s * 1000 > options.timeoutMs) throw Error('Source duration exceeds the selected playback timeout');
    context = await deadline(browser.newContext({ serviceWorkers: 'block' }), SETUP_TIMEOUT_MS, 'Isolated context creation');
    const page = await deadline(context.newPage(), SETUP_TIMEOUT_MS, 'Player page creation');
    page.setDefaultTimeout(SETUP_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(SETUP_TIMEOUT_MS);
    server = await createMediaServer(fd, Number(stat.size));
    await page.route('**/*', route => [server.mediaUrl, server.playerUrl].includes(route.request().url()) ? route.continue() : route.abort());
    await page.goto(server.playerUrl, { waitUntil: 'load' });
    receipt.playback = await play(page, server.mediaUrl, options.timeoutMs);
    receipt.checks = playerChecks(receipt.playback, receipt.file_metadata);
    receipt.media_requests = server.requests;
    if (!Object.values(receipt.checks).every(Boolean)) receipt.errors.push(failure('PLAYBACK_CHECK_FAILED', 'One or more playback/metadata checks failed; inspect checks and playback counters'));
  } catch (error) { receipt.errors.push(failure('ASSET_FAILED', error.message)); }
  finally {
    if (context) {
      try { await deadline(context.close(), 5000, 'Context cleanup'); }
      catch (error) { receipt.errors.push(failure('CONTEXT_CLEANUP_FAILED', error.message)); }
    }
    if (server) {
      try { await server.close(); }
      catch (error) { receipt.errors.push(failure('SERVER_CLEANUP_FAILED', error.message)); }
    }
    if (fd !== undefined) {
      try {
        if (receipt.source.sha256_before) receipt.source.sha256_after = await digestFd(fd);
        receipt.source.metadata_after = metadata(fs.fstatSync(fd, { bigint: true }));
        receipt.source.path_metadata_after = metadata(fs.statSync(sourcePath, { bigint: true }));
        receipt.source.path_identity_unchanged = fs.realpathSync(sourcePath) === realPath && sameMetadata(receipt.source.metadata_before, receipt.source.path_metadata_after);
        receipt.source.unchanged = receipt.source.sha256_before === receipt.source.sha256_after &&
          sameMetadata(receipt.source.metadata_before, receipt.source.metadata_after) && receipt.source.path_identity_unchanged;
        if (!receipt.source.unchanged) receipt.errors.push(failure('SOURCE_CHANGED', 'Selected source bytes or file identity changed during verification'));
      } catch (error) { receipt.errors.push(failure('SOURCE_RECHECK_FAILED', error.message)); }
      finally { fs.closeSync(fd); }
    }
    receipt.pass = receipt.errors.length === 0 && receipt.source.unchanged === true && !!receipt.checks && Object.values(receipt.checks).every(Boolean);
    receipt.playback_verdict = receipt.pass ? 'PASS' : 'FAIL';
  }
  return receipt;
}

export async function main(argv = process.argv.slice(2), environment = process.env) {
  const summary = { schema: SCHEMA, started_at: new Date().toISOString(), pass: false, playback_verdict: 'FAIL',
    ...pending, node_version: process.version, assets: [], errors: [],
    note: 'Player PASS covers only the exact selected video bytes in the recorded Chromium. Visual understanding, audibility, production and model execution require separate evidence.' };
  let output;
  let outputClaimed = false;
  let browser;
  try {
    // Claim a new private directory before parsing input or loading optional modules.
    if (argv[1] && !argv[1].startsWith('--')) {
      output = path.resolve(argv[1]);
      fs.mkdirSync(output, { mode: 0o700 });
      outputClaimed = true;
    }
    const options = parseArgs(argv, environment);
    if (!output) throw Error('A new output directory is required. ' + USAGE);
    summary.timeout_ms_per_asset = options.timeoutMs;
    const inputStat = fs.statSync(options.input);
    if (!inputStat.isFile() || inputStat.size > 1024 ** 2) throw Error('Asset list must be a regular JSON file no larger than 1 MiB');
    const inputBytes = fs.readFileSync(options.input);
    summary.asset_list_sha256 = crypto.createHash('sha256').update(inputBytes).digest('hex');
    const assets = JSON.parse(inputBytes.toString('utf8'));
    if (!Array.isArray(assets) || assets.length === 0 || assets.length > MAX_ASSETS) throw Error(`Asset list must be a nonempty array of at most ${MAX_ASSETS} entries`);
    summary.asset_count = assets.length;
    let runtimeError;
    try { browser = await launchBrowser(options, summary); }
    catch (error) { runtimeError = failure('BROWSER_SETUP_FAILED', error.message); summary.errors.push(runtimeError); }
    for (let index = 0; index < assets.length; index++) {
      const receipt = await verifyAsset(assets[index], index, options, browser, runtimeError, summary);
      const receiptFile = `${receipt.id}.json`;
      writeJson(path.join(output, receiptFile), receipt);
      summary.assets.push({ id: receipt.id, receipt: receiptFile, sha256: receipt.sha256 ?? null, pass: receipt.pass,
        playback_verdict: receipt.playback_verdict, errors: receipt.errors });
      console.log(receipt.id, receipt.pass ? 'PASS' : 'FAIL');
    }
    summary.pass = assets.length > 0 && summary.errors.length === 0 && summary.assets.length === assets.length && summary.assets.every(asset => asset.pass);
  } catch (error) { summary.errors.push(failure('RUN_FAILED', error.message)); summary.pass = false; }
  finally {
    if (browser) {
      try { await deadline(browser.close(), 10000, 'Browser cleanup'); summary.browser_closed = true; }
      catch (error) { summary.errors.push(failure('BROWSER_CLEANUP_FAILED', error.message)); summary.pass = false; }
    }
    summary.finished_at = new Date().toISOString();
    summary.playback_verdict = summary.pass ? 'PASS' : 'FAIL';
    // Existing output directories are never touched, including their summary.
    if (outputClaimed) {
      try { writeJson(path.join(output, 'summary.json'), summary); }
      catch (error) {
        summary.pass = false;
        summary.playback_verdict = 'FAIL';
        summary.errors.push(failure('SUMMARY_WRITE_FAILED', error.message));
        console.error(JSON.stringify(summary));
      }
    } else console.error(JSON.stringify(summary));
  }
  if (!summary.pass) console.error('Playback verification FAIL. ' + (output ? 'Inspect the new summary.json if created.' : USAGE));
  return summary.pass ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  // Exit after bounded cleanup even if a broken optional runtime retains handles.
  process.exit(await main());
}
