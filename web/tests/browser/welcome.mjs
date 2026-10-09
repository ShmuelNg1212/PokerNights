// The arrival into the app: the one page after a login (DESIGN.md, "Front door").
// Seed a fresh temporary database with seed_home.py alone. PN_OFF_URL, when set, is a second server
// on the same database started with DOOR_MOTION=False.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-welcome-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-welcome-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'')+' @'+(d.url||'')+':'+d.lineNumber+' after '+results.length+' checks');return}
 if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765', OFF=process.env.PN_OFF_URL || '';
// Runs before every document. On the first frame on which <main> exists it records whether the page is
// the arrival, what is hidden, every figure's text, and how long the movement is set to run.
const PROBE=`(()=>{const t0=performance.now();let seen=false,last=0;window.__frames=[];
 addEventListener('pagereveal',e=>{window.__vt=!!e.viewTransition});
 const figures=()=>[...document.querySelectorAll('main .amount, main .band-facts, main h2')].map(el=>el.textContent.replace(/\\s+/g,' ').trim());
 window.__figures=figures;
 const tick=now=>{const main=document.getElementById('main');
  if(main&&document.readyState!=='loading'&&!seen){seen=true;const cards=[...document.querySelectorAll('.group-home')],token=document.querySelector('.token-stack > *'),badge=document.querySelector('.badge-live'),first=document.querySelector('.home-first > *');
   const anims=document.getAnimations().filter(a=>/^welcome-/.test(a.animationName||''));
   window.__first={welcome:main.hasAttribute('data-welcome'),cards:cards.map(c=>Number(getComputedStyle(c).opacity)),token:token?Number(getComputedStyle(token).opacity):null,badge:badge?Number(getComputedStyle(badge).opacity):null,first:first?Number(getComputedStyle(first).opacity):null,
    main:getComputedStyle(main).transform,figures:figures(),count:anims.length,names:[...new Set(anims.map(a=>a.animationName))].sort(),end:Math.max(0,...anims.map(a=>a.effect.getComputedTiming().endTime)),
    delays:cards.map(c=>parseFloat(getComputedStyle(c).animationDelay)*1000)};}
  if(seen){if(last)window.__frames.push(now-last);last=now}
  if(now-t0<4000)requestAnimationFrame(tick)};requestAnimationFrame(tick)})()`;
