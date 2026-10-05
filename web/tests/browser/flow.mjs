// Motion system, stage 2: movement on the live set page (flow.js, changes.js). Seed a fresh temporary
// database with seed.py and seed_flow.py, serve it on 127.0.0.1:8765, then run. PN_DB names the SQLite
// file; the "other host" writes to it through the real services, and this page learns of it by polling.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-flow-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-flow-manifest.json','utf8'));
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
rmSync('/private/tmp/pn-flow-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-flow-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call is logged, and every redraw is photographed in numbers on its first frame:
// what each row shows, how far it is from its place and how opaque it is.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];window.__errors=[];window.__f=[];addEventListener('error',e=>__errors.push(e.message));
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className||el.tagName)+'',keys:Object.keys(k),delay:(o&&o.delay)||0});return a.apply(this,arguments)}}
 const m=el=>new DOMMatrix(getComputedStyle(el).transform);
 // Motion starts an animation on the frame after it is asked, before anything is painted; that frame is the first one seen.
 document.addEventListener('live:updated',()=>requestAnimationFrame(()=>{const live=document.getElementById('live');if(!live)return;const msg=live.querySelector('.books-message');
  window.__at=performance.now();
  __f.push({region:+getComputedStyle(live).opacity,runs:__runs.length,msg:msg?+getComputedStyle(msg).opacity:null,
   rows:[...live.querySelectorAll('li[data-watch]')].map(r=>({k:r.dataset.watch,o:+getComputedStyle(r).opacity,y:Math.round(m(r).m42),t:(r.querySelector('.player-figure')||r).textContent.replace(/\\s+/g,' ').trim()}))});
  if(window.__tap){const b=[...live.querySelectorAll('.buy-opener')].at(-1);window.__tapAt=Math.round(m(b.closest('li')).m42);b.click();window.__tap=false}}))})`;
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
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const dialog=`document.querySelector('dialog.sheet')`;
const rowsAtRest=`[...document.querySelectorAll('#live li[data-watch]')].every(r=>!r.getAttribute('style')&&getComputedStyle(r).opacity==='1'&&getComputedStyle(r).transform==='none')`;
const quiet=`document.getAnimations().filter(a=>a.playState==='running').length===0`;
const row=(f,pk)=>f.rows.find(r=>r.k==='player-'+pk);
const only=`__runs.every(r=>r.keys.every(k=>['transform','opacity'].includes(k)))`;

async function story(width,key){
 const W=`${width}px`,S=M[key],[p0,p1,p2,p3]=S.players,[n0,n1]=S.spare;
 const A=await user('hana',width);await A.go(`/s/${S.set}/`);await sleep(400);
 check(`${W} first sight of a set: nothing moves`,await A.js(`__runs.length===0&&${rowsAtRest}&&!document.querySelector('.just-changed')`));
 // Two players added by the other host.
 other(`games.add_participants(${S.set},host,[${n0},${n1}],u())`);
 let f=await A.redraw();const added=f.rows.slice(-2);
 check(`${W} added players: both rows start transparent and 12px low`,added.length===2&&added.every(r=>r.o<0.2&&r.y>=10&&r.y<=12));
 check(`${W} added players: the rows already there do not move`,f.rows.slice(0,4).every(r=>r.o===1&&r.y===0));
 check(`${W} added players: the second arrives 40ms after the first`,await A.js(`(()=>{const d=__runs.filter(r=>r.el.includes('player-row')).map(r=>r.delay);return d.length===2&&d[0]===0&&Math.abs(d[1]-0.04)<1e-9})()`));
 await A.shot(`flow-arrive-${width}`);await sleep(900);
 check(`${W} added players: at rest, opaque, no inline style`,await A.js(rowsAtRest));
 // A cash-out with "left" makes that row shorter: the rows below slide up into place.
 await A.js(`window.__tap=true`);
 const before=await A.js(`[...document.querySelectorAll('#live li[data-watch]')].map(r=>r.getBoundingClientRect().top+scrollY)`);
 other(`ledger.record_cash_out(${S.set},host,${p1},65000,u(),left=True)`);
 f=await A.redraw();
 const after=await A.js(`(()=>{const d=${dialog};return {open:d.open,title:d.querySelector('h2').textContent}})()`);
 const gap=f.rows[2].y;
 check(`${W} cash-out: rows below start displaced by the height the row changed (${gap}px)`,Math.abs(gap)>10&&f.rows.slice(2).every(r=>r.y===gap)&&f.rows.slice(0,2).every(r=>r.y===0));
 check(`${W} cash-out: the row shows the accepted amount on the first frame`,row(f,p1).t.includes('Cashed out ₱650')&&row(f,p1).o===1);
 check(`${W} a tap on a button of a moving row opens its sheet`,after.open&&/Buy-in|Rebuy/.test(after.title)&&await A.js(`window.__tapAt`)===gap);
 check(`${W} cash-out: the Left badge springs in and the name dims`,await A.js(`__runs.some(r=>r.el==='badge'&&r.keys.join()==='opacity,transform')&&getComputedStyle(document.querySelector('.just-left .player-name')).animationName==='name-dim'`));
 await A.shot(`flow-shift-${width}`);
 await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(900);
 const settled=await A.js(`[...document.querySelectorAll('#live li[data-watch]')].map(r=>r.getBoundingClientRect().top+scrollY)`);
 check(`${W} cash-out: rows end at rest, moved by ${Math.round(before[2]-settled[2])}px`,await A.js(rowsAtRest)&&Math.abs((before[2]-settled[2])-gap)<=1);
 // A rebuy by the other host.
 await sleep(2400);await A.js(`__runs.length=0`);
 other(`ledger.record_buy_in(${S.set},host,${p2},150000,u())`);
 f=await A.redraw();
 check(`${W} rebuy: the amount is the accepted value on the first frame, the row does not move`,row(f,p2).t.startsWith('₱2,500')&&row(f,p2).o===1&&row(f,p2).y===0);
 check(`${W} rebuy: the new edge drops and the badge springs in`,await A.js(`__runs.some(r=>r.el==='new-edge')&&__runs.some(r=>r.el.includes('change-label'))&&getComputedStyle(document.querySelector('.new-edge')).animationName==='none'&&document.querySelector('.just-changed .change-label').textContent==='Rebuy added'`));
 check(`${W} rebuy: the pot's underline draws`,await A.js(`getComputedStyle(document.querySelector('.pot-main.just-changed'),'::after').animationName==='mark-draw'&&getComputedStyle(document.querySelector('.pot-main')).boxShadow==='none'`));
 await A.shot(`flow-rebuy-${width}`);await sleep(2700);
 check(`${W} rebuy: the mark is fading at 2.7s`,await A.js(`document.querySelectorAll('.just-changed.change-fading').length===2`));await sleep(500);
 check(`${W} rebuy: the mark is gone after 3s`,await A.js(`!document.querySelector('.just-changed,.change-fading')&&document.querySelector('[data-watch=player-${p2}] .change-label').hidden`));
 // Your own action goes through the other redraw path (a morph).
 await A.js(`__runs.length=0`);
 const mine=A.redraw(false);
 await A.js(`(()=>{document.querySelector('[data-sheet-open=buy-${p3}]').click();const f=${dialog}.querySelector('[name=amount]');f.value='500';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);
 f=await mine;
 check(`${W} your own rebuy: accepted value on the first frame, edge and badge animate`,!!f&&row(f,p3).t.startsWith('₱1,500')&&await A.js(`__runs.some(r=>r.el==='new-edge')&&__runs.some(r=>r.el.includes('change-label'))`));
 await sleep(900);
 check(`${W} Motion animates only transform and opacity`,await A.js(only));
 check(`${W} no script error`,await A.js(`__errors.length===0`));
 return A;
}

try {
 const A=await story(390,'rows');
 // Twenty redraws leave nothing running and no inline style on a row.
 const S=M.rows;
 for(let i=0;i<20;i++){other(`ledger.record_buy_in(${S.set},host,${S.players[i%2?2:3]},50000,u())`);await A.redraw()}
 await sleep(1200);
 check('twenty redraws: nothing left running, rows without inline style',await A.js(`${quiet}&&${rowsAtRest}&&__errors.length===0`));
 // A hidden tab: the redraw happens, nothing animates.
 await A.js(`Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});__runs.length=0`);
 other(`games.add_participants(${S.set},host,[${S.spare[2]}],u())`);
 let f=await A.redraw();
 check('hidden tab: the new row is simply there',f.rows.length===7&&f.rows.at(-1).o===1&&f.rows.at(-1).y===0&&await A.js(`__runs.length===0`));
 await A.js(`delete document.hidden`);

 await story(1280,'wide');

 // A player joins: their own action, through the morph. The join line leaves and the rows move up.
 const J=M.join,C=await user('ben');await C.go(`/s/${J.set}/`);await sleep(300);
 const joined=C.redraw(false);await C.js(`document.querySelector('.join-row form').requestSubmit()`);f=await joined;
 check('join: your own row arrives transparent, the others slide up from where they were',!!f&&f.rows.length===4&&f.rows.at(-1).o<0.2&&f.rows.slice(0,3).every(r=>Math.abs(r.y)>10&&r.o===1));
 await sleep(900);check('join: at rest',await C.js(`${rowsAtRest}&&${only}&&__errors.length===0`));

 // The set changes state, counts are confirmed and the books balance.
 const K=M.count,H=await user('hana');await H.go(`/s/${K.set}/`);await sleep(300);
 other(`games.transition(${K.set},host,'end')`);
 f=await H.redraw();
 check('state change: the new state starts transparent and no row moves by itself',f.region<0.2&&f.rows.every(r=>r.y===0)&&await H.js(`__runs.length===1&&__runs[0].keys.join()==='opacity'`));
 await H.shot('flow-state');await sleep(500);
 check('state change: ends opaque with no inline style',await H.js(`getComputedStyle(document.getElementById('live')).opacity==='1'&&!document.getElementById('live').style.opacity`));
 // While you type, the redraw waits and nothing moves.
 await H.js(`__runs.length=0;document.querySelector('[data-count-input]').focus()`);const n=await H.js(`__f.length`);
 other(`ledger.confirm_counts(${K.set},host,{${K.players[0]}:120000},u())`);
 await H.js(`window.dispatchEvent(new Event('online'))`);await sleep(1500);
 check('typing: no redraw and no movement',await H.js(`__f.length`)===n&&await H.js(`__runs.length===0`));
 const blurred=H.redraw(false);await H.js(`document.activeElement.blur()`);f=await blurred;
 check('count confirmed: the status badge springs and the progress line is marked',!!f&&await H.js(`__runs.some(r=>r.el.includes('badge-live'))&&document.querySelector('.count-progress').classList.contains('just-changed')`));
 await sleep(600);
 other(`ledger.confirm_counts(${K.set},host,{${K.players[1]}:80000},u())
