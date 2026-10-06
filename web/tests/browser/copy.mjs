import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-copy-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
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
await size(390);return {s,js,go,click,shot,size,key,browserContextId};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
// WCAG contrast of an element's text against the page ground, via canvas so oklch resolves.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
try {
 const submit=P=>P.click(`document.querySelector('form.form-section [type=submit]')`);
 const A=await page();
 await send('Browser.grantPermissions',{permissions:['clipboardReadWrite','clipboardSanitizedWrite'],browserContextId:A.browserContextId});
 await send('Emulation.setFocusEmulationEnabled',{enabled:true},A.s);
 await A.go('/accounts/login/');await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await submit(A);
 const groups=await A.js(`[...new Set([...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).filter(h=>new RegExp('^/g/[0-9]+/$').test(h)))]`);
 let settings;for(const g of groups){settings=g+'?view=settings';await A.go(settings);if(await A.js(`!!document.querySelector('form[action$="/reset-link/"]')`))break;}
 check('no copy button before a link is created',await A.js(`!document.querySelector('[data-copy]')`));
 const make={invite:`document.querySelector('form[action$="/invites/new/"] button')`,reset:`document.querySelector('form[action$="/reset-link/"] button')`};
 const btn=id=>`document.querySelector('[data-copy="${id}"]')`,fld=id=>`document.getElementById('${id}')`,stat=id=>`document.querySelector('[data-copy-status="${id}"]')`;
 for(const [kind,id,path] of [['invite','new-invite-link','/join/'],['reset','new-reset-link','/accounts/reset/']]){
  await A.size(390);await A.go(settings);if(kind==='reset')await A.js(`${make.reset}.closest('details').open=true`);await A.click(make[kind]);
  const shown=await A.js(`${fld(id)}.value`);
  check(`${kind}: the button is shown inside the field's right edge`,await A.js(`(()=>{const b=${btn(id)},f=${fld(id)};if(b.hidden||b.textContent!=='Copy')return false;const r=b.getBoundingClientRect(),q=f.getBoundingClientRect();return r.right<=q.right+.5&&r.left>=q.left&&r.top>=q.top-.5&&r.bottom<=q.bottom+.5&&parseFloat(getComputedStyle(f).paddingRight)>=r.width})()`));
  check(`${kind}: 48px target`,await A.js(`(()=>{const r=${btn(id)}.getBoundingClientRect();return r.height>=48&&r.width>=48})()`));
  check(`${kind}: contrast of Copy`,await A.js(contrast(`[data-copy="${id}"]`))>=4.5);
  for(const width of [320,390,1280]){await A.size(width);check(`${kind}: fits ${width}`,await A.js(`document.documentElement.scrollWidth<=${width}&&${btn(id)}.getBoundingClientRect().right<=${width}`));await A.shot(`copy-${kind}-${width}`);}
  await A.size(390);
  await A.js(`navigator.clipboard.writeText('something else')`);
  await A.js(`${btn(id)}.click()`);await sleep(250);
  check(`${kind}: the whole address is on the clipboard`,shown.includes(path)&&await A.js(`navigator.clipboard.readText()`)===shown);
  check(`${kind}: says Copied and announces it without a visible line`,await A.js(`${btn(id)}.textContent==='Copied'&&${stat(id)}.textContent==='Link copied.'&&${stat(id)}.classList.contains('visually-hidden')&&${stat(id)}.getAttribute('role')==='status'`));
  check(`${kind}: contrast of Copied`,await A.js(contrast(`[data-copy="${id}"]`))>=4.5);await A.shot(`copy-${kind}-copied-390`);
  await sleep(2100);check(`${kind}: returns to Copy`,await A.js(`${btn(id)}.textContent==='Copy'&&!${btn(id)}.dataset.copied`));
  // A refusal by the browser.
  await A.js(`window.__real=navigator.clipboard.writeText.bind(navigator.clipboard);navigator.clipboard.writeText=()=>Promise.reject(new Error('refused'))`);
  await A.js(`${btn(id)}.click()`);await sleep(250);
  check(`${kind}: a refusal never says Copied, selects the address and says so`,await A.js(`(()=>{const f=${fld(id)},s=${stat(id)};return ${btn(id)}.textContent==='Copy'&&document.activeElement===f&&f.selectionStart===0&&f.selectionEnd===f.value.length&&s.textContent==='Could not copy. The link is selected: copy it from the menu.'&&!s.classList.contains('visually-hidden')&&s.getBoundingClientRect().height>0})()`));
  check(`${kind}: contrast of the refusal line`,await A.js(contrast(`[data-copy-status="${id}"]`))>=4.5);
  check(`${kind}: refusal fits`,await A.js(`document.documentElement.scrollWidth<=390`));await A.shot(`copy-${kind}-refused-390`);
  await A.js(`navigator.clipboard.writeText=window.__real`);await A.js(`${btn(id)}.click()`);await sleep(250);
  check(`${kind}: a later success clears the refusal line`,await A.js(`${btn(id)}.textContent==='Copied'&&${stat(id)}.classList.contains('visually-hidden')`));
 }
 // A browser with no clipboard at all (an http address).
 await A.go(settings);await A.click(make.invite);
 await A.js(`Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true})`);await A.js(`${btn('new-invite-link')}.click()`);await sleep(150);
 check('no clipboard: refusal line, address selected',await A.js(`!${stat('new-invite-link')}.classList.contains('visually-hidden')&&document.activeElement===${fld('new-invite-link')}`));
 // Leaving the screen and coming back in the app does not double the listener.
 await A.go(settings);await A.click(make.invite);
 await A.js(`window.__n=0;const w=navigator.clipboard.writeText.bind(navigator.clipboard);navigator.clipboard.writeText=t=>{window.__n++;return w(t)};window.pokerPage.stop();window.pokerPage.start()`);
 await A.js(`${btn('new-invite-link')}.click()`);await sleep(250);
 check('one copy per tap after the page scripts restart',await A.js(`window.__n===1`));
 check('keyboard: the button takes focus with the ring',await A.js(`(()=>{const b=${btn('new-invite-link')};b.focus();return document.activeElement===b&&b.matches(':focus-visible')?getComputedStyle(b).outlineStyle!=='none':document.activeElement===b})()`));
 // Without JavaScript.
 const C=await page();await C.go('/accounts/login/');await C.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await submit(C);
 await send('Emulation.setScriptExecutionDisabled',{value:true},C.s);await C.go(settings);await C.click(make.invite);
 check('no JavaScript: no visible button, the field still holds the link',await C.js(`!${btn('new-invite-link')}.getClientRects().length&&${fld('new-invite-link')}.value.includes('/join/')`));await C.shot('copy-nojs-390');
 writeFileSync(`${OUT}/copy.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
