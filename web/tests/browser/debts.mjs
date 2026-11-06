// Real debt writes on the synthetic seed_debts.py database. No application dependency.
import {createRequire} from 'node:module';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
const {chromium,webkit}=createRequire(import.meta.url)(process.env.PN_PLAYWRIGHT||'/private/tmp/pn-debts-browser-tools/node_modules/playwright');
const fixtures=JSON.parse(readFileSync('/private/tmp/pn-debts-manifest.json'));
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-debts-review';mkdirSync(OUT,{recursive:true});
const results=[];
function check(engine,name,ok,detail=''){results.push({engine,name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${engine}: ${name}${ok?'':' '+JSON.stringify(detail)}`);if(!ok)throw new Error(name);}
async function login(page,user){await page.goto(BASE+'/accounts/login/');await page.locator('[name=username]').fill(user);await page.locator('[name=password]').fill('tablestakes-91');await Promise.all([page.waitForURL(BASE+'/'),page.locator('form.form-section [type=submit]').click()]);}
for(const engine of (process.env.PN_ENGINES||'chromium,webkit').split(',')){
 const browser=await(engine==='webkit'?webkit:chromium).launch(engine==='webkit'?{}:{executablePath:process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const f=fixtures[engine],context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>{errors.push(e.message);console.log('PAGEERROR',page.url(),JSON.stringify({message:e.message,stack:e.stack}))});await login(page,f.receiver);await page.goto(`${BASE}/g/${f.group}/`);
  check(engine,'receiver sees one net pair of 200 from three sessions',await page.locator('[data-debt]').count()===1 && (await page.locator('#debts').innerText()).includes('₱200') && (await page.locator('#debts').innerText()).includes('from 3 sessions'));
  if(process.env.PN_BASELINE==='1'){await context.close();continue;}
  await page.evaluate(()=>window.__debtSentinel=42);
  await page.locator('.debt-detail > summary').click();await page.locator('.debt-detail .debt-transfers').waitFor({state:'visible'});
  check(engine,'expanded records show all three original amounts',await page.locator('.debt-detail .debt-transfers li').count()===3 && (await page.locator('.debt-detail').innerText()).includes('₱500') && (await page.locator('.debt-detail').innerText()).includes('₱100') && (await page.locator('.debt-detail').innerText()).includes('₱400'));
  await page.getByRole('button',{name:'Got ₱200 from Ana',exact:true}).click();
  const dialog=page.locator('dialog.sheet[open]');await dialog.waitFor();
  check(engine,'confirmation starts on Not yet',await dialog.locator('[data-sheet-focus]').evaluate(el=>el===document.activeElement));
  check(engine,'sheet names counterpart and holds all records',(await dialog.innerText()).includes('Settle with Ana?')&&await dialog.locator('.debt-transfers li').count()===3);
  await page.waitForFunction(()=>{const d=document.querySelector("dialog.sheet[open]");return d&&Math.abs(new DOMMatrix(getComputedStyle(d).transform).m42)<1});
  await page.screenshot({path:`${OUT}/${engine}-sheet-390.png`});
  await dialog.getByRole('button',{name:'Not yet',exact:true}).click();await dialog.waitFor({state:'hidden'});
  const payerContext=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),payer=await payerContext.newPage();
  await login(payer,f.payer);await payer.goto(`${BASE}/g/${f.group}/`);
  check(engine,'payer has no settle action and sees who confirms',await payer.locator('.debt-opener').count()===0&&(await payer.locator('#debts').innerText()).includes('Ben confirms when paid'));
  if(process.env.PN_DEBTS_PHASE!=='group'){
   await payer.goto(`${BASE}/n/${f.nights[0]}/`);const recap=payer.locator('dialog.sheet[open]');if(await recap.count()){await recap.locator('.sheet-head button').click();await recap.waitFor({state:'hidden'});}
  }
  await page.getByRole('button',{name:'Got ₱200 from Ana',exact:true}).click();await dialog.getByRole('button',{name:'Settle',exact:true}).click();
  await page.locator('[data-debt-receipt]').waitFor();await page.waitForFunction(()=>!document.querySelector('dialog.sheet[open]'));
  check(engine,'accepted settlement removes pair and preserves document',await page.locator('[data-debt]').count()===0&&await page.evaluate(()=>window.__debtSentinel===42));
  check(engine,'receipt states exact net and offers undo',(await page.locator('[data-debt-receipt]').innerText()).includes('Settled with Ana: ₱200')&&await page.locator('[data-debt-receipt] summary').count()===1);
  if(process.env.PN_DEBTS_PHASE!=='group'){
   await payer.waitForFunction(()=>document.querySelector('[data-transfer]')?.dataset.paid==='s',{timeout:20000});
   check(engine,'other phone sees cleared transfer through live poll',(await payer.locator('[data-transfer]').innerText()).includes('Settled with Ben'));
   for(const n of f.nights){await payer.goto(`${BASE}/n/${n}/`);check(engine,`session ${n} names settlement`,(await payer.locator('[data-transfer]').innerText()).includes('Settled with Ben'));}
  }
  await page.locator('[data-debt-receipt] summary').click();await page.locator('[data-debt-receipt] [name=reason]').fill('Browser check: confirmation made by mistake');await page.getByRole('button',{name:'Undo settlement',exact:true}).click();
  await page.locator('[data-debt]').waitFor();check(engine,'recorder undo restores the 200 net',(await page.locator('#debts').innerText()).includes('Got ₱200 from Ana'));
  if(process.env.PN_DEBTS_PHASE!=='group'){
   for(const n of f.nights){await payer.goto(`${BASE}/n/${n}/`);check(engine,`undo restores unpaid session ${n}`,await payer.locator('[data-transfer]').getAttribute('data-paid')==='0');}
  }
  check(engine,'no script errors',errors.length===0,errors);
  await payerContext.close();await context.close();
 }finally{await browser.close();}
}
writeFileSync(`${OUT}/results.json`,JSON.stringify(results,null,2));console.log(`${results.length} checks passed`);
