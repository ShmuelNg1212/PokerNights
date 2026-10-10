// The pot's figure when its amount changes (pot.js). Seed a fresh temporary database with seed.py and
// seed_pot.py, serve it on 127.0.0.1:8765, then run. PN_DB names the SQLite file; the "other host"
// writes to it through the real services, and this page learns of it by polling.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-pot-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-pot-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const other=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from games import services as games
from ledger import services as ledger
from groups.models import Member
host=Member.objects.get(user__username='hana',role='host')
u=uuid.uuid4
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-600))};
rmSync('/private/tmp/pn-pot-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-pot-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every redraw is photographed in numbers on its first frame: what the page says the pot is, what each
// drawn cell shows and how far along it is, the figure's box and the amount added.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__errors=[];window.__f=[];addEventListener('error',e=>__errors.push(e.message));
 const m=el=>new DOMMatrix(getComputedStyle(el).transform);
 window.__box=()=>{const r=document.querySelector('#live .pot-main .display-amount').getBoundingClientRect(),l=document.querySelector('#live .table-left,#live .felt').getBoundingClientRect();return [r.left,r.top,r.width,r.height,l.height].map(n=>Math.round(n*10)/10).join()};
 window.__pot=()=>{const main=document.querySelector('#live .pot-main');if(!main)return null;const fig=main.querySelector('.display-amount'),say=fig.querySelector('.visually-hidden'),d=main.querySelector('.pot-delta');
  return {value:main.dataset.value,said:say?say.textContent:fig.firstChild.nodeValue.trim(),rolling:!!fig.querySelector('.pot-roll'),hidden:(fig.querySelector('.pot-roll')||{getAttribute(){}}).getAttribute('aria-hidden'),box:__box(),
   delta:d?d.textContent:null,deltaO:d?+getComputedStyle(d).opacity:null,deltaY:d?Math.round(m(d).m42):null,
   cells:[...fig.querySelectorAll('.pot-cell')].map(c=>{const g=c.firstChild,x=c.querySelector('.pot-gone');return {ch:g.textContent,x:Math.round(m(c).m41*10)/10,o:+getComputedStyle(g).opacity,y:Math.round(m(g).m42),old:x?x.textContent:null,oldO:x?+getComputedStyle(x).opacity:null,oldY:x?Math.round(m(x).m42):null}})}};
 document.addEventListener('live:updating',()=>{window.__before=__box()});
 document.addEventListener('live:updated',()=>requestAnimationFrame(()=>{if(!document.getElementById('live'))return;window.__at=performance.now();const p=__pot();if(p)p.before=window.__before;__f.push(p);
  if(window.__tap){window.__tap=false;document.querySelector('#live .buy-opener,#live [data-sheet-open^=buy-]').click()}}))})`;
async function user(name,width=390,setup){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);if(setup)await setup(s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const redraw=async(poke=true)=>{const n=await js('__f.length');if(poke)await js(`window.dispatchEvent(new Event('online'))`);for(let i=0;i<120;i++){if(await js('__f.length')>n)return await js('__f.at(-1)');await sleep(50)}return null};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,shot,redraw};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const dialog=`document.querySelector('dialog.sheet')`;
// At rest the figure is the text the server drew: one text node first, nothing added, nothing running.
const plain=`(()=>{const f=document.querySelector('#live .pot-main .display-amount');return f.firstChild.nodeType===3&&!f.querySelector('.pot-roll,.pot-cell,.visually-hidden')&&!f.getAttribute('style')&&document.getAnimations().filter(a=>a.playState==='running').length===0})()`;
// The figure alone: the amount added may still be arriving beside the label.
const text=`(()=>{const f=document.querySelector('#live .pot-main .display-amount');return f.firstChild.nodeType===3&&!f.querySelector('.pot-roll,.pot-cell,.visually-hidden')&&!f.getAttribute('style')})()`;
const noDelta=`!document.querySelector('.pot-delta')`;
const changed=f=>f.cells.filter(c=>c.old!==null),kept=f=>f.cells.filter(c=>c.old===null);
// Waits until so long after the last redraw.
const at=ms=>`new Promise(ok=>setTimeout(ok,Math.max(0,${ms}-(performance.now()-__at))))`;
const figure=f=>f.cells.map(c=>c.ch).join('');

async function story(width,key){
 const W=`${width}px`,S=M[key],[p0,p1,p2]=S.players;
 const A=await user('hana',width);await A.go(`/s/${S.set}/`);await sleep(400);
 check(`${W} first sight of a set: the figure is plain and nothing is added`,await A.js(`${plain}&&${noDelta}&&__pot().said==='₱4,000'`));
 // A rebuy by the other host: ₱4,000 to ₱4,500. One digit changes.
 other(`ledger.record_buy_in(${S.set},host,${p0},50000,u())`);
 let f=await A.redraw();
 check(`${W} buy-in: the page's text is the accepted amount on the first frame`,f.value==='450000'&&f.said==='₱4,500'&&f.hidden==='true',f);
 check(`${W} buy-in: only the changed digit is rolling, new below and faint, old still showing`,f.rolling&&figure(f)==='₱4,500'&&changed(f).length===1&&changed(f)[0].ch==='5'&&changed(f)[0].old==='0'&&changed(f)[0].o<0.5&&changed(f)[0].y>0&&changed(f)[0].oldO>0.3,f.cells);
 check(`${W} buy-in: the characters that did not change do not move`,kept(f).length===5&&kept(f).every(c=>c.o===1&&c.y===0&&c.x===0),f.cells);
 check(`${W} buy-in: the figure's box and the panel are the same size and place during the roll`,f.box===f.before,[f.before,f.box]);
 check(`${W} buy-in: "+₱500" is beside the label, rising`,f.delta==='+₱500'&&f.deltaO<0.6&&f.deltaY>0,f);
 await A.shot(`pot-roll-${width}`);
 const done=await A.js(`new Promise(ok=>{(function look(){if(${text})ok(Math.round(performance.now()-__at));else if(performance.now()-__at>2000)ok(0);else requestAnimationFrame(look)})()})`);
 check(`${W} buy-in: plain text again within 600ms (${done}ms), same box`,done>0&&done<=600&&await A.js(`__box()`)===f.before&&await A.js(`__pot().said==='₱4,500'`));
 await A.js(at(800));await A.shot(`pot-added-${width}`);
 check(`${W} buy-in: the amount added is opaque, at rest and hidden from a screen reader`,await A.js(`(()=>{const d=document.querySelector('.pot-label .pot-delta'),c=getComputedStyle(d);return c.opacity==='1'&&c.transform==='none'&&d.getAttribute('aria-hidden')==='true'})()`));
 check(`${W} buy-in: the amount added leaves the label one line high and inside the panel`,await A.js(`(()=>{const l=document.querySelector('.pot-main .pot-label'),d=l.querySelector('.pot-delta').getBoundingClientRect(),p=document.querySelector('.pot-main').getBoundingClientRect();return l.getClientRects().length===1&&l.getBoundingClientRect().height<26&&d.right<=p.right+0.5&&document.documentElement.scrollWidth<=${width}})()`));
 await A.js(at(2800));check(`${W} buy-in: the amount added is fading at 2.8s`,await A.js(`+getComputedStyle(document.querySelector('.pot-delta')).opacity<1`));
 await A.js(at(3100));check(`${W} buy-in: the amount added is gone after 3s`,await A.js(`${noDelta}&&${plain}`));
 // Two buy-ins in one update: one roll, their sum. ₱4,500 to ₱6,200.
 other(`ledger.record_buy_in(${S.set},host,${p1},100000,u())
ledger.record_buy_in(${S.set},host,${p2},70000,u())`);
 f=await A.redraw();
 check(`${W} two buy-ins in one update: one roll to ₱6,200 and "+₱1,700"`,f.said==='₱6,200'&&f.delta==='+₱1,700'&&changed(f).map(c=>c.old+c.ch).join()==='46,52',f);
 // A cash-out lowers the figure: the roll goes the other way.
 await sleep(3200);
 other(`ledger.record_cash_out(${S.set},host,${p1},120050,u())`);
 f=await A.redraw();
 check(`${W} cash-out: the roll is downward with "−₱1,200.50", and centavos arrive`,f.said==='₱4,999.50'&&f.delta==='−₱1,200.50'&&changed(f).every(c=>c.y<0)&&f.cells.slice(-3).every(c=>c.old===null&&c.o<0.5),f);
 await sleep(700);
 // Nine characters set the figure in its smaller size, so the box is compared with the plain figure after the roll.
 check(`${W} cash-out: the box during the roll is the plain figure's`,f.box===await A.js(`__box()`)&&await A.js(text),[f.box,await A.js(`__box()`)]);
 await sleep(2500);
 // Your own rebuy goes through the other redraw path (a morph), and a second tap lands mid-roll.
 await A.js(`window.__tap=true`);
 const mine=A.redraw(false);
 await A.js(`(()=>{document.querySelector('[data-sheet-open=buy-${p2}]').click();const f=${dialog}.querySelector('[name=amount]');f.value='500';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);
 f=await mine;
 check(`${W} your own rebuy: the same roll and "+₱500"`,!!f&&f.rolling&&f.said==='₱5,499.50'&&f.delta==='+₱500',f);
 check(`${W} your own rebuy: a tap during the roll opens the sheet`,await A.js(`${dialog}.open`));
 await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(700);
 check(`${W} at rest after all of it: plain text, no script error`,await A.js(`${plain}&&__errors.length===0&&__pot().said==='₱5,499.50'`),await A.js(`__errors`));
 return A;
}

try {
 const A=await story(390,'roll');
 // A second change arrives while the first is rolling: it ends at the right amount.
 const S=M.roll;await sleep(3000);
 other(`ledger.record_buy_in(${S.set},host,${S.players[0]},50050,u())`);let f=await A.redraw();
 other(`ledger.record_buy_in(${S.set},host,${S.players[0]},50000,u())`);f=await A.redraw();
 check('a change during a roll: one drawn figure, the accepted amount',f.said==='₱6,500'&&figure(f)==='₱6,500'&&await A.js(`document.querySelectorAll('.pot-roll').length===1`),f);
 // Twenty redraws leave nothing behind.
 for(let i=0;i<20;i++){other(`ledger.record_buy_in(${S.set},host,${S.players[i%4]},50000,u())`);await A.redraw()}
 await sleep(3300);
 check('twenty redraws: plain text, nothing running, no amount left over',await A.js(`${plain}&&${noDelta}&&__errors.length===0&&__pot().said==='₱16,500'`),await A.js(`__pot()`));
 // A reload does not roll.
 await A.go(`/s/${S.set}/`);await sleep(500);
 check('reload: nothing moves',await A.js(`${plain}&&${noDelta}`));
 // A hidden tab: the redraw happens, nothing is added.
 await A.js(`Object.defineProperty(document,'hidden',{get:()=>true,configurable:true})`);
 other(`ledger.record_buy_in(${S.set},host,${S.players[0]},50000,u())`);f=await A.redraw();
 check('hidden tab: the figure is simply the new amount',f.said==='₱17,000'&&!f.rolling&&f.delta===null,f);
 await A.js(`delete document.hidden`);

 await story(1280,'desk');

 // The figure gets wider: ₱9,500 to ₱10,000. The peso sign stays itself and glides.
 const G=M.grow,D=await user('hana');await D.go(`/s/${G.set}/`);await sleep(400);
 const lefts=`(()=>{const n=document.querySelector('#live .pot-main .display-amount').firstChild,r=document.createRange(),x=[];for(let i=0;i<n.nodeValue.trim().length;i++){r.setStart(n,i);r.setEnd(n,i+1);x.push(Math.round(r.getBoundingClientRect().left*10)/10)}return x})()`;
 const was=await D.js(lefts);
 other(`ledger.record_buy_in(${G.set},host,${G.players[0]},50000,u())`);f=await D.redraw();
 check('wider: the new leading digit arrives, the peso sign is not rolled into a digit',f.said==='₱10,000'&&f.cells[0].ch==='₱'&&f.cells[0].old===null&&f.cells[1].ch==='1'&&f.cells[1].o<0.5,f.cells);
 check('wider: the page is no wider than the screen',await D.js(`document.documentElement.scrollWidth<=390`));
 await sleep(700);const now=await D.js(lefts);
 check('wider: ends as plain text in the right place',await D.js(plain)&&now.length===7&&Math.abs(now[0]-was[0])<=0.5,[was,now]);
 // Narrower again: a cash-out to ₱9,000.
 await sleep(2600);other(`ledger.record_cash_out(${G.set},host,${G.players[1]},100000,u())`);f=await D.redraw();
 check('narrower: ₱9,000 with "−₱1,000", no cell for the digit that went',f.said==='₱9,000'&&figure(f)==='₱9,000'&&f.delta==='−₱1,000',f);
 await sleep(700);check('narrower: plain text at rest',await D.js(plain));
 // The long size: past eight characters the figure is set smaller.
 await sleep(2600);other(`ledger.record_buy_in(${G.set},host,${G.players[0]},99100000,u())`);f=await D.redraw();
 check('long: ₱1,000,000 fits on one line with its amount added',f.said==='₱1,000,000'&&f.delta==='+₱991,000'&&await D.js(`document.documentElement.scrollWidth<=390&&document.querySelector('.pot-main .display-amount').classList.contains('amount-long')`),f);
 await sleep(700);check('long: plain text at rest, no error',await D.js(`${plain}&&__errors.length===0`),await D.js(`__errors`));

 // A chips game: the unit word stays under the number and is not rolled.
 const C=M.chips,H=await user('hana');await H.go(`/s/${C.set}/`);await sleep(400);
 other(`ledger.record_buy_in(${C.set},host,${C.players[0]},500,u())`);f=await H.redraw();
 check('chips: 4,000 to 4,500 rolls one digit and adds "+500 chips"',f.said==='4,500'&&figure(f)==='4,500'&&changed(f).length===1&&f.delta==='+500 chips'&&f.box===f.before,f);
 check('chips: the unit word is still there',await H.js(`document.querySelector('.pot-main .display-amount small').textContent==='chips'`));
 await H.shot('pot-chips');await sleep(700);
 check('chips: plain text at rest, no error',await H.js(`${plain}&&__errors.length===0`),await H.js(`__errors`));

 // Reduced motion: nothing moves, and the amount added is still.
 const P=M.still,R=await user('hana',390,s=>send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s));await R.go(`/s/${P.set}/`);await sleep(300);
 other(`ledger.record_buy_in(${P.set},host,${P.players[0]},50000,u())`);f=await R.redraw();
 check('reduced motion: the figure is plain at once and "+₱500" is there, still',f.said==='₱4,500'&&!f.rolling&&f.delta==='+₱500'&&f.deltaO===1&&f.deltaY===0&&await R.js(`document.getAnimations().length===0&&__errors.length===0`),f);
 await sleep(3100);check('reduced motion: the amount added is gone after 3s',await R.js(noDelta));
 // A blocked Motion file: the page is as it was before this change.
 const Q=M.plain,B=await user('hana',390,s=>send('Network.setBlockedURLs',{urls:['*motion-14.0.0.js*']},s));await B.go(`/s/${Q.set}/`);await sleep(300);
 other(`ledger.record_buy_in(${Q.set},host,${Q.players[0]},50000,u())`);f=await B.redraw();
 check('blocked library: the new amount, no roll, no amount added, no error',f.said==='₱4,500'&&!f.rolling&&f.delta===null&&await B.js(`!window.Motion&&__errors.length===0`),f);

 // The guards. A drawn copy that cannot take the plain figure's room is dropped, and so is an amount
 // this script would write differently from the server.
 const U=M.guard,X=await user('hana');await X.go(`/s/${U.set}/`);await sleep(300);
 await X.js(`document.head.insertAdjacentHTML('beforeend','<style id="wide">.pot-cell{padding-right:1px}</style>')`);
 other(`ledger.record_buy_in(${U.set},host,${U.players[0]},50000,u())`);f=await X.redraw();
 check('guard: a copy of another width is not shown; the figure is the plain new amount',f.said==='₱4,500'&&!f.rolling&&await X.js(`${text}&&__errors.length===0`),f);
 await X.js(`document.getElementById('wide').remove();document.querySelector('.pot-delta')?.remove()`);
 await X.js(`document.addEventListener('live:updated',()=>{document.querySelector('#live .felt').dataset.unit='chips'},true)`);
 other(`ledger.record_buy_in(${U.set},host,${U.players[0]},50000,u())`);f=await X.redraw();
 check('guard: an amount written differently from the server is not shown; the roll still runs',f.said==='₱5,000'&&f.delta===null&&f.rolling&&await X.js(`__errors.length===0`),f);
 writeFileSync(`${OUT}/pot.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