ledger.cash_out_counted(${K.set},host,list(FinalCount.objects.filter(session_id=${K.set},is_current=True).values_list('pk',flat=True)),u())`);
 f=await H.redraw();
 check('books balance: the rule draws with the spring and the words wait, hidden',f.msg<0.05&&await H.js(`(()=>{const b=document.querySelector('.balance-arrived');const c=getComputedStyle(b,'::before');return c.animationName==='books-rule'&&c.animationTimingFunction.startsWith('linear(')})()`));
 check('books balance: nothing wider than the screen while the rule overshoots',await H.js(`document.documentElement.scrollWidth<=390`));
 await H.shot('flow-balance-mid');
 const done=await H.js(`new Promise(ok=>{const msg=document.querySelector('.books-message'),box=document.querySelector('.balance-arrived');(function look(){if(getComputedStyle(msg).opacity==='1'&&document.getAnimations().filter(a=>a.playState==='running').length===0)ok(Math.round(performance.now()-__at));else if(performance.now()-__at>3000)ok(0);else requestAnimationFrame(look)})()})`);
 await sleep(100);
 check(`books balance: complete within 900ms (${done}ms), words at rest`,done>0&&done<=900&&await H.js(`!document.querySelector('.books-message').getAttribute('style')`));
 await H.shot('flow-balance');
 await H.go(`/s/${K.set}/`);await sleep(400);
 check('books balance: not again on reload',await H.js(`!document.querySelector('.balance-arrived')&&__runs.length===0`));

 // Reduced motion and a blocked Motion file: the page changes as before, with no Motion.
 const P=M.still,Q=M.plain;
 const R=await user('hana',390,s=>send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s));await R.go(`/s/${P.set}/`);
 other(`games.add_participants(${P.set},host,[${P.spare[0]}],u())
