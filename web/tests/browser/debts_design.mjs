// Responsive, native fallback and motion checks on seed_debts.py's synthetic data.
import {createRequire} from 'node:module';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
const {chromium,webkit}=createRequire(import.meta.url)(process.env.PN_PLAYWRIGHT||'/private/tmp/pn-debts-browser-tools/node_modules/playwright');
const fixtures=JSON.parse(readFileSync('/private/tmp/pn-debts-manifest.json'));
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765',OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-debts-review';mkdirSync(OUT,{recursive:true});
const results=[];function check(engine,name,ok,detail=''){results.push({engine,name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${engine}: ${name}${ok?'':' '+JSON.stringify(detail)}`);if(!ok)throw new Error(name);}
async function login(page,user){await page.goto(BASE+'/accounts/login/');await page.locator('[name=username]').fill(user);await page.locator('[name=password]').fill('tablestakes-91');await Promise.all([page.waitForURL(BASE+'/'),page.locator('form.form-section [type=submit]').click()]);}
for(const engine of (process.env.PN_ENGINES||'chromium,webkit').split(',')){
 const browser=await(engine==='webkit'?webkit:chromium).launch(engine==='webkit'?{}:{executablePath:process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const f=fixtures[engine];
  if(process.env.PN_DESIGN_MODE!=='motion'){
   const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),page=await context.newPage();
   await login(page,fixtures.stress.host);await page.goto(`${BASE}/g/${fixtures.stress.group}/`);
   check(engine,'20 pairs plus a separate chips row',await page.locator('[data-debt]').count()===21);
   check(engine,'full exact money and separate units visible',(await page.locator('#debts').innerText()).includes('₱1,000,000.50')&&(await page.locator('#debts').innerText()).includes('50 chips'));
   for(const width of [320,390,1280]){
    await page.setViewportSize({width,height:844});
    const geometry=await page.evaluate(()=>({wide:document.documentElement.scrollWidth,view:innerWidth,bad:[...document.querySelectorAll('.debt-summary,.debt-opener')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().height<47.5).map(e=>e.textContent.trim())}));
    check(engine,`${width}px has no sideways scroll`,geometry.wide<=width,geometry);
    check(engine,`${width}px targets are at least 48px`,geometry.bad.length===0,geometry.bad);
    await page.screenshot({path:`${OUT}/${engine}-debts-${width}.png`});
   }
   await page.setViewportSize({width:320,height:844});await page.evaluate(()=>document.documentElement.style.fontSize='200%');
   const enlarged=await page.evaluate(()=>({pageWidth:document.documentElement.scrollWidth,viewport:innerWidth,bad:[...document.querySelectorAll('#debts *')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&(b.right>innerWidth+1||b.left< -1)}).map(e=>e.className)}));
   check(engine,'200 percent text keeps the Debts section inside the phone',enlarged.bad.length===0,enlarged);if(enlarged.pageWidth>enlarged.viewport)console.log('KNOWN existing tab overflow at enlarged text',engine,JSON.stringify(enlarged));
   await context.close();
   const sheetContext=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),sheetPage=await sheetContext.newPage();
   await login(sheetPage,fixtures.stress.host);await sheetPage.goto(`${BASE}/g/${fixtures.stress.group}/`);await sheetPage.locator('.debt-opener').first().click();await sheetPage.locator('dialog.sheet[open]').waitFor();
   await sheetPage.waitForFunction(()=>{const d=document.querySelector('dialog.sheet[open]');return Math.abs(new DOMMatrix(getComputedStyle(d).transform).m42)<1});
   const sheet=await sheetPage.locator('dialog.sheet[open]').evaluate(el=>({right:el.getBoundingClientRect().right,width:el.scrollWidth,client:el.clientWidth,focus:document.activeElement.textContent.trim()}));
   check(engine,'long-name large-amount sheet stays inside the phone',sheet.right<=391&&sheet.width<=sheet.client+1,sheet);
   check(engine,'safe choice stays focused with a long name',sheet.focus==='Not yet',sheet);
   const close=await sheetPage.locator('dialog.sheet[open] .sheet-head button').boundingBox();check(engine,'long heading keeps the close target at 48px',close.width>=47.5&&close.height>=47.5,close);
   await sheetPage.screenshot({path:`${OUT}/${engine}-long-sheet-390.png`});await sheetContext.close();
   const native=await browser.newContext({viewport:{width:320,height:760},javaScriptEnabled:false}),np=await native.newPage();
   await login(np,f.receiver);await np.goto(`${BASE}/g/${f.group}/`);await np.locator('.debt-confirm > summary').click();await np.locator('.debt-confirm[open] .sheet-content').waitFor({state:'visible'});await np.getByRole('link',{name:'Not yet',exact:true}).waitFor({state:'visible'});
   check(engine,'without scripts confirmation and safe link work',await np.locator('.debt-confirm[open] .sheet-content').isVisible()&&await np.getByRole('link',{name:'Not yet',exact:true}).isVisible());
   await np.locator('.debt-confirm[open]').getByRole('button',{name:'Settle',exact:true}).click();await np.locator('[data-debt-receipt]').waitFor();
   check(engine,'without scripts settle removes the pair',await np.locator('[data-debt]').count()===0);
   await np.locator('[data-debt-receipt] summary').click();await np.locator('[data-debt-receipt] [name=reason]').fill('Native browser check');await np.getByRole('button',{name:'Undo settlement',exact:true}).click();
   check(engine,'without scripts undo restores the pair',await np.locator('[data-debt]').count()===1);await native.close();
  }
  if(process.env.PN_DESIGN_MODE!=='layout'){
   for(const reduced of [false,true]){
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:reduced?'reduce':'no-preference'}),page=await context.newPage();
    await login(page,f.receiver);await page.goto(`${BASE}/g/${f.group}/`);
    const fold=await page.evaluate(async()=>{const d=document.querySelector('.debt-detail'),summary=d.querySelector('summary'),closed=d.getBoundingClientRect().height,sizes=[];summary.click();for(let i=0;i<20;i++){await new Promise(requestAnimationFrame);sizes.push(d.getBoundingClientRect().height)}const full=d.getBoundingClientRect().height;return {closed,full,sizes};});
    check(engine,`${reduced?'reduced':'normal'} disclosure movement`,reduced?!fold.sizes.some(h=>h>fold.closed+1&&h<fold.full-1):fold.sizes.some(h=>h>fold.closed+1&&h<fold.full-1),fold);
    await page.locator('.debt-detail > summary').click();await page.waitForFunction(()=>!document.querySelector('.debt-detail').open&&!document.querySelector('.debt-detail').style.height);
    await page.evaluate(()=>{window.__debtFrames=[];document.addEventListener('turbo:render',()=>{for(let i=0;i<14;i++)requestAnimationFrame(()=>{document.querySelectorAll('.group-sessions:not(#debts),[data-debt],[data-debt-receipt]').forEach(el=>window.__debtFrames.push({key:el.dataset.debt||el.dataset.debtReceipt||el.getAttribute('aria-labelledby'),transform:getComputedStyle(el).transform,opacity:getComputedStyle(el).opacity}));});});});
    await page.getByRole('button',{name:'Got ₱200 from Ana',exact:true}).click();await page.locator('dialog.sheet[open]').getByRole('button',{name:'Settle',exact:true}).click();await page.locator('[data-debt-receipt]').waitFor();
    await page.waitForFunction(()=>window.__debtFrames.length>0);
    const {frames,moved}=await page.evaluate(()=>({frames:window.__debtFrames,moved:window.__debtFrames.some(x=>x.transform!=='none'&&Math.abs(new DOMMatrix(x.transform).m42)>1)}));
    check(engine,`${reduced?'reduced motion stays still':'remaining sections glide after settle'}`,reduced?!moved:moved,frames);
    await page.waitForFunction(()=>!document.querySelector('dialog.sheet[open]'));await page.locator('[data-debt-receipt] summary').click();await page.locator('[data-debt-receipt] [name=reason]').fill('Motion browser check');await page.getByRole('button',{name:'Undo settlement',exact:true}).click();await page.locator('[data-debt]').waitFor();
    await page.waitForFunction(()=>[...document.querySelectorAll('[data-debt], [data-debt-receipt], .group-sessions:not(#debts)')].every(e=>!e.style.transform&&!e.style.opacity));
    check(engine,`${reduced?'reduced':'normal'} motion cleans up inline styles`,true);
    await context.close();
   }
  }
 }finally{await browser.close();}
}
writeFileSync(`${OUT}/design-results.json`,JSON.stringify(results,null,2));console.log(`${results.length} checks passed`);
