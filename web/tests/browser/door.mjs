// The front door: the frame on every entry screen and each movement of the chip (DESIGN.md, "Front door").
// Seed a fresh temporary database with seed.py and seed_entry.py. PN_OFF_URL, when set, is a second server
// started with DOOR_MOTION=False and SIGNUP_REQUIRES_INVITE=True.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-door-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-door-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){errors.push(m.params.exceptionDetails.text);return}
 if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const M=JSON.parse(readFileSync('/private/tmp/pn-entry-manifest.json','utf8'));
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765', OFF=process.env.PN_OFF_URL || '';
// Runs before every document: records the first frame on which the sheet exists, the frames after it,
// and whether the browser carried the chip between two documents.
const PROBE=`(()=>{const t0=performance.now();let seen=false,last=0;window.__frames=[];
 addEventListener('pagereveal',e=>{window.__vt=!!e.viewTransition;if(e.viewTransition)e.viewTransition.ready.then(()=>{window.__carry=document.getAnimations().some(a=>a.effect&&a.effect.pseudoElement==='::view-transition-group(brand-mark)')},()=>{})});
 const tick=now=>{const sheet=document.querySelector('.door-sheet');
  if(sheet&&!seen){seen=true;const main=document.getElementById('main'),mark=document.querySelector('.door-mark'),field=document.querySelector('.door-sheet input:not([type=hidden])');
   const anims=main.getAnimations({subtree:true}).filter(a=>a.animationName);
   window.__first={arrival:main.dataset.arrival||'',mark:mark?Number(getComputedStyle(mark).opacity):null,sheetY:new DOMMatrix(getComputedStyle(sheet).transform).m42,field:field?Number(getComputedStyle(field.closest('.field')||field).opacity):null,
    focus:document.activeElement&&document.activeElement.name||'',count:anims.length,end:Math.max(0,...anims.map(a=>a.effect.getComputedTiming().endTime))};}
  if(seen){if(last)window.__frames.push(now-last);last=now}
  if(now-t0<4000)requestAnimationFrame(tick)};requestAnimationFrame(tick)})()`;