ledger.record_buy_in(${P.set},host,${P.players[0]},100000,u())`);
 f=await R.redraw();
 check('reduced motion: the row and the figure are there at once, nothing animates',f.rows.length===5&&f.rows.every(r=>r.o===1&&r.y===0)&&row(f,P.players[0]).t.startsWith('₱2,000')&&await R.js(`__runs.length===0&&!pokerMotion.on()&&document.getAnimations().length===0`));
 check('reduced motion: the change is still marked',await R.js(`!!document.querySelector('[data-watch=player-${P.players[0]}].just-changed')&&__errors.length===0`));
 const B=await user('hana',390,s=>send('Network.setBlockedURLs',{urls:['*motion-14.0.0.js*']},s));await B.go(`/s/${Q.set}/`);
 other(`games.add_participants(${Q.set},host,[${Q.spare[0]}],u())
ledger.record_buy_in(${Q.set},host,${Q.players[0]},100000,u())`);
 f=await B.redraw();
 check('blocked library: the row and the figure are there at once',f.rows.length===5&&f.rows.every(r=>r.o===1&&r.y===0)&&row(f,Q.players[0]).t.startsWith('₱2,000'));
 check('blocked library: the CSS edge animation plays, no error',await B.js(`!window.Motion&&getComputedStyle(document.querySelector('.new-edge')).animationName==='edge-added'&&getComputedStyle(document.querySelector('.pot-main.just-changed')).boxShadow!=='none'&&__errors.length===0`));
 writeFileSync(`${OUT}/flow.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
