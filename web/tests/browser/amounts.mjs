// Amounts typed on the app's keys are grouped as they are typed ("1,650.50") and are recorded as the same amount.
// Run after seed.py on a fresh temporary database (set 3 is a running pesos set, set 5 a running chips set).
// PN_DB names the SQLite file: the probe reads what was recorded.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-amounts-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9361','--user-data-dir=/private/tmp/pn-amounts-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9361/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 // A phone: a finger is the main pointer. A computer: a mouse.
 const phone=async(width=390,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:true},s);await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s)};
 const computer=async()=>{await send('Emulation.setTouchEmulationEnabled',{enabled:false},s);await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},s)};
 const point=async expr=>js(`(()=>{const el=${expr};el.scrollIntoView({block:'center'});const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 const down=async expr=>{const p=await point(expr);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},s);return p};
 const up=async()=>{await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},s)};
 const tap=async(expr,pause=40)=>{await down(expr);await up();await sleep(pause)};
 const shot=async name=>{await js('document.fonts.ready.then(()=>1)');const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await phone();
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,phone,computer,tap,down,up,shot};
}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail)}`)};
const DB=process.env.PN_DB;
const last=set=>spawnSync('sqlite3',[DB,`select amount from ledger_buyin where session_id=${set} order by id desc limit 1`],{encoding:'utf8'}).stdout.trim();
const D=`document.querySelector('dialog.sheet')`,F=`${D}.querySelector('[name=amount]')`,PAD=`document.querySelector('.numpad')`;
const key=k=>`${PAD}.querySelector('[data-key="${k}"]')`;
try {
 const A=await user('hana');
 const buy=async(set,keys,shown)=>{
  await A.go(`/s/${set}/`);await A.tap(`document.querySelector('.buy-opener')`,700);
  const before=last(set);
  await A.js(`${F}.select()`);for(const k of keys)await A.tap(key(k));
  const seen=await A.js(`${F}.value`);
  check(`set ${set}: the field reads "${shown}" as it is typed`,seen===shown,seen);
  await A.tap(`${D}.querySelector('[type=submit]')`,1500);
  return {before,after:last(set)};
 };
 let r=await buy(3,['1','0','0','0'],'1,000');
 check('pesos: "1,000" is recorded as 100000 centavos',r.after==='100000'&&r.before!==undefined,r);
 r=await buy(3,['1','6','5','0','alt','5','0'],'1,650.50');
 check('pesos: "1,650.50" is recorded as 165050 centavos',r.after==='165050',r);
 r=await buy(5,['1','5','0','0'],'1,500');
 check('chips: "1,500" is recorded as 1500 chips',r.after==='1500',r);
 // The server's value is grouped as the field's default too, so the page does not treat it as typed.
 await A.go('/s/3/');await A.tap(`document.querySelector('.buy-opener')`,700);
 let f=await A.js(`({v:${F}.value,d:${F}.defaultValue})`);
 check('buy-in sheet: the usual amount reads "1,000" and still counts as untouched',f.v==='1,000'&&f.d==='1,000',f);
 await A.js(`${D}.querySelector('.quick-amounts [data-amount]:last-child').click()`);await sleep(50);
 f=await A.js(`({v:${F}.value,focused:document.activeElement===${F}})`);
 check('a quick amount is grouped at once',/^\d{1,3}(,\d{3})+$/.test(f.v),f);
 // A keyboard: Backspace just after a comma removes the digit before it.
 await A.computer();await A.js(`${F}.value='12,345';${F}.focus();${F}.setSelectionRange(3,3)`);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8},A.s);await sleep(50);
 f=await A.js(`({v:${F}.value,at:${F}.selectionStart})`);
 check('keyboard: Backspace after the comma in "12,345" leaves "1,345" with the caret after the 1',f.v==='1,345'&&f.at===1,f);
 await A.phone();

 // New session: the unit marks follow the unit choice, and the date reads as the app writes dates.
 await A.go('/g/1/sessions/new/');await A.js(`document.querySelectorAll('details').forEach(d=>d.open=true)`);
 const marks=`(()=>{const f=document.querySelector('[name=small_blind]').closest('.unit-field'),v=e=>getComputedStyle(f.querySelector(e)).display!=='none';return {pre:v('.unit-pre'),post:v('.unit-post'),value:document.querySelector('[name=max_buy_in]').value}})()`;
 let m=await A.js(marks);check('new session in pesos: "₱" before the amount, no "chips", and the amounts are grouped',m.pre&&!m.post&&m.value.includes(','),m);
 await A.js(`(()=>{const u=document.querySelector('select[name=unit]');u.value='chips';u.dispatchEvent(new Event('change',{bubbles:true}))})()`);await sleep(100);
 m=await A.js(marks);check('new session in chips: "chips" after the amount, no "₱"',!m.pre&&m.post,m);
 const words=await A.js(`(()=>{const f=document.querySelector('[name=game_date]');f.value='2026-11-19';f.dispatchEvent(new Event('change',{bubbles:true}));return document.querySelector('[data-date-words]').textContent})()`);
 check('new session: the date line reads "Thu, Nov 19"',words==='Thu, Nov 19',words);
} catch(error){check('run completed: '+error.message.slice(0,300),false)}
finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length}/${results.length} checks passed`);
if(results.some(x=>!x.ok))process.exitCode=1;
