// Haptics (haptics.js) and the Vibration switch. Seed a fresh temporary SQLite database with
// seed_sheet_drag.py alone, start Django on 127.0.0.1:8765 with it, then run this file with PN_DB set
// to that database file. The probe records buy-ins and a cash-out (from a Django shell, so that the
// books balance while a phone watches): reseed before a repeat. No check can feel a vibration: this records what was asked of
// navigator.vibrate (the Android path) and each click on the iPhone's hidden switch.
import {spawn,execFileSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-haptics-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const IDS=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-drag-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const DB=process.env.PN_DB || '/private/tmp/pn-drag/db.sqlite3';
// A write by nobody on these phones: the service records it, as a host's other device would.
const shell=code=>execFileSync('.venv/bin/python',['manage.py','shell','-c',code],{env:{...process.env,DATABASE_URL:`sqlite:///${DB}`,DEBUG:'True'},stdio:['ignore','pipe','pipe']});
const PROFILE=process.env.PN_CHROME_PROFILE || '/private/tmp/pn-haptics-chrome';rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9344',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9344/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Three kinds of phone: Android (vibrate), iPhone (no vibrate, the switch input) and one with neither.
const KINDS={
 android:`Object.defineProperty(Navigator.prototype,'vibrate',{configurable:true,value:function(p){(window.__vib=window.__vib||[]).push(p);return true}});`,
 // One label.click() is a click on the label and one on the input it activates: one tick. Count the label's.
 iphone:`delete Navigator.prototype.vibrate;Object.defineProperty(HTMLInputElement.prototype,'switch',{configurable:true,get(){return this.hasAttribute('switch')}});
  addEventListener('click',e=>{if(e.target.matches&&e.target.matches('label[data-haptic]'))(window.__ticks=window.__ticks||[]).push(Math.round(performance.now()))},true);`,
 none:`delete Navigator.prototype.vibrate;`,
};
async function user(name,kind){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:KINDS[kind]+`window.__vib=window.__vib||[];window.__ticks=window.__ticks||[];addEventListener('DOMContentLoaded',()=>{window.__errors=[];addEventListener('error',e=>__errors.push(e.message))})`},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const tap=async expr=>{const p=await js(`(()=>{const r=(${expr}).getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},s);await sleep(40);await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},s);await sleep(150)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 await js(`localStorage.setItem('rack-dock','open');localStorage.setItem('rack-install','done')`);
 return {s,js,go,tap};}
const results=[];const check=(name,ok,detail='')=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||!detail?'':' — '+detail}`)};
const D=`document.querySelector('dialog.sheet')`,opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].find(b=>b.getClientRects().length)`;
const vib=A=>A.js(`JSON.stringify(__vib)`);
const reset=A=>A.js(`__vib.length=0;__ticks.length=0`);
const send_=(A,amount)=>A.js(`(()=>{const f=${D}.querySelector('[name=amount]');f.value='${amount}';f.form.noValidate=true;f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);
const menu=`document.getElementById('account')`,sw=`document.querySelector('[data-haptics-switch]')`;
try {
 // Android.
 const A=await user('hana','android');await A.go(`/s/${IDS.play}/`);
 check('android: haptics can play',await A.js(`pokerHaptics.can()&&pokerHaptics.enabled()`));
 await reset(A);await A.js(`pokerHaptics.play('done')`);
 check('done is [10, 50, 14]',await vib(A)==='[[10,50,14]]',await vib(A));
 await sleep(100);await reset(A);await A.js(`pokerHaptics.play('tick');pokerHaptics.play('tick')`);
 check('two plays within 60 ms give one vibration',await vib(A)==='[8]',await vib(A));
 await sleep(100);await reset(A);await A.js(`(()=>{const d=Object.getOwnPropertyDescriptor(Document.prototype,'hidden');Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});pokerHaptics.play('done');delete document.hidden})()`);
 check('nothing in a hidden tab',await vib(A)==='[]',await vib(A));
 await A.js(`pokerHaptics.play('nonsense')`);
 check('an unknown kind does nothing',await vib(A)==='[]');
 // A number key under a finger ticks; the sheet opening does not.
 await A.js(`${opener}.click()`);await sleep(800);await reset(A);
 await A.tap(`${D}.querySelector('.numpad-key[data-key="5"]')`);
 check('a number key ticks',await vib(A)==='[8]',await vib(A));
 // An accepted buy-in: done. A refused one: refused.
 await reset(A);await send_(A,'500');await sleep(2000);
 check('an accepted write vibrates done',await vib(A)==='[[10,50,14]]',await vib(A));
 await A.js(`${opener}.click()`);await sleep(800);await reset(A);await send_(A,'99999999');await sleep(2000);
 check('a refused write vibrates refused',(await vib(A)).includes('[24,40,24]')&&!(await vib(A)).includes('[10,50,14]'),await vib(A));
 await A.js(`${D}.open&&${D}.querySelector('.sheet-head button').click()`);await sleep(500);
 // Another person's buy-in, and polls with no change: nothing on this phone.
 const A2=await user('hana','android');await A2.go(`/s/${IDS.play}/`);
 await reset(A);const pot=await A.js(`document.querySelector('#live').textContent.length`);
 await A2.js(`${opener}.click()`);await sleep(800);await send_(A2,'700');await sleep(2500);
 await sleep(9000); // at least one poll brings A2's buy-in to A, then later polls change nothing
 check("A2's buy-in reached A's page",await A.js(`document.querySelector('#live').textContent.includes('7,') || document.querySelector('#live').textContent.length!==${pot}`));
 check("another person's buy-in and quiet polls: no vibration",await vib(A)==='[]',await vib(A));
 // A screen change by a tapped link: nothing.
 await reset(A);await A.js(`document.querySelector('.table-bar a').click()`);await sleep(1500);
 check('a screen change: no vibration',await vib(A)==='[]'&&await A.js(`location.pathname`)!==`/s/${IDS.play}/`,await vib(A));
 // The session page redraws itself for someone else's change with the Turbo visit nightlive.js makes
 // (nightlive.js:58). Every Turbo render says inplace:updated; with no form sent, nothing vibrates.
 await A.go(`/n/${IDS.play_night}/`);await reset(A);
 await A.js(`new Promise(r=>{document.addEventListener('inplace:updated',()=>{window.__rendered=true;r()},{once:true});Turbo.visit(location.pathname+location.search,{action:'replace'})})`);await sleep(600);
 check("the session page's own redraw: a Turbo render that says inplace:updated",await A.js(`!!window.__rendered`));
 check("the session page's own redraw: no vibration",await vib(A)==='[]',await vib(A));
 // The books balance: when they come to balance while the phone watches, once; not on a reload, and
 // not on another phone that first opens the set already balanced.
 await A.go(`/s/${IDS.count}/`);await sleep(500);await reset(A);
 check('the books do not balance yet',await A.js(`!document.querySelector('[data-balance]')`));
 shell(`import uuid; from django.contrib.auth import get_user_model; from groups.models import Member; from ledger import services as L; m=Member.objects.get(user__username='hana', role='host'); L.record_cash_out(${IDS.count}, m, ${IDS.count_last}, 50000, uuid.uuid4())`);
 await sleep(9000); // a poll brings the balance
 check('the books came to balance on the page',await A.js(`!!document.querySelector('[data-balance]')`));
 check('the books balancing: one done',await vib(A)==='[[10,50,14]]',await vib(A));
 await reset(A);await A.go(`/s/${IDS.count}/`);await sleep(500);
 check('a reload of a balanced set: nothing',await vib(A)==='[]',await vib(A));
 await A2.js(`__vib.length=0`);await A2.go(`/s/${IDS.count}/`);await sleep(500);
 check('another phone that first opens it balanced: nothing',await A2.js(`JSON.stringify(__vib)`)==='[]',await A2.js(`JSON.stringify(__vib)`));
 // The Vibration switch.
 await A.go(`/s/${IDS.play}/`);
 check('android: the Vibration switch is shown and on',await A.js(`!${sw}.hidden&&${sw}.getAttribute('aria-checked')==='true'`));
 await A.js(`${menu}.querySelector('summary').click()`);await sleep(400);
 check('the switch is a 48 px target with its label',await A.js(`${sw}.offsetHeight>=48&&${sw}.textContent.includes('Vibration')`),await A.js(`JSON.stringify({h:${sw}.getBoundingClientRect().height,open:${menu}.open})`));
 await reset(A);await A.js(`${sw}.click()`);await sleep(200);
 check('off: aria-checked false, kept in this browser',await A.js(`${sw}.getAttribute('aria-checked')==='false'&&localStorage.getItem('rack-haptics')==='off'`));
 await A.js(`pokerHaptics.play('done')`);
 check('off: nothing plays',await vib(A)==='[]',await vib(A));
 await A2.js(`(__vib.length=0,pokerHaptics.play('done'))`);
 check('another browser still vibrates',await A2.js(`JSON.stringify(__vib)`)==='[[10,50,14]]');
 await A.go(`/s/${IDS.play}/`);
 check('off survives a page change',await A.js(`${sw}.getAttribute('aria-checked')==='false'&&!pokerHaptics.enabled()`));
 await A.js(`${menu}.querySelector('summary').click()`);await sleep(400);await sleep(100);await reset(A);
 await A.js(`${sw}.click()`);await sleep(200);
 check('on again: it ticks to say so, and the menu stays open',await vib(A)==='[8]'&&await A.js(`${sw}.getAttribute('aria-checked')==='true'&&${menu}.open`),await vib(A));

 // iPhone: the switch input.
 const I=await user('hana','iphone');await I.go(`/s/${IDS.play}/`);
 check('iphone: haptics can play, by the switch',await I.js(`pokerHaptics.can()&&!('vibrate' in navigator)`));
 await I.js(`${opener}.click()`);await sleep(800);
 const before=await I.js(`(()=>{const f=${D}.querySelector('[name=amount]');f.focus();f.value='300';return JSON.stringify([...new FormData(f.form)])})()`);
 await reset(I);await I.js(`pokerHaptics.play('tick')`);
 check('iphone: a tick is one click on the hidden switch',await I.js(`__ticks.length`)===1);
 check('iphone: the switch is in the open sheet, in no form, with no box',await I.js(`(()=>{const h=document.querySelector('[data-haptic]');return !!h&&${D}.contains(h)&&!h.closest('form')&&h.getClientRects().length===0&&h.getAttribute('aria-hidden')==='true'})()`));
 check('iphone: focus stays on the amount',await I.js(`document.activeElement===${D}.querySelector('[name=amount]')`));
 check("iphone: the form's values are unchanged",await I.js(`JSON.stringify([...new FormData(${D}.querySelector('[name=amount]').form)])`)===before);
 await sleep(100);await reset(I);await I.js(`pokerHaptics.play('refused')`);await sleep(250);
 const ticks=await I.js(`__ticks`);
 check('iphone: refused is two clicks about 70 ms apart',ticks.length===2&&ticks[1]-ticks[0]>=50,JSON.stringify(ticks));
 check('iphone: the sheet is still open',await I.js(`${D}.open`));
 await I.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500);
 await I.js(`${menu}.querySelector('summary').click()`);await sleep(400);
 await I.js(`${sw}.click()`);await sleep(100);await I.js(`${sw}.click()`);await sleep(200);
 check('iphone: the switch ticks without closing the account menu',await I.js(`${menu}.open&&__ticks.length>=1`),await I.js(`JSON.stringify(__ticks)`));
 check('iphone: no errors',await I.js(`__errors.length===0`),await I.js(`JSON.stringify(__errors)`));

 // A phone with neither: the switch stays hidden and play does nothing.
 const N=await user('hana','none');await N.go(`/s/${IDS.play}/`);
 check('neither: the Vibration switch is hidden',await N.js(`${sw}.hidden&&!pokerHaptics.can()`));
 // A laptop: Chrome has navigator.vibrate, but the pointer is fine. No switch, no vibration.
 const L=await user('hana','android');await send('Emulation.setTouchEmulationEnabled',{enabled:false},L.s);
 await send('Emulation.setDeviceMetricsOverride',{width:1280,height:844,deviceScaleFactor:1,mobile:false},L.s);await L.go(`/s/${IDS.play}/`);
 check('a laptop: no Vibration switch, nothing plays',await L.js(`${sw}.hidden&&!pokerHaptics.can()&&(pokerHaptics.play('done'),__vib.length===0)`));
 check('neither: play does nothing and throws nothing',await N.js(`(pokerHaptics.play('done'),!document.querySelector('[data-haptic]'))`));
 check('android: no errors',await A.js(`__errors.length===0`),await A.js(`JSON.stringify(__errors)`));
} catch(error){console.error(error);check('probe ran to its end',false,String(error))}
finally {
 const failed=results.filter(r=>!r.ok).length;
 console.log(`${results.length-failed}/${results.length} checks passed`);
 writeFileSync(`${OUT}/results.json`,JSON.stringify(results,null,1));
 chrome.kill();process.exit(failed?1:0);
}
