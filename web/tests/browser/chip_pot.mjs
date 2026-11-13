// A chip to the pot (chipfly.js). Seed a fresh temporary SQLite database with seed_chip_pot.py alone, serve it on
// 127.0.0.1:8765, then run. PN_DB names the SQLite file; the "other host" writes to it through the real
// services, and each page learns of it by polling. PN_BLOCK_CHIPFLY=1 blocks the script, to see the checks fail.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-pot-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-chip-pot-check.sqlite3';
const M=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-chip-pot-manifest.json','utf8'));
const PROFILE=process.env.PN_CHROME_PROFILE || '/private/tmp/pn-chip-pot-chrome';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const other=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from games import services as games
from ledger import services as ledger
from ledger.models import BuyIn, CashOut
from groups.models import Member
host=Member.objects.get(user__username='hana',role='host')
u=uuid.uuid4
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-600))};
rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir='+PROFILE,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// A sampler, installed before the page's scripts. Each chip is noted in the task that adds it (what the pot
// says, whether a sheet is open, where the tokens and the pot are) and then read on every frame until it is gone.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__errors=[];window.__chips=[];window.__n=0;addEventListener('error',e=>__errors.push(e.message));
 const mid=el=>{const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width}};
 const read=c=>{const p=mid(c.el);p.o=+getComputedStyle(c.el).opacity;p.t=performance.now();c.samples.push(p)};
 window.__ends=()=>{const pot=document.querySelector('#live .pot-main .display-amount'),rows={};document.querySelectorAll('#live .player-row[data-watch]').forEach(r=>{rows[r.dataset.watch]=mid(r.querySelector('.chip'))});
  const dock=document.querySelector('.host-controls');return {pot:pot?mid(pot):null,rows,floor:dock&&getComputedStyle(dock).position==='fixed'?dock.getBoundingClientRect().top:innerHeight}};
 window.__styled=()=>[...document.querySelectorAll('#live [style]')].filter(e=>e.getAttribute('style').trim()).length;
 new MutationObserver(list=>list.forEach(m=>m.addedNodes.forEach(n=>{if(!n.classList||!n.classList.contains('fly-chip'))return;
  const main=document.querySelector('#live .pot-main'),fig=main&&main.querySelector('.display-amount'),say=fig&&fig.querySelector('.visually-hidden');
  const c={el:n,born:performance.now(),sinceUpdate:performance.now()-window.__at,colour:n.className,text:n.textContent,pot:main?main.dataset.value:null,said:fig?(say?say.textContent:fig.firstChild.nodeValue.trim()):null,
   sheet:!!document.querySelector('dialog[open]'),ends:__ends(),samples:[],gone:null,layerHits:getComputedStyle(n.parentNode).pointerEvents,hidden:n.parentNode.getAttribute('aria-hidden'),inLive:!!n.closest('#live')};
  read(c);__chips.push(c);
  if(window.__tap){window.__tap=false;document.querySelector('#live [data-sheet-open^=buy-]').click()}}))).observe(document.documentElement,{childList:true,subtree:true});
 (function look(){__chips.forEach(c=>{if(c.gone!==null)return;if(c.el.isConnected)read(c);else c.gone=performance.now()});requestAnimationFrame(look)})();
 document.addEventListener('live:updated',()=>{window.__at=performance.now();window.__n++})})`;
const SUMMARY=`__chips.map(c=>({born:c.born,since:Math.round(c.sinceUpdate),life:c.gone===null?null:Math.round(c.gone-c.born),colour:c.colour,text:c.text,pot:c.pot,said:c.said,sheet:c.sheet,ends:c.ends,hits:c.layerHits,hidden:c.hidden,inLive:c.inLive,
 first:c.samples[0],last:c.samples[c.samples.length-1],frames:c.samples.length,gap:Math.round(Math.max(0,...c.samples.slice(1).map((s,i)=>s.t-c.samples[i].t))),seen:Math.max(...c.samples.map(s=>s.o))}))`;
async function user(name,width=390,height=844,setup){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const blocked=[];if(process.env.PN_BLOCK_CHIPFLY)blocked.push('*chipfly.js*');if(setup)await setup(s,blocked);if(blocked.length)await send('Network.setBlockedURLs',{urls:blocked},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // Waits for the next redraw, then for every chip it started to be gone. Returns the chips of that redraw.
 const redraw=async(poke=true,settle=900)=>{const n=await js('__n'),had=await js('__chips.length');if(poke)await js(`window.dispatchEvent(new Event('online'))`);
  let drawn=false;for(let i=0;i<160;i++){if(await js('__n')>n){drawn=true;break}await sleep(50)}
  if(!drawn)return null;await sleep(settle);return (await js(SUMMARY)).slice(had)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,shot,redraw};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const near=(a,b,by)=>!!a&&!!b&&Math.abs(a.x-b.x)<=by&&Math.abs(a.y-b.y)<=by;
const dialog=`document.querySelector('dialog.sheet')`;
// Nothing of a chip is left: no layer, no chip, nothing running. The marks of changes.js stay for 3s and write
// inline styles of their own, so the live region's inline styles are compared once those have gone.
const clean=()=>`!document.querySelector('.chipfly,.fly-chip')&&document.getAnimations().filter(a=>a.playState==='running').length===0&&__errors.length===0`;
const row=p=>`player-${p}`;
// Row to pot: starts on the token, whole; ends at the pot, small and faint.
const toPot=(c,p,by=1)=>!!c&&near(c.first,c.ends.rows[row(p)],by)&&c.first.o===1&&Math.abs(c.first.w-c.ends.rows[row(p)].w)<=1&&near(c.last,c.ends.pot,8)&&c.last.w<c.first.w*0.75&&c.last.o<0.6;
// Pot to row: starts at the pot, small and unseen; ends on the token, whole.
const toRow=(c,p)=>!!c&&near(c.first,c.ends.pot,1)&&c.first.o===0&&c.first.w<c.ends.rows[row(p)].w*0.75&&near(c.last,c.ends.rows[row(p)],3)&&c.last.o>0.9;
const brief=list=>list&&list.map(c=>({since:c.since,life:c.life,first:c.first,last:c.last,pot:c.ends.pot,frames:c.frames,gap:c.gap}));

try {
 const S=M.main,[ben,p1,p2,p3,p4,p5]=S.players;
 const A=await user('hana');await A.go(`/s/${S.set}/`);
 const B=await user('ben');await B.go(`/s/${S.set}/`);
 const styledA=await A.js(`__styled()`),styledB=await B.js(`__styled()`);
 check('first sight of a set: no chip, no layer',await A.js(`__chips.length===0&&${clean()}`));

 // A rebuy by the other host. Each phone on the page sees one chip at its next redraw.
 other(`ledger.record_buy_in(${S.set},host,${p1},50000,u())`);
 let a=A.redraw(),b=B.redraw();a=await a;b=await b;
 check('rebuy, host phone: one chip from the row token to the pot',a&&a.length===1&&toPot(a[0],p1),brief(a));
 check('rebuy, second phone: one chip from the row token to the pot',b&&b.length===1&&toPot(b[0],p1),brief(b));
 check('rebuy: the pot says the accepted amount on the chip\'s first frame',a&&a[0]&&a[0].pot==='650000'&&a[0].said==='₱6,500',a&&a[0]&&[a[0].pot,a[0].said]);
 check('rebuy: the chip is a copy of the token (colour and initial) with no player id',a&&a[0]&&/\bchip\b/.test(a[0].colour)&&/\bk\d+\b/.test(a[0].colour)&&a[0].text.length>0&&await A.js(`!document.querySelector('.fly-chip[data-m]')`),a&&a[0]&&a[0].colour);
 check('rebuy: about 360ms, in a layer outside the live region that takes no pointer events and is hidden from a screen reader',a&&a[0]&&a[0].life>=300&&a[0].life<=480&&a[0].hits==='none'&&a[0].hidden==='true'&&!a[0].inLive,a&&a[0]&&[a[0].life,a[0].hits,a[0].hidden,a[0].inLive]);
 check('rebuy: nothing is left 1s later on either phone',await A.js(clean())&&await B.js(clean()),await A.js(`[__errors,document.getAnimations().length]`));

 await sleep(2600);
 check('rebuy: once the row\'s mark has gone, the live region has no inline style it did not have',await A.js(`__styled()`)===styledA&&await B.js(`__styled()`)===styledB,await A.js(`[...document.querySelectorAll('#live [style]')].map(e=>e.className+' / '+e.getAttribute('style'))`));
 // A cash-out: the other way.
 other(`ledger.record_cash_out(${S.set},host,${p2},40000,u())`);
 a=A.redraw();b=B.redraw();a=await a;b=await b;
 check('cash-out, host phone: one chip from the pot to the row token',a&&a.length===1&&toRow(a[0],p2),brief(a));
 check('cash-out, second phone: one chip from the pot to the row token',b&&b.length===1&&toRow(b[0],p2),brief(b));
 check('cash-out: the pot says the accepted amount on the chip\'s first frame, and the chip is seen on its way',a&&a[0]&&a[0].pot==='610000'&&a[0].seen===1,a&&a[0]&&[a[0].pot,a[0].seen]);

 // Corrections move no chip.
 await sleep(2400);
 other(`ledger.reverse_buy_in(${S.set},host,BuyIn.objects.filter(participant_id=${p1},reversal__isnull=True).latest('pk').pk,'Wrong amount')`);
 a=await A.redraw();
 check('a reversed buy-in: the redraw comes and no chip moves',a&&a.length===0&&await A.js(`document.querySelector('#live .pot-main').dataset.value==='560000'`),brief(a));
 other(`ledger.reverse_cash_out(${S.set},host,CashOut.objects.filter(participant_id=${p2},reversal__isnull=True).latest('pk').pk,'Wrong amount')`);
 a=await A.redraw();
 check('a reversed cash-out: no chip',a&&a.length===0,brief(a));

 // Several rows in one redraw.
 await sleep(1200);
 other(`ledger.record_buy_in(${S.set},host,${p3},50000,u())
