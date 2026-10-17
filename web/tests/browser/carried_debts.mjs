// Unpaid transfers carried into a later session (carry.js). Seed a fresh temporary database with
// seed_carried.py alone, serve it on 127.0.0.1:8765, then run. PN_DB names the SQLite file: the
// reopening is made through the real service while a player's page watches.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-carried-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-carried-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const py=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid, json, datetime
from django.utils import timezone
from groups.models import Member
from groups import services as groups
from games import services as games, seats
from games.models import GameSession, SeatDraw, Participant
host=Member.objects.get(user__username='hana',role='host')
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-900));return r.stdout.trim().split('\n').pop()};
rmSync('/private/tmp/pn-carry-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-carry-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,{width=390,height=844,reduce=false,scripts=true}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async file=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${file}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=8000)=>{const from=Date.now();while(Date.now()-from<ms){if(await js(expression))return Math.max(1,Date.now()-from);await sleep(80)}return 0};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(700);
 if(!scripts)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,until,name};}
const results=[];function check(name,ok,detail){results.push({name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const dismiss=async U=>{if(await U.js(`!!document.querySelector('dialog[open]')`)){await U.js(`document.querySelector('.sheet-head button').click()`);await sleep(450)}};
const list=`[...document.querySelectorAll('.transfer-list .transfer-line')].map(r=>r.querySelector('.transfer-parties').getAttribute('aria-label')+' '+r.querySelector('.transfer-amount').textContent.trim())`;
const row=id=>`document.querySelector('[data-transfer="${id}"]')`;
const WATCH=`window.__seen=[];window.__loads=(window.__loads||0)+1;new MutationObserver(l=>l.forEach(m=>{const t=m.target;if(t.classList&&t.classList.contains('just-carried'))__seen.push(t.dataset.transfer)})).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['class']})`;
try {
const ids=JSON.parse(py(`from settlement.models import Transfer
print(json.dumps({'ana_ben':Transfer.objects.get(plan__night_id=${M.first}).pk,'second':{t.payer.display_name+'>'+t.payee.display_name:t.pk for t in Transfer.objects.filter(plan__night_id=${M.second}).select_related('payer','payee')}}))`));
const tonight='/n/'+M.tonight+'/',first='/n/'+M.first+'/',second='/n/'+M.second+'/';
const H=await user('hana'),B=await user('ben');

// --- Before closing.
await H.go(tonight);
check('the host is shown three earlier transfers, all ticked, each with its session',await H.js(`(()=>{const b=[...document.querySelectorAll('[data-carry-pick] input[name=carry]')];return b.length===3&&b.every(x=>x.checked)&&[...document.querySelectorAll('.carry-option')].map(l=>l.textContent.replace(/\\s+/g,' ').trim()).join('|')==='Ana pays BenGarage table, '+document.querySelectorAll('.carry-option .small')[0].textContent.split(', ')[1]+'₱500|Carlo pays DeeRooftop table, '+document.querySelectorAll('.carry-option .small')[1].textContent.split(', ')[1]+'₱300|Ben pays AnaRooftop table, '+document.querySelectorAll('.carry-option .small')[2].textContent.split(', ')[1]+'₱120'})()`),await H.js(`[...document.querySelectorAll('.carry-option')].map(l=>l.textContent.replace(/\\s+/g,' ').trim())`));
check('the line under the list counts them',(await H.js(`document.querySelector('[data-carry-count]').textContent`))==="All 3 will be carried into tonight's list.");
check('each row is a 48px target and the page does not scroll sideways',await H.js(`[...document.querySelectorAll('.carry-option')].every(l=>l.getBoundingClientRect().height>=48)&&document.documentElement.scrollWidth<=390`));
await H.js(`document.querySelector('[data-carry-pick]').scrollIntoView({block:'center'})`);await H.shot('carried-pick-390');
await H.js(`document.querySelectorAll('[data-carry-pick] input')[1].click()`);
check('unticking moves only transform and opacity',await H.js(`document.getAnimations().filter(a=>!(a instanceof CSSTransition)&&a.effect.target.closest('[data-carry-pick]')).every(a=>a.effect.getKeyframes().every(k=>Object.keys(k).every(p=>['transform','opacity','offset','easing','composite','computedOffset'].includes(p))))`));
await sleep(450);
check('unticking one says 2 of 3 and dims its row',(await H.js(`document.querySelector('[data-carry-count]').textContent`))==="2 of 3 will be carried into tonight's list."&&await H.js(`Number(getComputedStyle(document.querySelectorAll('.carry-option .grow')[1]).opacity)<0.7&&Number(getComputedStyle(document.querySelectorAll('.carry-option .grow')[0]).opacity)===1&&!document.querySelectorAll('.carry-option .grow')[1].getAttribute('style')`));
await H.shot('carried-pick-unticked-390');
await B.go(tonight);
check('a player is shown no list to tick',await B.js(`!document.querySelector('[data-carry-pick]')&&!document.querySelector('form[action$="/close/"]')`));
await B.go('/');const homeBefore=await B.js(`document.querySelector('main').textContent.replace(/\\s+/g,' ')`);
await B.go(first);await dismiss(B);await B.js(WATCH);
check('before: the earlier transfer is not paid',(await B.js(`${row(ids.ana_ben)}.dataset.paid`))==='0'&&/Not paid/.test(await B.js(`${row(ids.ana_ben)}.textContent`)));

// --- Close with two of the three.
await H.js(`document.querySelector('form[action$="/close/"] button[type=submit]').click()`);await sleep(1400);await dismiss(H);
const closed=await H.js(list);
check('one list settles tonight and the two ticked debts',JSON.stringify(closed)===JSON.stringify(['Dee pays Carlo ₱200','Ana pays Carlo ₱130','Ben pays Carlo ₱20']),closed);
check('the list says what it includes',/^Includes 2 unpaid transfers from earlier sessions$/.test(await H.js(`document.querySelector('.night-carried summary').textContent.replace(/\\s+/g,' ').trim()`)));
await H.js(`document.querySelector('.night-carried summary').click()`);
check('opened by a tap, the carried rows come in',await H.js(`document.getAnimations().filter(a=>!(a instanceof CSSTransition)&&a.effect.target.closest('.carried-list')).length>=2`));
await sleep(1100);
check('each carried transfer is listed with a link to its session, on one line each',await H.js(`(()=>{const li=[...document.querySelectorAll('.carried-list > li')];return li.length===2&&li[0].querySelector('.carried-who').textContent==='Ana owed Ben'&&li[1].querySelector('.carried-who').textContent==='Ben owed Ana'&&li[0].querySelector('a').getAttribute('href')==='${first}'&&li[1].querySelector('a').getAttribute('href')==='${second}'&&li.every(x=>x.querySelector('.carried-who').getBoundingClientRect().height<30)&&li.every(x=>!x.getAttribute('style'))})()`),await H.js(`[...document.querySelectorAll('.carried-list > li')].map(x=>[x.querySelector('.carried-who').textContent,x.querySelector('a').getAttribute('href'),Math.round(x.querySelector('.carried-who').getBoundingClientRect().height),x.getAttribute('style')])`));
await H.js(`document.querySelector('#transfers-title').scrollIntoView()`);await H.shot('carried-closed-host-390');

// --- The earlier sessions.
const turned=await B.until(`${row(ids.ana_ben)}.dataset.paid==='c'`,9000);
check('the earlier session turns to Carried on the player\'s open page by itself',turned>0&&await B.js(`__loads===1`),turned);
check('the row says where it went, with a link, and moved once',await B.js(`/Carried to Kitchen table/.test(${row(ids.ana_ben)}.querySelector('.transfer-state').textContent)&&${row(ids.ana_ben)}.querySelector('.transfer-state a').getAttribute('href')==='${tonight}'&&__seen.filter(x=>x==='${ids.ana_ben}').length===1`),await B.js(`__seen`));
check('it counts as settled there',await B.js(`document.querySelector('.night-overview .felt .row > .badge').textContent.trim()==='Settled'&&/1 carried to a later session/.test(document.querySelector('.settle-table').textContent)`));
await B.js(`${row(ids.ana_ben)}.scrollIntoView({block:'center'})`);await B.shot('carried-earlier-390');
await H.go(second);await dismiss(H);
check('the session with one carried and one unpaid is partly settled; only the unpaid one can be marked paid',await H.js(`document.querySelector('.night-overview .felt .row > .badge').textContent.trim()==='Partly settled'&&${row(ids.second['Ben>Ana'])}.dataset.paid==='c'&&!${row(ids.second['Ben>Ana'])}.querySelector('form')&&${row(ids.second['Carlo>Dee'])}.dataset.paid==='0'&&!!${row(ids.second['Carlo>Dee'])}.querySelector('form[action$="/paid/"]')`));
check('the host is told the order of reopening there',await H.js(`/Reopen that session first\\./.test(document.body.textContent)&&!document.querySelector('[data-sheet-open="reopen-night"]')`));

// --- The player's own figure.
await B.go(tonight);await sleep(300);
check('the make-up waits behind the recap that opens by itself',await B.js(`!!document.querySelector('dialog[open]')&&!localStorage.getItem('rack-makeup:'+document.querySelector('.makeup').dataset.makeup)`));
await dismiss(B);
const rose=await B.until(`document.getAnimations().some(a=>!(a instanceof CSSTransition)&&a.effect.target.closest('.makeup'))`,1500);
check('after the recap closes the make-up arrives once',rose>0,rose);
await sleep(900);
check('the player reads how the figure is made up',JSON.stringify(await B.js(`[...document.querySelectorAll('.makeup > div')].map(d=>d.querySelector('dt').textContent.replace(/\\s+/g,' ').trim().replace(/ · [A-Z][a-z]+ \\d+/,'')+' '+d.querySelector('dd').textContent.trim())`))===JSON.stringify(['This session −₱400','Ana owed you +₱500','You owed Ana −₱120','To settle −₱20']),await B.js(`[...document.querySelectorAll('.makeup > div')].map(d=>d.textContent.replace(/\\s+/g,' ').trim())`));
check('it leaves no inline style and the lead figure is what is paid',await B.js(`[...document.querySelectorAll('.makeup *')].every(e=>!e.getAttribute('style'))&&document.querySelector('[data-my-part]').dataset.myPart==='pay:2000'`));
await B.js('scrollTo(0,0)');await B.shot('carried-player-390');
await B.go(tonight);await dismiss(B);await sleep(500);
check('it does not arrive a second time',await B.js(`document.getAnimations().filter(a=>a.effect&&a.effect.target&&a.effect.target.closest('.makeup')).length===0`));
await B.go('/');const homeAfter=await B.js(`document.querySelector('main').textContent.replace(/\\s+/g,' ')`);
check('Your groups counts the debts once: ₱20 to pay, the earlier ₱500 and ₱120 gone',/₱500/.test(homeBefore)&&/₱20\b/.test(homeAfter)&&!/₱500/.test(homeAfter)&&!/₱120/.test(homeAfter),[homeBefore.slice(0,160),homeAfter.slice(0,160)]);
await B.shot('carried-home-390');

// --- Sizes.
const S=await user('hana',{width:320,height:568});await S.go(tonight);await dismiss(S);await S.js(`document.querySelector('.night-carried').open=true`);
check('320px: nothing scrolls sideways and amounts stay on one line',await S.js(`document.documentElement.scrollWidth<=320&&[...document.querySelectorAll('.carried-list .amount')].every(a=>a.getBoundingClientRect().height<30)`));
await S.js(`document.querySelector('.night-carried').scrollIntoView()`);await S.shot('carried-closed-320');
const W=await user('hana',{width:1280,height:800});await W.go(tonight);await dismiss(W);await W.js(`document.querySelector('.night-carried').open=true`);await sleep(200);
check('1280px: nothing scrolls sideways',await W.js(`document.documentElement.scrollWidth<=1280`));await W.shot('carried-closed-1280');

// --- Reopening releases them.
await H.go(tonight);await dismiss(H);
await H.js(`document.querySelector('[data-sheet-open="reopen-night"]').click()`);await sleep(500);
check('the reopen sheet says the carried transfers are unpaid again',/The 2 earlier transfers it carried are unpaid again in their own sessions\./.test(await H.js(`document.querySelector('dialog[open]').textContent.replace(/\\s+/g,' ')`)));
await dismiss(H);
await B.go(first);await dismiss(B);await B.js(WATCH);
py(`from settlement import services as settlement
settlement.reopen_night(${M.tonight}, host, 'wrong count')`);
const back=await B.until(`${row(ids.ana_ben)}.dataset.paid==='0'`,9000);
check('reopening the later session makes the earlier transfer unpaid again on the open page',back>0&&/Not paid/.test(await B.js(`${row(ids.ana_ben)}.textContent`))&&await B.js(`document.querySelector('.night-overview .felt .row > .badge').textContent.trim()==='Unsettled'`),back);
await B.go('/');check('Your groups shows the earlier debts again',/₱500/.test(await B.js(`document.querySelector('main').textContent`)));

// --- Reduced motion, then without scripts.
const R=await user('hana',{reduce:true});await R.go(tonight);
await R.js(`document.querySelectorAll('[data-carry-pick] input')[0].click()`);
check('reduced motion: the count still answers and nothing moves',(await R.js(`document.querySelector('[data-carry-count]').textContent`))==="2 of 3 will be carried into tonight's list."&&await R.js(`document.getAnimations().length===0`));
const N=await user('hana',{scripts:false});await N.go(tonight);
check('without scripts the list is there, ticked, with no count line',await N.js(`document.querySelectorAll('[data-carry-pick] input:checked').length===3&&document.querySelector('[data-carry-count]').hidden`));
await N.js(`document.querySelector('form[action$="/close/"] button[type=submit]').click()`);await sleep(1200);
const plain=await N.js(list);
check('without scripts closing carries all three into one list',JSON.stringify(plain)===JSON.stringify(['Ana pays Dee ₱100','Ana pays Carlo ₱30','Ben pays Carlo ₱20']),plain);
check('without scripts the carried list reads as a disclosure',await N.js(`!!document.querySelector('details.night-carried')&&document.querySelectorAll('.carried-list > li').length===3`));
check('no script error',errors.length===0,errors);
} finally {
const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length} of ${results.length} passed`);
chrome.kill();process.exit(failed.length?1:0);
}
