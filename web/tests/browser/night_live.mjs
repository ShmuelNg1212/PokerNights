// The session page updates by itself (nightlive.js). Seed a fresh temporary database with
// seed_reopen.py, serve it on 127.0.0.1:8765, then run. PN_DB names the SQLite file: the "host"
// writes to it through the real services, and the player's page learns of it by asking.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-nightlive-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-reopen-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const host=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from groups.models import Member
from settlement import services as settlement
from settlement.models import Transfer, Payment
host=Member.objects.get(user__username='hana',role='host')
def transfers(night): return list(Transfer.objects.filter(plan__night_id=night, plan__is_current=True).order_by('position'))
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-700))};
rmSync('/private/tmp/pn-nightlive-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-nightlive-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Counts the questions the page asks, notes each class a transfer row is given, and marks the document so a reload would show.
const BOOT=`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__asked=[];window.__settled=[];window.__arrived=[];
 const _f=window.fetch;window.fetch=function(u,o){if(String(u).includes('/state/'))__asked.push(performance.now());return _f.apply(this,arguments)};
 addEventListener('DOMContentLoaded',()=>{window.__loaded=(window.__loaded||0)+1;new MutationObserver(list=>list.forEach(m=>{const t=m.target;if(t.classList&&t.classList.contains('just-paid')&&t.dataset.transfer)__settled.push(t.dataset.transfer);if(t.classList&&t.classList.contains('settle-arrived'))__arrived.push(t.dataset.settled)})).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['class']})})`;
async function user(name,width=390,seenRecap=true){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT+(seenRecap?`;const _g=Storage.prototype.getItem;Storage.prototype.getItem=function(k){return String(k).startsWith('rack-recap:')?'1':_g.call(this,k)}`:'')},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(400);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=9000)=>{const t0=Date.now();while(Date.now()-t0<ms){if(await js(expression))return Math.max(1,Date.now()-t0);await sleep(100)}return 0};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(900);
 return {s,js,go,shot,until};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const row=n=>`document.querySelectorAll('[data-transfer]')[${n}]`;
const closed=M.closed.night,open=M.open.night;

