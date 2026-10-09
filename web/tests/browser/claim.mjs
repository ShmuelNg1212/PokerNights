// Claim links at 320, 390 and 1280px, on a fresh database seeded with seed_claim.py. See README.md.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-claim-check`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8771';
async function page(){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const size=width=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:c.width,height:Math.max(c.height,844),scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
const key=async(k,code,vk,extra={})=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:k,code,windowsVirtualKeyCode:vk,...extra},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:k,code,windowsVirtualKeyCode:vk},s)};
await size(390);return {s,js,go,click,shot,size,key,browserContextId};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
// WCAG contrast of an element's text against the page ground, via canvas so oklch resolves.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
const sized=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, #players summary')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const submit=P=>P.click(`document.querySelector('form.form-section [type=submit]')`);
const login=async(P,name)=>{await P.go('/accounts/login/');await P.js(`document.querySelector('[name=username]').value='${name}';document.querySelector('[name=password]').value='tablestakes-91'`);await submit(P);};
const row=name=>`[...document.querySelectorAll('#players [data-roster] > li')].find(li=>li.querySelector('.roster-name > span').textContent.trim().startsWith(${JSON.stringify(name)}))`;
try {
 const A=await page();await send('Browser.grantPermissions',{permissions:['clipboardReadWrite','clipboardSanitizedWrite'],browserContextId:A.browserContextId});await login(A,'rosa');
 const settings=(await A.js(`[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).find(h=>new RegExp('^/g/[0-9]+/$').test(h))`))+'?view=settings';
 const issue=async name=>{await A.go(settings);await A.js(`${row(name)}.querySelector('details').open=true`);await sleep(300);await A.click(`${row(name)}.querySelector('form[action$="/claim-link/"] button')`);return (await A.js(`document.getElementById('new-claim-link').value`)).replace(BASE,'');};
 await A.go(settings);await A.js(`${row('Tito Boy')}.querySelector('details').open=true`);await sleep(300);
 check('the action is offered for a player without a login only',await A.js(`!!${row('Tito Boy')}.querySelector('form[action$="/claim-link/"]')&&!${row('benny')}.querySelector('form[action$="/claim-link/"]')`));
 check('48px targets in Manage',await A.js(sized));await A.shot('claim-manage-390');
 const tito=await issue('Tito Boy');
 check('the link is shown once with what it does',await A.js(text('Whoever opens it becomes Tito Boy in this group.'))&&tito.startsWith('/claim/'));
 for(const w of [320,390,1280]){await A.size(w);check(`notice fits ${w}`,await A.js(fits(w)));}await A.size(390);await A.shot('claim-notice-390');
 await A.js(`document.querySelector('[data-copy="new-claim-link"]').click()`);await sleep(250);
 check('Copy puts the whole address on the clipboard',(await A.js(`navigator.clipboard.readText()`)).endsWith(tito));
 await A.go(settings);check('the link is not shown again and the row says it is live',await A.js(`!document.getElementById('new-claim-link')`)&&await A.js(text('Claim link active until')));

 // A newcomer signs up from the link and is the player.
 const B=await page();await B.go(tito);
 check('a signed-out visitor lands on Sign up, naming the group',await B.js(`location.pathname==='/accounts/signup/'`)&&await B.js(text('Thursday Regulars')));
 check('opening changed nothing',await A.js(`(async()=>{const r=await fetch(location.href);return (await r.text()).includes('Claim link active until')})()`));
 await B.js(`document.querySelector('[name=username]').value='titoboy';document.querySelector('[name=password1]').value='tablestakes-91';document.querySelector('[name=password2]').value='tablestakes-91'`);await submit(B);
 check('the new account arrives in the group as the player',await B.js(text("You're in as Tito Boy."))&&await B.js(`new RegExp('^/g/[0-9]+/$').test(location.pathname)`));
 await B.go(settings);check('the player keeps the name and the history',await B.js(`(()=>{const li=${row('Tito Boy')};return li.textContent.includes('(you)')&&li.textContent.includes('1 session · last played Oct 1')&&!li.textContent.includes('No login')})()`));await B.shot('claim-arrived-390');

 // An account with an empty entry confirms and replaces it.
 const lola=await issue('Lola');const C=await page();await login(C,'benny');await C.go(lola);
 check('the confirm page names the group, the player and the account',await C.js(text('Join Thursday Regulars as Lola'))&&await C.js(text('You are logged in as benny.'))&&await C.js(text('That entry is replaced by Lola.')));
 for(const w of [320,390,1280]){await C.size(w);await C.go(lola);await sleep(500);check(`confirm fits ${w}`,await C.js(fits(w)));check(`confirm 48px ${w}`,await C.js(sized));await C.shot(`claim-confirm-${w}`);}
 await C.size(390);await C.go(lola);await sleep(900);
 check('the token is whole and no inline style is left',await C.js(`(()=>{const c=document.querySelector('[data-pop]');const s=getComputedStyle(c);return s.opacity==='1'&&!c.getAttribute('style')})()`));
 check('contrast of the account line and the note',await C.js(contrast('.claim-who p'))>=4.5&&await C.js(contrast('.claim-who p + p'))>=4.5&&await C.js(contrast('.link-button'))>=4.5);
 check('focus is visible on Log out',await C.js(`(()=>{const b=document.querySelector('.link-button');b.focus();return getComputedStyle(b).outlineStyle!=='none'})()`));
 await submit(C);check('benny is Lola now',await C.js(text("You're in as Lola.")));
 await A.go(settings);check('the empty entry is gone and Lola has a login',await A.js(`!${row('benny')}&&!${row('Lola')}.textContent.includes('No login')`));

 // An account with games of its own is refused.
 const nonoy=await issue('Nonoy');const D=await page();await login(D,'dana');await D.go(nonoy);
 check('an account with records is refused with the reason and no button',await D.js(text('Two records cannot be joined yet.'))&&await D.js(`!document.querySelector('main form')`));
 for(const w of [320,390]){await D.size(w);check(`refusal fits ${w}`,await D.js(fits(w)));}await D.shot('claim-refused-390');
 await D.go(tito);check('a used link does not work',await D.js(text("This claim link doesn't work"))&&await D.js(text('already been used')));await D.shot('claim-dead-390');

 // Without JavaScript.
 const pedro=await issue('Pedro');const E=await page();await login(E,'eli');await send('Emulation.setScriptExecutionDisabled',{value:true},E.s);await E.go(pedro);
 check('no JavaScript: the token and the page are whole',await E.js(`getComputedStyle(document.querySelector('[data-pop]')).opacity==='1'`)&&await E.js(text('Claim Pedro')));
 await submit(E);check('no JavaScript: the claim works',await E.js(text("You're in as Pedro.")));
 writeFileSync(`${OUT}/claim.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
