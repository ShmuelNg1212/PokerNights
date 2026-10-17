// The header (2026-10-17): the brand on Your groups, the way back on deeper pages, the account token and its
// panel (account.js). Seed a fresh temporary database with seed.py, seed_end_set.py, seed_night.py and
// seed_opening.py, serve it on 127.0.0.1:8765, then run. Logs out once, at the end of each context.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-header-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-header-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9344','--user-data-dir=/private/tmp/pn-header-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9344/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call, error and view transition is logged.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className&&el.className.baseVal===undefined?el.className:el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}});
 window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__vt=[];
 (()=>{const start=document.startViewTransition&&document.startViewTransition.bind(document);if(!start)return;
 document.startViewTransition=function(cb){const t=start(cb),rec={go:document.documentElement.dataset.go||'',anims:[],ok:null};__vt.push(rec);
  t.ready.then(()=>{rec.anims=document.getAnimations().filter(a=>a.effect&&a.effect.pseudoElement&&a.effect.pseudoElement.startsWith('::view-transition')).map(a=>({p:a.effect.pseudoElement.replace('::view-transition-',''),n:a.animationName||''}))},e=>{rec.ok=false});
  t.finished.then(()=>{if(rec.ok===null)rec.ok=true});return t}})()`;
async function user(name,width=390,{reduce=false,noJs=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:2,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(200)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // A real tap at an element's middle, so the browser's own default actions run.
 const tap=async sel=>{const p=await js(`(()=>{const r=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},s)};
 const tapAt=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 const key=async k=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:k,code:k,windowsVirtualKeyCode:k==='Escape'?27:k==='Tab'?9:13},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 if(noJs){await send('Emulation.setScriptExecutionDisabled',{value:true},s)}
 return {s,js,go,shot,tap,tapAt,key};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,400)}`)};

// The header's facts: one row, its height, its start, the token, the panel.
const facts=`(()=>{const h=document.querySelector('.site-header'),hb=h.getBoundingClientRect(),start=h.querySelector(':scope > .brand, :scope > .table-bar'),end=h.querySelector('.header-end');
 const kids=[...h.querySelectorAll(':scope > .brand, .table-bar > a, .live-status, .alerts:not([hidden]) .alerts-bell, .account-button')].filter(e=>e.getClientRects().length);
 const mid=hb.top+hb.height/2,one=kids.every(e=>{const r=e.getBoundingClientRect();return Math.abs(r.top+r.height/2-mid)<=2});
 const back=h.querySelector('.table-bar > a'),words=h.querySelector('.back-words'),btn=h.querySelector('.account-button'),b=btn.getBoundingClientRect();
 const p=document.querySelector('.account-panel'),pr=p.getBoundingClientRect();
 return {height:Math.round(hb.height),one,start:start.className,back:back?Math.round(back.getBoundingClientRect().height):null,clipped:words?words.scrollWidth>words.clientWidth:null,
  wordsLines:words?Math.round(words.getBoundingClientRect().height/parseFloat(getComputedStyle(words).lineHeight||20)):null,
  token:[Math.round(b.width),Math.round(b.height)],tokenRight:Math.round(innerWidth-b.right),open:document.getElementById('account').open,
  panel:{left:Math.round(pr.left),right:Math.round(pr.right),top:Math.round(pr.top)},overflow:document.documentElement.scrollWidth>innerWidth,main:!!document.querySelector('main .table-bar'),errors:__errors}})()`;
const caretOnToken=`(()=>{const p=document.querySelector('.account-panel'),b=document.querySelector('.account-button').getBoundingClientRect(),c=parseFloat(getComputedStyle(p).getPropertyValue('--caret'));
 return Math.abs((p.getBoundingClientRect().right-c)-(b.left+b.width/2))<=2})()`;
const outButton=`(()=>{const b=document.querySelector('.account-out');return b.getClientRects().length>0&&b.offsetHeight>=48})()`;

const pages={home:'/',group:'/g/1/',night:'/n/1/',set:'/s/3/',counted:'/s/7/cash-out-counted/'};
for(const width of (process.env.PN_BELL?[]:(process.env.PN_WIDTHS||'320,390,1280').split(',').map(Number))){
 const A=await user('hana',width);
 for(const [name,path] of Object.entries(pages)){
  await A.go(path);const f=await A.js(facts);
  check(`${width} ${name}: one row of ${f.height}px, nothing wider than the screen`,f.one&&f.height===69&&!f.overflow,f);
  if(name==='home')check(`${width} home: the brand starts the header, no way back`,f.start==='brand'&&f.back===null&&!f.main,f);
  else check(`${width} ${name}: the way back starts the header (48px), none left in the page`,f.start==='table-bar'&&f.back>=48&&!f.main,f);
  check(`${width} ${name}: the token is a 48px target ending the header at 16px`,f.token[0]===48&&f.token[1]===48&&f.tokenRight===16,f);
  if(name!=='counted')await A.shot(`${name}-${width}`);
 }
 // The set page's live status: words from 360px, the dot alone below.
 await A.go(pages.set);await sleep(2600);
 const live=await A.js(`(()=>{const l=document.querySelector('.site-header .live-status');return {text:l.textContent,size:parseFloat(getComputedStyle(l).fontSize),dot:getComputedStyle(l,'::before').width}})()`);
 check(`${width} set: the live status is in the header${width<360?' as its dot alone':' with its words'}`,/Live/.test(live.text)&&live.dot==='7px'&&(width<360?live.size===0:live.size>0),live);
 // A long name ends in an ellipsis on one line.
 await A.js(`document.querySelector('.back-words').textContent='Session: The very long table name that nobody would ever really type'`);
 const long=await A.js(facts);check(`${width} a long way back stays on one line${width<900?', ending in an ellipsis':''}`,(width>=900||long.clipped)&&long.one&&!long.overflow,long);
 await A.shot(`long-${width}`);
 // The panel: opens from the token, inside the screen, its caret on the token; Escape, the outside and the token close it.
 await A.go(pages.group);await A.tap('.account-button');await sleep(400);
 let f=await A.js(facts);
 check(`${width} the token opens its panel inside the screen, under the header`,f.open&&f.panel.left>=8&&f.panel.right<=width-8&&f.panel.top>=69,f);
 check(`${width} the panel's caret points at the token`,await A.js(caretOnToken));
 check(`${width} the panel names the account and offers Log out at 48px`,await A.js(`document.querySelector('.account-name').textContent==='hana'`)&&await A.js(outButton),await A.js(`(()=>{const b=document.querySelector('.account-out');return [b.getBoundingClientRect().height,getComputedStyle(b).minHeight,document.querySelector('.account-name').textContent]})()`));
 if(width!==1280)await A.shot(`panel-${width}`);
 check(`${width} Motion moved only transform and opacity`,await A.js(`__runs.length>0&&__runs.every(r=>r.keys.every(k=>['transform','opacity'].includes(k)))`),await A.js('__runs'));
 await A.key('Escape');await sleep(350);
 check(`${width} Escape closes it and focus returns to the token`,await A.js(`!document.getElementById('account').open&&document.activeElement===document.querySelector('.account-button')`));
 await A.tap('.account-button');await sleep(350);await A.tapAt(width/2,780);await sleep(350);
 check(`${width} a tap outside closes it`,!(await A.js(facts)).open);
 await A.tap('.account-button');await sleep(350);await A.tap('.account-button');await sleep(350);
 check(`${width} the token closes it again`,!(await A.js(facts)).open);
 // Opened and closed fast: the tap during the close turns it back.
 await A.tap('.account-button');await sleep(300);await A.tap('.account-button');await sleep(60);
 // Sampled every frame from just before the tap: a turn back never drops to nothing and starts over.
 await A.js(`window.__ops=[];(function f(t0){const o=+getComputedStyle(document.querySelector('.account-panel')).opacity;__ops.push(o);if(__ops.length<40)requestAnimationFrame(()=>f())})()`);
 await A.tap('.account-button');await sleep(700);
 const ops=await A.js('__ops');check(`${width} caught while closing, it turns back from where it is`,Math.min(...ops)>0.3&&ops.at(-1)===1,{min:Math.min(...ops),last:ops.at(-1)});
 check(`${width} a tap during the close opens it again`,await A.js(`document.getElementById('account').open&&document.querySelector('.account-panel').style.opacity!=='0'&&getComputedStyle(document.querySelector('.account-panel')).opacity==='1'`),await A.js(`(()=>{const d=document.getElementById('account'),p=d.querySelector('.account-panel');return {open:d.open,cls:d.className,leaving:d.dataset.leaving,inline:p.getAttribute('style'),op:getComputedStyle(p).opacity}})()`));
 // Another screen closes it; a refresh of the same page (the set's morph) leaves it open.
 await A.go(pages.set);await A.tap('.account-button');await sleep(350);
 await A.js(`Turbo.visit(location.href,{action:'replace'})`);await sleep(1200);
 check(`${width} a refresh of the set page leaves the panel open`,(await A.js(facts)).open);
 await A.tap('.table-bar > a');await sleep(900);
 check(`${width} the way back closes it`,!(await A.js(facts)).open&&await A.js(`location.pathname==='/n/1/'||location.pathname.startsWith('/n/')`));
 // The header stays still between screens; the way back's words move 8px with a fade.
 await A.go(pages.group);
 await A.js(`__vt.length=0;document.querySelector('a.session-link').click()`);await sleep(900);
 let r=await A.js('__vt.at(-1)');
 check(`${width} deeper: the words come from the right; the header stays`,r&&r.go==='deeper'&&r.anims.some(a=>a.p==='new(header-back)'&&a.n==='back-in-right')&&r.anims.some(a=>a.p==='old(header-back)'&&a.n==='back-out-left')&&!r.anims.some(a=>/^(old|new)\(site-header\)/.test(a.p)&&a.n),r);
 await A.js(`__vt.length=0;document.querySelector('.table-bar > a').click()`);await sleep(900);
 r=await A.js('__vt.at(-1)');
 check(`${width} back: the words come from the left`,r&&r.go==='back'&&r.anims.some(a=>a.p==='new(header-back)'&&a.n==='back-in-left'),r);
 await A.js(`__vt.length=0;document.querySelector('.table-bar > a').click()`);await sleep(900);
 r=await A.js('__vt.at(-1)');
 check(`${width} back to Your groups: the brand takes the words' place`,r&&r.go==='back'&&r.anims.some(a=>a.p==='new(header-back)')&&await A.js(`location.pathname==='/'&&!!document.querySelector('.site-header > .brand')`),r);
 check(`${width} no name is left behind and no script error`,await A.js(`document.querySelectorAll('[style*="view-transition-name"]').length===0&&!document.documentElement.dataset.go&&__errors.length===0`),await A.js('__errors'));
 // Log out from the panel reaches Log in.
 await A.go(pages.night);await A.tap('.account-button');await sleep(350);await A.tap('.account-out');await sleep(1500);
 check(`${width} Log out from the panel reaches Log in`,await A.js(`location.pathname==='/accounts/login/'&&!document.querySelector('.site-header')`));
}
// Reduced motion: the panel appears at once and nothing moves.
if(!process.env.PN_BELL){const R=await user('hana',390,{reduce:true});await R.go(pages.group);await R.js('__runs.length=0');await R.tap('.account-button');await sleep(100);
 check('reduced motion: the panel is there at once, with no movement',await R.js(`document.getElementById('account').open&&__runs.length===0&&getComputedStyle(document.querySelector('.account-panel')).opacity==='1'`));
 await R.key('Escape');await sleep(100);check('reduced motion: Escape closes it at once',!(await R.js(facts)).open);}
