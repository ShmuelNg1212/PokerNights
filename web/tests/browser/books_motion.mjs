// Books off: motion (2026-10-17). On set 9 ("Recount needed") the gap panel arrives once when the last
// cash-out lands while the page watches, by a poll and by an action's in-place answer; not on reload, not on
// later redraws, not when only its amount changes. When a correction balances the books a copy of it leaves
// and the balanced rule draws; an override gets the leave only. Records change through the real services
// (manage.py shell) while the page watches. Seed a fresh database with seed.py and seed_end_set.py, serve it
// with PN_DB naming the SQLite file, then run.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-books-motion-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8774';
const DB=process.env.PN_DB || '/private/tmp/pn-agent4.sqlite3';
const PY=process.env.PN_PYTHON || '/Users/shm/PokerNights/.venv/bin/python';
const SET=9;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const PRE=`import uuid
from groups.models import Member
from games.models import Participant, GameSession
from games import services as G
from ledger import services as L
from ledger.models import CashOut
h=Member.objects.get(user__username='hana',role='host')
ps=list(Participant.objects.filter(session_id=${SET}).order_by('pk'))
def rev(i): L.reverse_cash_out(${SET},h,CashOut.objects.filter(participant=ps[i],reversal__isnull=True).latest('pk').pk,'Wrong amount')
def cash(i,a): L.record_cash_out(${SET},h,ps[i].pk,a,uuid.uuid4())
from django.db import transaction
# A correction seen in one redraw: what a watching phone sees when its poll covers both steps.
def fix(a):
    with transaction.atomic(): rev(1); cash(1,a)
def touch():G.touch(GameSession.objects.get(pk=${SET}))
`;
function py(code){const r=spawnSync(PY,['manage.py','shell','-c',PRE+code],{env:{...process.env,DEBUG:'True',DATABASE_URL:`sqlite:///${DB}`},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-800))}

