// Actions update in place (Turbo, forms only). Seed a fresh temporary database with seed.py,
// seed_end_set.py, seed_night.py and seed_opening.py. The script restarts the Django server on
// 127.0.0.1:8765 itself to produce a failed send (PN_DB names the SQLite file; PN_PORT another port).
import {spawn,execSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-inplace-review';mkdirSync(OUT,{recursive:true});
const DB=process.env.PN_DB||'/private/tmp/pn-dock-check.sqlite3';const PORT=process.env.PN_PORT||'8765';const BASE='http://127.0.0.1:'+PORT;
const M=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function stopServer(){try{execSync(`pkill -f "runserver 127.0.0.1:${PORT}"`)}catch{}}
async function startServer(){stopServer();await sleep(700);spawn('.venv/bin/python',['manage.py','runserver','127.0.0.1:'+PORT,'--noreload'],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},stdio:'ignore',detached:true}).unref();for(let i=0;i<40;i++){try{if((await fetch(BASE+'/healthz')).ok)return}catch{}await sleep(250)}throw Error('server did not start')}
rmSync('/private/tmp/pn-inplace-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9358','--user-data-dir=/private/tmp/pn-inplace-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9358/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const events=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)events.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await js('window.__mark=1')};
 const click=async(expr,ms=900)=>{await js(expr+'.click()');await sleep(ms)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const reqs=(since,type)=>events.slice(since).filter(e=>e.sessionId===s&&e.method==='Network.requestWillBeSent'&&(!type||e.params.type===type)).map(e=>e.params.request.method+' '+new URL(e.params.request.url).pathname);
 const errors=since=>events.slice(since).filter(e=>e.sessionId===s&&e.method==='Runtime.exceptionThrown').length;
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,click,shot,reqs,errors};}
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const same=`window.__mark===1`;const total=`Number(document.querySelector('[data-watch=in-play]').dataset.value)`;
const opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1)`;
const near=(a,b)=>Math.abs(a-b)<=4;
try {
 await startServer();const A=await user('hana');
 // --- A rebuy from a sheet, near the bottom of the list.
 await A.go('/s/3/');
 check('forms are opt-in, and the page cache is off',await A.js(`Turbo.config.forms.mode==='optin'&&document.querySelector('meta[name=turbo-cache-control]').content==='no-cache'&&document.querySelector('meta[name=turbo-refresh-method]').content==='morph'`));
 await A.js(`document.querySelector('.host-more').open=true;document.querySelector('.host-more details[data-key=cancel]').open=true;document.querySelector('#cancel-reason').value='typed elsewhere';${opener}.scrollIntoView({block:'center'})`);await sleep(200);
 let y=await A.js('window.scrollY'),t0=await A.js(total),mark=events.length;
 await A.click(opener,500);const id1=await A.js(`document.querySelector('dialog [name=request_id]').value`);
 await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('rebuy: the page did not reload',await A.js(same));
 check('rebuy: the total rose by the amount',await A.js(total)===t0+50000);
 check('rebuy: scroll position kept',near(await A.js('window.scrollY'),y));
 check('rebuy: the sheet closed and focus returned to its opener',await A.js(`!document.querySelector('dialog[open]')&&document.activeElement===${opener}`));
 check('rebuy: text typed elsewhere is still there',await A.js(`document.querySelector('#cancel-reason').value==='typed elsewhere'`));
 check('rebuy: opened sections stayed open',await A.js(`document.querySelector('.host-more').open&&document.querySelector('.host-more details[data-key=cancel]').open`));
 const r1=A.reqs(mark);console.log('  requests for a rebuy:',r1.length,r1.join(' | '));
 check('rebuy: one POST, no document request',r1.filter(r=>r.startsWith('POST')).length===1&&A.reqs(mark,'Document').length===0&&r1.length<=3);
 // One trip: the POST is answered with the page (config/inplace.py). Polls of the set's state and cached static files are not part of the action.
 check('rebuy: the POST is the only request to the server, the page is not fetched again',r1.filter(r=>!r.includes('/state/')&&!r.includes('/static/')).join()==='POST /s/3/buyins/add/');
 check('rebuy: no script error',A.errors(mark)===0);
 await A.shot('inplace-rebuy-390');
 // --- A second rebuy carries a fresh request id and is recorded again.
 await A.click(opener,500);const id2=await A.js(`document.querySelector('dialog [name=request_id]').value`);
 check('the sheet reopens with a fresh request id',!!id2&&id2!==id1);
 await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('a second rebuy is recorded as a second buy-in',await A.js(total)===t0+100000&&await A.js(same));
 // --- A refused amount keeps the sheet open, then sends once corrected.
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='abc'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('refused amount: sheet stays open with the error beside the field',await A.js(`!!document.querySelector('dialog[open] .sheet-error')&&document.querySelector('dialog .sheet-error').textContent.includes('Enter an amount')&&document.querySelector('dialog [name=amount]').value==='abc'&&document.querySelector('dialog [name=amount]').getAttribute('aria-invalid')==='true'&&${same}`));
 check('refused amount: nothing recorded, button ready again, no floating duplicate',await A.js(total)===t0+100000&&await A.js(`!document.querySelector('dialog form [type=submit]').disabled&&!document.querySelector('.message-error.toast')`));
 await A.shot('inplace-refused-390');
 await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('corrected amount is recorded once and the sheet closes',await A.js(total)===t0+150000&&await A.js(`!document.querySelector('dialog[open]')`));
 // --- A double tap sends once.
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='500'`);mark=events.length;
 await A.js(`(()=>{const b=document.querySelector('dialog form [type=submit]');b.click();b.click()})()`);await sleep(1500);
 check('double tap: one POST and one buy-in',A.reqs(mark).filter(r=>r.startsWith('POST')).length===1&&await A.js(total)===t0+200000);
 // --- Nothing changes before the server answers.
 await send('Network.emulateNetworkConditions',{offline:false,latency:900,downloadThroughput:-1,uploadThroughput:-1},A.s);
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.js(`document.querySelector('dialog form [type=submit]').click()`);await sleep(350);
 check('while waiting: button busy, total unchanged, sheet still open',await A.js(`document.querySelector('dialog form [type=submit]').disabled&&!!document.querySelector('dialog[open]')`)&&await A.js(total)===t0+200000);
 await sleep(2600);check('after the answer: total updated',await A.js(total)===t0+250000);
 await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1},A.s);
 // --- The poll keeps working and does not fight the update.
 mark=events.length;await sleep(9000);
 const polls=events.slice(mark).filter(e=>e.sessionId===A.s&&e.method==='Network.responseReceived'&&e.params.response.url.includes('/state/')).map(e=>e.params.response.status);console.log('  poll statuses after an update:',polls.join(','));
 check('after an update the poll finds nothing new',polls.length>=1&&polls.every(st=>st===204)&&await A.js(`document.querySelector('#cancel-reason').value==='typed elsewhere'&&${same}`));
 // --- Two hosts: B acts, A's page follows by poll and A can still act in place.
 const B=await user('hana');await B.go('/s/3/');await B.click(opener,500);await B.js(`document.querySelector('dialog [name=amount]').value='1000'`);await B.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('second host: recorded in place',await B.js(same)&&await B.js(total)===t0+350000);
 await sleep(5500);check('first host sees it by poll and keeps typed text',await A.js(total)===t0+350000&&await A.js(`document.querySelector('#cancel-reason').value==='typed elsewhere'&&${same}`));
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('first host can still act in place after a poll',await A.js(total)===t0+400000&&await A.js(same));
 // --- A failed send says so, changes nothing, and can be sent again.
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='500'`);stopServer();await sleep(900);
 await A.click(`document.querySelector('dialog form [type=submit]')`,1500);
 check('failed send: the sheet says it was not sent and stays ready',await A.js(`!!document.querySelector('dialog[open] .sheet-error')&&document.querySelector('dialog .sheet-error').textContent.includes("wasn't sent")&&!document.querySelector('dialog form [type=submit]').disabled&&document.querySelector('dialog [name=amount]').value==='500'&&${same}`));
 await A.shot('inplace-failed-390');
 await startServer();await A.click(`document.querySelector('dialog form [type=submit]')`,1500);
 check('sent again once the server is back: recorded once',await A.js(total)===t0+450000&&await A.js(`!document.querySelector('dialog[open]')`));
 // --- A refusal outside a sheet floats, because the page may be scrolled.
 await A.go(`/s/${M.live.set}/`);await A.js(`window.scrollTo(0,document.documentElement.scrollHeight)`);await A.js(`document.querySelector('.host-more').open=true`);y=await A.js('window.scrollY');
 await A.click(`document.querySelector('button[value=close]')`,1300);
 check('refused transition: a floating error, announced, page not reloaded',await A.js(`!!document.querySelector('.message-error.toast[role=alert]')&&${text('Players have joined')}&&${same}`));
 await A.shot('inplace-error-toast-390');
 // --- Set transitions in place: start, end play, resume.
 await A.click(`document.querySelector('button[value=start]')`,1400);
 check('start the set: in place, now running',await A.js(same)&&await A.js(`!!document.querySelector('button[value=end]')&&!!document.querySelector('.badge-live')`));
 await A.click(`document.querySelector('button[value=end]')`,1400);
 check('end play: in place, count-up shown with its dock',await A.js(same)&&await A.js(`!!document.querySelector('#counts-form')&&!!document.querySelector('.host-controls')&&!document.querySelector('.dock-toggle').hidden`));
 // --- Counting: confirm one typed count; a reason typed in another form survives.
 await A.js(`document.querySelector('.count-row details').open=true;document.querySelector('.count-row details [name=reason]').value='another form';const f=document.querySelector('[data-count-input]');f.value='1000';f.dispatchEvent(new Event('input',{bubbles:true}));f.scrollIntoView({block:'center'})`);const top=`Math.round(document.querySelector('[data-count-input]').getBoundingClientRect().top)`;y=await A.js(top);
 await A.click(`document.querySelector('[data-confirm-typed]')`,1400);
 console.log('  count field top before/after:',y,await A.js(top));
 check('count confirm: in place, the field stays under the finger',await A.js(same)&&Math.abs(await A.js(top)-y)<=16);
 check('count confirm: the row is counted and its field is empty again',await A.js(`document.querySelector('.count-row [data-status]').dataset.status==='ready'&&document.querySelector('[data-count-input]').value===''&&document.querySelector('[data-count-input]').dataset.saved==='100000'`));
 check('count confirm: the reason typed in another form is kept and its section stays open',await A.js(`document.querySelector('.count-row details').open&&document.querySelector('.count-row details [name=reason]').value==='another form'`));
 check('count confirm: the preview follows',await A.js(`document.querySelector('[data-count-preview] [data-count-label]').textContent==='Confirmed counts'`));
 await A.js(`document.querySelector('.host-more').open=true`);await A.click(`document.querySelector('button[value=resume]')`,1400);
 check('resume play: in place, running again',await A.js(same)&&await A.js(`!!document.querySelector('button[value=end]')`));
 // --- A success message floats and is in the status region once.
 await A.go('/s/3/');await A.js(`(()=>{const d=[...document.querySelectorAll('.player-row details, [data-sheet-source^=player]')][0];const f=document.querySelector('form[action*="/buyins/"][action$="/reverse/"]');f.querySelector('[name=reason]').value='typo';window.__f=f})()`);
 await A.js(`window.__f.requestSubmit()`);await sleep(1400);
 check('success message: floats once inside the status region',await A.js(`document.querySelectorAll('.messages[role=status] .message-success.toast').length===1&&${text('Buy-in reversed.')}&&${same}`));
 // --- Session page: mark paid and undo.
 await A.go('/n/1/');await A.js(`document.querySelector('form[action$="/paid/"] button').scrollIntoView({block:'center'})`);y=await A.js('window.scrollY');
 const tr=await A.js(`document.querySelector('form[action$="/paid/"]').closest('[data-transfer]').dataset.transfer`);
 await A.click(`document.querySelector('[data-transfer="${tr}"] form[action$="/paid/"] button')`,1400);
 check('mark paid: in place, scroll kept, row shows Paid and Undo',await A.js(same)&&near(await A.js('window.scrollY'),y)&&await A.js(`document.querySelector('[data-transfer="${tr}"]').classList.contains('is-paid')&&!!document.querySelector('[data-transfer="${tr}"] form[action$="/unpaid/"]')`));
 await A.click(`document.querySelector('[data-transfer="${tr}"] form[action$="/unpaid/"] button')`,1400);
 check('undo: in place, row back to Not paid',await A.js(same)&&await A.js(`!document.querySelector('[data-transfer="${tr}"]').classList.contains('is-paid')`));
 // --- Links and out-of-scope forms still load a page the ordinary way.
 await A.go('/s/3/');await A.click(`document.querySelector('.table-bar a')`,1200);
 check('a link changes the screen',await A.js(`location.pathname.startsWith('/n/')&&!!document.querySelector('.night-layout')`));
 await A.click(`document.querySelector('form[action$="/logout/"] button')`,1400);check('a form that leads elsewhere still loads a page',await A.js(`window.__mark!==1&&location.pathname==='/accounts/login/'`));await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await A.click(`document.querySelector('form.form-section [type=submit]')`,1400);await A.go('/n/1/');
 check('forms that lead elsewhere are not marked',await A.js(`[...document.querySelectorAll('form[action$="/close/"], form[action$="/next-set/"], form[action$="/logout/"]')].every(f=>f.dataset.turbo!=='true')`));
 // --- Without JavaScript the same form reloads as before.
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go('/s/3/');const before=await A.js(total);
 await A.js(`(()=>{const f=[...document.querySelectorAll('form[action$="/buyins/add/"]')].at(-1);f.querySelector('[name=amount]').value='500';f.submit()})()`);await sleep(1200);
 check('no JavaScript: the native form still records',await A.js(total)===before+50000);
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
 writeFileSync(`${OUT}/inplace.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill();stopServer()}
if(results.some(x=>!x.ok))process.exitCode=1;
