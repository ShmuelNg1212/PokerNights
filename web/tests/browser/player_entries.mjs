import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-entries-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const M=JSON.parse(readFileSync('/private/tmp/pn-entries-manifest.json','utf8'));
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
// Players record their own rebuy and send their own final count; the host confirms. Seed a fresh temporary
// database with seed.py and seed_player_entries.py, serve it, then run. Three browsers: the host, maria and Ben.
const SET='/s/'+M.set+'/';
const until=async(P,expr,ms=9000)=>{const end=Date.now()+ms;while(Date.now()<end){if(await P.js(expr))return true;await sleep(250)}return false};
const logIn=async(P,name)=>{await P.go('/accounts/login/');await P.js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91'`);await P.click(`document.querySelector('form.form-section [type=submit]')`);await P.go(SET);await P.js(`window.__same=true`)};
const row=pk=>`document.querySelector('[data-watch$="-${pk}"]')`;
const rowText=pk=>`${row(pk)}.innerText`;
const type=(P,sel,v)=>P.js(`(()=>{const el=document.querySelector(${JSON.stringify(sel)});el.value=${JSON.stringify(v)};el.dispatchEvent(new Event('input',{bubbles:true}))})()`);
const sheetSubmit=`document.querySelector('dialog[open] form [type=submit]')`;
try {
 const H=await page(),P=await page(),B=await page();
 await logIn(H,'hana');await logIn(P,'maria');await logIn(B,'ben');
 // --- A player's own rebuy.
 check('player: one Rebuy button, on their own row',await P.js(`(()=>{const b=[...document.querySelectorAll('.buy-opener')].filter(x=>x.getClientRects().length);return b.length===1&&b[0].closest('[data-watch]').dataset.watch==='player-${M.maria}'&&b[0].textContent.trim()==='Rebuy'&&b[0].getBoundingClientRect().height>=48})()`));
 check('player: no cash-out or other player action',await P.js(`!document.querySelector('.cash-opener')&&!document.querySelector('form[action*="cashouts"]')&&!document.querySelector('form[action*="/reverse/"]')`));
 for(const width of [320,390,1280]){await P.size(width);check('player set page fits '+width,await P.js(`document.documentElement.scrollWidth<=${width}`));await P.shot('entries-player-running-'+width);}
 await P.size(390);
 await P.click(`document.querySelector('.buy-opener')`);
 check('player: the sheet is the host\'s sheet',await P.js(`(()=>{const d=document.querySelector('dialog[open]');return !!d&&d.innerText.includes('Allowed:')&&d.querySelectorAll('.quick-amounts button').length===4&&${sheetSubmit}.textContent.trim()==='Confirm rebuy'&&d.querySelector('[name=seen_count]').value==='1'})()`));
 await P.shot('entries-player-sheet-390');
 await P.click(sheetSubmit);
 check('player: the rebuy shows at once, in place',await until(P,`${rowText(M.maria)}.includes('1 buy-in + 1 rebuy')&&!document.querySelector('dialog[open]')&&window.__same===true`,3000));
 check('host sees it without a reload, marked',await until(H,`${rowText(M.maria)}.includes('1 buy-in + 1 rebuy')&&${rowText(M.maria)}.includes('₱2,000')&&window.__same===true`));
 check('host: the row says Rebuy added',await H.js(`[...${row(M.maria)}.querySelectorAll('.change-label')].some(b=>!b.hidden&&b.textContent==='Rebuy added')`));
 check('the other player sees it too',await until(B,`${rowText(M.maria)}.includes('1 buy-in + 1 rebuy')&&window.__same===true`));
 await H.shot('entries-host-after-rebuy-390');
 // --- The same rebuy from two phones.
 await H.click(`${row(M.maria)}.querySelector('.buy-opener')`);
 check('host sheet remembers two buy-ins',await H.js(`document.querySelector('dialog[open] [name=seen_count]').value==='2'`));
 await P.click(`document.querySelector('.buy-opener')`);await P.click(sheetSubmit);
 await until(P,`${rowText(M.maria)}.includes('2 rebuys')`,3000);
 await until(H,`${rowText(M.maria)}.includes('2 rebuys')`);
 check('host sheet stays open through the update',await H.js(`!!document.querySelector('dialog[open]')`));
 await H.click(sheetSubmit);
 check('host: the doubled rebuy is refused and says who recorded the other',await until(H,`(()=>{const d=document.querySelector('dialog[open]');return !!d&&d.innerText.includes('maria already has a new rebuy (₱1,000, recorded by maria at ')&&d.innerText.includes('Nothing was added.')})()`,3000));
 check('nothing was added',await H.js(`${rowText(M.maria)}.includes('2 rebuys')`));await H.shot('entries-host-doubled-390');
 await H.click(sheetSubmit);
 check('host: a second, deliberate try is recorded',await until(H,`${rowText(M.maria)}.includes('3 rebuys')&&!document.querySelector('dialog[open]')`,3000));
 // --- Without JavaScript the player's rebuy is a plain form.
 const N=await page();await N.go('/accounts/login/');await N.js(`document.querySelector('[name=username]').value='ben';document.querySelector('[name=password]').value='tablestakes-91'`);await N.click(`document.querySelector('form.form-section [type=submit]')`);
 await send('Emulation.setScriptExecutionDisabled',{value:true},N.s);await N.go(SET);
 check('no JavaScript: one plain rebuy form, on the own row',await N.js(`document.querySelectorAll('form[action$="/buyins/add/"]').length===1&&!!${row(M.ben)}.querySelector('form[action$="/buyins/add/"]')`));
 await N.js(`${row(M.ben)}.querySelector('details[data-sheet-source^="buy-"]').open=true`);await N.click(`${row(M.ben)}.querySelector('form[action$="/buyins/add/"] [type=submit]')`);
 check('no JavaScript: the rebuy is recorded',await N.js(`${rowText(M.ben)}.includes('1 buy-in + 1 rebuy')`));
 // --- The host ends play; players enter their own counts.
 await H.click(`document.querySelector('button[name=action][value=end]')`);
 check('player: a field for their own count appears',await until(P,`!!document.querySelector('#own-count')&&document.querySelectorAll('form[action$="/counts/enter/"]').length===1&&!!document.querySelector('.own-count-lead #own-count')`));
 await P.js(`window.__same=true`);await B.go(SET);await B.js(`window.__same=true`);await H.go(SET);await H.js(`window.__same=true`);
 for(const width of [320,390,1280]){await P.size(width);
  check('player count-up fits '+width,await P.js(`document.documentElement.scrollWidth<=${width}`));
  check('player count field and button are 48px '+width,await P.js(`['#own-count','.own-count [type=submit]'].every(s=>document.querySelector(s).getBoundingClientRect().height>=48)`));
  await P.shot('entries-player-count-'+width);}
 await P.size(390);
 check('player: label, help and no host field',await P.js(`document.querySelector('label[for=own-count]').textContent.trim()==='Your count (₱)'&&document.querySelector('#own-count-help').textContent.includes('The host confirms it.')&&!document.querySelector('[data-count-input]')&&!document.querySelector('#counts-form')`));
 check('contrast of the help',await P.js(contrast('#own-count-help'))>=4.5);
 // On a phone the app's own number keys serve the field (numpad.mjs covers the keys themselves).
 await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},P.s);await P.go(SET);
 await P.js(`document.querySelector('#own-count').focus()`);await sleep(500);
 check('player: the app\'s number keys open for the field and name it',await P.js(`matchMedia('(pointer: coarse)').matches&&document.querySelector('#own-count').getAttribute('inputmode')==='none'&&document.documentElement.classList.contains('numpad-open')&&!!document.querySelector('.numpad-panel')&&document.querySelector('.numpad-panel').innerText.includes('Your count')`));
 check('player: the field is not under the keys',await P.js(`document.querySelector('#own-count').getBoundingClientRect().bottom<=document.querySelector('.numpad-panel').getBoundingClientRect().top`));
 await P.shot('entries-player-numpad-390');
 await send('Emulation.setTouchEmulationEnabled',{enabled:false},P.s);await P.go(SET);await P.js(`window.__same=true`);
 await type(P,'#own-count','1,450');await P.click(`document.querySelector('.own-count [type=submit]')`);
 check('player: sent, waiting for the host',await until(P,`document.querySelector('.own-count-lead').textContent.replace(/\\s+/g,' ').includes('You entered ₱1,450. Waiting for the host to confirm.')&&!!document.querySelector('.own-count-change')&&!document.querySelector('.own-count-change').open&&window.__same===true`,3000));
 check('player: the row says Entered, not confirmed',await P.js(`!!${row(M.maria)}.querySelector('[data-status=entered]')&&/ntered\\s*₱1,450/.test(${rowText(M.maria)})`));
 check('contrast of the waiting line',await P.js(contrast('.own-count-state'))>=4.5);await P.shot('entries-player-entered-390');
 check('host sees the entered count without a reload',await until(H,`/ntered\\s*₱1,450/.test(${rowText(M.maria)})&&window.__same===true`));
 check('host: the field hints the number and stays empty',await H.js(`(()=>{const f=document.querySelector('#count-${M.maria}');return f.value===''&&f.placeholder==='1450'&&f.dataset.entered==='145000'&&!!document.querySelector('[name=entry_${M.maria}]')&&document.querySelector('#count-entered-${M.maria}').textContent.includes('maria entered ₱1,450. Leave the field empty to accept it, or type another number.')})()`));
 check('host: the main button offers to confirm it, and the total counts it as a preview',await H.js(`(()=>{const b=document.querySelector('[data-confirm-typed]');return !b.hidden&&b.textContent==='Confirm 1 count'&&document.querySelector('[data-count-label]').textContent==="Preview · players' counts"&&document.querySelector('[data-count-accounted]').textContent==='₱1,450'})()`));
 check('contrast of the host hint',await H.js(contrast('#count-entered-'+M.maria))>=4.5);
 for(const width of [320,390,1280]){await H.size(width);check('host count-up fits '+width,await H.js(`document.documentElement.scrollWidth<=${width}`));await H.shot('entries-host-entered-'+width);}
 await H.size(390);
 check('the other player sees it and has their own field only',await until(B,`/ntered\\s*₱1,450/.test(${rowText(M.maria)})&&document.querySelectorAll('#own-count').length===1&&!!document.querySelector('.own-count-lead #own-count')&&window.__same===true`));
 // --- Typing survives the other side's update.
 await type(H,'#count-'+M.anton,'650');
 check('host: typed and entered are confirmed together',await H.js(`document.querySelector('[data-confirm-typed]').textContent==='Confirm 2 counts'&&document.querySelector('[data-count-label]').textContent==='Preview · unsaved counts'`));
 await P.js(`document.querySelector('.own-count-change').open=true`);await type(P,'#own-count','1,500');await P.click(`document.querySelector('.own-count [type=submit]')`);
 await until(P,`${rowText(M.maria)}.includes('You entered ₱1,500.')`,3000);
 check('host: the changed number arrives, the typed count stays',await until(H,`document.querySelector('#count-${M.maria}').placeholder==='1500'&&document.querySelector('#count-${M.anton}').value==='650'&&document.querySelector('[data-confirm-typed]').textContent==='Confirm 2 counts'&&document.querySelector('[data-count-accounted]').textContent==='₱2,150'`));
 await P.js(`document.querySelector('.own-count-change').open=true`);await type(P,'#own-count','77');
 await type(B,'#own-count','900');await B.click(`document.querySelector('.own-count [type=submit]')`);
 check('player: half-typed number and open Change survive another player\'s update',await until(P,`/ntered\\s*₱900/.test(${rowText(M.ben)})&&document.querySelector('#own-count').value==='77'&&document.querySelector('.own-count-change').open&&window.__same===true`));
 // --- The host types over one number and accepts the other.
 await until(H,`/ntered\\s*₱900/.test(${rowText(M.ben)})`);
 await type(H,'#count-'+M.maria,'1,400');
 check('host: three counts to confirm',await H.js(`document.querySelector('[data-confirm-typed]').textContent==='Confirm 3 counts'&&document.querySelector('[data-count-accounted]').textContent==='₱2,950'`));
 await H.shot('entries-host-before-confirm-390');
 await H.click(`document.querySelector('[data-confirm-typed]')`);
 check('host: confirmed as typed for maria, as entered for Ben',await until(H,`${rowText(M.maria)}.includes('Counted ₱1,400')&&${rowText(M.ben)}.includes('Counted ₱900')&&${rowText(M.anton)}.includes('Counted ₱650')&&!document.querySelector('[data-status=entered]')`,4000));
 check('host: the confirmed total is the server\'s',await H.js(`document.querySelector('[data-count-label]').textContent==='Confirmed counts'&&document.querySelector('[data-count-accounted]').textContent==='₱2,950'`));
 check('player: told the host confirmed another number, field gone',await until(P,`document.querySelector('.own-count-lead').textContent.replace(/\\s+/g,' ').includes('The host confirmed ₱1,400. You entered ₱1,500.')&&!document.querySelector('#own-count')`));
 check('other player: told the host confirmed theirs',await until(B,`document.querySelector('.own-count-lead').textContent.replace(/\\s+/g,' ').includes('The host confirmed your count.')&&!document.querySelector('#own-count')`));
 await P.shot('entries-player-confirmed-390');
 check('no script error on any page',(await Promise.all([H,P,B].map(X=>X.js(`!(window.__errors&&window.__errors.length)`)))).every(Boolean));
 writeFileSync(`${OUT}/player_entries.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
