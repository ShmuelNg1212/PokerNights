// Two hosts count up one set. Seed a fresh temporary database with seed_multi_host.py, serve it on
// 127.0.0.1:8765, then run. PN_DB names the SQLite file. Host Ivy writes through the real services;
// host Hana's and player Ben's pages must learn of each change by themselves. Each check prints how
// long the change took to arrive.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-multi-host-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-multi-host.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-multi-host-manifest.json','utf8'));
const LIMIT=Number(process.env.PN_LIMIT || 3000); // how soon another host's change must show
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ivy=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from groups.models import Member
from games import services as games
from ledger import services as ledger
from settlement import services as settlement
ivy=Member.objects.get(user__username='ivy')
S=${M.set}
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-700));return r.stdout.trim()};
rmSync('/private/tmp/pn-multi-host-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9342','--user-data-dir=/private/tmp/pn-multi-host-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9342/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BOOT=`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__asked=[];
 const _f=window.fetch;window.fetch=function(u,o){if(String(u).includes('/state/'))__asked.push(performance.now());return _f.apply(this,arguments)};`;
async function user(name,width=390){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 // Both pages keep focus as if each were the phone in someone's hand.
 await send('Emulation.setFocusEmulationEnabled',{enabled:true},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(400);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=9000)=>{const t0=Date.now();while(Date.now()-t0<ms){if(await js(expression))return Math.max(1,Date.now()-t0);await sleep(100)}return 0};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(900);
 return {s,js,go,shot,until};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok,note});console.log(`${ok?'PASS':'FAIL'} ${name}${note===undefined?'':' :: '+JSON.stringify(note)}`)};
const P=M.p;
const row=name=>`document.getElementById('count-row-${P[name]}')`;
const field=name=>`document.getElementById('count-${P[name]}')`;
const ready=name=>`(${row(name)}||{className:''}).className.includes('is-ready')`;
const counted=(name,shown)=>`(${row(name)}||{textContent:''}).textContent.includes(${JSON.stringify(shown)})`;
const type=(name,value)=>`(()=>{const f=${field(name)};f.focus();f.value=${JSON.stringify(value)};f.dispatchEvent(new Event('input',{bubbles:true}));return document.activeElement===f})()`;
const arrive=(n,t)=>check(n,t>0&&t<=LIMIT,t||'never');

try{
 const H=await user('hana');const B=await user('ben');
 await H.go(`/s/${M.set}/`);await B.go(`/s/${M.set}/`);
 check('both pages are on the count-up of one set',await H.js(`!!${field('Cara')}`)&&await B.js(`!!${row('Cara')}`));
 const base=await H.js('__asked.length');await sleep(4500);
 check('the count-up page asks for changes',await H.js(`__asked.length>${base}`),await H.js(`__asked.length-${base}`));

 // 0. A choice in a select survives another host's change (the override's absorber has no data-keep).
 await H.go(`/s/${M.books}/`);
 check('0. the override form is on a set whose books are off',await H.js(`!!document.getElementById('absorber')`));
 await H.js(`(()=>{const d=document.querySelector('details[data-key=override]');d.open=true;const s=document.getElementById('absorber');s.value='equal';s.dispatchEvent(new Event('change',{bubbles:true}));s.blur()})()`);
 const v0=await H.js(`document.getElementById('live').dataset.version`);
 ivy(`from django.db.models import F
from games.models import GameSession
GameSession.objects.filter(pk=${M.books}).update(version=F('version') + 1)`);
 arrive('0. another host\'s change reaches the host',await H.until(`document.getElementById('live').dataset.version!==${JSON.stringify(v0)}`));
 check('0. …and the absorber chosen is kept',await H.js(`document.getElementById('absorber').value==='equal'&&document.querySelector('details[data-key=override]').open`),await H.js(`document.getElementById('absorber').value`));
 await H.go(`/s/${M.set}/`);

 // 1. Ivy saves a count while Hana only looks.
 ivy(`ledger.confirm_count(S, ivy, ${P.Cara}, 120000, uuid.uuid4())`);
 arrive('1. a count saved by the other host reaches the host',await H.until(ready('Cara')));
 arrive('1. …and the player',await B.until(counted('Cara','1,200')));

 // 2. Hana is typing Dino's count when Ivy saves Ben's.
 check('2. the host types in a count field',await H.js(type('Dino','700')));
 ivy(`ledger.confirm_count(S, ivy, ${P.Ben}, 50000, uuid.uuid4())`);
 arrive('2. a count saved by the other host arrives while this host types',await H.until(ready('Ben')));
 check('2. …the field being typed in keeps its value and focus',await H.js(`${field('Dino')}.value==='700'&&document.activeElement===${field('Dino')}`),await H.js(`[${field('Dino')}.value,document.activeElement.id]`));
 await H.js(`document.activeElement.blur()`);
 check('2. after the field is left the update has landed',await H.until(ready('Ben'),2000)>0);
 await H.shot('multi-host-390-1-counts');

 // 3. Ivy saves Dino's count while Hana's field still holds her unsent 700.
 ivy(`ledger.confirm_count(S, ivy, ${P.Dino}, 80000, uuid.uuid4())`);
 arrive('3. the other host\'s count for the same player arrives',await H.until(ready('Dino')));
 check('3. …this host\'s unsent value is kept, not lost',await H.js(`${field('Dino')}.value==='700'`),await H.js(`${field('Dino')}.value`));
 check('3. …and the page says the other host saved a different count',await H.js(`/Ivy/.test(${row('Dino')}.textContent)&&/800/.test(${row('Dino')}.textContent)`),await H.js(`${row('Dino')}.textContent.replace(/\\s+/g,' ').trim().slice(0,160)`));
 await H.js(`${row('Dino')}.scrollIntoView({block:'center'})`);await H.shot('multi-host-390-1b-clash');
 check('3. …the note does not widen the page',await H.js(`document.documentElement.scrollWidth<=390`));
 await H.js(`(()=>{const f=${field('Dino')};f.value='';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('3. …and clearing the field removes the note',await H.js(`${row('Dino')}.querySelector('[data-count-clash]').hidden`));

 // 4. Ivy confirms the last count and cashes everyone out.
 ivy(`from ledger.models import FinalCount
ledger.confirm_count(S, ivy, ${P.Ivy}, 150000, uuid.uuid4())
ledger.cash_out_counted(S, ivy, list(FinalCount.objects.filter(session_id=S, is_current=True).values_list('pk', flat=True)), uuid.uuid4())`);
 arrive('4. cash-outs by the other host reach the host',await H.until(`!document.querySelector('[data-count-input]')`));
 arrive('4. …and the player',await B.until(`/Cashed out/.test((${row('Cara')}||{textContent:''}).textContent)`));

 // 5. Ivy finalizes.
 ivy(`settlement.finalize(S, ivy)`);
 arrive('5. a finalize by the other host reaches the host',await H.until(`document.getElementById('live').dataset.state==='finalized'`));
 arrive('5. …and the player',await B.until(`document.getElementById('live').dataset.state==='finalized'`));
 await H.shot('multi-host-390-2-final');

 // 6. Ivy starts the next set.
 const next=ivy(`print(games.start_next_set(${M.night}, ivy).pk)`).split("\n").pop();
 arrive('6. the other host is taken to the next set',await H.until(`location.pathname==='/s/${next}/'`,9000));
 arrive('6. the player sees the notice for the next set',await B.until(`!!document.querySelector('[data-next-set="${next}"]')`));
 check('6. the player stays on the set they were looking at',await B.js(`location.pathname==='/s/${M.set}/'`));
 await H.shot('multi-host-390-3-next');

 // Usage: every 2 seconds on a busy set, every 4 after a quiet minute, nothing while hidden.
 const asks=async(u,ms)=>{const n=await u.js('__asked.length');await sleep(ms);return await u.js('__asked.length')-n};
 const busy=await asks(B,8200);
 check('a finalized set just ended asks about every 2 seconds',busy>=3&&busy<=5,busy);
 await B.js(`const _n=Date.now;Date.now=()=>_n()+70000`);await sleep(2500);
 const quiet=await asks(B,8200);
 check('…and about every 4 seconds after a quiet minute',quiet>=1&&quiet<=3,quiet);
 await B.js(`Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))`);
 check('…and not at all while the tab is hidden',await asks(B,6000)===0);

 // Cost: one unchanged poll, timed from the page.
 const cost=await H.js(`(async()=>{const r=document.getElementById('live');const t=[];for(let i=0;i<10;i++){const t0=performance.now();const x=await fetch(r.dataset.url+'?v='+encodeURIComponent(r.dataset.version),{headers:{'X-Requested-With':'fetch'},cache:'no-store'});t.push([x.status,performance.now()-t0])}return t})()`);
 check('an unchanged poll answers 204',cost.every(([st])=>st===204),cost.map(([st,ms])=>`${st} ${ms.toFixed(1)}ms`).join(', '));
 for(const [n,u] of [['host',H],['player',B]])check(`${n}: no script error`,await u.js(`__errors.length===0`),await u.js('__errors'));
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
