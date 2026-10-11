// The home-screen suggestion after a login, per phone, and Join with a link inside the installed app.
// Seed a fresh temporary database with seed_install.py, serve it on 127.0.0.1:8765, then run.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-install-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const UA={
 iphone:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
 android:'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
 messenger:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/MessengerLiteForiOS;FBAV/460.0.0;FBDV/iPhone15,2]',
 desktop:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'};
rmSync('/private/tmp/pn-install-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-install-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// offer: the browser's install event arrives at load, with a prompt() that records the call and answers as told.
const BOOT=({offer,standalone})=>`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__t0=performance.now();
 window.__copied=[];try{Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>(__copied.push(t),Promise.resolve()),readText:()=>Promise.resolve(window.__clip||'')},configurable:true})}catch(e){}
 ${standalone?`Object.defineProperty(navigator,'standalone',{value:true,configurable:true});`:''}
 ${offer?`addEventListener('DOMContentLoaded',()=>setTimeout(()=>{const e=new Event('beforeinstallprompt',{cancelable:true});window.__prompted=0;e.prompt=()=>{__prompted++};e.userChoice=new Promise(ok=>window.__answer=ok);window.dispatchEvent(e);window.__prevented=e.defaultPrevented},50));`:''}`;
async function user(kind,width,{offer=false,standalone=false,reduced=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Emulation.setUserAgentOverride',{userAgent:UA[kind]},s);
 if(kind!=='desktop')await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 if(reduced)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT({offer,standalone})},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(400);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=4000)=>{for(let t=0;t<ms;t+=50){if(await js(expression))return true;await sleep(50)}return false};
 const login=async(name,next='')=>{await go('/accounts/login/'+(next?`?next=${encodeURIComponent(next)}`:''));await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(350);for(let i=0;i<30;i++){if(await js(`document.readyState==='complete'&&!location.pathname.startsWith('/accounts/login')`))break;await sleep(100)}};
 const logout=async()=>{await js(`document.querySelector('form[action$="/logout/"]').submit()`);await sleep(700)};
 return {s,js,go,shot,until,login,logout,width};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const D=`document.getElementById('install-sheet')`,OPEN=`${D}.open`,PART=`${D}.dataset.part`;
const visible=sel=>`[...${D}.querySelectorAll(${JSON.stringify(sel)})].filter(e=>e.getClientRects().length)`;
const tidy=w=>`${visible('.btn')}.every(e=>e.getBoundingClientRect().height>=48)&&${D}.scrollWidth<=${D}.clientWidth&&document.documentElement.scrollWidth<=${w}`;
const tap=sel=>`${visible(sel)}[0].click()`;

try{
 // iPhone, Safari.
 const A=await user('iphone',390);await A.login('hana');
 const early=await A.js(`({open:${OPEN},welcome:document.getElementById('main').hasAttribute('data-came-in'),ms:performance.now()-__t0})`);
 check('iPhone: the page after a login is marked, and the sheet waits for the arrival',early.welcome&&!early.open,early);
 check('iPhone: the sheet rises by itself with the Share steps',await A.until(`${OPEN}&&${PART}==='ios'`,3000));
 const at=await A.js(`performance.now()-__t0`);check('iPhone: not before the arrival has had its second',at>=1000,at);
 const moment=await A.js(`({drop:${D}.querySelector('.install-icon img').getAnimations().map(a=>a.animationName),title:${D}.querySelector('h2').textContent,steps:${visible('.install-steps li')}.length,buttons:${visible('.btn')}.map(e=>e.textContent.trim()||e.getAttribute('aria-label')),focus:${D}.contains(document.activeElement)})`);
 check('iPhone: the icon drops onto its tile once',moment.drop.includes('install-drop'),moment.drop);
 check('iPhone: two steps, "Done, it\'s on my home screen" and "Not now", focus inside',moment.steps===2&&moment.buttons.join('|')==="Close|Done, it's on my home screen|Not now"&&moment.focus&&/home screen/.test(moment.title),moment);
 check('iPhone: says the app has its own login',await A.js(`/log in once more inside the app/.test(${visible('[data-install-part] p')}.map(e=>e.textContent).join(' '))`));
 await sleep(1700);
 check('iPhone: at rest nothing runs; targets 48px; nothing overflows',await A.js(`document.getAnimations().filter(a=>a.playState==='running').length===0&&${tidy(390)}`));
 await A.shot('install-390-1-iphone');
 await A.js(tap('.install-actions [data-install-close]'));await sleep(500);
 check('iPhone: Not now closes it and focus is on the page',await A.js(`!${OPEN}&&document.activeElement===document.getElementById('main')`));
 await A.go(`/g/${M.group}/`);await sleep(1500);
 check('iPhone: it does not return on the next screen',await A.js(`!${OPEN}`));
 await A.go('/');await sleep(700);
 check('iPhone: Your groups keeps "Add to home screen", 48px, and no link field',await A.js(`(()=>{const b=document.querySelector('[data-install-open]');return !${OPEN}&&!b.hidden&&b.getBoundingClientRect().height>=48&&document.querySelector('[data-app-link]').hidden})()`));
 await A.js(`document.querySelector('[data-install-open]').click()`);await sleep(500);
 check('iPhone: it opens the same sheet on demand',await A.js(`${OPEN}&&${PART}==='ios'`));
 await A.js(`${D}.dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(500);
 check('iPhone: Escape closes it and focus returns to the button',await A.js(`!${OPEN}&&document.activeElement===document.querySelector('[data-install-open]')`));
 // Every login asks again; "Done" ends it.
 await A.logout();await A.login('hana');
 check('iPhone: the next login shows it again',await A.until(`${OPEN}`,3000));
 await A.js(tap('[data-install-done]'));await sleep(500);
 await A.logout();await A.login('hana');await sleep(2200);
 check('iPhone: after "Done, it\'s on my home screen" a login shows nothing, and the button is gone',await A.js(`!${OPEN}&&document.querySelector('[data-install-open]').hidden`));
 // 320px.
 const N=await user('iphone',320);await N.login('hana');await N.until(OPEN,3000);await sleep(900);
 check('320px: the sheet fits',await N.js(tidy(320)));await N.shot('install-320-1-iphone');

 // Android with the browser's install offer.
 const B=await user('android',390,{offer:true});await B.login('hana');
 check('Android: the sheet has one primary, Install',await B.until(`${OPEN}&&${PART}==='install'`,3000)&&await B.js(`__prevented===true&&${visible('.btn-primary')}.length===1&&${visible('.btn-primary')}[0].textContent.trim()==='Install'&&${D}.querySelector('[data-install-done]').hidden&&${tidy(390)}`));
 await sleep(900);await B.shot('install-390-2-android');
 await B.js(tap('[data-install-go]'));await sleep(100);
 check('Android: Install opens the browser\'s own dialog',await B.js(`__prompted===1&&${OPEN}`));
 await B.js(`__answer({outcome:'accepted'})`);await sleep(500);
 check('Android: accepted closes the sheet and is remembered',await B.js(`!${OPEN}&&localStorage.getItem('rack-install')==='done'`));
 const C=await user('android',390,{offer:true});await C.login('hana');await C.until(OPEN,3000);
 await C.js(tap('[data-install-go]'));await C.js(`__answer({outcome:'dismissed'})`);await sleep(300);
 check('Android: declined leaves the menu steps, nothing remembered',await C.js(`${OPEN}&&${PART}==='menu'&&localStorage.getItem('rack-install')===null`));
 const E=await user('android',390);await E.login('hana');
 check('Android without the offer: the menu steps',await E.until(`${OPEN}&&${PART}==='menu'`,3000)&&await E.js(`${visible('.install-steps li')}.length===2&&${tidy(390)}`));
 await sleep(900);await E.shot('install-390-3-menu');
 await E.js(`window.dispatchEvent(new Event('appinstalled'))`);await sleep(500);
 check('Android: the browser reporting the install closes it for good',await E.js(`!${OPEN}&&localStorage.getItem('rack-install')==='done'`));

 // A chat app's browser.
 const F=await user('messenger',390);await F.login('hana');
 check('in a chat app\'s browser: says to open the real browser, with Copy link',await F.until(`${OPEN}&&${PART}==='inapp'`,3000)&&await F.js(`/cannot add apps/.test(${D}.textContent)&&${D}.querySelector('[data-install-done]').hidden&&${tidy(390)}`));
 await sleep(900);await F.shot('install-390-4-inapp');
 await F.js(tap('[data-install-copy]'));await sleep(150);
 check('Copy link copies the site\'s address and says so',await F.js(`__copied.length===1&&__copied[0]===location.origin+'/'&&${visible('[data-install-copy]')}[0].textContent==='Copied'`));

 // Pages that have their own business first.
 const G=await user('iphone',390);await G.login('cara',`/join/${M.invite}/`);await sleep(2000);
 check('a join page after a login is not covered',await G.js(`location.pathname.startsWith('/join/')&&!${OPEN}`),await G.js('location.pathname'));
 await G.js(`document.querySelector('main form [type=submit], main form button').click()`);await sleep(600);
 check('…and the suggestion shows on the page after it',await G.until(`!location.pathname.startsWith('/join/')&&${OPEN}`,3500),await G.js('location.pathname'));
 const H=await user('iphone',390);await H.login('ben',`/n/${M.night}/`);await sleep(2200);
 check('a session whose recap opens by itself keeps the screen',await H.js(`!${OPEN}&&!!document.querySelector('dialog.sheet[open]:not(#install-sheet)')`));
 await H.go('/');
 check('…and the suggestion shows on the next page',await H.until(OPEN,3000));

 // Where it must not show.
 const P=await user('desktop',1280);await P.login('hana');await sleep(2200);
 check('desktop: no sheet and no button',await P.js(`!${OPEN}&&document.querySelector('[data-install-open]').hidden&&document.querySelector('[data-app-link]').hidden`));
 const R=await user('iphone',390,{reduced:true});await R.login('hana');await R.until(OPEN,3000);
 check('reduced motion: the sheet is simply there',await R.js(`${D}.getAnimations({subtree:true}).length===0`));

 // The installed app.
 const S=await user('iphone',390,{standalone:true});await S.login('hana');await sleep(2200);
 check('installed app: no sheet, no button; Join with a link is offered',await S.js(`!${OPEN}&&document.querySelector('[data-install-open]').hidden&&!document.querySelector('[data-app-link]').hidden&&document.querySelector('[data-app-link] summary').getBoundingClientRect().height>=48`));
 await S.js(`document.querySelector('[data-app-link]').open=true;document.querySelector('[data-app-link]').scrollIntoView({block:'center'})`);await sleep(200);
 await S.js(`document.getElementById('app-link').value='https://example.com/join/abc/';document.querySelector('[data-app-link-form] [type=submit]').click()`);await sleep(150);
 check('installed app: a link to another site is refused in words',await S.js(`location.pathname==='/'&&!document.getElementById('app-link-error').hidden&&/not a PokerNights/.test(document.getElementById('app-link-error').textContent)&&document.activeElement.id==='app-link'`));
 await S.shot('install-390-5-link');
 check('installed app: the link form fits, 48px controls',await S.js(`document.documentElement.scrollWidth<=390&&[...document.querySelectorAll('[data-app-link] .btn, #app-link')].filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=48)`));
 await S.js(`window.__clip=location.origin+'/join/${M.invite}/';document.querySelector('[data-app-link-paste]').click()`);await sleep(150);
 check('installed app: Paste fills the field',await S.js(`document.getElementById('app-link').value.endsWith('/join/${M.invite}/')`));
 await S.js(`document.querySelector('[data-app-link-form] [type=submit]').click()`);
 check('installed app: a pasted invite opens inside the app',await S.until(`location.pathname==='/join/${M.invite}/'`,3000));
 for(const [n,u] of [['iPhone',A],['Android',B],['chat',F],['installed',S]])check(`${n}: no script error`,await u.js(`__errors.length===0`),await u.js('__errors'));
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
