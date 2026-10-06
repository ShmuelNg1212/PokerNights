import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-reset-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
async function page(){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const size=width=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:c.width,height:Math.max(c.height,844),scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
const key=async(k,code,vk,extra={})=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:k,code,windowsVirtualKeyCode:vk,...extra},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:k,code,windowsVirtualKeyCode:vk},s)};
await size(390);return {s,js,go,click,shot,size,key};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
// WCAG contrast of an element's text against the page ground, via canvas so oklch resolves.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
try {
 const fill=(P,a,b)=>P.js(`document.querySelector('[name=new_password1]').value=${JSON.stringify(a)};document.querySelector('[name=new_password2]').value=${JSON.stringify(b??a)}`);
 const submit=P=>P.click(`document.querySelector('form.form-section [type=submit]')`);
 const logIn=async(P,name,password)=>{await P.go('/accounts/login/');await P.js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value=${JSON.stringify(password)}`);await submit(P)};
 const create=`document.querySelector('form[action$="/reset-link/"] button')`;
 // The host creates the link.
 const A=await page();await logIn(A,'hana','tablestakes-91');
 // The seeded group is the one with a second account in it.
 const groups=await A.js(`[...new Set([...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).filter(h=>new RegExp('^/g/[0-9]+/$').test(h)))]`);
 let settings;for(const g of groups){settings=g+'?view=settings';await A.go(settings);if(await A.js(`!!document.querySelector('form[action$="/reset-link/"]')`))break;}
 check('one member can be sent a link: not the host, not a player without a login',await A.js(`document.querySelectorAll('form[action$="/reset-link/"]').length===1&&${create}.textContent.trim()==='Create password reset link'`));
 await A.js(`${create}.closest('details').open=true`);
 check('the action matches its neighbours',await A.js(`(()=>{const d=${create}.closest('details');const hs=[...d.querySelectorAll('button')].map(b=>Math.round(b.getBoundingClientRect().height));return new Set(hs).size===1})()`));
 await A.shot('reset-manage-390');
 await A.click(create);
 check('the link is shown once, in the Players section',await A.js(`location.hash==='#players'&&${text('Reset link for Ben.')}&&${text('Send it to Ben only. Whoever opens it can set the password.')}&&${text('It works once and expires ')}&&document.querySelector('#players .notice-good input').value.startsWith(location.origin+'/accounts/reset/')`));
 const link=new URL(await A.js(`document.querySelector('#players .notice-good input').value`)).pathname;
 for(const width of [320,390,1280]){await A.size(width);check('notice fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}&&document.querySelector('#players .notice-good input').getBoundingClientRect().right<=${width}`));await A.shot('reset-notice-'+width);}
 await A.size(390);check('contrast of the notice',await A.js(contrast('#players .notice-good p'))>=4.5);
 await A.go(settings);await A.js(`${create}.closest('details').open=true`);
 check('after a reload the link is gone and the row says it is active',await A.js(`!document.querySelector('#players .notice-good')&&!document.body.innerHTML.includes('/accounts/reset/')&&${text('Reset link active until ')}&&!!document.querySelector('form[action$="/reset-link/cancel/"]')&&${create}.textContent.trim()==='Create a new reset link'`));
 await A.shot('reset-active-390');
 // The player opens it, signed out.
 const B=await page();
 for(const width of [320,390,1280]){await B.size(width);await B.go(link);
  check('reset page fits '+width,await B.js(`document.documentElement.scrollWidth<=${width}`));
  check('reset page 48px targets '+width,await B.js(targets));
  await B.shot('reset-page-'+width);}
 await B.size(390);
 check('reset page: heading, username, no site header, title without the name',await B.js(`document.querySelector('h1').textContent==='Set a new password'&&${text('Your username is ben.')}&&!document.querySelector('.site-header')&&document.title==='Reset password · PokerNights'`));
 check('reset page fits a 390x844 phone',await B.js(`document.documentElement.scrollHeight<=844`));
 check('cursor starts in New password; one Show button for both fields',await B.js(`document.activeElement.name==='new_password1'&&document.querySelectorAll('[data-password-toggle]').length===1&&!document.querySelector('[data-password-toggle]').hidden`));
 for(const sel of ['h1','.entry-invite','.hint','.password-toggle'])check('contrast '+sel,await B.js(contrast(sel))>=4.5);
 await fill(B,'tablestakes-92');await B.click(`document.querySelector('[data-password-toggle]')`);
 check('show reveals both fields',await B.js(`['new_password1','new_password2'].every(n=>document.querySelector('[name='+n+']').type==='text'&&document.querySelector('[name='+n+']').autocomplete==='new-password')`));
 await B.go(link);await fill(B,'12345678');await submit(B);
 check('refused password: plain words, one alert, focus on the refused field, fields empty',await B.js(`${text('Use more than digits.')}&&document.querySelectorAll('[role=alert]').length===1&&document.activeElement.name==='new_password1'&&document.querySelector('[name=new_password1]').value===''&&location.pathname===${JSON.stringify(link)}`));
 check('refused page fits',await B.js(`document.documentElement.scrollWidth<=390`));await B.shot('reset-refused-390');
 await fill(B,'tablestakes-92','tablestakes-93');await submit(B);
 check('mismatch is reported under Repeat password',await B.js(`${text("The two passwords don't match.")}&&document.activeElement.name==='new_password2'`));
 await B.js(`document.querySelector('form.form-section').addEventListener('submit',()=>setTimeout(()=>{window.__busy=document.querySelector('form.form-section [type=submit]').textContent},20))`);
 await fill(B,'tablestakes-92');await submit(B);
 check('saving logs in and lands on Your groups',await B.js(`location.pathname==='/'&&!!document.querySelector('.site-header')&&${text("Password changed. You're logged in.")}`));await B.shot('reset-done-390');
 // The link is spent; the old password is gone and the new one works.
 const C=await page();
 for(const width of [320,390,1280]){await C.size(width);await C.go(link);check('used link fits '+width,await C.js(`document.documentElement.scrollWidth<=${width}`));check('used link 48px targets '+width,await C.js(targets));await C.shot('reset-used-'+width);}
 await C.size(390);
 check('used link says why and offers Log in',await C.js(`document.querySelector('h1').textContent==="This reset link doesn't work"&&${text('This reset link has already been used. Ask a host of your group for a new one.')}&&document.querySelectorAll('.notice-bad[role=alert]').length===1&&!document.querySelector('form')&&!!document.querySelector('.entry-alt a[href="/accounts/login/"]')&&!${text('ben')}`));
 check('contrast of the refusal',await C.js(contrast('.notice-bad'))>=4.5);
 await C.go('/accounts/reset/not-a-token/');check('unknown link is refused',await C.js(text('This reset link is not valid.')));
 await logIn(C,'ben','tablestakes-91');check('old password is refused, and the line points to a host',await C.js(`location.pathname==='/accounts/login/'&&${text('Forgot your password? Ask a host of your group for a reset link.')}`));
 await logIn(C,'ben','tablestakes-92');check('new password logs in',await C.js(`location.pathname==='/'`));
 await C.go(settings);check('a player sees no reset action',await C.js(`!document.querySelector('form[action*="/reset-link/"]')`));
 // Host: the used link no longer shows as active; a new one can be cancelled.
 await A.go(settings);check('used link is no longer active',await A.js(`!${text('Reset link active until ')}`));
 await A.js(`${create}.closest('details').open=true`);await A.click(create);
 const second=new URL(await A.js(`document.querySelector('#players .notice-good input').value`)).pathname;
 await A.js(`document.querySelector('form[action$="/reset-link/cancel/"]').closest('details').open=true`);await A.click(`document.querySelector('form[action$="/reset-link/cancel/"] button')`);
 check('cancel says so and clears the row',await A.js(`${text('Reset link cancelled.')}&&!${text('Reset link active until ')}`));
 await C.go(second);check('a cancelled link is refused',await C.js(text('This reset link is not valid.')));
 // Without JavaScript the page still works.
 const D=await page();await A.go(settings);await A.js(`${create}.closest('details').open=true`);await A.click(create);
 const third=new URL(await A.js(`document.querySelector('#players .notice-good input').value`)).pathname;
 await send('Emulation.setScriptExecutionDisabled',{value:true},D.s);await D.go(third);
 check('no JavaScript: no Show button, native form',await D.js(`!document.querySelector('[data-password-toggle]').getClientRects().length&&document.querySelector('[name=new_password1]').type==='password'`));
 await fill(D,'tablestakes-94');await submit(D);check('no JavaScript: saving logs in',await D.js(`location.pathname==='/'&&!!document.querySelector('.site-header')`));
 writeFileSync(`${OUT}/reset.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
