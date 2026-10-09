import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-entry-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const M=JSON.parse(readFileSync('/private/tmp/pn-entry-manifest.json','utf8'));
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
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>Math.round(el.getBoundingClientRect().height*100)/100>=48)`;
// WCAG contrast of an element's text against the page ground, via canvas so oklch resolves.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
try {
 const A=await page();
 const pages=[['login','/accounts/login/'],['login-invited','/accounts/login/?next='+encodeURIComponent(M.invite)],['signup','/accounts/signup/'],['signup-invited','/accounts/signup/?next='+encodeURIComponent(M.invite)],['signup-long','/accounts/signup/?next='+encodeURIComponent(M.long)]];
 for(const width of [320,390,1280])for(const [name,path] of pages){await A.size(width);await A.go(path);
  check(`${name} fits ${width}`,await A.js(`document.documentElement.scrollWidth<=${width}`));
  check(`${name} 48px targets ${width}`,await A.js(targets));
  check(`${name} lockup, no site header ${width}`,await A.js(`!!document.querySelector('.door-hero .door-mark')&&!!document.querySelector('.door-sheet')&&!document.querySelector('.site-header')&&document.querySelector('form [type=submit]').getBoundingClientRect().width>=Math.min(${width},440)-66`));
  await A.shot(`entry-${name}-${width}`);}
 await A.size(390);
 await A.go('/accounts/signup/?next='+encodeURIComponent(M.invite));console.log('  invited sign-up height at 390:',await A.js(`document.documentElement.scrollHeight`),'button bottom:',await A.js(`Math.round(document.querySelector('form [type=submit]').getBoundingClientRect().bottom)`));check('invited sign-up: Create account visible without scrolling at 390x844',await A.js(`document.querySelector('form [type=submit]').getBoundingClientRect().bottom<=844`));
 await A.go('/accounts/login/');check('login fits a 390x844 phone',await A.js(`document.documentElement.scrollHeight<=844`));
 await A.go('/accounts/signup/?next='+encodeURIComponent(M.invite));check('contrast invite link',await A.js(contrast('.entry-invite a'))>=4.5);await A.go('/accounts/login/');for(const sel of ['.entry-line','.entry-alt','.entry-alt a','.password-toggle','h1'])check('contrast '+sel,await A.js(contrast(sel))>=4.5);
 await A.go('/accounts/signup/');check('contrast hint',await A.js(contrast('.hint'))>=4.5);
 // Invite naming.
 await A.go('/accounts/login/?next='+encodeURIComponent(M.invite));check('login names the inviting group',await A.js(text("You're invited to "+M.group)));
 check('sign-up link keeps the invite',await A.js(`document.querySelector('.entry-alt a').getAttribute('href').endsWith('?next='+${JSON.stringify(M.invite)})`));
 await A.go(M.expired);check('expired invite shows the reason at once, signed out',await A.js(`location.pathname===${JSON.stringify(M.expired)}&&!!document.querySelector('.notice-bad[role=alert]')&&!document.querySelector('.site-header')&&!!document.querySelector('.entry-alt a[href="/accounts/login/"]')&&document.querySelector('h1').textContent.includes("doesn't work")`));await A.shot('entry-invite-expired-390');
 await A.go('/accounts/login/?next='+encodeURIComponent(M.expired));check('expired invite names nothing',await A.js(`!${text("You're invited")}`));
 // Show / Hide.
 await A.go('/accounts/signup/');
 check('toggle is shown by the script',await A.js(`!document.querySelector('[data-password-toggle]').hidden&&document.querySelectorAll('[data-password-toggle]').length===1`));
 await A.js(`document.querySelector('[name=username]').value='someone';document.querySelector('[name=password1]').value='tablestakes-91';document.querySelector('[name=password2]').value='tablestakes-91';document.querySelector('[data-password-toggle]').focus()`);
 await A.click(`document.querySelector('[data-password-toggle]')`);
 check('show reveals both fields and keeps names',await A.js(`['password1','password2'].every(n=>document.querySelector('[name='+n+']').type==='text'&&document.querySelector('[name='+n+']').autocomplete==='new-password')&&document.querySelector('[data-password-toggle]').getAttribute('aria-label')==='Hide password'&&!document.querySelector('[data-password-toggle]').hasAttribute('aria-pressed')&&document.querySelector('[data-password-toggle]').textContent==='Hide'&&document.activeElement.matches('[data-password-toggle]')`));
 await A.shot('entry-signup-shown-390');
 await A.js(`window.__types=null;document.querySelector('form.form-section').addEventListener('submit',e=>{window.__types=[...e.target.querySelectorAll('[name^=password]')].map(f=>f.type);e.preventDefault()})`);
 await A.click(`document.querySelector('form.form-section [type=submit]')`);
 check('fields return to password type on submit',await A.js(`JSON.stringify(window.__types)==='["password","password"]'`));
 // Keyboard order and focus ring on login.
 await A.go('/accounts/login/');await A.js(`document.querySelector('[name=username]').focus()`);const order=[];
 for(let i=0;i<4;i++){await A.key('Tab','Tab',9);order.push(await A.js(`document.activeElement.name||document.activeElement.className||document.activeElement.textContent.trim()`));}
 check('keyboard order: password, show, log in, sign up',JSON.stringify(order)===JSON.stringify(['password','password-toggle','btn btn-primary btn-block','Sign up']));
 await A.go('/accounts/login/');await A.js(`document.querySelector('[name=username]').focus()`);await A.key('Tab','Tab',9);await A.key('Tab','Tab',9);
 check('show button has the focus ring',await A.js(`document.activeElement.matches('.password-toggle')&&getComputedStyle(document.activeElement).outlineWidth==='3px'`));
 // Errors.
 await A.go('/accounts/login/');await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='wrong-password'`);await A.click(`document.querySelector('form.form-section [type=submit]')`);
 check('wrong login: one notice, username kept, password empty',await A.js(`document.querySelectorAll('.notice-bad').length===1&&document.querySelector('[name=username]').value==='hana'&&document.querySelector('[name=password]').value===''`));
 check('wrong login: plain words, forgot line, focus on Password',await A.js(`${text("That username and password don't match.")}&&${text('Forgot your password? Ask a host of your group for a reset link.')}&&document.activeElement.name==='password'&&document.querySelectorAll('[role=alert]').length===1&&document.querySelectorAll('[aria-invalid=true]').length===2`));
 check('contrast forgot line',await A.js(contrast('.entry-forgot'))>=4.5);
 for(const width of [320,390]){await A.size(width);check('login error fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot('entry-login-error-'+width);}
 await A.size(390);await A.go('/accounts/signup/');await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password1]').value='12345678';document.querySelector('[name=password2]').value='12345678'`);await A.click(`document.querySelector('form.form-section [type=submit]')`);
 check('refused sign-up: one alert and focus on the refused field',await A.js(`document.querySelectorAll('[role=alert]').length===1&&${text('Check the highlighted fields.')}&&document.activeElement.name==='username'`));
 check('refused sign-up names the rules under the fields',await A.js(`document.querySelector('#id_password1_error').textContent.includes('Use more than digits.')&&!document.querySelector('#id_password2_error')&&${text('That name is taken. Try another.')}&&document.querySelector('[name=username]').value==='hana'&&getComputedStyle(document.querySelector('[name=username]')).borderTopColor!==getComputedStyle(document.querySelector('[name=password1]')).color`));
 for(const width of [320,390]){await A.size(width);check('sign-up error fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot('entry-signup-error-'+width);}
 await A.size(390);
 // The whole flow from an invite link, signed out: link -> log in -> sign up -> join -> group.
 // A newcomer: invite link -> sign up -> group, in two screens.
 const B=await page();await B.go(M.invite);
 check('invite link leads a signed-out person to sign up',await B.js(`location.pathname==='/accounts/signup/'&&${text("Join "+M.group)}&&${text('It never moves money.')}&&document.querySelector('.entry-invite').textContent.includes('Already have an account?')&&!document.querySelector('.entry-alt')&&document.querySelector('.entry-invite a').getBoundingClientRect().bottom<document.querySelector('[name=username]').getBoundingClientRect().top`));
 check('sign up says who sees the name and where a reset comes from',await B.js(`${text('Your friends see this name.')}&&${text('A host of your group can send you a reset link.')}`));
 check('contrast reset note',await B.js(contrast('.hint-note'))>=4.5);
 await B.js(`document.querySelector('[name=username]').value='newcomer';document.querySelector('[name=password1]').value='tablestakes-91';document.querySelector('[name=password2]').value='tablestakes-91'`);
 await B.js(`document.querySelector('form.form-section').addEventListener('submit',()=>setTimeout(()=>{window.__busy=document.querySelector('form.form-section [type=submit]').textContent},5))`);
 await B.click(`document.querySelector('form.form-section [type=submit]')`);
 check('sign-up lands in the group with a welcome',await B.js(`location.pathname.startsWith('/g/')&&${text('Welcome to '+M.group+". You're in.")}`));await B.shot('entry-welcome-390');
 // An existing account: invite link -> sign up -> "Log in" -> the Join confirmation.
 const D=await page();await D.go(M.invite);await D.click(`document.querySelector('.entry-invite a')`);
 check('existing account: log in keeps the invite',await D.js(`location.pathname==='/accounts/login/'&&${text("You're invited to "+M.group)}`));
 await D.js(`document.querySelector('[name=username]').value='visitor';document.querySelector('[name=password]').value='tablestakes-91'`);await D.click(`document.querySelector('form.form-section [type=submit]')`);
 check('existing account is asked before joining',await D.js(`location.pathname===${JSON.stringify(M.invite)}&&${text('Join '+M.group)}&&/\\d+ players?\\./.test(document.body.textContent)&&${text('can join their games')}&&!!document.querySelector('.site-header')`));
 for(const width of [320,390,1280]){await D.size(width);check('join fits '+width,await D.js(`document.documentElement.scrollWidth<=${width}`));check('join 48px targets '+width,await D.js(targets));await D.shot('entry-join-'+width);}
 await D.size(320);await D.go(M.long);check('long group name wraps on the join page',await D.js(`document.documentElement.scrollWidth<=320`));await D.shot('entry-join-long-320');
 await D.size(390);await D.go('/join/not-a-token/');check('bad invite shows the error',await D.js(`!!document.querySelector('.notice-bad[role=alert]')`));await D.shot('entry-join-error-390');
 await D.go(M.invite);await D.click(`document.querySelector('form.form-section [type=submit]')`);
 check('join enters the group',await D.js(`location.pathname.startsWith('/g/')&&${text('Welcome to '+M.group)}`));
 // Skip link and busy label.
 const E=await page();await E.go('/accounts/login/');await E.js(`document.querySelector('.skip-link').focus()`);
 check('skip link is a 48px target when focused',await E.js(`(()=>{const r=document.querySelector('.skip-link').getBoundingClientRect();return r.height>=48&&r.left>=0})()`));
 await E.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='x';document.querySelector('form.form-section').addEventListener('submit',e=>{e.preventDefault();setTimeout(()=>{window.__busy=document.querySelector('form.form-section [type=submit]').textContent},20)})`);await E.click(`document.querySelector('form.form-section [type=submit]')`);
 check('busy label says Logging in',await E.js(`window.__busy==='Logging in…'`));
 // Without JavaScript: no Show button, native log in.
 const C=await page();await send('Emulation.setScriptExecutionDisabled',{value:true},C.s);await C.go('/accounts/login/');
 check('no JavaScript: no Show button, form intact',await C.js(`!document.querySelector('[data-password-toggle]').getClientRects().length&&document.querySelector('[name=password]').type==='password'`));await C.shot('entry-login-nojs-390');
 await C.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await C.click(`document.querySelector('form.form-section [type=submit]')`);
 check('no JavaScript: log in works',await C.js(`location.pathname==='/'&&!!document.querySelector('.site-header')`));
 writeFileSync(`${OUT}/entry.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
