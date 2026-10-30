// Create session → the session page: the screen moves deeper in the same page. Run after seed_session_options.py on a fresh temporary database.
import {spawn} from 'node:child_process';
import {mkdirSync,rmSync,readFileSync,writeFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-session-arrival-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765',PROFILE='/private/tmp/pn-session-arrival-chrome',PORT=9352;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok,detail)=>{results.push(!!ok);console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,500)}`)};
// Every screen change the script starts, as in screens.mjs, and whether the browser animated a page load by itself.
const LOG=`(()=>{window.__vt=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));
 addEventListener('pagereveal',e=>{window.__loadMoved=!!e.viewTransition});
 const start=document.startViewTransition&&document.startViewTransition.bind(document);if(!start)return;
 document.startViewTransition=function(cb){const t=start(cb),rec={go:document.documentElement.dataset.go||'',anims:[],ok:null};__vt.push(rec);
  t.ready.then(()=>{rec.anims=document.getAnimations().filter(a=>a.effect&&a.effect.pseudoElement&&a.effect.pseudoElement.startsWith('::view-transition')).map(a=>({p:a.effect.pseudoElement.replace('::view-transition-',''),n:a.animationName||'',d:Math.round(a.effect.getComputedTiming().endTime)}))},e=>{rec.ok=false;rec.err=String(e)});
  t.finished.then(()=>{if(rec.ok===null)rec.ok=true});return t}})()`;
async function user(name,width,setup){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);if(setup)await setup(s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const settle=async()=>{await sleep(600);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(200)};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await settle()};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await settle();
 return {s,js,go,shot,settle};
}
const {group}=JSON.parse(readFileSync('/private/tmp/pn-session-options-manifest.json','utf8'));
const NEW=`/g/${group}/sessions/new/`,FORM=`document.querySelector('form.form-groups')`,TAP=`${FORM}.querySelector('[type=submit]').click()`;
// Sessions are numbered in order on a fresh database, so the number on the page says how many were made.
let last=0;const made=async A=>{const n=await A.js(`location.pathname.startsWith('/n/')?Number(location.pathname.split('/')[2]):-1`),more=n-last;if(n>0)last=n;return more};
// Marks this page, so a change of screen that keeps it can be told from a page load.
const mark=`window.__same=true;__vt.length=0`;
try{
 for(const width of [390,1280]){
  const W=`${width}px`,A=await user('hana',width);
  // Create
  await A.go(NEW);await A.js(mark);
  await A.js(TAP);for(let i=0,shot=false;i<200&&!shot;i++){await sleep(10);if(await A.js(`__vt.length>0&&__vt.at(-1).ok===null`)){await A.shot(`moving-${width}`);shot=true}}await A.settle();
  const r=await A.js(`({same:!!window.__same,path:location.pathname,vt:window.__vt&&__vt.at(-1)||null,n:window.__vt&&__vt.length,left:(document.documentElement.dataset.go||'')+document.querySelectorAll('[style*="view-transition-name"]').length})`);
  check(`${W} Create session lands on the session page`,/^\/n\/\d+\/$/.test(r.path),r);
  check(`${W} the change happens in the same page`,r.same,r);
  const moved=(p,n)=>r.vt&&r.vt.anims.some(a=>a.p===p&&a.n===n);
  check(`${W} the screen moves deeper`,r.vt&&r.vt.ok&&r.vt.go==='deeper'&&moved('old(root)','screen-out-left')&&moved('new(root)','screen-in-right'),r.vt);
  check(`${W} the top bar stays still and the movement lasts 300ms or less`,r.vt&&r.vt.anims.length&&r.vt.anims.every(a=>a.d<=300)&&!r.vt.anims.some(a=>a.p==='old(site-header)'||a.p==='new(site-header)'),r.vt);
  check(`${W} nothing is left on the page`,r.left==='0'&&await A.js(`__errors.length===0`),r);
  const one=await made(A);check(`${W} one session was made`,one===1,one);
  check(`${W} the session page runs`,await A.js(`!!document.querySelector('#announce')&&document.activeElement===document.getElementById('main')`));
  // Announced: the notice arrives with the screen.
  await A.go(NEW);await A.js(`document.querySelector('[name=announce]').checked=true;document.querySelector('[name=announce]').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[name=start_time]').value='20:30'`);await A.js(TAP);await A.settle();await made(A);
  check(`${W} the announced notice shows on arrival`,await A.js(`document.body.textContent.includes('Announced. Players can answer now.')`));
  // Double tap
  await A.go(NEW);await A.js(`${TAP};${TAP}`);await A.settle();let more=await made(A);
  check(`${W} a double tap makes one session`,more===1,more);
  // Back: a new request, so a second session
  await A.js(`history.back()`);await A.settle();
  check(`${W} Back shows the form, ready to send`,await A.js(`location.pathname===${JSON.stringify(NEW)}&&!${FORM}.dataset.sent&&!${FORM}.querySelector('[type=submit]').disabled`));
  await A.js(TAP);await A.settle();more=await made(A);
  check(`${W} creating again after Back makes a second session`,more===1,more);
  // Refusal: a chips preset on a pesos game
  await A.go(NEW);const chips=await A.js(`fetch(location.href).then(r=>r.text()).then(t=>new DOMParser().parseFromString(t,'text/html').querySelector('option[data-unit=chips]').value)`);
  await A.js(`(()=>{const c=document.querySelector('[name=chip_preset_id]'),o=document.createElement('option');o.value=${JSON.stringify(chips)};c.appendChild(o);c.value=${JSON.stringify(chips)};document.querySelector('[name=location]').value='Kept place'})();${mark}`);
  await A.js(TAP);await A.settle();
  check(`${W} a refusal stays on the form with the typed text and the reason`,await A.js(`location.pathname===${JSON.stringify(NEW)}&&document.body.textContent.includes('uses another unit')&&document.querySelector('[name=location]').value==='Kept place'`));
  check(`${W} a refusal stays in the same page and does not move the screen`,await A.js(`!!window.__same&&__vt.every(x=>x.go==='')`),await A.js(`[!!window.__same,window.__vt]`));
  check(`${W} the form can be sent again after a refusal`,await A.js(`!${FORM}.dataset.sent&&!${FORM}.querySelector('[type=submit]').disabled`));
  await A.js(`document.querySelector('[name=chip_preset_id]').value='';${TAP}`);await A.settle();more=await made(A);
  check(`${W} the corrected form makes one session`,more===1,more);
 }
 // Reduced motion
 const R=await user('hana',390,s=>send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s));
 await R.go(NEW);await R.js(mark);await R.js(TAP);await R.settle();await made(R);
 check('reduced motion: the session page arrives with no movement',await R.js(`location.pathname.startsWith('/n/')&&__vt.length===0`),await R.js(`[location.pathname,window.__vt]`));
 check('reduced motion: nothing is left on the page',await R.js(`!document.documentElement.dataset.go`));
}finally{await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(Boolean).length} of ${results.length}`);
if(results.some(x=>!x))process.exitCode=1;
