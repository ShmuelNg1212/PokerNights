// Drag a sheet down to close it (sheets.js). Seed a fresh temporary SQLite database with
// seed_sheet_drag.py alone, start Django on 127.0.0.1:8765 with it, then run this file.
// Touches are real touch input through the DevTools protocol, so a drag on a scrolled sheet scrolls it.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-drag-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const IDS=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-drag-manifest.json','utf8'));
const INSTALLED='rack-install';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const PROFILE=process.env.PN_CHROME_PROFILE || '/private/tmp/pn-drag-chrome';rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9343',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9343/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Each Motion call on the sheet is logged, and each vibration, and each error.
const LOG=`window.__vib=[];Object.defineProperty(Navigator.prototype,'vibrate',{configurable:true,value:function(p){__vib.push(p);return true}});
addEventListener('DOMContentLoaded',()=>{window.__runs=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k){if(el&&el.classList&&el.classList.contains('sheet'))__runs.push(Object.keys(k));return a.apply(this,arguments)}}})`;
async function user(name,width=390,{block=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);
 await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 if(block)await send('Network.setBlockedURLs',{urls:['*motion-14.0.0.js*']},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(200)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const touch=(type,p)=>send('Input.dispatchTouchEvent',{type,touchPoints:p?[{x:p.x,y:p.y}]:[]},s);
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 // The host menu open, and the home-screen suggestion already answered, so its sheet never takes focus.
 await js(`localStorage.setItem('rack-dock','open');localStorage.setItem(${JSON.stringify(INSTALLED)},'done')`);
 return {s,js,go,shot,touch};}
const results=[];const check=(name,ok,detail='')=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||!detail?'':' — '+detail}`)};
const D=`document.querySelector('dialog.sheet')`,opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].find(b=>b.getClientRects().length)`;
const ty=`new DOMMatrix(getComputedStyle(${D}).transform).m42`;
// A point on the sheet's head, clear of Close; or the middle of any element.
const head=A=>A.js(`(()=>{const r=${D}.querySelector('.sheet-head').getBoundingClientRect();return {x:r.left+60,y:r.top+r.height/2}})()`);
const at=(A,expr)=>A.js(`(()=>{const r=(${expr}).getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
// Down by dy over ms in steps, then rest before lifting (hold) or lift at once (a flick).
async function drag(A,p,dy,{steps=10,ms=300,hold=150,lift=true,during}={}){
 await A.touch('touchStart',p);
 for(let i=1;i<=steps;i++){await sleep(ms/steps);await A.touch('touchMove',{x:p.x,y:p.y+dy*i/steps})}
 if(hold)await sleep(hold);
 const seen=during?await A.js(during):null;
 if(lift)await A.touch('touchEnd');
 return seen;
}
const openBuy=async A=>{await A.js(`${opener}.click()`);await sleep(800)};
const rest=async A=>A.js(`${D}.open&&${ty}===0&&${D}.style.transform===''`);
try {
 const A=await user('hana');await A.go(`/s/${IDS.play}/`);
 check('a set page with Motion on',await A.js(`!!window.Motion&&pokerMotion.on()&&!!${D}`));
 await openBuy(A);
 const grab=await A.js(`(()=>{const s=getComputedStyle(${D}.querySelector('.sheet-head'),'::before');return {w:s.width,h:s.height,c:s.content}})()`);
 check('grab handle: 36 × 4 px above the title below 900 px',grab.w==='36px'&&grab.h==='4px'&&grab.c!=='none',JSON.stringify(grab));
 await A.shot('drag-handle');
 // A short drag follows the finger and goes back.
 let seen=await drag(A,await head(A),60,{during:`({y:${ty},fade:+getComputedStyle(${D},'::backdrop').opacity})`});
 check('a drag follows the finger 1:1',Math.abs(seen.y-60)<=2,JSON.stringify(seen));
 check('the backdrop fades with the distance',seen.fade<1,JSON.stringify(seen));
 await sleep(700);
 check('a short drag goes back and leaves no inline transform',await rest(A));
 check('the backdrop is full again',await A.js(`+getComputedStyle(${D},'::backdrop').opacity===1`));
 // Up, it resists to 12 px.
 seen=await drag(A,await head(A),-200,{during:ty});await sleep(700);
 check('up, the sheet resists to 12 px',seen<=0&&seen>=-12.5,String(seen));
 // A long drag closes; focus returns to the opener.
 const height=await A.js(`${D}.offsetHeight`);
 await drag(A,await head(A),Math.min(height*0.3,160)+20);await sleep(600);
 check('a drag past the close distance closes the sheet',await A.js(`!${D}.open`));
 check('closed: focus on the opener, no inline style',await A.js(`document.activeElement===${opener}&&${D}.style.transform===''&&!${D}.style.getPropertyValue('--sheet-drag')`));
 check('the drag used the fling preset on transform only',await A.js(`__runs.every(k=>k.every(n=>n==='transform'||n==='opacity'))`));
 // A flick closes after a short distance.
 await openBuy(A);
 // Each protocol call takes about 30 ms, so the flick is three moves sent without a pause.
 const flick=Math.min(height*0.3,160)-30;
 await drag(A,await head(A),flick,{steps:3,ms:0,hold:0});await sleep(600);
 check('a flick short of the close distance closes the sheet',await A.js(`!${D}.open`));
 // The drag tick: once, when the close distance is first passed, even after going back up and down.
 await openBuy(A);await A.js(`__vib.length=0`);
 const p=await head(A),far=Math.min(height*0.3,160);
 await A.touch('touchStart',p);
 for(const y of [20,60,far+10,far+30,20,far+30,far+10,10]){await sleep(40);await A.touch('touchMove',{x:p.x,y:p.y+y})}
 await sleep(150);await A.touch('touchEnd');await sleep(700);
 check('one tick per drag at the close distance',await A.js(`JSON.stringify(__vib)==='[8]'`),await A.js(`JSON.stringify(__vib)`));
 check('ended near the top: the sheet goes back',await rest(A));
 // A drag that starts on a number key types and does not drag.
 await A.js(`${D}.querySelector('[name=amount]').value=''`);
 const key=await at(A,`${D}.querySelector('.numpad-key[data-key="5"]')`);
 seen=await drag(A,key,120,{during:ty});await sleep(500);
 check('a drag from a number key does not move the sheet',seen===0,String(seen));
 check('the number key typed its digit',await A.js(`${D}.querySelector('[name=amount]').value.includes('5')`));
 // A drag from a quick amount drags, and the quick amount is not pressed as well.
 const quick=await A.js(`!!${D}.querySelector('[data-amount]')`);
 if(quick){
  await A.js(`${D}.querySelector('[name=amount]').value='777'`);
  await drag(A,await at(A,`${D}.querySelector('[data-amount]')`),40);await sleep(700);
  check('a drag from a button drags and does not press it',await A.js(`${D}.open&&${D}.querySelector('[name=amount]').value==='777'`));
 }
 // No drag while the sheet's form is sent.
 await A.js(`${D}.querySelector('form').dataset.sent='1'`);
 seen=await drag(A,await head(A),200,{during:ty});await sleep(600);
 check('no drag while a form in the sheet is sent',seen===0&&await A.js(`${D}.open`),String(seen));
 await A.js(`delete ${D}.querySelector('form').dataset.sent`);
 // A touch during the rise takes the sheet from where it is.
 await A.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500);
 // The protocol's 30 ms per call cannot catch a 300 ms rise on its head, and headless Chrome runs its
 // frames without a vsync limit, so even a slow rise is over before a touch arrives. The sheet gets a
 // rise held at its middle instead; the drag takes over any movement in progress the same way.
 await A.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500);await openBuy(A);
 await A.js(`window.__ys=[];window.__sampling=true;(function f(){const d=${D};if(d.open)__ys.push(new DOMMatrix(getComputedStyle(d).transform).m42);if(__sampling)requestAnimationFrame(f)})();window.__c=pokerMotion.run(${D},{transform:['translateY(300px)','translateY(0px)']},{duration:2,ease:'linear'});requestAnimationFrame(()=>{__c.time=1.6;__c.pause()})`);
 await sleep(500);
 const r=await head(A),from=await A.js(ty);
 seen=await drag(A,r,40,{steps:4,ms:0,hold:120,during:ty});
await sleep(900);
 const ys=await A.js(`(__sampling=false,__ys)`);
 const rise={from:Math.round(from),seen:Math.round(seen),jump:Math.round(Math.max(0,...ys.slice(ys.findIndex(y=>y>0)+1).map((y,i,a)=>i?y-a[i-1]:0)))}; // from the held rise's own start
 // From where it was plus the finger; the finger moves 10 px a step, so a frame lower by much more is a
 // jump to somewhere else. It stays short of the close distance and goes back.
 check('a touch during a rise takes the sheet from where it is',from>30&&Math.abs(seen-(from+40))<=3&&rise.jump<=30,JSON.stringify(rise));
 check('then at rest with no inline transform',await rest(A));
 check('no errors on the set page',await A.js(`__errors.length===0`),await A.js(`JSON.stringify(__errors)`));
 await A.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500);
 // Escape and the backdrop still close.
 await openBuy(A);await A.js(`${D}.dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(500);
 check('Escape (cancel) still closes',await A.js(`!${D}.open`));
 // The recap: scrolled content scrolls; the head drags at any scroll.
 await A.go(`/n/${IDS.twelve}/`);await sleep(7000); // the finale, then the automatic recap
 if(await A.js(`${D}&&${D}.open`)){await A.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500)}
 await A.js(`document.querySelector('[data-sheet-open="recap"]').click()`);await sleep(900);
 check('the recap sheet scrolls',await A.js(`${D}.scrollHeight>${D}.clientHeight+100`));
 await A.js(`${D}.scrollTop=300`);await sleep(100);
 const body=await A.js(`(()=>{const r=${D}.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height*0.6}})()`);
 seen=await drag(A,body,150,{during:`({y:${ty},top:${D}.scrollTop})`});await sleep(500);
 check('a drag on scrolled content scrolls and does not drag',seen.y===0&&seen.top<300,JSON.stringify(seen));
 const grabRecap=await A.js(`getComputedStyle(${D}.querySelector('.sheet-head')).position`);
 check('the recap head stays sticky',grabRecap==='sticky',grabRecap);
 await A.js(`${D}.scrollTop=300`);await sleep(100);
 seen=await drag(A,await head(A),200,{during:ty});await sleep(600);
 check('the recap head drags at any scroll and closes',seen>150&&await A.js(`!${D}.open`),String(seen));
 await A.shot('drag-recap-closed');
 // A page change during a drag leaves nothing behind.
 await A.go(`/s/${IDS.play}/`);await openBuy(A);
 const p3=await head(A);await A.touch('touchStart',p3);await sleep(30);await A.touch('touchMove',{x:p3.x,y:p3.y+40});await sleep(30);
 await A.js(`Turbo.visit('/')`);await sleep(1200);await A.touch('touchEnd');await sleep(300);
 check('a page change during a drag: no error, no sheet left',await A.js(`__errors.length===0&&!document.querySelector('dialog.sheet[open]')`));

 // 1280 px: the sheet is centred and never drags.
 const W=await user('hana',1280);await W.go(`/s/${IDS.play}/`);await openBuy(W);
 seen=await drag(W,await head(W),200,{during:ty});await sleep(500);
 check('1280 px: no drag',seen===0&&await W.js(`${D}.open`),String(seen));
 check('1280 px: no grab handle',await W.js(`getComputedStyle(${D}.querySelector('.sheet-head'),'::before').content==='none'`));
 // A mouse never drags.
 const M=await user('hana');await M.go(`/s/${IDS.play}/`);await openBuy(M);
 const mp=await head(M);
 await send('Input.dispatchMouseEvent',{type:'mousePressed',x:mp.x,y:mp.y,button:'left',clickCount:1},M.s);
 for(let i=1;i<=8;i++){await sleep(30);await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:mp.x,y:mp.y+i*25,button:'left',buttons:1},M.s)}
 seen=await M.js(ty);await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:mp.x,y:mp.y+200,button:'left',clickCount:1},M.s);await sleep(400);
 check('a mouse does not drag',seen===0&&await M.js(`${D}.open`),String(seen));

 // Reduced motion: the sheet follows the finger; a release is at once closed or back.
 const R=await user('hana');await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);
 await R.go(`/s/${IDS.play}/`);await openBuy(R);
 seen=await drag(R,await head(R),60,{during:ty});await sleep(60);
 check('reduced motion: the sheet follows the finger',Math.abs(seen-60)<=2,String(seen));
 check('reduced motion: back at once',await rest(R));
 await drag(R,await head(R),200);await sleep(60);
 check('reduced motion: closed at once',await R.js(`!${D}.open&&${D}.style.transform===''`));
 // Without the Motion file: the same as reduced motion.
 const B=await user('hana',390,{block:true});await B.go(`/s/${IDS.play}/`);
 check('blocked Motion file: Motion is off',await B.js(`!window.Motion&&!pokerMotion.on()`));
 await openBuy(B);
 seen=await drag(B,await head(B),60,{during:ty});await sleep(60);
 check('blocked Motion file: follows, then back at once',Math.abs(seen-60)<=2&&await rest(B),String(seen));
 await drag(B,await head(B),200);await sleep(60);
 check('blocked Motion file: closed at once',await B.js(`!${D}.open`));
} catch(error){console.error(error);check('probe ran to its end',false,String(error))}
finally {
 const failed=results.filter(r=>!r.ok).length;
 console.log(`${results.length-failed}/${results.length} checks passed`);
 writeFileSync(`${OUT}/results.json`,JSON.stringify(results,null,1));
 chrome.kill();process.exit(failed?1:0);
}