rmSync('/private/tmp/pn-books-motion-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9354','--user-data-dir=/private/tmp/pn-books-motion-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9354/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call and error is logged. Each redraw notes, after changes.js has run, the gap panel's first
// frame (inline style, amount) and any copy left behind; the frame after, what is on screen.
const LOG=`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__runs=[];window.__frames=[];
addEventListener('DOMContentLoaded',()=>{
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className&&el.className.baseVal===undefined?el.className:el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}
 document.addEventListener('live:updated',()=>{const g=document.querySelector('#live #books-gap, #live .discrepancy'),c=document.querySelector('.books-ghost'),b=document.querySelector('[data-balance]');
  const f={gap:!!g,inline:g?[g.style.opacity,g.style.transform]:null,amount:g?g.querySelector('.discrepancy-amount').textContent.trim():null,
   ghost:c?{pos:getComputedStyle(c).position,pe:getComputedStyle(c).pointerEvents,op:c.style.opacity,hidden:c.getAttribute('aria-hidden'),role:c.getAttribute('role'),id:c.id}:null,
   balance:b?b.classList.contains('balance-arrived'):null};
  __frames.push(f);requestAnimationFrame(()=>{f.next=g?Number(getComputedStyle(g).opacity):null})});
});`;
async function user(name,width=390,{reduce=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:2,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const tap=async sel=>{await js(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({block:'center'})`);await sleep(100);const p=await js(`(()=>{const r=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 return {s,js,go,shot,tap};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,500)}`)};
// Waits for a redraw that satisfies the test, up to 12s (a poll every 4s).
async function until(P,expr,ms=12000){const end=Date.now()+ms;while(Date.now()<end){if(await P.js(expr))return true;await sleep(150)}return false}
const gapRuns=`__runs.filter(r=>/discrepancy/.test(r.el)&&!/books-ghost/.test(r.el))`;
const onlyCompositor=`__runs.every(r=>r.keys.every(k=>['transform','opacity'].includes(k)))`;
const reset=`__runs.length=0;__frames.length=0`;

py('rev(1)'); // Carlo is not cashed out: the books cannot be judged yet.
const H=await user('hana',390);
await H.go(`/s/${SET}/`);
await H.js(`for(const k of Object.keys(localStorage))if(/^(gap|balanced):/.test(k))localStorage.removeItem(k)`);
await H.go(`/s/${SET}/`);
check('before the last cash-out: no gap panel, nothing moved',await H.js(`!document.querySelector('.discrepancy')&&${gapRuns}.length===0`));

// 1. The last cash-out lands while the page watches: the gap arrives, once, by a poll.
await H.js(reset);py('cash(1,90000)');
check('the gap panel comes with the next poll',await until(H,`!!document.querySelector('.discrepancy')`));
await sleep(150);
let f=await H.js(`__frames.find(f=>f.gap)`);
check('arrival: the panel rises with shift (opacity and transform), once',await H.js(`${gapRuns}.length===1&&${gapRuns}[0].keys.join()==='opacity,transform'`),await H.js(gapRuns));
check('arrival: its first frame is hidden 8px down, the amount already at its value',f&&f.inline[0]==='0'&&f.inline[1]==='translateY(8px)'&&/100/.test(f.amount)&&f.next<0.6,f);
await sleep(700);
check('arrival: at rest it is fully shown with no inline style left',await H.js(`(()=>{const g=document.querySelector('.discrepancy');return getComputedStyle(g).opacity==='1'&&!g.style.opacity&&!g.style.transform})()`));
await H.shot('arrived-390');

// 2. Later redraws while it stays: nothing moves.
await H.js(reset);py('touch()');
await until(H,`__frames.length>0`);await sleep(300);
check('a later poll while the gap stays: it does not arrive again',await H.js(`__frames.length>0&&${gapRuns}.length===0`),await H.js('[__frames,__runs]'));

// 3. Reload: it is simply there.
await H.go(`/s/${SET}/`);
check('reload: the gap is there and nothing moved',await H.js(`!!document.querySelector('.discrepancy')&&${gapRuns}.length===0&&!document.querySelector('.discrepancy').style.opacity`));

// 4. A correction that does not fix it: the amount changes, the panel does not re-enter.
await H.js(reset);py(`fix(95000)`);
check('a correction that leaves a gap: the new amount shows',await until(H,`/50/.test(document.querySelector('.discrepancy-amount')?.textContent||'')`));
await sleep(300);
check('a changed amount: no re-entry',await H.js(`${gapRuns}.length===0`),await H.js('__runs'));

// 5. A correction that balances: the panel leaves as a copy, the balanced rule draws.
await H.js(reset);py(`fix(100000)`);
check('the balancing correction comes with a poll',await until(H,`!!document.querySelector('[data-balance]')`));
f=await H.js(`__frames.find(f=>!f.gap&&f.balance!==null)`);
check('resolve: a copy of the panel stays on the first frame, fixed, untappable, hidden from readers',f&&f.ghost&&f.ghost.pos==='fixed'&&f.ghost.pe==='none'&&f.ghost.op==='1'&&f.ghost.hidden==='true'&&!f.ghost.role&&!f.ghost.id,f);
check('resolve: the copy leaves (opacity and transform) and the balanced rule draws once',await H.js(`__runs.some(r=>/books-ghost/.test(r.el)&&r.keys.join()==='opacity,transform')&&__runs.some(r=>/books-message/.test(r.el))&&!!document.querySelector('.balance-arrived')`),await H.js('__runs'));
await sleep(500);
check('resolve: no copy left after 500ms',await H.js(`!document.querySelector('.books-ghost')`));
check('only transform and opacity animated',await H.js(onlyCompositor),await H.js('__runs'));
await H.shot('balanced-390');

// 6. The gap comes back with an amount already seen: no arrival.
await H.js(reset);py(`fix(90000)`);
await until(H,`!!document.querySelector('.discrepancy')`);await sleep(300);
check('the same amount again: no second arrival',await H.js(`!!document.querySelector('.discrepancy')&&${gapRuns}.length===0`),await H.js('__runs'));

// 7. Off to covered by an override, by an action's in-place answer: the leave only, no balanced reveal.
await H.js(`localStorage.removeItem('balanced:${SET}');${reset}`);
await H.js(`document.querySelector('details[data-key=override]').open=true;document.getElementById('override-note').value='Recount lost'`);
await H.tap('details[data-key=override] [type=submit]');
check('the override is answered in place',await until(H,`!!document.querySelector('[data-balance]')`));
f=await H.js(`__frames.find(f=>!f.gap&&f.balance!==null)`);
check('override: the panel leaves as a copy',f&&f.ghost&&await H.js(`__runs.some(r=>/books-ghost/.test(r.el))`),[f,await H.js('[__frames,__runs]')]);
check('override: no balanced reveal',await H.js(`!document.querySelector('.balance-arrived')&&!__runs.some(r=>/books-message/.test(r.el))`),await H.js('__runs'));
await sleep(500);check('override: no copy left',await H.js(`!document.querySelector('.books-ghost')`));

// 8. An unseen gap arriving by an action's in-place answer (Remove the override).
await H.js(`for(const k of Object.keys(localStorage))if(/^gap:/.test(k))localStorage.removeItem(k);${reset}`);
await H.tap('form[action$="override/remove/"] button');
check('removing the override brings the gap back in place',await until(H,`!!document.querySelector('.discrepancy')`));
await sleep(150);f=await H.js(`__frames.find(f=>f.gap)`);
check('in-place answer: the gap arrives once, from its first frame',await H.js(`${gapRuns}.length===1`)&&f&&f.inline[0]==='0',[f,await H.js('[__frames,__runs]')]);

// 9. A screen change while the copy leaves: nothing survives.
await H.js(reset);py(`fix(100000)`);
await until(H,`!!document.querySelector('.books-ghost')`,12000);
await H.js(`Turbo.visit('/')`);await sleep(1200);
check('a screen change leaves no copy behind',await H.js(`!document.querySelector('.books-ghost')`));
check('no script error (motion)',await H.js(`__errors.length===0`),await H.js('__errors'));

// 10. Reduced motion: states change at once, nothing moves, no copy.
py(`fix(90000)`);
const R=await user('hana',390,{reduce:true});
await R.go(`/s/${SET}/`);
await R.js(`for(const k of Object.keys(localStorage))if(/^(gap|balanced):/.test(k))localStorage.removeItem(k)`);
py('rev(1)');await until(R,`!document.querySelector('.discrepancy')`);
await R.js(reset);py('cash(1,90000)');
check('reduced motion: the gap shows',await until(R,`!!document.querySelector('.discrepancy')`));
check('reduced motion: it is simply there, no motion, no inline style',await R.js(`__runs.length===0&&!document.querySelector('.discrepancy').style.opacity`),await R.js('__runs'));
await R.js(reset);py(`fix(100000)`);
check('reduced motion: the balanced state shows',await until(R,`!!document.querySelector('[data-balance]')`));
check('reduced motion: no copy, nothing moved',await R.js(`!document.querySelector('.books-ghost')&&__frames.every(f=>!f.ghost)&&__runs.length===0`),await R.js('[__frames,__runs]'));
check('no script error (reduced motion)',await R.js(`__errors.length===0`),await R.js('__errors'));

// Back to the seeded state: ₱100 missing.
py(`fix(90000)`);
const failed=results.filter(r=>!r.ok).length;
console.log(`${results.length-failed}/${results.length} passed`);
ws.close();chrome.kill();process.exit(failed?1:0);