// No JavaScript: the disclosure opens natively and Log out works.
if(!process.env.PN_BELL){const N=await user('hana',390,{noJs:true});await N.go(pages.set);
 check('no JavaScript: the way back and the token are in the header',await N.js(`(()=>{const h=document.querySelector('.site-header');return !!h.querySelector('.table-bar > a')&&!!h.querySelector('.account-button')})()`).catch(()=>null)!==false);
 await N.tap('.account-button');await sleep(300);await N.shot('nojs-panel-390');
 await N.tap('.account-out');await sleep(1500);
 const at=await send('Runtime.evaluate',{expression:'location.pathname',returnByValue:true},N.s);
 check('no JavaScript: the panel opens and Log out reaches Log in',at.result.value==='/accounts/login/',at.result.value);}
// With the alerts fixtures (PN_BELL names a player of seed_arrivals.py, the server has VAPID keys):
// the bell and the token, each panel closing the other, on one row at 320.
if(process.env.PN_BELL){const B=await user(process.env.PN_BELL,320);await B.go(`/s/${process.env.PN_BELL_SET||1}/`);await sleep(600);
 const f=await B.js(facts);check('320 with the bell: the way back, the status, the bell and the token on one row',f.one&&!f.overflow&&await B.js(`!document.getElementById('alerts').hidden`),f);
 await B.shot('bell-320');
 await B.tap('.account-button');await sleep(350);await B.tap('[data-alerts-bell]');await sleep(400);
 check('the bell closes the account panel and opens its own',await B.js(`!document.getElementById('account').open&&!document.querySelector('.alerts-panel').hidden`));
 await B.tap('.account-button');await sleep(400);
 check('the token closes the alerts panel and opens its own',await B.js(`document.getElementById('account').open&&document.querySelector('.alerts-panel').hidden`));
 await B.shot('bell-account-320');}
console.log(`${results.filter(r=>r.ok).length}/${results.length} passed`);
chrome.kill();process.exit(results.every(r=>r.ok)?0:1);
