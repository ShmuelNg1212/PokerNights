// The profile (2026-10-17): Your profile in the account panel, the record across groups, and the settings rows.
// Seed a fresh temporary database with seed.py, seed_end_set.py, seed_night.py, seed_opening.py and
// seed_profile.py, serve it on 127.0.0.1:8765, then run. Logs in as ben, who plays in three groups.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-profile-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-profile-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9345','--user-data-dir=/private/tmp/pn-profile-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9345/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
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
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgba=v=>{c.clearRect(0,0,1,1);c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});let bg=el;while(bg.parentElement&&rgba(getComputedStyle(bg).backgroundColor)[3]===0)bg=bg.parentElement;const a=lum(rgba(getComputedStyle(el).color)),b=lum(rgba(getComputedStyle(bg).backgroundColor));return Math.round((Math.max(a,b)+.05)/(Math.min(a,b)+.05)*100)/100})()`;
const layout=`(()=>{const small=[...document.querySelectorAll('main a, main button, main summary, main input')].filter(e=>e.getClientRects().length&&!e.closest('.chart')).map(e=>[e.className||e.tagName,Math.round(e.getBoundingClientRect().height)]).filter(([,h])=>h<48);
 const name=[...document.querySelectorAll('.profile-group-name')].find(n=>n.textContent.startsWith('The Thursday'));
 return {overflow:document.documentElement.scrollWidth>innerWidth,small,ellipsis:name?getComputedStyle(name).webkitLineClamp==='2'&&name.getBoundingClientRect().height<=2*parseFloat(getComputedStyle(name).lineHeight)+1&&name.getBoundingClientRect().right<=name.closest('.stat-link').getBoundingClientRect().right&&name.title===name.textContent:null,errors:__errors}})()`;

for(const width of [320,390,1280]){
 const A=await user('ben',width);await A.go('/');
 // The way in: the token, then Your profile at 48px, then the page.
 await A.tap('.account-button');await sleep(400);
 check(`${width} the panel offers Your profile at 48px above Log out`,await A.js(`(()=>{const p=document.querySelector('.account-profile'),o=document.querySelector('.account-out');return p.offsetHeight>=48&&p.getBoundingClientRect().bottom<=o.getBoundingClientRect().top})()`));
 if(width===390)await A.shot('panel-390');
 await A.tap('.account-profile');await sleep(1200);
 check(`${width} Your profile opens the profile`,await A.js(`location.pathname==='/me/'&&!!document.querySelector('.profile-page')`));
 await sleep(800);
 const f=await A.js(layout);
 check(`${width} no horizontal overflow`,!f.overflow,f);
 check(`${width} every target is at least 48px`,f.small.length===0,f.small);
 check(`${width} a long group name takes two lines at most and keeps its full name`,f.ellipsis===true,f);
 check(`${width} no script error`,f.errors.length===0,f.errors);
 check(`${width} two pesos groups, then each chips group, never a chips total`,await A.js(`(()=>{const lists=document.querySelectorAll('.profile-groups');return lists.length===2&&lists[0].children.length===2&&lists[1].children.length===2&&!document.querySelector('.player-lead').textContent.includes('chips')})()`),await A.js(`[...document.querySelectorAll('.profile-groups')].map(l=>l.children.length)`));
 for(const sel of ['.profile-jump','.stat-label','.player-rank','.stat-tile dt','.stat-tile-note','.stat-facts','.profile-setting-value','.chart-say'])check(`${width} contrast ${sel}`,await A.js(contrast(sel))>=4.5,await A.js(contrast(sel)));
 await A.shot(`profile-${width}`);
 await A.js(`document.getElementById('pesos-heading').scrollIntoView()`);await sleep(300);await A.shot(`profile-groups-${width}`);
 await A.js(`scrollTo(0,document.body.scrollHeight)`);await sleep(300);await A.shot(`profile-end-${width}`);await A.js(`scrollTo(0,0)`);await sleep(200);
 // Name and password jumps to the settings, under the header.
 await A.tap('.profile-jump');await sleep(900);
 check(`${width} Name and password brings the settings into view under the header`,await A.js(`(()=>{const t=document.getElementById('settings-heading').getBoundingClientRect().top,b=document.querySelector('.profile-settings-list').getBoundingClientRect().bottom;return t>=69&&b<=innerHeight})()`),await A.js(`document.getElementById('settings-heading').getBoundingClientRect().top`));
 check(`${width} linked group rows carry a chevron`,await A.js(`[...document.querySelectorAll('.profile-groups a.stat-link')].every(a=>a.querySelector('.icon-chevron-right'))`));
 await A.js(`scrollTo(0,0)`);await sleep(200);
 // This year keeps the screen where it was and replaces the history entry.
 await A.js(`scrollTo(0,120)`);await sleep(200);const before=await A.js('history.length');
 await A.tap('.pills a:not([aria-current])');await sleep(1200);
 check(`${width} This year keeps the scroll and replaces the entry`,await A.js(`location.search==='?period=year'&&Math.abs(scrollY-120)<4&&history.length===${before}`),await A.js(`[location.search,scrollY,history.length]`));
 // The password row opens; a wrong current password comes back open with its error, no password kept.
 await A.js(`document.getElementById('password').scrollIntoView({block:'center'})`);await sleep(200);
 await A.tap('#password > summary');await sleep(400);
 check(`${width} the password row opens its form`,await A.js(`document.getElementById('password').open&&document.querySelector('[name=current_password]').offsetHeight>=48`));
 await A.js(`document.querySelector('[name=current_password]').value='wrong-guess-91';document.querySelector('[name=new_password1]').value='river-card-4417';document.querySelector('[name=new_password2]').value='river-card-4417';document.querySelector('#password form').requestSubmit()`);await sleep(1500);
 check(`${width} a wrong current password comes back open with its error and no password`,await A.js(`document.getElementById('password').open&&document.querySelector('#password .errors').textContent.includes('not your current password')&&![...document.querySelectorAll('input[type=password]')].some(i=>i.value)`));
 if(width===390){await A.shot('password-error-390');
  await A.tap('#name > summary');await sleep(400);await A.shot('name-390');}
}
// Reduced motion: nothing moves when the page opens.
{const R=await user('ben',390,{reduce:true});await R.go('/me/');await sleep(900);
 check('reduced motion: no animation runs',await R.js(`__runs.length===0&&document.getAnimations().filter(a=>a.playState==='running').length===0`),await R.js(`[__runs,document.getAnimations().map(a=>a.animationName||a.id)]`));}
// No JavaScript: the page and both rows still work.
{const N=await user('ben',390,{noJs:true});await N.go('/me/#name');await sleep(300);
 await N.tap('#name > summary');await sleep(300);
 const r=await send('Runtime.evaluate',{expression:`document.getElementById('name').open&&!!document.querySelector('.player-net')`,returnByValue:true},N.s);
 check('no JavaScript: the record shows and the name row opens',r.result.value===true);}
console.log(`${results.filter(r=>r.ok).length}/${results.length} passed`);
chrome.kill();process.exit(results.every(r=>r.ok)?0:1);
