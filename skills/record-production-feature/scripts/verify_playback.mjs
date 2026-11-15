// Sequential real Chromium playback at 1x. Requires project-local playwright.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(path.join(process.cwd(), 'package.json'));
const { chromium } = require('playwright');
const [input, output] = process.argv.slice(2);
if (!input || !output) throw Error('Usage: verify_playback.mjs assets.json NEW_OUTPUT_DIRECTORY');
const assets = JSON.parse(fs.readFileSync(input, 'utf8'));
fs.mkdirSync(output, { recursive: false });
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const server = http.createServer((req, res) => {
  const match = /^\/(\d+)\.mp4$/.exec(req.url);
  if (!match || !assets[Number(match[1])]) { res.writeHead(404).end(); return; }
  const file = assets[Number(match[1])].path;
  const size = fs.statSync(file).size;
  const range = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range ?? '');
  const start = range ? Number(range[1]) : 0;
  const end = range && range[2] ? Math.min(size - 1, Number(range[2])) : size - 1;
  if (start > end || start >= size) { res.writeHead(416).end(); return; }
  res.writeHead(range ? 206 : 200, { 'Content-Type': 'video/mp4', 'Content-Length': end - start + 1,
    'Accept-Ranges': 'bytes', ...(range ? { 'Content-Range': `bytes ${start}-${end}/${size}` } : {}) });
  fs.createReadStream(file, { start, end }).pipe(res);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ headless: true,
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) });
let failed = false;
try {
  for (let i = 0; i < assets.length; i++) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const sha256 = digest(assets[i].path);
    let receipt;
    try {
      // Serve only the selected media; never expose a workspace directory or user profile.
      await page.goto(`http://127.0.0.1:${server.address().port}/${i}.mp4`);
      receipt = await page.evaluate(async () => {
        const video = document.querySelector('video');
        if (!video) throw Error('Native media player missing');
        video.muted = true;
        video.playbackRate = 1;
        const started = performance.now();
        const checkpoints = [];
        return await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => reject(Error('Playback exceeded bounded timeout')), 180000);
          video.addEventListener('timeupdate', () => checkpoints.push({ time_s: video.currentTime, wall_ms: performance.now() - started }));
          video.addEventListener('error', () => { clearTimeout(timeout); reject(Error('Media error ' + video.error?.code)); }, { once: true });
          video.addEventListener('ended', () => {
            clearTimeout(timeout);
            const quality = video.getVideoPlaybackQuality();
            resolve({ ended: video.ended, current_time_s: video.currentTime, duration_s: video.duration,
              wall_ms: performance.now() - started, playback_rate: video.playbackRate,
              media_error: video.error?.code ?? null, total_frames: quality.totalVideoFrames,
              dropped_frames: quality.droppedVideoFrames, checkpoints });
          }, { once: true });
          video.play().catch(reject);
        });
      });
      receipt.pass = receipt.ended && receipt.media_error === null && receipt.total_frames > 0
        && receipt.playback_rate === 1 && Math.abs(receipt.current_time_s - receipt.duration_s) < 0.1
        && receipt.wall_ms >= receipt.duration_s * 900 && digest(assets[i].path) === sha256;
    } catch (error) { receipt = { pass: false, error: String(error) }; }
    const id = `asset-${i + 1}`;
    fs.writeFileSync(path.join(output, `${id}.json`), JSON.stringify({ id, sha256, ...receipt }, null, 2));
    failed ||= !receipt.pass;
    console.log(id, receipt.pass ? 'PASS' : 'FAIL');
    await context.close();
  }
} finally { await browser.close(); server.close(); }
process.exitCode = failed ? 1 : 0;
