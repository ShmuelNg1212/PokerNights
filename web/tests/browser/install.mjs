// Installable app: manifest, service worker, offline notice and page, kill switch, refresh on return.
// Seed a fresh temporary database with seed.py, seed_end_set.py and seed_night.py first. This script
// stops and restarts the Django server on 127.0.0.1:8765 itself (PN_DB names the SQLite file).
import {spawn,execSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-install-review';mkdirSync(OUT,{recursive:true});
const DB=process.env.PN_DB||'/private/tmp/pn-dock-check.sqlite3';const BASE='http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function stopServer(){try{execSync('pkill -f "runserver 127.0.0.1:8765"')}catch{}}
async function startServer(extra={}){stopServer();await sleep(700);spawn('.venv/bin/python',['manage.py','runserver','127.0.0.1:8765','--noreload'],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB,...extra},stdio:'ignore',detached:true}).unref();for(let i=0;i<40;i++){try{if((await fetch(BASE+'/healthz')).ok)return}catch{}await sleep(250)}throw Error('server did not start')}
rmSync('/private/tmp/pn-install-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9355','--user-data-dir=/private/tmp/pn-install-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9355/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// The default browser context, not an incognito one: Chrome refuses to call an incognito page installable.
const{targetId}=await send('Target.createTarget',{url:'about:blank'});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:BASE+path},s).catch(()=>{});await sleep(500);for(let i=0;i<30;i++){try{if(await js('document.readyState')==='complete')break}catch{}await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(700)};
const shot=async name=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const swState=`(async()=>{const regs=await navigator.serviceWorker.getRegistrations();const keys=await caches.keys();const urls=[];for(const k of keys){for(const r of await (await caches.open(k)).keys())urls.push(new URL(r.url).pathname)}return {scopes:regs.map(r=>new URL(r.scope).pathname),active:regs.map(r=>!!r.active),keys,urls}})()`;
try {
 await startServer();
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 // Installability, as Chrome itself judges it.
 await go('/');await js(`navigator.serviceWorker.ready.then(()=>true)`);
 const manifest=await send('Page.getAppManifest',{},s);console.log('  manifest url',manifest.url,'errors',JSON.stringify(manifest.errors));
 check('manifest is found and parses without errors',manifest.url.endsWith('/static/manifest.webmanifest')&&manifest.errors.length===0);
 const inst=await send('Page.getInstallabilityErrors',{},s);console.log('  installability errors',JSON.stringify(inst.installabilityErrors));
 check('Chrome reports no installability error',inst.installabilityErrors.length===0);
 check('touch icon, manifest link and standalone meta are in the page',await js(`!!document.querySelector('link[rel=apple-touch-icon][href$="app-180.png"]')&&!!document.querySelector('link[rel=manifest]')&&document.querySelector('meta[name=apple-mobile-web-app-capable]').content==='yes'`));
 check('icons are served as PNG',await js(`Promise.all(['180','192','512','maskable-512'].map(n=>fetch('/static/icons/app-'+n+'.png').then(r=>r.ok&&r.headers.get('content-type').includes('png')))).then(a=>a.every(Boolean))`));
 // The worker: scope, and a cache with exactly the offline page.
 let st=await js(swState);console.log('  worker',JSON.stringify(st));
 check('worker is active at scope /',st.scopes.length===1&&st.scopes[0]==='/'&&st.active[0]);
 check('its cache holds exactly the offline page',st.keys.length===1&&JSON.stringify(st.urls)==='["/offline/"]');
 // Walk the app, then confirm nothing else was cached and pages come from the server.
 for(const p of ['/','/g/1/','/g/1/?view=stats','/n/1/','/s/3/','/s/3/log/'])await go(p);
 st=await js(swState);check('after browsing, the cache still holds only the offline page',JSON.stringify(st.urls)==='["/offline/"]');
 await go('/g/1/?view=settings');const before=await js(`document.querySelector('main').textContent.includes('Fresh Table 77')`);
 await js(`(()=>{const f=[...document.querySelectorAll('form')].find(f=>f.action.includes('/tables/new/'));f.querySelector('[name=name]').value='Fresh Table 77';f.querySelector('[name=seat_count]').value='6';f.submit()})()`);await sleep(900);await go('/g/1/?view=settings');
 check('a changed page is served fresh, never from the worker',!before&&await js(`document.querySelector('main').textContent.includes('Fresh Table 77')`));
 // Every screen has a way back in standalone display mode.
 await send('Emulation.setEmulatedMedia',{features:[{name:'display-mode',value:'standalone'}]},s);
 const screens=['/g/1/','/g/1/?view=stats','/g/1/?view=settings','/g/1/sessions/new/','/g/1/presets/new/','/g/1/archive/','/g/1/delete/','/n/1/','/n/1/archive/','/n/1/delete/','/s/3/','/s/3/log/','/s/3/settings/','/s/3/players/add-several/','/s/2/','/s/2/cash-out-counted/','/s/1/'];let dead=[];
 for(const p of screens){await go(p);const ok=await js(`[...document.querySelectorAll('a[href]')].some(a=>a.getClientRects().length&&(a.matches('.brand')||a.closest('.table-bar')||/back|keep the/i.test(a.textContent)||a.closest('p.small')))`);if(!ok)dead.push(p)}
 console.log('  screens walked',screens.length,'without a way back',JSON.stringify(dead));check('every screen has a way back in standalone mode',dead.length===0);
 await send('Emulation.setEmulatedMedia',{features:[]},s);
 // Refresh on return.
 const away=async(setup='')=>{await js(`window.__mark=1;window.pokerNights.awayMs(0);${setup}`);await js(`(()=>{let h=true;Object.defineProperty(document,'hidden',{get:()=>h,configurable:true});document.dispatchEvent(new Event('visibilitychange'));h=false;document.dispatchEvent(new Event('visibilitychange'))})()`);await sleep(1200);return await js(`window.__mark!==1`)};
 await go('/n/1/');check('a session page reloads on return',await away());
 await go('/');check('Your groups reloads on return',await away());
 await go('/s/3/');check('a set page does not reload (it refreshes itself)',!(await away()));
 await go('/g/1/sessions/new/');check('a page with typed text does not reload',!(await away(`document.querySelector('[name=location]').value='typed';`)));
 await go('/g/1/sessions/new/');check('an untouched form page reloads',await away());
 await go('/s/3/');await js(`document.querySelector('[data-sheet-open]').click()`);await sleep(400);check('a page with an open sheet does not reload',await js(`!!document.querySelector('dialog[open]')`)&&!(await away()));
 await go('/n/1/');await js(`window.__mark=1;(()=>{let h=true;Object.defineProperty(document,'hidden',{get:()=>h,configurable:true});document.dispatchEvent(new Event('visibilitychange'));h=false;document.dispatchEvent(new Event('visibilitychange'))})()`);await sleep(900);check('a short absence does not reload',await js(`window.__mark===1`));
 // Offline notice and blocked submit (the browser reports offline; the server is still up).
 await go('/g/1/sessions/new/');
 check('notice is hidden while online',await js(`document.getElementById('offline-notice').hidden&&!document.documentElement.classList.contains('is-offline')`));
 await send('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1},s);await sleep(600);
 check('notice appears when the phone goes offline',await js(`(()=>{const n=document.getElementById('offline-notice');return !n.hidden&&n.getClientRects().length>0&&n.getAttribute('role')==='status'&&n.getBoundingClientRect().top===0})()`));
 check('the header sits below the notice, not under it',await js(`Math.round(document.querySelector('.site-header').getBoundingClientRect().top)>=Math.round(document.getElementById('offline-notice').getBoundingClientRect().bottom)`));
 for(const w of [320,390]){await send('Emulation.setDeviceMetricsOverride',{width:w,height:844,deviceScaleFactor:1,mobile:true},s);check('notice fits '+w,await js(`document.documentElement.scrollWidth<=${w}`));await shot('install-notice-'+w)}
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 await js(`document.querySelector('form.form-groups').noValidate=true;document.querySelector('[name=location]').value='kept';window.__here=1`);await click(`document.querySelector('form.form-groups [type=submit]')`);
 check('a form is not sent while offline and keeps what was typed',await js(`window.__here===1&&document.querySelector('[name=location]').value==='kept'&&document.getElementById('offline-notice').classList.contains('nudge')&&document.querySelector('form.form-groups [type=submit]').disabled===false`));
 await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1},s);await sleep(600);
 check('notice clears when the connection returns',await js(`document.getElementById('offline-notice').hidden&&!document.documentElement.classList.contains('is-offline')`));
 // A navigation that fails (the server is gone) shows the offline page; Try again recovers.
 await go('/n/1/');stopServer();await sleep(900);
 await go('/g/1/');
 check('a failed navigation shows the offline page',await js(`document.title.startsWith("You're offline")&&${text("You're offline")}&&!!document.getElementById('retry')&&location.pathname==='/g/1/'`));
 console.log('  offline page',await js(`JSON.stringify({back:document.getElementById('back').hidden,hist:history.length,res:performance.getEntriesByType('resource').map(e=>e.name)})`));check('the offline page offers Go back and uses no outside file',await js(`!document.getElementById('back').hidden&&!document.querySelector('link[rel=stylesheet]')&&!document.querySelector('script[src]')&&!document.querySelector('img')`));
 for(const w of [320,390,1280]){await send('Emulation.setDeviceMetricsOverride',{width:w,height:844,deviceScaleFactor:1,mobile:w<900},s);check('offline page fits '+w,await js(`document.documentElement.scrollWidth<=${w}&&[...document.querySelectorAll('a,button')].filter(e=>!e.hidden).every(e=>e.getBoundingClientRect().height>=48)`));await shot('install-offline-'+w)}
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 await startServer();await click(`document.getElementById('retry')`);await sleep(600);
 check('Try again returns to the real page once the server answers',await js(`location.pathname==='/g/1/'&&!!document.querySelector('.site-header')&&!document.title.startsWith("You're offline")`));
 // A failed form post also lands on the offline page, and Go back returns to the form.
 await go('/g/1/sessions/new/');stopServer();await sleep(900);await js(`document.querySelector('form.form-groups').noValidate=true;document.querySelector('[name=location]').value='still here'`);await click(`document.querySelector('form.form-groups [type=submit]')`);await sleep(600);
 check('a failed form post shows the offline page',await js(`document.title.startsWith("You're offline")`));
 await startServer();
 // Kill switch: the next worker removes itself and its cache, and pages stop registering one.
 await startServer({SERVICE_WORKER:'False'});await go('/');await sleep(2500);await go('/');await sleep(1500);
 st=await js(swState);console.log('  after kill switch',JSON.stringify(st));
 check('kill switch removes the worker and its cache',st.scopes.length===0&&st.keys.length===0);
 check('pages no longer ask for a worker',await js(`document.documentElement.dataset.sw===undefined`));
 // Without JavaScript nothing changes.
 await startServer();await send('Emulation.setScriptExecutionDisabled',{value:true},s);await go('/n/1/');
 check('no JavaScript: notice stays hidden and the page renders',await js(`document.getElementById('offline-notice').hidden&&!!document.querySelector('.night-layout')`));
 await send('Emulation.setScriptExecutionDisabled',{value:false},s);
 writeFileSync(`${OUT}/install.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill();stopServer()}
if(results.some(x=>!x.ok))process.exitCode=1;
