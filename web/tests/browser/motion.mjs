// Motion system, stage 1 (motion.js on Motion 14.0.0). Seed a fresh temporary database with seed.py,
// seed_end_set.py, seed_night.py and seed_opening.py, then run against 127.0.0.1:8765.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-motion-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-motion-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),events=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)events.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call is logged, so a check can say what moved and with which properties.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k){__runs.push({el:(el.className||el.name||el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}})`;
async function user(name,width=390){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const mouse=async(type,expr)=>{const p=await js(`(()=>{const r=${expr}.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 // Since the set page revamp the host menu starts folded in play; these checks press its buttons.
 await js(`localStorage.setItem('rack-dock','open')`);
 return {s,js,go,shot,mouse};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1)`,dialog=`document.querySelector('dialog.sheet')`;
const ty=el=>`new DOMMatrix(getComputedStyle(${el}).transform).m42`;
const fail=async(A,words)=>{await A.js(`document.dispatchEvent(new CustomEvent('inplace:failed',{detail:{form:null,message:${JSON.stringify(words)}}}))`);await sleep(600)};
const buy=async(A,amount,ms=1500)=>{await A.js(`${opener}.click()`);await A.js(`(()=>{const f=${dialog}.querySelector('[name=amount]');f.value='${amount}';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);await sleep(ms)};
try {
 const A=await user('hana');await A.go('/s/3/');
 check('Motion loaded and switched on',await A.js(`!!window.Motion&&pokerMotion.on()&&document.documentElement.classList.contains('motion-on')`));
 // Buttons: a press sinks, a release springs back and leaves no inline style.
 const btn=`document.querySelector('.host-controls .next-action')`;
 await A.js(`${btn}.addEventListener('click',e=>e.preventDefault(),{once:true})`);
 await A.mouse('mousePressed',btn);await sleep(120);
 check('press: the button sinks',await A.js(`${ty(btn)}>1`));await A.shot('motion-press');
 await A.mouse('mouseReleased',btn);await sleep(700);
 check('release: the button is back with no inline transform',await A.js(`${ty(btn)}===0&&${btn}.style.transform===''`));
 check('busy control runs the progress line',await A.js(`(()=>{const b=${btn};b.setAttribute('aria-busy','true');const ok=getComputedStyle(b,'::after').animationName==='busy-line';b.removeAttribute('aria-busy');return ok})()`));
 // Sheets: rise with a spring, rest at the bottom edge, close from wherever they are.
 await A.js(`${opener}.click()`);await sleep(60);
 check('sheet: open at once and rising',await A.js(`${dialog}.open&&${ty(dialog)}>20`));await A.shot('motion-sheet-rising');
 await sleep(800);
 check('sheet: at rest on the bottom edge',await A.js(`${ty(dialog)}===0&&Math.round(${dialog}.getBoundingClientRect().bottom)===844`));
 await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(60);
 check('sheet: still open while leaving',await A.js(`${dialog}.open&&${ty(dialog)}>0`));await sleep(500);
 check('sheet: closed, no leftover style, focus on its opener',await A.js(`!${dialog}.open&&${dialog}.style.transform===''&&document.activeElement===${opener}`));
 await A.js(`${opener}.click()`);await sleep(50);await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(500);
 check('sheet: a close during the rise closes it',await A.js(`!${dialog}.open&&!${dialog}.classList.contains('closing')`));
 // An action sent while the sheet is still rising is accepted without waiting.
 const count=`document.querySelectorAll('.buy-stack i').length`;const c0=await A.js(count);
 await A.js(`window.__t=0;addEventListener('turbo:before-fetch-request',()=>{window.__t=performance.now()-window.__c},{once:true})`);
 await A.js(`${opener}.click()`);await A.js(`(()=>{const f=${dialog}.querySelector('[name=amount]');f.value='500';window.__c=performance.now();f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);await sleep(1500);
 check('action during the rise is sent within 50ms',await A.js(`window.__t>0&&window.__t<50`));
 check('action during the rise is recorded and the sheet closes',await A.js(count)>c0&&await A.js(`!${dialog}.open`));
 // Toasts: arrive, stack, and leave.
 await fail(A,'The first message was not sent.');
 check('toast: shown',await A.js(`document.querySelectorAll('.toast').length===1&&getComputedStyle(document.querySelector('.toast')).opacity==='1'`));
 await fail(A,'The second message was not sent.');
 check('toasts: the second pushes the first up',await A.js(`(()=>{const t=[...document.querySelectorAll('.toast')].map(x=>x.getBoundingClientRect());return t.length===2&&t[0].bottom<=t[1].top})()`));await A.shot('motion-toasts');
 await A.js(`[...document.querySelectorAll('.toast')].at(-1).querySelector('button').click()`);await sleep(60);
 check('toast: leaving, still drawn',await A.js(`document.querySelectorAll('.toast.leaving').length===1`));await sleep(700);
 check('toast: gone, and the other drops to the base line',await A.js(`document.querySelectorAll('.toast').length===1&&Math.round(${ty(`document.querySelector('.toast')`)})===0`));
 // A refusal nudges the field that explains it.
 await A.js(`__runs.length=0`);await A.js(`${opener}.click()`);await A.js(`(()=>{const f=${dialog}.querySelector('[name=amount]');f.value='abc';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);await sleep(1500);
 check('refusal: sheet stays and the amount field is nudged',await A.js(`!!document.querySelector('dialog[open] .sheet-error')&&__runs.some(r=>r.keys.join()==='x'&&r.el.includes('sheet-amount'))`));
 await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(500);
 // Only movement and opacity are animated by Motion.
 await A.js(`${btn}.addEventListener('click',e=>e.preventDefault(),{once:true})`);await A.mouse('mousePressed',btn);await A.mouse('mouseReleased',btn);await sleep(400);
 check('Motion animates only movement, scale and opacity',await A.js(`__runs.length>0&&__runs.every(r=>r.keys.every(k=>['x','y','scale','opacity','transform'].includes(k)))`));
 // The host menu opens with the spring.
 const toggle=`document.querySelector('.dock-toggle')`,dock=`document.querySelector('.host-controls')`;
 await A.js(`${toggle}.click()`);await sleep(700);
 check('host menu: opening uses a spring curve',await A.js(`(()=>{${toggle}.click();const a=${dock}.getAnimations()[0];return !!a&&a.effect.getTiming().easing.startsWith('linear(')})()`));await sleep(900);
 check('host menu: at rest, expanded',await A.js(`${dock}.getAnimations().length===0&&${toggle}.getAttribute('aria-expanded')==='true'`));
 // Ten screen changes leave nothing running and one set of listeners.
 for(let i=0;i<5;i++){await A.js(`Turbo.visit('/')`);await sleep(500);await A.js(`Turbo.visit('/s/3/')`);await sleep(600)}
 await A.js(`__runs.length=0`);await A.js(`${btn}.addEventListener('click',e=>e.preventDefault(),{once:true})`);await A.mouse('mousePressed',btn);await sleep(100);
 check('after ten screen changes: one press, one animation',await A.js(`__runs.length===1`));
 await A.mouse('mouseReleased',btn);await sleep(700);
 check('after ten screen changes: nothing left running',await A.js(`document.getAnimations().filter(a=>a.playState==='running'&&!(a.animationName||'').startsWith('busy')).length===0&&__errors.length===0`));
 // Desktop width.
 const D=await user('hana',1280);await D.go('/s/3/');await D.js(`${opener}.click()`);await sleep(800);
 check('1280px: the sheet rests on the bottom edge',await D.js(`${dialog}.open&&${ty(dialog)}===0`));await D.shot('motion-sheet-1280');
 // Reduced motion: nothing moves and every state still changes.
 const R=await user('hana');await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await R.go('/s/3/');
 check('reduced motion: Motion is off',await R.js(`!pokerMotion.on()&&!document.documentElement.classList.contains('motion-on')`));
 await R.mouse('mousePressed',btn.replace('A.','R.'));await sleep(80);check('reduced motion: a press does not move',await R.js(`${ty(btn)}===0`));
 await R.js(`${btn}.addEventListener('click',e=>e.preventDefault(),{once:true})`);await R.mouse('mouseReleased',btn);
 await R.js(`${opener}.click()`);check('reduced motion: sheet open at rest at once',await R.js(`${dialog}.open&&${ty(dialog)}===0`));
 await R.js(`${dialog}.querySelector('.sheet-head button').click()`);check('reduced motion: sheet closes at once',await R.js(`!${dialog}.open`));
 await sleep(150); // the dialog's close event is delivered a moment after close()
 const r0=await R.js(count);await buy(R,500);
 await fail(R,'Not sent.');
 check('reduced motion: action recorded, toast shown',await R.js(count)>r0&&await R.js(`document.querySelectorAll('.toast').length===1`));
 await R.js(`document.querySelector('.toast button').click()`);
 check('reduced motion: toast leaves at once, nothing animated',await R.js(`document.querySelectorAll('.toast').length===0&&__runs.length===0`));
 // The Motion file does not load: the app works with its plain CSS motion.
 const B=await user('hana');await send('Network.setBlockedURLs',{urls:['*motion-14.0.0.js*']},B.s);await B.go('/s/3/');
 check('blocked library: Motion is off, no error',await B.js(`!window.Motion&&!pokerMotion.on()&&!document.documentElement.classList.contains('motion-on')&&__errors.length===0`));
 await B.js(`${opener}.click()`);await sleep(500);check('blocked library: sheet opens',await B.js(`${dialog}.open`));
 await B.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(400);check('blocked library: sheet closes',await B.js(`!${dialog}.open`));
 const b0=await B.js(count);await buy(B,500);
 await fail(B,'Not sent.');
 check('blocked library: action recorded, toast shown, no error',await B.js(count)>b0&&await B.js(`document.querySelectorAll('.toast').length===1&&__errors.length===0`));
 await B.js(`document.querySelector('.toast button').click()`);check('blocked library: toast dismissed',await B.js(`document.querySelectorAll('.toast').length===0`));
 await B.js(`${toggle}.click()`);await sleep(600);check('blocked library: host menu still slides and settles',await B.js(`${toggle}.getAttribute('aria-expanded')==='false'&&${dock}.getAnimations().length===0`));
 writeFileSync(`${OUT}/motion.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
