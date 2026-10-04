// Edugate exchange in the browser: import a schedule file -> review -> add -> optimize -> export PDF.
// Needs a server on port 8001 (fresh MIZAN_DB) and a schedule file: EDUGATE_FILE=<Edugate PDF or app screenshot>.
// Personal schedules are not committed; pass your own file. Optional EDUGATE_END_FIX="ARB 202=18:20" fills a cut-off end time.
const { createRequire } = require('node:module');
const frontendRequire = createRequire(require('node:path').resolve('frontend/package.json'));
const { chromium } = frontendRequire('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async()=>{
 const file=process.env.EDUGATE_FILE;
 if(!file||!fs.existsSync(file)){console.log('SKIP set EDUGATE_FILE to an Edugate PDF or app screenshot');return}
 const browser=await chromium.launch({headless:true,executablePath:process.env.PW_EXE||undefined,channel:process.env.PW_EXE?undefined:(process.env.MIZAN_BROWSER||'chrome')});
 const page=await (await browser.newContext({viewport:{width:1440,height:1000}})).newPage();
 const failures=[];page.on('pageerror',e=>failures.push(e.message));
 const root=process.env.MIZAN_TEST_URL||'http://127.0.0.1:8001';
 const out=path.resolve('work/browser');fs.mkdirSync(out,{recursive:true});
 const tag=process.env.EDUGATE_TAG||path.extname(file).slice(1);
 await page.goto(root);
 await page.getByRole('button',{name:'Enter workspace'}).click();
 await page.getByRole('heading',{name:/Every hour of the week/}).waitFor();
 await page.getByRole('button',{name:'Semester lab',exact:true}).click();
 await page.getByRole('heading',{name:'Edugate schedules'}).waitFor();
 await page.locator('.eg-drop input[type=file]').setInputFiles(file);
 await page.getByText(/courses read — check them before adding/).waitFor({timeout:60000});
 const rows=await page.locator('.eg-table tbody tr:not(.eg-note)').count();
 assert.ok(rows>=4,`expected at least 4 rows, got ${rows}`);
 for(const fix of (process.env.EDUGATE_END_FIX||'').split(',').filter(Boolean)){
  const [code,end]=fix.split('=');
  const row=page.locator('.eg-table tbody tr:not(.eg-note)').filter({has:page.locator(`input[value="${code}"]`)});
  await row.getByLabel('End').fill(end);
 }
 await page.screenshot({path:path.join(out,`edugate-review-${tag}.png`),fullPage:true});
 await page.getByLabel('Student ID').fill('TEST-EDU-1');
 await page.getByLabel('Student name').fill('Test Student');
 const add=page.getByRole('button',{name:'Add to Mizan and optimize'});
 assert.equal(await add.isDisabled(),false,'review still incomplete');
 await add.click();
 await page.getByRole('button',{name:'Run optimization'}).click();
 await page.getByRole('heading',{name:/Better schedules, backed by evidence/}).waitFor({timeout:60000});
 await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Semester lab',exact:true}).click();
 await page.screenshot({path:path.join(out,`edugate-before-export-${tag}.png`)});
 await page.getByLabel('Timetable to export').selectOption({index:1});
 const href=await page.getByRole('link',{name:'Download schedule (PDF)'}).getAttribute('href');
 const pdf=await page.request.get(root+href);
 assert.equal(pdf.status(),200);
 assert.equal(pdf.headers()['content-type'],'application/pdf');
 fs.writeFileSync(path.join(out,`edugate-export-${tag}.pdf`),await pdf.body());
 await page.screenshot({path:path.join(out,`edugate-after-${tag}.png`),fullPage:true});
 assert.deepEqual(failures,[]);
 console.log(`PASS edugate ${tag}: ${rows} rows read, imported, optimized, exported`);
 await browser.close();
})().catch(async e=>{console.error(e);process.exit(1)});
