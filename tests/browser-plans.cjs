// Three real solver strategies -> bilingual comparison -> select -> approve -> publish.
// Use an isolated database. The test publishes a proposal.
const {createRequire}=require('node:module');
const path=require('node:path');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const frontendRequire=createRequire(path.resolve('frontend/package.json'));
const {chromium}=frontendRequire('playwright');

(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.MIZAN_BROWSER||'chrome'});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const root=process.env.MIZAN_TEST_URL||'http://127.0.0.1:8001';
  const out=path.resolve('work/browser-plans');fs.mkdirSync(out,{recursive:true});
  await page.goto(root);await page.getByRole('button',{name:'Enter workspace',exact:true}).click();
  await page.getByRole('heading',{name:/Every hour of the week/}).waitFor();
  const revision=(await (await page.request.get(root+'/api/scenarios/baseline')).json()).revision;
  const count=(await (await page.request.get(root+'/api/proposals?scenario_id=baseline')).json()).length;
  await page.getByRole('button',{name:'Recommendations',exact:true}).click();
  await page.getByRole('button',{name:'Compare three plans',exact:true}).click();
  await page.getByLabel('Search seconds per plan',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Generate three plans',exact:true}).waitFor({state:'visible'});
  const response=page.waitForResponse(r=>r.url().endsWith('/plan-comparisons')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Generate three plans',exact:true}).click();
  const comparison=await (await response).json();
  assert.equal(comparison.base_revision,revision);assert.equal(comparison.plans.length,3);
  assert.ok(comparison.distinct_plans>=2,'at least two genuinely different timetables');
  assert.equal((await (await page.request.get(root+'/api/proposals?scenario_id=baseline')).json()).length,count,'generation writes no proposals');
  await page.locator('.plan-table').waitFor();
  assert.ok(await page.locator('.plan-table-scroll').evaluate(e=>e.scrollWidth<=e.clientWidth+1),'all three plans fit on desktop');
  for(let i=0;i<3;i++){
   const p=comparison.plans[i];
   if(p.available){
    const cell=page.locator('[data-measure="1"] td').nth(i+1);
    assert.equal((await cell.innerText()).replaceAll(',',''),String(p.comparison.recovered_hours));
    assert.equal(p.conflict_count,0);
   }
  }
  const numbers=await page.locator('.plan-table tbody td').allInnerTexts();
  await page.waitForTimeout(400);await page.screenshot({path:path.join(out,'comparison-en.png'),fullPage:true});
  await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'العربية',exact:true}).click();
  await page.getByRole('button',{name:'قارن ثلاث خطط',exact:true}).click();
  await page.locator('.plan-table').waitFor();
  assert.equal(await page.locator('html').getAttribute('dir'),'rtl');
  assert.deepEqual(await page.locator('.plan-table tbody td').allInnerTexts(),numbers);
  await page.waitForTimeout(400);await page.screenshot({path:path.join(out,'comparison-ar.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'page does not overflow on mobile');
  const region=page.locator('.plan-table-scroll');
  assert.ok(await region.evaluate(e=>e.scrollWidth>e.clientWidth),'comparison scrolls inside its own region');
  await page.screenshot({path:path.join(out,'comparison-mobile-ar.png'),fullPage:true});
  await page.keyboard.press('Escape');await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('button',{name:'English',exact:true}).click();
  await page.getByRole('button',{name:'Compare three plans',exact:true}).click();await page.locator('.plan-table').waitFor();
  await page.getByRole('button',{name:'Review Fewest changes',exact:true}).click();
  await page.getByRole('heading',{name:'Review the evidence',exact:true}).waitFor();
  await page.getByRole('dialog',{name:'Review the evidence',exact:true}).getByRole('heading',{name:'Fewest changes',exact:true}).waitFor();
  assert.equal((await (await page.request.get(root+'/api/scenarios/baseline')).json()).revision,revision);
  await page.getByRole('button',{name:'Approve proposal',exact:true}).click();
  await page.getByText('Approved · not yet published').first().waitFor();
  await page.getByRole('button',{name:'Revalidate & publish locally',exact:true}).click();
  await page.getByText(/Published\. The official timetable is now version/).waitFor();
  assert.equal((await (await page.request.get(root+'/api/scenarios/baseline')).json()).revision,revision+1);
  await page.getByRole('button',{name:'Compare three plans',exact:true}).click();await page.locator('.plan-table').waitFor();
  await page.getByText(/Outdated comparison:/).waitFor();
  assert.ok(await page.getByRole('button',{name:'Review Most time saved',exact:true}).isDisabled());
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({passed:true,distinct:comparison.distinct_plans,plans:comparison.plans.map(p=>({key:p.key,status:p.status,hours:p.comparison?.recovered_hours,sections:p.comparison?.changes.length,benefiting:p.comparison?.benefiting,worsened:p.comparison?.worsened})),checks:['read-only generation','displayed metrics','EN/AR parity','mobile overflow','selection','approval','publication','staleness'],pageErrors:errors},null,2));
  console.log('PASS three plans: real solver, read-only search, EN/AR, mobile, selection, approval, publication, staleness');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
