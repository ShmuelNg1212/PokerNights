// The chip rack: drawn chips add one, +20 adds a stack, the stack follows the quantity. Run after seed_chip_numpad.py
// on a fresh temporary database (twelve colours for player ben). It writes nothing, so it can run before chip_numpad.mjs.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-chip-rack-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9349','--user-data-dir=/private/tmp/pn-chip-rack-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9349/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
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

const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${detail===undefined?'':' '+JSON.stringify(detail)}`)};
const ids=JSON.parse(readFileSync('/private/tmp/pn-chip-numpad-manifest.json','utf8'));
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown'&&m.params.exceptionDetails.url)errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text)});
const P=await user('ben');await send('Runtime.enable',{},P.s);
const D=`document.querySelector('dialog[open]')`,R=c=>`${D}.querySelector('[name=qty_${c}]').closest('[data-chip-quantity-row]')`;
const quiet=()=>P.js(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>/Not now/.test(b.textContent)&&b.getClientRects().length);if(b)b.click()})()`);
// A person scrolls a colour into the open part of the sheet, above the keys, before tapping it.
const tapRow=async(expr,pause=60)=>{const p=await P.js(`(()=>{const el=${expr};el.closest('[data-chip-quantity-row]').scrollIntoView({block:'start'});const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},P.s);await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},P.s);await sleep(pause)};
const open=async()=>{await P.go(`/s/${ids.set}/`);await sleep(400);await quiet();await sleep(300);await P.tap(`document.querySelector('#own-count')`);await sleep(500);await P.tap(`document.querySelector('.numpad-panel [data-numpad-chips]:not([hidden])')`);await sleep(900)};
try {
 for(const [w,h] of [[390,844],[320,568]]) {
  await P.phone(w,h);await open();
  check(`${w}: the sheet opens on the first quantity with the keys`,await P.js(`document.activeElement?.name==='qty_white'&&!!${D}.querySelector('[data-numpad-slot] .numpad')`));
  check(`${w}: every colour has a drawn chip and +20`,await P.js(`[...${D}.querySelectorAll('[data-chip-quantity-row]')].every(r=>r.querySelector('[data-chip-tap]').getClientRects().length&&r.querySelector('[data-chip-stack]').getClientRects().length)`));
  check(`${w}: 48 px targets`,await P.js(`[...${D}.querySelectorAll('[data-chip-tap],[data-chip-stack],[data-chip-quantity]')].every(el=>{const r=el.getBoundingClientRect();return r.height>=48&&r.width>=48})`));
  // Three taps on the white chip, then a stack and two loose on red.
  for(let i=0;i<3;i++) await tapRow(`${R('white')}.querySelector('[data-chip-tap]')`,60);
  check(`${w}: a chip tap adds one`,await P.js(`${D}.querySelector('[name=qty_white]').value`)==='3');
  check(`${w}: the field keeps focus and takes the keys`,await P.js(`document.activeElement?.name==='qty_white'`));
  check(`${w}: three discs lie on the rack`,await P.js(`${R('white')}.querySelectorAll('.rack-disc').length`)===3);
  // Holding the chip takes one off; a mis-tap is undone without the keys.
  {const p=await P.js(`(()=>{const r=${R('white')}.querySelector('[data-chip-tap]').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
   await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},P.s);await sleep(700);await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},P.s);await sleep(200);}
  check(`${w}: holding a chip takes one off`,await P.js(`${D}.querySelector('[name=qty_white]').value`)==='2',await P.js(`${D}.querySelector('[name=qty_white]').value`));
  await tapRow(`${R('white')}.querySelector('[data-chip-tap]')`,60);
  await tapRow(`${R('red')}.querySelector('[data-chip-stack]')`,60);await tapRow(`${R('red')}.querySelector('[data-chip-tap]')`,60);await tapRow(`${R('red')}.querySelector('[data-chip-tap]')`,60);
  check(`${w}: +20 adds a stack`,await P.js(`${D}.querySelector('[name=qty_red]').value`)==='22');
  check(`${w}: one stack and two discs`,await P.js(`[${R('red')}.querySelectorAll('.rack-stack').length,${R('red')}.querySelectorAll('.rack-disc').length].join()`)==='1,2');
  await P.tap(`${D}.querySelector('.numpad-key[data-key="del"]')`,60);
  check(`${w}: the keys edit the tapped colour and the rack follows`,await P.js(`${D}.querySelector('[name=qty_red]').value==='2'&&${R('red')}.querySelectorAll('.rack-stack').length===0&&${R('red')}.querySelectorAll('.rack-disc').length===2`),await P.js(`${D}.querySelector('[name=qty_red]').value`));
  const total=await P.js(`${D}.querySelector('[data-chip-total]').textContent`);
  check(`${w}: the total follows taps and keys`,total==='₱7',total);
  check(`${w}: the make-up bar has one part per colour in use`,await P.js(`${D}.querySelectorAll('[data-chip-makeup] i').length`)===2);
  check(`${w}: no sideways scroll`,await P.js(`document.documentElement.scrollWidth<=${w}&&${D}.scrollWidth<=${D}.clientWidth`));
  await P.shot(`rack-${w}`);
  // Seven stacks write ×7.
  for(let i=0;i<7;i++) await tapRow(`${R('blue')}.querySelector('[data-chip-stack]')`,40);
  check(`${w}: past four stacks the rack writes ×N`,await P.js(`${R('blue')}.querySelector('.rack-more')?.textContent`)==='×7');
  await P.shot(`rack-many-${w}`);
  await P.js(`${D}.close()`);await sleep(300);
 }
 // Reduced motion: a tap changes the rack at once.
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},P.s);
 await P.phone(390,844);await open();
 await tapRow(`${R('green')}.querySelector('[data-chip-tap]')`,0);
 check('reduced motion: the disc is there without movement',await P.js(`(()=>{const d=${R('green')}.querySelector('.rack-disc');return !!d&&d.getAnimations().length===0&&getComputedStyle(d).opacity==='1'})()`));
 check('no script errors',errors.length===0,errors);
} catch(e) { check('run completed: '+e.message,false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