async function page(opts={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 if(!opts.plain)await send('Page.addScriptToEvaluateOnNewDocument',{source:PROBE},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const size=(width,height=844)=>send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const go=async(path,pause=1300,base=BASE)=>{await send('Page.navigate',{url:base+path},s);await sleep(pause);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const click=async(expr,pause=650)=>{await js(expr+'.click()');await sleep(pause)};
 const shot=async name=>{const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:c.width,height:c.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const type=async text=>{for(const ch of text){await send('Input.dispatchKeyEvent',{type:'keyDown',text:ch,key:ch},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:ch},s)}};
 const back=async()=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8},s)};
 await size(390);return {s,js,go,click,shot,size,type,back};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
// WCAG contrast of an element's text against the surface it sits on, via canvas so oklch resolves.
const contrast=(sel,on)=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.querySelector(${JSON.stringify(on)})).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
// The angle a part of the chip is turned to, in degrees, and where its middle is on the screen.
const angle=sel=>`(()=>{const m=new DOMMatrix(getComputedStyle(document.querySelector(${JSON.stringify(sel)})).transform);return Math.round(Math.atan2(m.b,m.a)*180/Math.PI)})()`;
const middle=sel=>`(()=>{const r=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()`;
const same=(a,b)=>Math.abs(a[0]-b[0])<0.1&&Math.abs(a[1]-b[1])<0.1;
const running=`document.getElementById('main').getAnimations({subtree:true}).filter(a=>a.playState==='running').length`;
const clean=`['.door-mark','.door-ring','.door-under','.door-moon'].every(s=>{const el=document.querySelector(s);return !el.style.willChange&&!el.style.opacity})`;
const login=async(P,user='hana',pass='tablestakes-91')=>{await P.js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value=${JSON.stringify(pass)}`);await P.click(`document.querySelector('form.form-section [type=submit]')`,1500)};
try {
 // --- The frame, on every screen at three sizes.
 const A=await page();
 const screens=[['login','/accounts/login/'],['login-invited','/accounts/login/?next='+encodeURIComponent(M.invite)],['signup','/accounts/signup/'],['signup-invited','/accounts/signup/?next='+encodeURIComponent(M.invite)],['signup-long','/accounts/signup/?next='+encodeURIComponent(M.long)],['invite-dead',M.expired],['reset-dead','/accounts/reset/not-a-link/'],['claim-dead','/claim/not-a-link/']];
 for(const [width,height] of [[320,568],[390,844],[1280,800]])for(const [name,path] of screens){await A.size(width,height);await A.go(path,500);
  check(`${name} fits ${width}`,await A.js(`document.documentElement.scrollWidth<=${width}`));
  check(`${name} 48px targets ${width}`,await A.js(targets));
  check(`${name} frame ${width}`,await A.js(`!!document.querySelector('.door-hero .door-mark')&&!!document.querySelector('.door-sheet h1')&&!document.querySelector('.site-header')`));
  await A.shot(`door-${name}-${width}`);}
 await A.size(390);await A.go('/accounts/login/',500);
 check('phone: the sheet runs edge to edge and to the bottom of the screen',await A.js(`(()=>{const r=document.querySelector('.door-sheet').getBoundingClientRect();return r.left===0&&r.width===390&&Math.round(r.bottom)===844&&document.documentElement.scrollHeight===844})()`));
 for(const [name,path] of [['sign up','/accounts/signup/'],['invited sign up','/accounts/signup/?next='+encodeURIComponent(M.invite)]]){await A.go(path,500);const bottom=await A.js(`Math.round(document.querySelector('form [type=submit]').getBoundingClientRect().bottom)`);check(`${name}: the whole button shows without a scroll at 390x844`,bottom<=844,`button ends at ${bottom}, page is ${await A.js('document.documentElement.scrollHeight')}`);}
 check('invited sign up leads with the group',await A.js(`document.querySelector('h1').textContent==='Join '+${JSON.stringify(M.group)}&&${text('Create your account to get in.')}&&document.querySelector('.entry-invite a').getBoundingClientRect().bottom<document.querySelector('[name=username]').getBoundingClientRect().top&&!document.querySelector('.entry-alt')`));
 check('sign up keeps the description, at the foot',await A.js(`document.querySelector('.door-foot').textContent.includes('It never moves money.')&&document.querySelector('.door-foot').getBoundingClientRect().top>document.querySelector('form [type=submit]').getBoundingClientRect().bottom`));
 for(const sel of ['h1','.hint','.door-foot','.entry-invite','.password-toggle'])check('contrast on the sheet '+sel,await A.js(contrast(sel,'.door-sheet'))>=4.5);
 await A.go('/accounts/login/',500);for(const sel of ['.entry-alt','.entry-alt a','label'])check('contrast on the sheet '+sel,await A.js(contrast(sel,'.door-sheet'))>=4.5);
 for(const sel of ['.entry-name','.entry-line'])check('contrast on the ground '+sel,await A.js(contrast(sel,'body'))>=4.5);
 await A.size(1280,800);await A.go('/accounts/login/',500);
 check('desktop: the sheet is a centred 440px card',await A.js(`(()=>{const r=document.querySelector('.door-sheet').getBoundingClientRect();return r.width===440&&Math.abs(r.left+r.width/2-640)<1&&getComputedStyle(document.querySelector('.door-sheet')).borderBottomLeftRadius==='26px'})()`));
 await A.js(`document.querySelector('[name=username]').focus()`);
 check('the focus ring shows on the sheet',await A.js(`getComputedStyle(document.activeElement).outlineWidth==='3px'`));
 await A.size(390);

 // --- Arrival.
 const B=await page();await B.go('/accounts/login/');let f=await B.js('window.__first');
 check('first visit: the full arrival starts on the first frame',f.arrival==='full'&&f.mark<0.2&&f.sheetY>12&&f.field<0.2&&f.count>=8,JSON.stringify(f));
 check('first visit: the username field has focus on the first frame',f.focus==='username');
 check('the full arrival is over within 1,100ms',f.end<=1100,`${Math.round(f.end)}ms`);
 check('at rest nothing runs and the page is whole',await B.js(`${running}===0&&getComputedStyle(document.querySelector('.door-mark')).opacity==='1'&&getComputedStyle(document.querySelector('.entry-name')).fontStretch==='88%'`));
 await B.go('/accounts/login/');f=await B.js('window.__first');
 check('second visit: the short arrival, within 300ms',f.arrival==='short'&&f.count===2&&f.end<=300&&f.sheetY>0,JSON.stringify(f));
 await B.go('/accounts/signup/');f=await B.js('window.__first');check('sign up in the same session is short too',f.arrival==='short');
 const C=await page();await send('Page.navigate',{url:BASE+'/accounts/login/'},C.s);for(let i=0;i<60;i++){if(await C.js(`!!window.__first&&!!window.pokerMotion`))break;await sleep(15)}
 const during=await C.js(running);await C.type('h');await sleep(50);
 check('a key ends the arrival within 50ms and is typed',during>0&&await C.js(`${running}===0&&document.querySelector('[name=username]').value==='h'&&!document.getElementById('main').dataset.arrival`),`${during} running before the key`);
 const C2=await page();await send('Page.navigate',{url:BASE+'/accounts/login/'},C2.s);for(let i=0;i<60;i++){if(await C2.js(`!!window.__first&&!!window.pokerMotion`))break;await sleep(15)}
 await C2.js(`document.querySelector('.door-sheet h1').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))`);await sleep(50);
 check('a tap ends the arrival',await C2.js(`${running}===0`));

 // --- The chip answers.
 await sleep(400);const at=await C.js(middle('.door-ring')),under=await C.js(middle('.door-under'));
 check('one key turned the ring a notch',await C.js(angle('.door-ring'))===20&&await C.js(angle('.door-under'))===20);
 await C.type('ana');await sleep(450);
 check('each key turns the ring and its underside together',await C.js(angle('.door-ring'))===80&&await C.js(angle('.door-under'))===80);
 check('the ring turns about its own middle',same(await C.js(middle('.door-ring')),at)&&same(await C.js(middle('.door-under')),under));
 check('the crescent stays still',await C.js(angle('.door-moon'))===0);
 await C.back();await sleep(450);check('delete turns it back',await C.js(angle('.door-ring'))===60);
 await C.type('abcdefgh');await sleep(60);const mid=await C.js(`${running}`);await sleep(500);
 check('fast typing: one movement at a time, ending where it should',await C.js(angle('.door-ring'))===-140&&await C.js(`${running}===0`),`${mid} running mid-way`);
 check('at rest the chip keeps no hint for the compositor',await C.js(clean));
 await C.click(`document.querySelector('[data-password-toggle]')`,500);
 check('Show tips the crescent',await C.js(angle('.door-moon'))===-32&&await C.js(`document.querySelector('[name=password]').type==='text'`));
 await C.click(`document.querySelector('[data-password-toggle]')`,500);
 check('Hide tips it back',await C.js(angle('.door-moon'))===0);
 // Sending: the page stops its own load just after the form leaves, so the spin can be seen.
 await C.js(`document.querySelector('form.form-section').addEventListener('submit',()=>setTimeout(()=>window.stop(),40));document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='x';document.querySelector('form.form-section [type=submit]').click()`);
 await sleep(300);const s1=await C.js(angle('.door-ring'));await sleep(200);const s2=await C.js(angle('.door-ring'));
 check('while the form is on its way the ring spins',s1!==s2&&await C.js(`document.querySelector('form.form-section [type=submit]').getAttribute('aria-busy')==='true'`),`${s1}° then ${s2}°`);
 await C.go('/accounts/login/',600);await C.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='wrong-password';document.querySelector('form.form-section [type=submit]').click()`);
 for(let i=0;i<200;i++){if(await C.js(`!!window.__first&&document.body.dataset.method==='POST'&&!!document.querySelector('.notice-bad')&&!!window.pokerMotion`).catch(()=>false))break;await sleep(15)}
 f=await C.js('window.__first');const shaking=await C.js(`document.querySelector('.door-mark').getAnimations().length`);
 check('a refused page plays no arrival',f.arrival===''&&f.count===0&&f.mark===1,JSON.stringify(f));
 check('a refused page shakes the chip once',shaking===1,`${shaking} movement`);await sleep(700);
 check('after the shake nothing is left on the chip',await C.js(`!document.querySelector('.door-mark').getAttribute('style')&&${running}===0`),await C.js(`JSON.stringify([document.querySelector('.door-mark').getAttribute('style'),${running}])`));
 check('the refusal still says what to do, with focus on Password',await C.js(`document.querySelectorAll('.notice-bad').length===1&&document.activeElement.name==='password'&&document.querySelector('[name=username]').value==='hana'`));
 await C.shot('door-login-refused-390');

 // --- One place: Log in and Sign up.
 const D=await page();await D.go('/accounts/login/');await D.js('window.__doc=1');
 await D.js(`document.querySelector('.entry-alt a').click()`);let moved=null;
 for(let i=0;i<40&&!moved;i++){moved=await D.js(`(()=>{const names=document.getAnimations().map(a=>a.effect&&a.effect.pseudoElement).filter(Boolean);return names.length?names:null})()`);await sleep(10)}
 check('to Sign up: the chip, the name and the sheet move as themselves',!!moved&&['brand-mark','door-name','door-sheet'].every(n=>moved.includes(`::view-transition-group(${n})`)),moved&&[...new Set(moved)].filter(n=>n.includes('group')).join(' '));
 await sleep(700);
 check('to Sign up: same document, no second arrival',await D.js(`window.__doc===1&&location.pathname==='/accounts/signup/'&&!document.getElementById('main').dataset.arrival&&${running}===0&&document.getAnimations().length===0`));
 for(let i=0;i<10;i++){await D.click(`document.querySelector('.entry-alt a')`,450)}
 await sleep(500);check('ten changes later nothing runs',await D.js(`window.__doc===1&&location.pathname==='/accounts/signup/'&&document.getAnimations().length===0`),await D.js(`JSON.stringify([window.__doc,location.pathname,document.getAnimations().map(a=>(a.effect.pseudoElement||a.effect.target.className.baseVal||a.effect.target.className)+' '+a.playState)])`));
 await D.js(`document.querySelector('[name=username]').focus()`);await D.type('z');await sleep(450);
 check('ten changes later one key still turns one notch',await D.js(angle('.door-ring'))===20);

 // --- Getting in and out.
 const E=await page();await E.go('/accounts/login/');await login(E);
 check('getting in: the browser carries the chip into the top bar',await E.js(`location.pathname==='/'&&window.__vt===true&&window.__carry===true`),await E.js(`JSON.stringify([window.__vt,window.__carry])`));
 check('inside the app the top bar gives the name up',await E.js(`document.documentElement.dataset.doorDone==='1'&&getComputedStyle(document.querySelector('.brand img')).viewTransitionName==='none'`));
 await E.js(`document.querySelector('.site-header form [type=submit]').click()`);await sleep(1500);
 check('logging out carries it back',await E.js(`location.pathname==='/accounts/login/'&&window.__vt===true&&window.__carry===true&&!document.documentElement.dataset.doorDone`),await E.js(`JSON.stringify([location.pathname,window.__vt,window.__carry])`));
 f=await E.js('window.__first');check('after logging out the arrival is the short one',f.arrival==='short');

 // --- Late frames with the processor slowed four times, with and without the name's width moving.
 const late=async still=>{const P=await page();await send('Emulation.setCPUThrottlingRate',{rate:4},P.s);
  if(still)await send('Page.addScriptToEvaluateOnNewDocument',{source:`document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='@keyframes door-name{from{opacity:0}}';document.head.append(s)})`},P.s);
  await P.go('/accounts/login/',1800);const frames=(await P.js('window.__frames')).slice(0,66);return {late:frames.filter(d=>d>34).length,worst:Math.round(Math.max(...frames))}};
 const moving=await late(false),fixed=await late(true);
 check('slowed four times: the name widening adds no late frame',moving.late<=fixed.late,`widening ${JSON.stringify(moving)}, without ${JSON.stringify(fixed)}`);

 // --- Fail safe.
 const R=await page();await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await R.go('/accounts/login/');f=await R.js('window.__first');
 check('reduced motion: nothing arrives, the page is whole',f.count===0&&f.mark===1&&f.sheetY===0&&f.field===1,JSON.stringify(f));
 await R.js(`document.querySelector('[name=username]').focus()`);await R.type('hana');await sleep(300);await R.click(`document.querySelector('[data-password-toggle]')`,300);
 check('reduced motion: the chip is still and Show still works',await R.js(angle('.door-ring'))===0&&await R.js(angle('.door-moon'))===0&&await R.js(`document.querySelector('[name=password]').type==='text'`));
 await R.go('/accounts/login/');await login(R);check('reduced motion: log in works, with no carry',await R.js(`location.pathname==='/'&&!window.__carry`));
 const N=await page({plain:true});await send('Emulation.setScriptExecutionDisabled',{value:true},N.s);await N.go('/accounts/login/',1400);
 check('no JavaScript: the frame is whole',await N.js(`getComputedStyle(document.querySelector('.door-mark')).opacity==='1'&&getComputedStyle(document.querySelector('.field')).opacity==='1'&&document.getAnimations().length===0`));
 await login(N);check('no JavaScript: log in works',await N.js(`location.pathname==='/'&&!!document.querySelector('.site-header')`));
 const X=await page();await send('Network.enable',{},X.s);await send('Network.setBlockedURLs',{urls:['*vendor/motion-*']},X.s);const before=errors.length;await X.go('/accounts/login/');
 await X.js(`document.querySelector('[name=username]').focus()`);await X.type('hana');await X.click(`document.querySelector('[data-password-toggle]')`,200);
 check('Motion blocked: the arrival still plays, the chip is still, no script error',(await X.js('window.__first')).arrival==='full'&&await X.js(`!window.Motion`)&&await X.js(angle('.door-ring'))===0&&errors.length===before,errors.slice(before).join('; '));
 await X.go('/accounts/login/');await login(X);check('Motion blocked: log in works',await X.js(`location.pathname==='/'`));
 if(OFF){const O=await page();await O.go('/accounts/login/',1300,OFF);f=await O.js('window.__first');
  check('switch off: the frame, with no arrival',f.arrival===''&&f.count===0&&f.mark===1&&await O.js(`!document.documentElement.dataset.door&&!!document.querySelector('.door-sheet')`));
  await O.js(`document.querySelector('[name=username]').focus()`);await O.type('hana');await sleep(300);
  check('switch off: the chip is still and carries no name',await O.js(angle('.door-ring'))===0&&await O.js(`getComputedStyle(document.querySelector('.door-mark')).viewTransitionName==='none'`));
  await login(O);check('switch off: log in works, with no carry',await O.js(`location.pathname==='/'&&!window.__carry&&getComputedStyle(document.querySelector('.brand img')).viewTransitionName==='none'`));
  for(const [width,height] of [[320,568],[390,844],[1280,800]]){await A.size(width,height);await A.go('/accounts/signup/',500,OFF);
   check(`invite needed: frame, fit and targets ${width}`,await A.js(`${text('Sign-up needs an invite')}&&!!document.querySelector('.door-sheet')&&document.documentElement.scrollWidth<=${width}&&${targets}`));await A.shot(`door-closed-${width}`);}
 } else console.log('SKIP switch off and invite needed: PN_OFF_URL is not set');
 check('no script error anywhere',errors.length===0,errors.join('; '));
 writeFileSync(`${OUT}/door.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