try{
 const P=await user('ben');await P.go(`/n/${closed}/`);
 const rows=await P.js(`document.querySelectorAll('[data-transfer]').length`);
 check('a player\'s closed session page carries its stamp and asks',rows>0&&await P.js(`!!document.querySelector('.night-layout').dataset.stamp`)&&await P.until(`__asked.length>=1`,7000)>0,rows);
 await P.js(`window.__mark='same document';scrollTo(0,260)`);await sleep(200);const y=await P.js('scrollY');
 // The host marks the first transfer paid.
 host(`settlement.mark_paid(${closed}, host, transfers(${closed})[0].pk, uuid.uuid4())`);
 const took=await P.until(`${row(0)}.dataset.paid==='1'`);
 check('a paid mark reaches the player within about 5 seconds',took>0&&took<7500,took);
 check('…without a reload, at the same scroll position',await P.js(`window.__mark==='same document'&&__loaded===1&&Math.abs(scrollY-${y})<=2`),await P.js('[__loaded,scrollY]'));
 check('…and the row settles as it does for the host',await P.js(`__settled.includes(${row(0)}.dataset.transfer)`));
 check('…the count of paid transfers follows',await P.js(`/1 of ${rows}/.test(document.querySelector('.night-settle').textContent.replace(/\\s+/g,' '))`),await P.js(`document.querySelector('.night-overview').textContent.replace(/\\s+/g,' ').slice(0,200)`));
 await P.shot('nightlive-390-1-paid');
 // An open disclosure survives the next redraw.
 await P.js(`document.querySelector('details[data-key=payment-records]').open=true`);
 host(`settlement.mark_unpaid(${closed}, host, transfers(${closed})[0].pk)`);
 check('an undone mark reaches the player; the open disclosure stays open',await P.until(`${row(0)}.dataset.paid==='0'`)>0&&await P.js(`document.querySelector('details[data-key=payment-records]').open`));
 // A sheet holds the redraw back.
 await P.js(`document.querySelector('[data-sheet-open=share]').click()`);await sleep(700);
 host(`settlement.mark_paid(${closed}, host, transfers(${closed})[0].pk, uuid.uuid4())`);await sleep(7500);
 check('while a sheet is open the page is not redrawn under it',await P.js(`document.querySelector('dialog.sheet').open&&${row(0)}.dataset.paid==='0'&&!!document.querySelector('dialog.sheet [data-share]')`));
 await P.js(`document.querySelector('dialog.sheet .sheet-head button').click()`);
 const after=await P.until(`${row(0)}.dataset.paid==='1'`,5000);
 check('…and it lands within moments of closing the sheet',after>0&&after<3500,after);
 check('…after which the sheet still opens',(await P.js(`document.querySelector('[data-sheet-open=share]').click()`),await P.until(`document.querySelector('dialog.sheet').open&&!document.querySelector('dialog.sheet [data-share-stage]').hidden`,4000))>0);
 await P.js(`document.querySelector('dialog.sheet .sheet-head button').click()`);await sleep(500);
 // The last mark.
 host(`[settlement.mark_paid(${closed}, host, t.pk, uuid.uuid4()) for t in transfers(${closed})[1:]]`);
 check('once every transfer is paid the player has seen their "settled" arrive, exactly once',await P.until(`!!document.querySelector('[data-settled]')&&[...document.querySelectorAll('[data-transfer]')].every(r=>r.dataset.paid==='1')`)>0&&await P.js(`new Set(__arrived).size===1&&__arrived.length>=1`),await P.js('__arrived'));
 await P.shot('nightlive-390-2-settled');
 // Hidden: no questions. Back: one at once.
 await P.js(`Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));window.__n=__asked.length`);await sleep(6500);
 check('a hidden tab asks nothing',await P.js(`__asked.length===__n`),await P.js(`__asked.length-__n`));
 await P.js(`Object.defineProperty(document,'hidden',{value:false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))`);await sleep(600);
 check('…and asks at once on return',await P.js(`__asked.length===__n+1`));
 // Quiet for two minutes (the clock is moved): every 20 seconds instead of every 5.
 await P.js(`const _n=Date.now;Date.now=()=>_n()+130000;window.__n=__asked.length`);await sleep(11500);
 check('after two quiet minutes it asks less often',await P.js(`__asked.length-__n<=1`),await P.js(`__asked.length-__n`));

 // An open session: the close arrives, and the recap opens by itself as on a fresh load.
 const Q=await user('ben',390,false);await Q.go(`/n/${open}/`);
 check('a player waiting on an open session',await Q.js(`/Session open/.test(document.body.textContent)&&!document.querySelector('.night-settle')`));
 await Q.js(`window.__mark='same document'`);
 host(`settlement.close_night(${open}, host)`);
 const t=await Q.until(`!!document.querySelector('.night-settle')&&document.querySelectorAll('[data-transfer]').length>0`);
 check('the close reaches the player within about 5 seconds, without a reload',t>0&&t<7500&&await Q.js(`window.__mark==='same document'`),t);
 check('…and the recap opens by itself, once',await Q.until(`!!document.querySelector('dialog.sheet[open] .recap')`,4000)>0);
 await Q.shot('nightlive-390-3-closed');
 await Q.js(`document.querySelector('dialog.sheet .sheet-head button').click()`);await sleep(600);
 host(`settlement.reopen_night(${open}, host, 'One more set')`);
 check('a reopening reaches the player with its reason',await Q.until(`!document.querySelector('.night-settle')&&/Session open/.test(document.body.textContent)&&/One more set/.test((document.querySelector('.night-overview .correction')||{}).textContent||'')`)>0);
 check('…and no recap opens over it',await Q.js(`!document.querySelector('dialog[open]')`));
 // Two hosts: the host's own page is asked about too.
 const H=await user('hana');await H.go(`/n/${closed}/`);
 host(`settlement.mark_unpaid(${closed}, host, transfers(${closed})[0].pk)`);
 check('a host sees another host\'s change the same way',await H.until(`${row(0)}.dataset.paid==='0'`)>0);
 for(const [n,u] of [['player',P],['waiting player',Q],['host',H]])check(`${n}: no script error`,await u.js(`__errors.length===0`),await u.js('__errors'));
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
