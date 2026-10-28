// The app's number keys on chip values and chip counts. Run after seed_chip_numpad.py on a fresh temporary database.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-numpad-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-chip-numpad-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9346','--user-data-dir=/private/tmp/pn-chip-numpad-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9346/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
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
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text)});
const H=await user('hana'),P=await user('ben');await send('Runtime.enable',{},H.s);await send('Runtime.enable',{},P.s);
const key=(scope,k)=>`document.querySelector('${scope} .numpad-key[data-key="${k}"]')`;
try {
 // Setup: the value field takes the keys in the bottom panel.
 await H.go(`/n/${ids.setup}/chip-values/`);
 check('phone: a finger is the main pointer',await H.js(`matchMedia('(pointer: coarse)').matches`));
 const V=`document.querySelector('[name=chips-0-value]')`;
 await H.tap(V);await sleep(400);
 check('setup: the phone keyboard is off for the value field',await H.js(`${V}.getAttribute('inputmode')==='none'&&document.activeElement===${V}`));
 check('setup: the panel names the field',await H.js(`document.querySelector('.numpad-panel [data-numpad-label]')?.textContent==='Value (₱)'`));
 check('setup: pesos keys offer a decimal point',await H.js(`${key('.numpad-panel','alt')}.textContent==='.'`));
 for(const k of ['2','5','alt','5']) await H.tap(key('.numpad-panel',k),80);
 check('setup: keys write 25.5',await H.js(`${V}.value`)==='25.5',await H.js(`${V}.value`));
 await H.tap(`document.querySelector('[name=chips-0-label]')`);await sleep(400);
 check('setup: a text field puts the keys away',await H.js(`!document.querySelector('.numpad-panel')?.isConnected`));
 await H.shot('setup-390');
 // Count: twelve colours in a sheet. The keys and the total stay in view.
 for(const [w,h] of [[390,844],[320,568]]) {
  await P.phone(w,h);await P.go(`/s/${ids.set}/`);
  // Where the keys serve the phone, their Chips key is the way into the sheet; the card's own link stays hidden.
  check(`count ${w}: the card's chip link is hidden`,await P.js(`!document.querySelector('.own-count .chip-count-option').getClientRects().length`));
  await P.tap(`document.querySelector('#own-count')`);await sleep(500);
  await P.tap(`document.querySelector('.numpad-panel [data-numpad-chips]:not([hidden])')`);await sleep(800);
  const D=`document.querySelector('dialog[open]')`,Q=n=>`${D}.querySelector('[name=qty_${n}]')`;
  check(`count ${w}: the sheet holds the keys`,await P.js(`!!${D}?.querySelector('form [data-numpad-slot] .numpad')`));
  check(`count ${w}: the phone keyboard is off for quantities`,await P.js(`${Q('white')}.getAttribute('inputmode')==='none'`));
  check(`count ${w}: whole counts offer 00, not a point`,await P.js(`${key('dialog[open]','alt')}.textContent==='00'`));
  check(`count ${w}: keys and total are on screen`,await P.js(`(()=>{const k=${D}.querySelector('.numpad').getBoundingClientRect(),t=${D}.querySelector('[data-chip-total]').getBoundingClientRect();return k.bottom<=innerHeight+1&&t.top>=0&&t.bottom<=k.top})()`));
  await P.tap(Q('white'));await P.tap(key('dialog[open]','4'),80);
  await P.tap(Q('teal'));await P.tap(key('dialog[open]','2'),80);
  check(`count ${w}: the tapped row is not under the keys`,await P.js(`${Q('teal')}.getBoundingClientRect().bottom<=${D}.querySelector('.chip-count-dock').getBoundingClientRect().top+1`));
  check(`count ${w}: keys write quantities and the total follows`,await P.js(`${Q('white')}.value==='4'&&${Q('teal')}.value==='2'&&${D}.querySelector('[data-chip-total]').textContent==='₱28'`),await P.js(`${D}.querySelector('[data-chip-total]').textContent`));
  check(`count ${w}: no sideways scroll`,await P.js(`document.documentElement.scrollWidth<=${w}&&${D}.scrollWidth<=${D}.clientWidth`));
  await P.shot(`count-sheet-${w}`);
  if(w===320){
   await P.js(`${D}.querySelector('.chip-count-send [type=submit]:not([name])').scrollIntoView({block:'center'})`);await sleep(200);
   await P.tap(`document.querySelector('dialog[open] .chip-count-send [type=submit]:not([name])')`);await sleep(1500);
   check('count: the keyed count reaches the server',await P.js(`!document.querySelector('dialog[open]')&&document.querySelector('.own-count').textContent.includes('₱28')`),await P.js(`document.querySelector('.own-count')?.textContent.replace(/\\s+/g,' ').slice(0,200)`));
  } else { await P.js(`${D}.close()`);await sleep(400); }
 }
 check('no script errors',errors.length===0,errors);
} catch(e) { check('run completed: '+e.message,false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
