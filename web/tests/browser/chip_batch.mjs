// The chip sheet as a calculator: it fills the count field, and Confirm all counts saves chip and typed counts together.
// Run after seed_chip_values.py on a fresh temporary database. It consumes set 1 and the second set.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-batch-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-chip-batch-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir=/private/tmp/pn-chip-batch-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
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
const ids=JSON.parse(readFileSync('/private/tmp/pn-chip-manifest.json','utf8'));
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text)});
const H=await user('hana'),P=await user('ben');await send('Runtime.enable',{},H.s);await send('Runtime.enable',{},P.s);
const D=`document.querySelector('dialog[open]')`,key=(scope,k)=>`${scope}.querySelector('.numpad-key[data-key="${k}"]')`;
const quiet=u=>u.js(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>/Not now/.test(b.textContent)&&b.getClientRects().length);if(b)b.click()})()`);
const chips=async(u,field)=>{await u.tap(`document.querySelector('${field}')`);await sleep(500);await u.tap(`document.querySelector('.numpad-panel [data-numpad-chips]:not([hidden])')`);await sleep(900)};
try {
 // Host, set 1: A by chips, ben typed, one confirm.
 await H.go(`/s/${ids.set}/`);await sleep(500);await quiet(H);await sleep(300);
 await chips(H,`#count-${ids.a}`);
 check('host: the sheet offers Use count before any quantity',await H.js(`${D}.querySelector('.chip-count-send .btn-primary').textContent.trim()`)==='Use count');
 await H.tap(`${D}.querySelector('[data-chip-quantity]')`);
 for(const k of ['4']) await H.tap(key(D,k),80);
 await H.tap(`${D}.querySelectorAll('[data-chip-quantity]')[2]`);await H.tap(key(D,'3'),80);
 const label=await H.js(`${D}.querySelector('.chip-count-send .btn-primary').textContent.trim()`);
 check('host: the button names the total',label==='Use ₱320',label);
 await H.shot('host-sheet');
 await H.tap(`${D}.querySelector('.chip-count-send .btn-primary')`);await sleep(900);
 check('host: Use closes the sheet without a write',await H.js(`!document.querySelector('dialog[open]')&&!document.querySelector('.message-success')`));
 check('host: the field shows the total',await H.js(`document.querySelector('#count-${ids.a}').value`)==='320');
 check('host: focus is back in the field',await H.js(`document.activeElement?.id`)===`count-${ids.a}`);
 check('host: the row says by chips',await H.js(`!document.querySelector('#count-row-${ids.a} [data-chip-note]').hidden`));
 const carry=JSON.parse(await H.js(`document.querySelector('[name=chips_${ids.a}]').value`));
 check('host: the chip field holds the quantities',JSON.stringify(carry.quantities)===JSON.stringify([['white','4'],['green','3']])&&carry.empty_stack===false,carry);
 check('host: the dock preview counts the filled total',await H.js(`document.querySelector('[data-count-preview]')?.textContent.includes('₱320')`));
 // Reopen: the quantities are still there.
 await H.tap(`document.querySelector('.numpad-panel [data-numpad-chips]:not([hidden])')`);await sleep(900);
 check('host: reopening shows the quantities',await H.js(`${D}.querySelector('[data-chip-quantity]').value`)==='4');
 await H.tap(`${D}.querySelector('.sheet-head button')`);await sleep(700);
 // ben typed with the keys: Next goes to his field.
 await H.tap(`document.querySelector('#count-${ids.player}')`);await sleep(400);
 for(const k of ['1','6','8','0']) await H.tap(key(`document.querySelector('.numpad-panel')`,k),60);
 await H.shot('host-filled');
 await H.tap(`document.querySelector('.numpad-panel [data-numpad-done]')`);await sleep(500);
 // On a phone the host dock carries the confirm once counts are typed.
 await H.tap(`document.querySelector('[data-confirm-typed]:not([hidden])')`);await sleep(1800);
 const page=await H.js(`document.body.innerText`);
 check('host: one confirm saves both counts',page.includes('2 counts confirmed'),page.match(/\d+ counts? confirmed|Nothing was saved[^\n]*/)?.[0]);
 check('host: A is counted with a chip breakdown',await H.js(`(()=>{const r=document.querySelector('#count-row-${ids.a}');return r.textContent.includes('₱320')&&!!r.querySelector('.chip-breakdown')})()`));
 check('host: no chip note after the save',await H.js(`[...document.querySelectorAll('[data-chip-note]')].every(n=>n.hidden)`));
 // Host, second set: typing over a filled total drops the chips.
 await H.go(`/s/${ids.second}/`);await sleep(500);
 const second=await H.js(`document.querySelector('[data-chip-carry]').dataset.chipCarry`);const pid=second.split('-').pop();
 await chips(H,`#count-${pid}`);
 await H.tap(`${D}.querySelector('[data-chip-quantity]')`);await H.tap(key(D,'2'),80);
 await H.tap(`${D}.querySelector('.chip-count-send .btn-primary')`);await sleep(900);
 await H.tap(key(`document.querySelector('.numpad-panel')`,'5'),80);await sleep(200);
 check('host: typing over the total drops the chips',await H.js(`document.querySelector('[name=chips_${pid}]').value===''&&document.querySelector('#count-row-${pid} [data-chip-note]').hidden&&document.querySelector('#count-${pid}').value==='105'`),await H.js(`document.querySelector('#count-${pid}').value`));
 // Player, second set: the card is filled by the sheet and sends.
 await P.go(`/s/${ids.second}/`);await sleep(500);await quiet(P);await sleep(300);
 await chips(P,'#own-count');
 await P.tap(`${D}.querySelectorAll('[data-chip-quantity]')[1]`);await P.tap(key(D,'4'),80);
 check('player: the button names the total',await P.js(`${D}.querySelector('.chip-count-send .btn-primary').textContent.trim()`)==='Use ₱100');
 await P.tap(`${D}.querySelector('.chip-count-send .btn-primary')`);await sleep(900);
 check('player: the card shows the total and by chips',await P.js(`document.querySelector('#own-count').value==='100'&&!document.querySelector('.own-count [data-chip-note]').hidden`));
 await P.shot('player-filled');
 await P.tap(`document.querySelector('.numpad-panel [data-numpad-done]')`);await sleep(500);
 await P.tap(`document.querySelector('.own-count [type=submit]')`);await sleep(1800);
 check('player: Send sends the chip count',await P.js(`document.querySelector('.own-count').textContent.includes('You entered')&&document.querySelector('.own-count').textContent.includes('₱100')&&!!document.querySelector('.own-count .chip-breakdown')`),await P.js(`document.querySelector('.own-count').innerText.replace(/\\s+/g,' ').slice(0,200)`));
 check('no script errors',errors.length===0,errors);
} catch(e) { check('run completed: '+e.message,false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