async function page(opts={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 if(!opts.plain)await send('Page.addScriptToEvaluateOnNewDocument',{source:PROBE},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const size=(width,height=844)=>send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}};
 const go=async(path,pause=900,base=BASE)=>{await send('Page.navigate',{url:base+path},s);await sleep(pause);await settle()};
 // Logs in through the form and waits until the page behind it has drawn its first frame.
 const login=async(user,next='',base=BASE,pause=1500)=>{await go('/accounts/login/'+(next?'?next='+encodeURIComponent(next):''),700,base);
  await js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);
  for(let i=0;i<200;i++){if(await js(`!document.querySelector('.entry-page')&&!!window.__first`).catch(()=>false))break;await sleep(15)}if(pause){await sleep(pause);await settle()}};
 const shot=async name=>{const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:c.width,height:c.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await size(390);return {s,js,go,login,shot,size};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const moving=`document.getAnimations().filter(a=>/^welcome-/.test(a.animationName||'')&&a.playState==='running').length`;
const rest=`!document.getElementById('main').hasAttribute('data-welcome')&&document.getAnimations().length===0&&[...document.querySelectorAll('.group-home, .token-stack > *, .badge-live, .home-create, .brand img')].every(el=>!el.getAttribute('style')&&getComputedStyle(el).opacity==='1')`;
try {
 // --- Five cards: a set in play, dues, records.
 for(const [width,height] of [[320,568],[390,844],[1280,800]]){const P=await page();await P.size(width,height);await P.login('mara');const f=await P.js('window.__first');
  check(`five cards ${width}: the first frame is the start of the arrival`,f.welcome&&f.cards.length===5&&f.cards.every(o=>o<0.2)&&f.token<0.2&&f.badge<0.2&&f.main==='none',JSON.stringify({cards:f.cards,token:f.token,badge:f.badge,main:f.main}));
  check(`five cards ${width}: every figure is at its value on the first frame`,f.figures.length>=10&&JSON.stringify(f.figures)===JSON.stringify(await P.js('window.__figures()')),`${f.figures.length} figures`);
  check(`five cards ${width}: over within 900ms`,f.end>0&&f.end<=900,`${Math.round(f.end)}ms`);
  check(`five cards ${width}: at rest nothing runs, nothing is left, the mark is off`,await P.js(rest));
  check(`five cards ${width}: no overflow`,await P.js(`document.documentElement.scrollWidth<=${width}`));
  if(width===390){
   check('cards arrive in order, the fourth and fifth together',JSON.stringify(f.delays)===JSON.stringify([100,170,240,310,310]),JSON.stringify(f.delays));
   check('cards, players, the badge, the dues line, New group and the top bar mark each move',['welcome-fade','welcome-land','welcome-mark','welcome-pop','welcome-rise','welcome-token'].every(n=>f.names.includes(n)),f.names.join(' '));
   check('the chip was carried in by the browser',await P.js('window.__vt===true'));
   await P.shot('welcome-home-390');}}
 // --- One card.
 const A=await page();await A.login('pia');let f=await A.js('window.__first');
 check('one card: it arrives and comes to rest',f.welcome&&f.cards.length===1&&f.cards[0]<0.2&&f.end<=900&&await A.js(rest),JSON.stringify(f.cards));
 // --- Once only.
 await A.go('/');f=await A.js('window.__first');check('a reload plays nothing',!f.welcome&&f.count===0&&f.cards[0]===1);
 await A.js(`document.querySelector('.group-home h2 a').click()`);await sleep(900);await A.js('history.back()');await sleep(900);
 check('Back plays nothing',await A.js(`location.pathname==='/'&&${moving}===0&&!document.getElementById('main').hasAttribute('data-welcome')&&getComputedStyle(document.querySelector('.group-home')).opacity==='1'`));
 await A.js(`document.querySelector('.site-header form [type=submit]').click()`);await sleep(1300);await A.login('pia');f=await A.js('window.__first');
 check('logging in again plays it again',f.welcome&&f.cards[0]<0.2);
 // --- Nothing waits.
 const B=await page();await B.login('mara','',BASE,0);const during=await B.js(moving);
 await B.js(`document.querySelector('.token-row').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))`);await sleep(50);
 check('a tap ends the arrival within 50ms',during>0&&await B.js(`${moving}===0&&!document.getElementById('main').hasAttribute('data-welcome')`),`${during} running before the tap`);
 const B2=await page();await B2.login('mara','',BASE,0);const during2=await B2.js(moving);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},B2.s);await sleep(50);
 check('a key ends the arrival within 50ms',during2>0&&await B2.js(`${moving}===0`),`${during2} running before the key`);
 const B3=await page();await B3.login('mara','',BASE,0);const href=await B3.js(`document.querySelector('.home-band.felt a.btn').getAttribute('href')`);
 await B3.js(`(()=>{const a=document.querySelector('.home-band.felt a.btn');a.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));a.click()})()`);await sleep(1200);
 check('a tap on a card during the arrival opens the table',await B3.js(`location.pathname===${JSON.stringify(href)}`),href);
 // --- Other landing pages.
 const C=await page();const group=await (async()=>{await C.login('pia');return C.js(`document.querySelector('.group-home h2 a').getAttribute('href')`)})();
 await C.js(`document.querySelector('.site-header form [type=submit]').click()`);await sleep(1300);await C.login('pia',group);f=await C.js('window.__first');
 check('a group page after a login: only the top bar mark lands, nothing else moves',await C.js(`location.pathname===${JSON.stringify(group)}`)&&f.welcome&&JSON.stringify(f.names)==='["welcome-land"]'&&f.main==='none',JSON.stringify(f.names));
 check('a group page after a login: the mark is taken off',await C.js(`!document.getElementById('main').hasAttribute('data-welcome')&&document.getAnimations().length===0`));
 // --- A newcomer's first screen.
 const D=await page();await D.go('/accounts/signup/',700);
 await D.js(`document.querySelector('[name=username]').value='newcomer'+Date.now()%100000;document.querySelector('[name=password1]').value='tablestakes-91';document.querySelector('[name=password2]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);
 for(let i=0;i<200;i++){if(await D.js(`!document.querySelector('.entry-page')&&!!window.__first`).catch(()=>false))break;await sleep(15)}await sleep(1500);f=await D.js('window.__first');
 check('a newcomer: the first screen rises in turn',await D.js(`!!document.querySelector('.home-first')`)&&f.welcome&&f.first<0.2&&f.end<=900&&f.names.includes('welcome-rise'),JSON.stringify({first:f.first,end:f.end}));
 check('a newcomer: at rest the form is whole and focusable',await D.js(`document.getAnimations().length===0&&[...document.querySelectorAll('.home-first > *')].every(el=>getComputedStyle(el).opacity==='1')`));
 await D.shot('welcome-first-390');
 // --- Late frames with the processor slowed four times, on the arrival and on a plain visit.
 const L=await page();await send('Emulation.setCPUThrottlingRate',{rate:4},L.s);await L.login('mara','',BASE,1800);
 const withIt=(await L.js('window.__frames')).slice(0,60);await L.go('/',1800);const plain=(await L.js('window.__frames')).slice(0,60);
 const late=frames=>({late:frames.filter(d=>d>34).length,worst:Math.round(Math.max(...frames))});
 check('slowed four times: the arrival adds no late frame',late(withIt).late<=late(plain).late+1,`arrival ${JSON.stringify(late(withIt))}, plain visit ${JSON.stringify(late(plain))}`);
 // --- Fail safe.
 const R=await page();await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await R.login('mara');f=await R.js('window.__first');
 check('reduced motion: the page is whole on the first frame and nothing moves',f.welcome&&f.count===0&&f.cards.every(o=>o===1)&&f.token===1&&f.badge===1,JSON.stringify(f.cards));
 const N=await page({plain:true});await N.go('/accounts/login/',700);await send('Emulation.setScriptExecutionDisabled',{value:true},N.s);
 await N.js(`document.querySelector('[name=username]').value='mara';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(2200);
 check('no JavaScript: the arrival plays by itself and the page ends whole',await N.js(`location.pathname==='/'&&document.getElementById('main').hasAttribute('data-welcome')&&document.getAnimations().length===0&&[...document.querySelectorAll('.group-home, .token-stack > *, .badge-live')].every(el=>getComputedStyle(el).opacity==='1')&&getComputedStyle(document.querySelector('.home-dues h3'),'::after').opacity==='0'`));
 const X=await page();await send('Network.enable',{},X.s);await send('Network.setBlockedURLs',{urls:['*vendor/motion-*']},X.s);const before=errors.length;await X.login('mara');f=await X.js('window.__first');
 check('Motion blocked: the arrival plays, ends clean, no script error',f.welcome&&f.cards[0]<0.2&&await X.js(`!window.Motion&&${rest}`)&&errors.length===before,errors.slice(before).join('; '));
 if(OFF){const O=await page();await O.login('mara','',OFF);f=await O.js('window.__first');
  check('switch off: no arrival, the page is whole',await O.js(`location.pathname==='/'`)&&!f.welcome&&f.count===0&&f.cards.every(o=>o===1));
 } else console.log('SKIP switch off: PN_OFF_URL is not set');
 check('no script error anywhere',errors.length===0,errors.join('; '));
 writeFileSync(`${OUT}/welcome.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
