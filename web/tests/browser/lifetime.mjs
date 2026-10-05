import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-lifetime-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:(process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765')+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

// Script lifetime: every page script starts and stops cleanly. Run after seed.py, seed_end_set.py and seed_night.py.
const polls=async(A,ms)=>{await A.js(`window.__polls=0;window.__f=window.__f||window.fetch;window.fetch=function(u){if(String(u).includes('/state/'))window.__polls++;return window.__f.apply(this,arguments)}`);await sleep(ms);return await A.js('window.__polls')};
try {
 const A=await user('hana');await send('Runtime.enable',{},A.s);const errs=[];const seen=new Set();
 await A.go('/s/3/');
 check('page scripts are registered and running',await A.js(`!!window.pokerPage&&pokerPage.running()`));
 check('all scripts load from the head, none from the body',await A.js(`document.querySelectorAll('head script[src]').length>=14&&document.querySelectorAll('body script').length===0`));
 check('a fresh set page: one sheet dialog, dock ready',await A.js(`document.querySelectorAll('dialog.sheet').length===1&&!document.querySelector('.dock-toggle').hidden&&document.documentElement.classList.contains('sheets-enabled')`));
 check('a fresh set page polls once every four seconds',[2,3].includes(await polls(A,8500)));
 // Stop and start ten times, as ten screen changes would.
 await A.js(`for(let i=0;i<10;i++){pokerPage.stop();pokerPage.start()}`);
 check('after ten restarts: still one dialog',await A.js(`document.querySelectorAll('dialog.sheet').length===1`));
 const n=await polls(A,8500);console.log('  polls in 8.5 s after ten restarts:',n);
 check('after ten restarts: still one poll loop',[2,3].includes(n));
 await A.click(`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1)`);
 check('after ten restarts: one tap opens one sheet',await A.js(`document.querySelectorAll('dialog[open]').length===1`));
 await A.click(`document.querySelector('dialog .sheet-head button')`);
 check('after ten restarts: the dock toggle still collapses once per tap',await A.js(`(()=>{const b=document.documentElement.classList.contains('dock-collapsed');document.querySelector('.dock-toggle').click();return document.documentElement.classList.contains('dock-collapsed')!==b})()`));
 await A.click(`document.querySelector('.dock-toggle')`);
 // Stopped: nothing keeps running.
 await A.click(`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1)`);await A.js(`pokerPage.stop()`);
 check('stopped: the sheet is closed and removed, with its content back in the page',await A.js(`document.querySelectorAll('dialog').length===0&&!document.documentElement.classList.contains('sheets-enabled')&&!document.documentElement.classList.contains('dock-enabled')&&document.querySelectorAll('[data-sheet-source] .sheet-content').length===document.querySelectorAll('[data-sheet-source]').length`));
 const quiet=await polls(A,8500);console.log('  polls in 8.5 s while stopped:',quiet);
 check('stopped: no poll at all',quiet===0);
 check('stopped: a tap on a sheet button does nothing and raises no error',await A.js(`(()=>{[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1).click();return document.querySelectorAll('dialog[open]').length===0})()`));
 await A.js(`pokerPage.start()`);
 check('started again: everything is back',await A.js(`document.querySelectorAll('dialog.sheet').length===1&&!document.querySelector('.dock-toggle').hidden`)&&[2,3].includes(await polls(A,8500)));
 // The other pages: start and stop without their elements, and the modules that do apply still work.
 for(const p of ['/','/g/1/','/g/1/?view=settings','/n/1/','/s/2/','/g/1/sessions/new/','/s/3/players/add-several/']){await A.go(p);await A.js(`for(let i=0;i<5;i++){pokerPage.stop();pokerPage.start()}`);
  check('restarts are clean on '+p,await A.js(`pokerPage.running()&&document.querySelectorAll('dialog.sheet').length<=1`));}
 await A.go('/s/3/players/add-several/');await A.js(`for(let i=0;i<3;i++){pokerPage.stop();pokerPage.start()}`);
 check('the player picker still shows its search after restarts',await A.js(`!document.querySelector('[data-pick-search-box]')||!document.querySelector('[data-pick-search-box]').hidden`));
 await A.go('/s/2/');await A.js(`for(let i=0;i<3;i++){pokerPage.stop();pokerPage.start()}`);await A.js(`(()=>{const f=document.querySelector('[data-count-input]');f.value='5';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('the count preview still follows typing after restarts',await A.js(`document.querySelector('[data-count-preview] [data-count-label]').textContent.includes('unsaved')`));
 const B=await user('');await B.go('/accounts/login/');await B.js(`for(let i=0;i<3;i++){pokerPage.stop();pokerPage.start()}`);await B.click(`document.querySelector('[data-password-toggle]')`);
 check('the Show button still toggles once per tap after restarts',await B.js(`document.querySelector('[name=password]').type==='text'`));
 writeFileSync(`${OUT}/lifetime.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
