// Drives a two-minute Mizan demo in a real, visible Chrome window with on-screen captions.
// Start from a freshly reset database (Reset Mizan Demo.cmd) with the app running on MIZAN_URL.
// A backup recording is saved to work/demo-video/. Usage: node scripts/demo/record-demo.cjs
const { createRequire } = require('node:module');
const path = require('node:path');
const req = createRequire(path.resolve(__dirname, '../../frontend/package.json'));
const { chromium } = req('playwright');

const ROOT = process.env.MIZAN_URL || 'http://127.0.0.1:8000';
const PREROLL = Number(process.env.PREROLL_SECONDS || 20);
const HEADLESS = process.env.HEADLESS === '1';
const RAW = process.env.RAW === '1'; // no captions or click markers, for recording a separate voice-over
const outDir = path.resolve(__dirname, '../../work/demo-video');
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: HEADLESS, channel: 'chrome', args: HEADLESS ? [] : ['--kiosk', '--disable-infobars'] });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, recordVideo: { dir: outDir, size: { width: 1920, height: 1080 } } });
  const page = await context.newPage();
  const marks = [];
  const started = Date.now();
  const mark = label => marks.push(`${((Date.now() - started) / 1000).toFixed(1)}s ${label}`);

  // Caption bar and click ring live in the page; they survive in-app navigation (single-page app).
  const caption = async (text, sub = '') => RAW ? undefined : page.evaluate(([text, sub]) => {
    let bar = document.getElementById('demo-caption');
    if (!bar) {
      bar = document.createElement('div'); bar.id = 'demo-caption'; bar.dir = 'ltr';
      bar.style.cssText = 'position:fixed;left:50%;bottom:40px;transform:translateX(-50%);z-index:2147483647;max-width:1400px;padding:18px 28px;background:#141413;color:#f6f6f3;font:500 30px/1.35 "Archivo Variable","Noto Kufi Arabic",sans-serif;box-shadow:0 18px 40px -16px #0008;border-top:4px solid #1d3cff;text-align:center;pointer-events:none;transition:opacity .25s';
      document.body.appendChild(bar);
    }
    bar.style.opacity = '0';
    setTimeout(() => { bar.innerHTML = text + (sub ? `<div style="font-size:22px;color:#c9c9c3;margin-top:6px">${sub}</div>` : ''); bar.style.opacity = text ? '1' : '0'; }, 180);
  }, [text, sub]);
  const ring = async locator => {
    if (RAW) return;
    const box = await locator.boundingBox();
    if (!box) return;
    await page.evaluate(([x, y]) => {
      const r = document.createElement('div');
      r.style.cssText = `position:fixed;left:${x - 26}px;top:${y - 26}px;width:52px;height:52px;border-radius:50%;border:4px solid #ff6414;z-index:2147483646;pointer-events:none`;
      document.body.appendChild(r);
      r.animate([{ transform: 'scale(.4)', opacity: 1 }, { transform: 'scale(1.4)', opacity: 0 }], { duration: 700, easing: 'cubic-bezier(.16,1,.3,1)' }).onfinish = () => r.remove();
    }, [box.x + box.width / 2, box.y + box.height / 2]);
    await wait(250);
  };
  const click = async locator => { await locator.scrollIntoViewIfNeeded(); await ring(locator); await locator.click(); };
  const show = async locator => page.evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'center' }), await locator.elementHandle());

  // 0 · Pre-roll: time to press Start in the screen recorder.
  await page.goto(ROOT);
  await page.evaluate(() => { localStorage.setItem('mizan-lang', 'en'); });
  await page.goto(ROOT);
  await page.evaluate(() => document.fonts.ready);
  for (let s = PREROLL; s > 0; s--) { await caption(`Recording starts in ${s}…`); await wait(1000); }
  mark('start');

  // 1 · Opening
  await caption('Mizan checks a university timetable before it is published.', 'Local AI · synthetic data · a person approves every change');
  await wait(5000);
  await click(page.getByRole('button', { name: 'Enter workspace' }));
  await page.getByRole('heading', { name: /Every hour of the week/ }).waitFor();
  await wait(1500);

  // 2 · The cost
  mark('overview');
  await caption('This timetable is valid, but students lose 15,000 hours a week in gaps.', 'Every number is graded: red is critical, green is good');
  await ring(page.locator('.ov-big'));
  await wait(7500);
  await caption('Every cohort waits about 10 hours a week, against a 0.75-hour target.');
  await wait(4500);

  // 3 · Optimize
  mark('optimize');
  await caption('Mizan searches valid alternatives within limits a person sets…');
  await click(page.getByRole('button', { name: 'Optimize semester' }));
  await page.getByLabel('Solver time budget (seconds)').fill('5');
  await wait(1200);
  await click(page.getByRole('button', { name: 'Run optimization' }));
  await caption('Searching and independently re-validating every candidate…');
  await page.getByRole('heading', { name: 'Review the evidence' }).waitFor({ timeout: 60000 });
  await wait(800);
  await caption('Five moves: about 1,800 student-hours back, nobody worse off, zero conflicts.', 'Optimal only within the searched options — and it says so');
  await wait(6500);
  await show(page.locator('.comparison-table'));
  await caption('Before and after, computed from the data — green where it improved.');
  await wait(5000);

  // 4 · Human approval
  mark('approve');
  await show(page.locator('.stations'));
  await caption('A person approves. Publishing re-validates first.');
  await click(page.getByRole('button', { name: 'Approve proposal', exact: true }));
  await wait(1500);
  await click(page.locator('.proposal-card').first());
  await wait(1000);
  await click(page.getByRole('button', { name: 'Revalidate & publish locally', exact: true }));
  await page.getByText('Decision saved. The audit trail has been updated.').waitFor();
  await wait(2500);

  // 5 · Mid-semester change
  mark('change');
  await click(page.getByRole('button', { name: 'Change requests', exact: true }));
  await caption('A professor asks to move a class. Mizan checks it before it happens.');
  await wait(2000);
  const reason = page.getByLabel('Reason', { exact: true });
  await click(reason);
  await reason.pressSequentially('Professor unavailable on Sunday morning', { delay: 25 });
  await click(page.getByRole('button', { name: 'Evaluate change', exact: true }));
  await page.getByRole('heading', { name: 'Feasible alternatives' }).waitFor({ timeout: 30000 });
  await caption('Blocked: 77 conflicts, each one named.', 'Professor, room and student overlaps');
  await wait(5000);
  await show(page.getByRole('heading', { name: 'Feasible alternatives' }));
  await caption('…and three alternatives that already pass validation.');
  await wait(3500);
  await click(page.getByRole('button', { name: 'Propose this', exact: true }).first());
  await page.getByRole('button', { name: 'Approve proposal', exact: true }).waitFor();
  await wait(1800);
  await click(page.getByRole('button', { name: 'Close', exact: true }));
  await wait(800);

  // 6 · Staffing shortfall
  mark('shortfall');
  await caption('Is it a scheduling problem, or a real staffing shortage?');
  await page.getByRole('combobox', { name: 'Scenario', exact: true }).selectOption('shortfall');
  await wait(1500);
  await click(page.getByRole('button', { name: 'Workforce', exact: true }));
  await page.getByRole('button', { name: 'Prepare requisition', exact: true }).waitFor();
  await wait(1600);
  await caption('A proven shortfall: one Machine Learning section cannot be covered. 112 students at risk.', 'Capacity proof, not a solver that ran out of time');
  await wait(7000);
  await click(page.getByRole('button', { name: 'Prepare requisition', exact: true }));
  await caption('Only a proven shortage can start recruitment, and hiring decisions stay human.');
  await wait(4500);

  // 7 · Arabic
  mark('arabic');
  const dismiss = page.getByRole('button', { name: 'Dismiss' });
  if (await dismiss.count()) await dismiss.first().click();
  await click(page.getByRole('button', { name: 'العربية', exact: true }));
  await click(page.getByRole('button', { name: 'نظرة عامة', exact: true }));
  await caption('Fully bilingual: the same verified numbers, right to left.', 'ثنائي اللغة بالكامل: الأرقام نفسها، من اليمين إلى اليسار');
  await wait(7000);

  // 8 · Close
  mark('close');
  await caption('Mizan · ميزان — Measure. Recommend. Prove. A person decides.', 'Runs entirely on one PC · fine-tuned local coordinator · 80 automated tests');
  await wait(6000);
  mark('end');

  const video = page.video();
  await context.close();
  await browser.close();
  const file = video ? await video.path() : '';
  console.log(JSON.stringify({ marks, backupVideo: file }, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