ledger.record_buy_in(${S.set},host,${p4},50000,u())`);
 a=await A.redraw();
 check('two rebuys in one redraw: two chips, each from its own row, 60ms apart',a&&a.length===2&&toPot(a[0],p3)&&toPot(a[1],p4)&&Math.abs(a[1].born-a[0].born-60)<=30,a&&[brief(a),a.length===2&&a[1].born-a[0].born]);
 await sleep(1200);
 other([ben,p1,p2,p3,p4].map(p=>`ledger.record_buy_in(${S.set},host,${p},50000,u())`).join('\n'));
 a=await A.redraw();
 check('five rebuys in one redraw: no chip',a&&a.length===0&&await A.js(clean()),brief(a));

 // The sender's own rebuy: the sheet is closing when the page is redrawn, and the chip waits for it.
 await sleep(3200);
 let mine=A.redraw(false,1400);
 await A.js(`(()=>{document.querySelector('[data-sheet-open=buy-${p5}]').click();const f=${dialog}.querySelector('[name=amount]');f.value='500';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);
 a=await mine;
 check('your own rebuy: one chip from the row to the pot, after the sheet has closed',a&&a.length===1&&toPot(a[0],p5)&&a[0].sheet===false,a&&[brief(a),a[0]&&a[0].sheet]);
 check('your own rebuy: the sheet is closed and nothing is left',await A.js(`!${dialog}.open&&${clean()}`),await A.js(`__errors`));
 // A tap during the flight is the page's tap.
 await sleep(2000);
 await A.js(`window.__tap=true`);
 other(`ledger.record_buy_in(${S.set},host,${p1},50000,u())`);
 a=await A.redraw();
 check('a tap on Rebuy during the flight opens the sheet, and the chip still ends',a&&a.length===1&&a[0].life>0&&await A.js(`${dialog}.open`),brief(a));
 await A.js(`${dialog}.querySelector('.sheet-head button').click()`);await sleep(700);
 await A.shot('chip-pot-rest-390');

 // A hidden tab, a reload and a full replacement show the new figures and move nothing.
 await A.go(`/s/${S.set}/`);
 check('reload: no chip',await A.js(`__chips.length===0&&!document.querySelector('.chipfly')`));
 // The poll is held back, so that the page learns of the rebuy from the replacement alone.
 const before=await A.js(`(()=>{const real=window.fetch;window.fetch=function(u){return String(u&&u.url||u).includes('/live')?new Promise(()=>{}):real.apply(this,arguments)};return document.querySelector('#live .pot-main').dataset.value})()`);
 await A.js(`Turbo.visit('/')`);await sleep(1500);
 other(`ledger.record_buy_in(${S.set},host,${p2},50000,u())`);
 await A.js(`Turbo.visit('/s/${S.set}/')`);await sleep(2000);
 const after=await A.js(`[document.querySelector('#live .pot-main').dataset.value,__chips.length,!!document.querySelector('.chipfly'),__errors]`);
 check('a full replacement (away and back): the new amount, no chip',after[0]!==before&&after[1]===0&&!after[2]&&!after[3].length,[before,after]);

 // The start of a set belongs to the overture.
 const T=M.start,E=await user('ben');await E.go(`/s/${T.set}/`);
 other(`games.transition(${T.set},host,'start',opening_buy_ins=False)`);
 let e=await E.redraw(true,2600);
 check('the start of a set: the redraw comes and no chip moves',e&&e.length===0&&await E.js(`document.getElementById('live').dataset.state==='running'&&__errors.length===0`),brief(e));
 other(`ledger.record_buy_in(${T.set},host,${T.players[1]},50000,u())`);
 e=await E.redraw();
 check('a rebuy after the start: one chip',e&&e.length===1&&toPot(e[0],T.players[1],1.5),brief(e));

 const H=M.hidden,V=await user('hana');await V.go(`/s/${H.set}/`);
 await V.js(`Object.defineProperty(document,'hidden',{get:()=>true,configurable:true})`);
 other(`ledger.record_buy_in(${H.set},host,${H.players[1]},50000,u())`);
 let v=await V.redraw();
 check('hidden tab: the new amount, no chip',v&&v.length===0&&await V.js(`document.querySelector('#live .pot-main').dataset.value==='450000'&&!document.querySelector('.chipfly')`),brief(v));

 // 320 x 568 with twelve players: the first row is on the screen, the last is under the dock or below it.
 const N=M.small,C=await user('hana',320,568);await C.go(`/s/${N.set}/`);
 other(`ledger.record_buy_in(${N.set},host,${N.players[0]},50000,u())`);
 let c=await C.redraw();
 check('320px: a chip from the first row to the pot; the page is no wider than the screen',c&&c.length===1&&toPot(c[0],N.players[0])&&await C.js(`document.documentElement.scrollWidth<=320`),brief(c));
 await sleep(2400);
 other(`ledger.record_buy_in(${N.set},host,${N.players[11]},50000,u())`);
 c=await C.redraw();
 const far=c&&c[0]&&c[0].ends.rows[row(N.players[11])];
 check('320px: a row out of sight sends its chip from that edge, unseen at first, to the pot',c&&c.length===1&&far.y>c[0].ends.floor-12&&c[0].first.o===0&&c[0].first.y>=c[0].ends.floor&&c[0].seen===1&&near(c[0].last,c[0].ends.pot,8),[brief(c),far]);
 await sleep(2400);
 other(`ledger.record_cash_out(${N.set},host,${N.players[11]},20000,u())`);
 c=await C.redraw();
 check('320px: a cash-out to a row out of sight goes to that edge and fades',c&&c.length===1&&near(c[0].first,c[0].ends.pot,1)&&c[0].last.y>c[0].ends.floor-30&&c[0].last.o<0.6,brief(c));
 // The pot is out of sight too: nothing to show.
 await sleep(2400);
 await C.js(`window.scrollTo(0,document.documentElement.scrollHeight)`);await sleep(300);
 const potGone=await C.js(`document.querySelector('#live .pot-main .display-amount').getBoundingClientRect().bottom<0`);
 other(`ledger.record_buy_in(${N.set},host,${N.players[11]},50000,u())`);
 c=await C.redraw();
 check('320px, scrolled down: the pot is off the screen and the chip goes to the top edge and fades',potGone&&c&&c.length===1&&c[0].last.y<10&&c[0].last.o<0.6,[potGone,brief(c)]);
 await C.shot('chip-pot-rest-320');

 // 1280px: two columns.
 const K=M.desk,D=await user('hana',1280,800);await D.go(`/s/${K.set}/`);
 other(`ledger.record_buy_in(${K.set},host,${K.players[2]},50000,u())`);
 let d=await D.redraw();
 check('1280px: one chip from the row token to the pot',d&&d.length===1&&toPot(d[0],K.players[2]),brief(d));
 await sleep(2400);
 other(`ledger.record_cash_out(${K.set},host,${K.players[2]},30000,u())`);
 d=await D.redraw();
 check('1280px: one chip from the pot to the row token',d&&d.length===1&&toRow(d[0],K.players[2]),brief(d));

 // Reduced motion and a blocked Motion file: the page of today.
 const P=M.still,R=await user('hana',390,844,s=>send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s));await R.go(`/s/${P.set}/`);
 other(`ledger.record_buy_in(${P.set},host,${P.players[1]},50000,u())`);
 let r=await R.redraw();
 check('reduced motion: the new amount, no chip, no error',r&&r.length===0&&await R.js(`document.querySelector('#live .pot-main').dataset.value==='450000'&&!document.querySelector('.chipfly')&&__errors.length===0`),brief(r));
 const Q=M.plain,X=await user('hana',390,844,(s,blocked)=>{blocked.push('*motion-14.0.0.js*')});await X.go(`/s/${Q.set}/`);
 other(`ledger.record_buy_in(${Q.set},host,${Q.players[1]},50000,u())`);
 let x=await X.redraw();
 check('blocked Motion file: the new amount, no chip, no error',x&&x.length===0&&await X.js(`!window.Motion&&document.querySelector('#live .pot-main').dataset.value==='450000'&&__errors.length===0`),brief(x));

 // A slow phone: the flight keeps its frames.
 const L=M.slow,Z=await user('hana',390,844,s=>send('Emulation.setCPUThrottlingRate',{rate:4},s));await Z.go(`/s/${L.set}/`);
 other(`ledger.record_buy_in(${L.set},host,${L.players[1]},50000,u())`);
 let z=await Z.redraw(true,1500);
 check('processor slowed four times: one chip, no frame over 50ms',z&&z.length===1&&z[0].gap<=50&&z[0].frames>=8,z&&z[0]&&[z[0].gap,z[0].frames,z[0].life]);
 writeFileSync(`${OUT}/chip_pot.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
