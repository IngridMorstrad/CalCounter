// Records a synced demo video of the Kiro Tasks app using Playwright.
// Actions are scheduled on an absolute timeline (relative to recording start)
// so they line up with the pre-generated narration in timings.json.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const HERE = __dirname;
const APP_URL = "file://" + path.join(HERE, "index.html");
const OUT_DIR = path.join(HERE, "video_raw");
const timings = JSON.parse(fs.readFileSync(path.join(HERE, "timings.json")));

const W = 1280, H = 720;

// Absolute start time (seconds from recording start) of each beat.
const starts = [];
let acc = timings.lead_in;
for (const b of timings.beats) { starts.push(acc); acc += b.duration; }
const TOTAL = acc;

const TASKS = [
  "Review the Kiro design doc",
  "Ship the v2 release notes",
  "Record the demo video",
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    recordVideo: { dir: OUT_DIR, size: { width: W, height: H } },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  // t0 == recording start (recording began at context creation, ~now).
  const t0 = Date.now();
  const at = (beatIdx, offset) => starts[beatIdx] + offset; // seconds from t0
  const waitUntil = async (sec) => {
    const target = t0 + sec * 1000;
    const delta = target - Date.now();
    if (delta > 0) await sleep(delta);
  };

  await page.goto(APP_URL);
  await page.evaluate(() => { localStorage.clear(); location.reload(); });
  await page.waitForSelector("#new-task");

  async function addTask(text) {
    const input = page.locator("#new-task");
    await input.click();
    await input.fill("");
    await input.pressSequentially(text, { delay: 55 });
    await sleep(250);
    await page.locator("#add-btn").click();
  }

  // ---- Beat 1: add first task ("type ... press Add") ----
  await waitUntil(at(1, 1.6));
  await addTask(TASKS[0]);

  // ---- Beat 2: add two more ----
  await waitUntil(at(2, 1.8));
  await addTask(TASKS[1]);
  await waitUntil(at(2, 4.6));
  await addTask(TASKS[2]);

  // ---- Beat 3: complete the top task ----
  await waitUntil(at(3, 4.0));
  await page.locator(".item").first().locator(".check").click();

  // ---- Beat 4: filters Active -> Completed -> All ----
  await waitUntil(at(4, 2.8));
  await page.locator('.filter[data-filter="active"]').click();
  await waitUntil(at(4, 5.2));
  await page.locator('.filter[data-filter="completed"]').click();
  await waitUntil(at(4, 7.6));
  await page.locator('.filter[data-filter="all"]').click();

  // ---- Beat 5: hover + delete an active task ----
  await waitUntil(at(5, 3.6));
  // first active (not done) item
  const activeItem = page.locator(".item:not(.done)").first();
  await activeItem.hover();
  await sleep(1200);
  await waitUntil(at(5, 6.4));
  await activeItem.locator(".del").click();

  // ---- Beat 6: clear completed, then reload to show persistence ----
  await waitUntil(at(6, 2.6));
  await page.locator("#clear-done").click();
  await waitUntil(at(6, 6.2));
  await page.reload();
  await page.waitForSelector("#new-task");

  // ---- Beat 7: outro, hold on the final state ----
  await waitUntil(TOTAL + 1.2);

  const video = page.video();
  await context.close();
  await browser.close();

  const src = await video.path();
  const dest = path.join(HERE, "demo_raw.webm");
  fs.copyFileSync(src, dest);
  console.log("VIDEO_PATH=" + dest);
  console.log("PLANNED_TOTAL=" + TOTAL.toFixed(2));
})().catch((e) => { console.error(e); process.exit(1); });
