// Phone-width geometry and first frames in Chromium and WebKit. See README.md for the isolated
// Playwright test tool. The application has no Playwright dependency. Use fresh seed.py/end_set/night/opening data.
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
const {chromium,webkit}=createRequire(import.meta.url)(process.env.PN_PLAYWRIGHT||'playwright');
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-mobile-motion-review';mkdirSync(OUT,{recursive:true});
const fixtures=JSON.parse(readFileSync('/private/tmp/pn-mobile-motion-manifest.json'));
const results=[];
const check=(engine,name,ok,detail)=>{results.push({engine,name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${engine}: ${name}${ok?'':' '+JSON.stringify(detail)}`)};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
for(const engine of (process.env.PN_ENGINES||'chromium,webkit').split(',')){
 const browser=await (engine==='webkit'?webkit:chromium).launch(engine==='webkit'?{}:{executablePath:process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try {
  for(const fallback of [false,true]){
   const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
   if(fallback){
    // Remove the actual CSS enhancement as well as the JS capability. This exercises the fallback
    // in Chromium too; a JS-only override would leave native CSS motion running underneath it.
    await context.route('**/static/css/app.css*',async route=>{const response=await route.fetch();await route.fulfill({response,body:(await response.text()).replace('@supports (interpolate-size: allow-keywords) and selector(details::details-content)','@supports (pn-test-unsupported: 1)')})});
    await context.addInitScript(()=>{const supports=CSS.supports.bind(CSS);CSS.supports=(...args)=>args[0]==='interpolate-size'?false:supports(...args)});
   }
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(BASE+'/accounts/login/');await page.locator('[name=username]').fill('hana');await page.locator('[name=password]').fill('tablestakes-91');
   await Promise.all([page.waitForURL(BASE+'/'),page.locator('form.form-section [type=submit]').click()]);
   const label=engine+(fallback?' fallback':' native');
   await page.goto(BASE+'/g/1/?view=settings');
   const native=await page.evaluate(()=>CSS.supports('interpolate-size','allow-keywords')&&CSS.supports('selector(details::details-content)'));
   console.log('CAPABILITY',label,JSON.stringify({native,version:browser.version()}));
   // One synchronous read during opening proves the content moves, not just its chevron.
   const measure=selector=>page.evaluate(async selector=>{
    const el=document.querySelector(selector);el.open=false;await new Promise(r=>setTimeout(r,250));
    const closed=el.getBoundingClientRect().height,heights=[];el.querySelector('summary').click();
    for(let i=0;i<22;i++){await new Promise(requestAnimationFrame);heights.push(el.getBoundingClientRect().height)}
    const full=el.getBoundingClientRect().height;
    return {closed,full,open:el.open,mid:heights.find(h=>h>closed+1&&h<full-1)};
   },selector);
   const sizes=await measure('#tables');
   check(label,'settings expands through an intermediate height',sizes.open&&sizes.mid>sizes.closed&&sizes.mid<sizes.full,sizes);
   await page.evaluate(async()=>{const s=document.querySelector('#tables > summary');s.click();await new Promise(r=>setTimeout(r,40));s.click()});await delay(350);
   check(label,'rapid close-open finishes open without clipping styles',await page.evaluate(()=>{const d=document.getElementById('tables');return d.open&&!d.style.height&&!d.style.overflow&&!d.hasAttribute('data-disclosure-closing')}));
   // A link inside an open disclosure must keep its own action.
   check(label,'disclosure controls remain reachable',await page.locator('#tables input:not([type=hidden])').first().isVisible());
   await page.goto(BASE+'/s/3/');
   const facts=await measure('.set-facts');
   check(label,'set Details content expands',facts.mid>facts.closed&&facts.mid<facts.full,facts);
   const closing=await page.evaluate(async()=>{
    const d=document.querySelector('.set-facts');d.querySelector('summary').click();
    // Establish the changed style now. A timer alone can defer style resolution in headless Chrome.
    void getComputedStyle(d.querySelector('.facts-more .icon')).transform;
    await new Promise(r=>setTimeout(r,50));
    const result={requestedClosed:!d.open||d.hasAttribute('data-disclosure-closing'),caret:new DOMMatrix(getComputedStyle(d.querySelector('.facts-more .icon')).transform).a,line:getComputedStyle(d.querySelector('.facts-line')).visibility};
    d.querySelector('summary').click();await new Promise(r=>setTimeout(r,350));return result;
   });
   check(label,'closing Details turns its caret and restores its summary at once',closing.requestedClosed&&closing.caret>-.99&&closing.line==='visible',closing);
   // A poll during a close must not restore an open that was only held for exit motion.
   const snapshot=await page.evaluate(()=>{const copy=document.getElementById('live').cloneNode(true);copy.querySelector('.set-facts').open=false;return {html:copy.innerHTML,state:'running',version:987654}});
   await page.evaluate(snapshot=>{
    const fetch=window.fetch;window.fetch=(input,options)=>String(input).includes('/s/3/state/')?Promise.resolve(new Response(JSON.stringify(snapshot),{headers:{'Content-Type':'application/json'}})):fetch(input,options);
    document.querySelector('.set-facts > summary').click();window.dispatchEvent(new Event('online'));
   },snapshot);
   await page.waitForFunction(()=>document.getElementById('live').dataset.version==='987654');await delay(350);
   check(label,'live update settles a closing disclosure closed',await page.evaluate(()=>{const el=document.querySelector('.set-facts');return !el.open&&!el.style.height&&!el.hasAttribute('data-disclosure-closing')}));
   // Sample the sheet on every frame before its real delegated click handler runs.
   const sheet=await page.evaluate(async()=>{
    const d=document.querySelector('dialog.sheet'),frames=[];let sampling=true;
    function frame(){if(d.open)frames.push({y:new DOMMatrix(getComputedStyle(d).transform).m42,opacity:+getComputedStyle(d).opacity});if(sampling)requestAnimationFrame(frame)}
    requestAnimationFrame(frame);document.querySelector('[data-sheet-open^=buy]').click();await new Promise(r=>setTimeout(r,850));sampling=false;
    return {first:frames[0],last:frames.at(-1),style:d.style.transform,open:d.open};
   });
   check(label,'sheet begins below the screen and cleans its entry style',sheet.open&&sheet.first?.y>20&&sheet.last?.y===0&&sheet.style==='',sheet);
   await page.locator('dialog[open] .sheet-head button').click();await delay(350);
   await page.evaluate(()=>{document.querySelector('[data-sheet-open^=player]').click()});await delay(70);
   await page.locator('dialog[open] .sheet-head button').click();await delay(350);
   check(label,'close during entry leaves the sheet closed and clear',await page.evaluate(()=>{const d=document.querySelector('dialog.sheet');return !d.open&&!d.style.transform&&!d.classList.contains('closing')}));
   await page.evaluate(()=>document.querySelector('[data-sheet-open^=player]').click());await delay(650);
   await page.locator('dialog[open] [data-sheet-swap^=cash]').click();await delay(650);
   check(label,'player-to-cash-out swap is clear and keeps focus in the sheet',await page.evaluate(()=>{const d=document.querySelector('dialog.sheet'),b=d.querySelector('.sheet-body');return d.open&&d.querySelector('[name=amount]')===document.activeElement&&!b.style.transform&&!b.style.opacity}));
   await page.locator('dialog[open] .sheet-head button').click();await delay(350);
   // Pressing an actual touch target must open the account flyout. Its caret is measured at rest.
   await page.locator('.account-button').tap();await delay(700);
   const caret=await page.evaluate(()=>{const b=document.querySelector('.account-button').getBoundingClientRect(),p=document.querySelector('.account-panel'),r=p.getBoundingClientRect();return {open:document.getElementById('account').open,error:Math.abs(r.right-parseFloat(getComputedStyle(p).getPropertyValue('--caret'))-(b.left+b.width/2)),left:r.left,right:r.right}});
   check(label,'account touch opens an aligned flyout inside the phone',caret.open&&caret.error<=2&&caret.left>=8&&caret.right<=382,caret);
   await page.screenshot({path:`${OUT}/${engine}-${fallback?'fallback':'native'}-account.png`});
   await page.keyboard.press('Escape');await delay(300);
   await page.locator('.site-header .table-bar > a').tap();await page.waitForURL('**/n/*/');
   await page.goBack();await page.waitForURL(BASE+'/s/3/');await delay(500);
   check(label,'touch navigation and Back return to the set with no stale menu',await page.evaluate(()=>location.pathname==='/s/3/'&&!document.getElementById('account').open&&!document.querySelector('dialog[open]')));
   await page.emulateMedia({reducedMotion:'reduce'});
   await page.waitForFunction(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
   await page.evaluate(()=>{const d=document.querySelector('.set-facts');d.open=false;d.querySelector('summary').click()});
   check(label,'reduced motion opens the disclosure at rest',await page.evaluate(()=>{const d=document.querySelector('.set-facts');return d.open&&!d.style.height&&!d.getAnimations().length}));
   await page.emulateMedia({reducedMotion:'no-preference'});
   await page.goto(BASE+`/s/${fixtures[label]}/`);
   const completion=await page.evaluate(async()=>{
    const fetch=window.fetch;window.fetch=(input,options)=>{if(typeof input==='string'&&input.includes('/state/')){const url=new URL(input,location.href);url.searchParams.set('v','-1');input=url.href}return fetch(input,options)};
    const samples=[];let running=true;
    let updates=0;document.addEventListener('live:updated',()=>{updates++;sample()});
    document.addEventListener('live:updated',()=>window.dispatchEvent(new Event('online')),{once:true});
    function sample(){const d=document.querySelector('.prep-done');if(d)samples.push({open:d.open,tick:getComputedStyle(d.querySelector('.prep-mark .icon path')).animationName,height:d.getBoundingClientRect().height})}
    function frame(){sample();if(running)requestAnimationFrame(frame)}
    requestAnimationFrame(frame);
    document.querySelector('.host-more').open=true;document.querySelector('details[data-key="add-one"]').open=true;document.querySelector('details[data-key="add-one"] button[type=submit]').click();
    await new Promise(r=>setTimeout(r,1000));running=false;
    const d=document.querySelector('.prep-done');return {samples,updates,open:d?.open,height:d?.style.height,classes:!!document.querySelector('.prep-completing,.prep-folding,.prep-ticked')};
   });
   check(label,'checklist holds its tick and a live poll leaves the fold closed',completion.samples.some(x=>x.open&&x.tick==='tick-draw')&&completion.updates>=2&&!completion.open&&!completion.height&&!completion.classes,completion);
   check(label,'no runtime errors',errors.length===0,errors);
   const plain=await browser.newContext({storageState:await context.storageState(),viewport:{width:390,height:844},isMobile:true,hasTouch:true,javaScriptEnabled:false});
   const plainPage=await plain.newPage();await plainPage.goto(BASE+'/s/3/');await plainPage.locator('.set-facts > summary').tap();
   check(label,'without JavaScript the native disclosure still opens',await plainPage.locator('.set-facts').getAttribute('open')!==null);
   await plain.close();
   await context.close();
  }
 } finally {await browser.close()}
}
writeFileSync(`${OUT}/mobile-motion.json`,JSON.stringify(results,null,2));
console.log(`${results.filter(r=>r.ok).length} of ${results.length}`);
if(results.some(r=>!r.ok))process.exitCode=1;
