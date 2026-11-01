// Slice F: real host writes, cross-phone state changes and interruptible motion.
// Seed a fresh temporary database with seed.py and seed_fluid.py. PN_DB selects that database.
// This script consumes its fixtures. See README.md for the server and capture paths.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-fluid-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-fluid-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
// A write by someone else: the services, in another process.
const other=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from games import services as games
from ledger import services as ledger
from ledger.models import FinalCount
from groups.models import Member
host=Member.objects.get(user__username='hana',role='host')
u=uuid.uuid4
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-600))};
rmSync('/private/tmp/pn-fluid-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9359','--user-data-dir=/private/tmp/pn-fluid-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9359/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call is logged, and every redraw is photographed in numbers on its first frame:
// what each row shows, how far it is from its place and how opaque it is.
const LOG=`addEventListener('DOMContentLoaded',()=>{
 window.__runs=[];window.__errors=[];window.__f=[];
 addEventListener('error',e=>__errors.push(e.message));addEventListener('unhandledrejection',e=>__errors.push(String(e.reason)));
 if(window.Motion){const animate=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:el.className+'',keys:Object.keys(k),duration:o.duration,delay:o.delay||0});return animate.apply(this,arguments)}}
 document.addEventListener('live:updated',()=>requestAnimationFrame(()=>{
  const live=document.getElementById('live');if(!live)return;
  const head=live.querySelector('[data-carry=title]'),work=live.querySelector('.count-workspace,.table-players,.final-results');
  const read=el=>el?{o:+getComputedStyle(el).opacity,x:new DOMMatrix(getComputedStyle(el).transform).m41,top:el.getBoundingClientRect().top}:null;
  const fold=live.querySelector('.prep-done'),tick=fold&&fold.querySelector('summary .prep-mark path'),felt=live.querySelector('.table-v2 .felt');
  __f.push({state:live.dataset.state,head:read(head),work:read(work),fold:fold?{open:fold.open,tick:getComputedStyle(tick).animationName}:null,
   pot:live.querySelector('.display-amount')?.textContent.trim(),clip:felt?getComputedStyle(felt).clipPath:null,
   rows:[...live.querySelectorAll('.player-row')].map(r=>({o:+getComputedStyle(r).opacity,y:new DOMMatrix(getComputedStyle(r).transform).m42,text:r.querySelector('.player-figure').textContent.trim()}))});
 }))})`;
async function user(name,width=390,setup){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);if(setup)await setup(s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // Waits for the next redraw of the live region; the poll is asked at once instead of after 4s.
 const redraw=async(poke=true)=>{const n=await js('__f.length');if(poke)await js(`window.dispatchEvent(new Event('online'))`);for(let i=0;i<120;i++){if(await js('__f.length')>n)return await js('__f.at(-1)');await sleep(50)}return null};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,shot,redraw};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail)}`)};
const until=async(A,expr)=>{for(let i=0;i<100;i++){if(await A.js(expr))return true;await sleep(20)}return false};
const frame=async(A,state,step)=>{const n=await A.js('__f.length');await A.js(step);await until(A,`__f.length>${n}&&__f[${n}].state==='${state}'`);return A.js(`__f[${n}]`)};
const press=action=>`(()=>{const b=document.querySelector('.host-controls button[value=${action}]');b.form.requestSubmit(b)})()`;
try {
 const H=await user('hana');await H.js(`localStorage.setItem('rack-dock','open')`);await H.go(`/s/${M.start.set}/`);
 const P=await user('ben');await P.go(`/s/${M.start.set}/`);
 const head=await H.js(`document.querySelector('[data-carry=title]').getBoundingClientRect().top`);
 let f=await frame(H,'running',press('start'));await P.js(`window.dispatchEvent(new Event('online'))`);
 check('host first write: Start shows the accepted pot on its first frame',f?.state==='running'&&f.pot==='₱2,000'&&f.rows.every(r=>r.o===1),f);
 check('host first write: felt keeps its existing 500ms sweep',f?.clip?.startsWith('inset(')&&await H.js(`__runs.some(r=>r.keys.includes('clipPath')&&r.duration===0.5)`),f);
 await until(P,`__f.some(f=>f.state==='running')`);
 check('another phone sees the start and the same exact pot',await P.js(`__f.some(f=>f.state==='running'&&f.pot==='₱2,000')&&__runs.some(r=>r.keys.includes('clipPath'))`),await P.js(`({frames:__f,runs:__runs,errors:__errors})`));
 await sleep(1000);
 check('start ends within 900ms and leaves no hidden row or inline movement',await H.js(`[...document.querySelectorAll('.player-row,.pot-side,.table-v2 .felt')].every(r=>getComputedStyle(r).opacity==='1'&&!r.style.transform&&!r.style.clipPath&&!r.style.opacity)&&document.getAnimations().length===0`));
 await H.shot('fluid-start-390');
 f=await frame(H,'reconciliation',press('end'));
 check('count-up keeps the head in place and advances the workspace',f.head.o===1&&f.head.x===0&&Math.abs(f.head.top-head)<1&&f.work.o<1&&f.work.x>0&&f.work.x<=12,f);
 await sleep(350);await H.shot('fluid-count-390');
 await H.js(`document.querySelector('.host-more').open=true`);await sleep(250);
 f=await frame(H,'running',press('resume'));
 check('Resume play moves back, with the head fixed and no second felt sweep',f.head.o===1&&f.head.x===0&&f.work.x<0&&f.work.x>=-12&&await H.js(`__runs.filter(r=>r.keys.includes('clipPath')).length===1`),f);
 await sleep(400);
 await frame(H,'reconciliation',press('end'));await sleep(350);
 const ids=M.start.players;
 other(`ledger.confirm_counts(${M.start.set},host,{${ids[0]}:100000,${ids[1]}:100000},u())\nledger.cash_out_counted(${M.start.set},host,list(FinalCount.objects.filter(session_id=${M.start.set},is_current=True).values_list('pk',flat=True)),u())`);
 await H.redraw();await sleep(1000);
 other(`from settlement import services as settlement\nsettlement.finalize(${M.start.set},host)`);
 f=await H.redraw();
 check('Final keeps the head in place and advances results',f.head.o===1&&f.head.x===0&&f.work.o<1&&f.work.x>0&&f.work.x<=12,f);
 const pos=await H.js(`(()=>{const b=document.querySelector('.next-opener');b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation()},{once:true});const r=b.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 await send('Input.dispatchMouseEvent',{type:'mousePressed',...pos,button:'left',clickCount:1},H.s);await sleep(200);
 const held=await H.js(`new DOMMatrix(getComputedStyle(document.querySelector('.next-opener')).transform).m42`);
 check('a held press takes over What next arrival',held>=0.8&&held<=1.2&&await H.js(`__runs.some(r=>r.el.includes('next-opener')&&r.keys.join()==='y'&&r.duration===undefined)`),held);
 await send('Input.dispatchMouseEvent',{type:'mouseReleased',...pos,button:'left',clickCount:1},H.s);await sleep(1000);
 check('What next arrival is bounded to 300ms, and release leaves no inline residue',await H.js(`[...document.querySelectorAll('.next-card,.final-results')].every(e=>!e.style.transform&&!e.style.opacity)&&__runs.filter(r=>r.el.includes('next-card')&&r.duration!==undefined).every(r=>r.duration+r.delay<=0.3)`),await H.js(`({styles:[...document.querySelectorAll('.next-card,.final-results')].map(e=>({name:e.className,style:e.getAttribute('style')})),runs:__runs.filter(r=>r.el.includes('next-card'))})`));
 await H.shot('fluid-final-390');
 for(const key of ['checklist','interrupt','poll']) {
  await H.go(`/s/${M[key].set}/`);
  if(key==='poll') await H.js(`(()=>{const original=window.fetch;window.fetch=function(input,options){if(typeof input==='string'&&input.includes('/state/')){const url=new URL(input,location.href);url.searchParams.set('v','-1');input=url.href}return original.call(this,input,options)};document.addEventListener('live:updated',()=>window.dispatchEvent(new Event('online')),{once:true})})()`);
  f=await frame(H,'setup',`document.querySelector('.host-more').open=true;document.querySelector('details[data-key="add-one"]').open=true;document.querySelector('details[data-key="add-one"] button[type=submit]').click()`);
  check(`${key}: the completed tick is visible before the fold closes`,f.fold?.open&&f.fold.tick==='tick-draw',f);
  if(key==='interrupt') {
   await H.js(`document.querySelector('.prep-done > summary').click()`);await sleep(30);await H.js(`document.querySelector('.prep-done > summary').click()`);
  }
  await sleep(350);
  check(`${key}: completion ends within 300ms and honors a tap to reopen`,await H.js(`!document.querySelector('.prep-ticked,.prep-completing,.prep-folding')&&document.querySelector('.prep-done').open===${key==='interrupt'}&&document.querySelector('.host-controls .next-action').textContent==='Start the set'`));
  if(key==='checklist') check('the next step lights after the tick and fold',await H.js(`(()=>{const next=document.querySelector('.prep-title'),sample=document.createElement('span');sample.style.color='var(--brass)';next.append(sample);const ok=getComputedStyle(next).color===getComputedStyle(sample).color;sample.remove();return ok})()`));
  if(key==='poll') check('a poll during completion does not save an automatic open as user state',await H.js(`__f.length>=2&&!document.querySelector('.prep-done').open`));
 }
 // Native disclosure interruption reverses the current height, without a bespoke script.
 await H.go('/s/3/');
 await H.js(`document.querySelector('.set-facts > summary').click()`);await sleep(50);
 let d=await H.js(`(()=>{const el=document.querySelector('.set-facts'),c=getComputedStyle(el,'::details-content');return {h:parseFloat(c.blockSize),d:c.transitionDuration}})()`);
 await sleep(180);const full=await H.js(`parseFloat(getComputedStyle(document.querySelector('.set-facts'),'::details-content').blockSize)`);
 check('native disclosure opens at an intermediate height in 200ms',d.h>0&&d.h<full&&d.d.split(', ').includes('0.2s'),{...d,full});
 await H.js(`document.querySelector('.set-facts > summary').click()`);await sleep(40);await H.js(`document.querySelector('.set-facts > summary').click()`);await sleep(250);
 check('native disclosure reverses rapid taps and stays open with no leftover style',await H.js(`document.querySelector('.set-facts').open&&!document.querySelector('.set-facts').getAttribute('style')&&document.querySelector('.set-facts').getAnimations({subtree:true}).length===0`));
 for(const key of ['reduced','blocked']) {
  const A=await user('hana',390,s=>key==='reduced'?send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s):send('Network.setBlockedURLs',{urls:['*motion-14.0.0.js*']},s));
  await A.go(`/s/${M[key].set}/`);f=await frame(A,'running',press('start'));await sleep(350);
  check(`${key}: Start works, with the accepted amounts and no signature movement`,f.pot==='₱2,000'&&f.rows.every(r=>r.o===1&&r.y===0)&&await A.js(`__runs.length===0&&__errors.length===0`),f);
  check(`${key}: disclosure stays usable`,await A.js(`document.querySelector('.set-facts > summary').click();document.querySelector('.set-facts').open`));
 }
 check('no script or unhandled promise error in the host write flow',await H.js('__errors.length===0'),await H.js('__errors'));
 writeFileSync(`${OUT}/fluid.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(r=>r.ok).length} of ${results.length}`);if(results.some(r=>!r.ok))process.exitCode=1;
