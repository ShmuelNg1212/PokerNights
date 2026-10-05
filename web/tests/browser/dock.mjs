import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-dock-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:(process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765')+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

// Collapsible host dock. Run after seed.py, seed_end_set.py, seed_night.py, seed_remaining.py, seed_opening.py and seed_counts.py.
const M=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8')),C=JSON.parse(readFileSync('/private/tmp/pn-counts-manifest.json','utf8'));
const SETS={draft:4,open:M.live.set,running:3,counting:C.php,long:11};
const LAST=Object.fromEntries(['draft','open','running','counting','long'].map(k=>[k,'#main > p.center a']));
const size=(A,width)=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
const dock=`document.querySelector('.host-controls')`,toggle=`document.querySelector('.dock-toggle')`;
const clears=sel=>`(()=>{window.scrollTo(0,document.documentElement.scrollHeight);const all=document.querySelectorAll(${JSON.stringify(sel)});const el=all[all.length-1];return !el||el.getBoundingClientRect().bottom<=${dock}.getBoundingClientRect().top})()`;
const shown=`[...${dock}.children].filter(el=>el.getClientRects().length).map(el=>el.className)`;
try {
 const A=await user('hana');
 await A.go('/s/3/');await A.js(`localStorage.removeItem('rack-dock')`);
 for(const width of [320,390]) {
  await size(A,width);
  for(const [name,id] of Object.entries(SETS)) {
   await A.go(`/s/${id}/`);const tag=`${name} ${width}`;
   check(tag+' starts expanded with toggle',await A.js(`${toggle}.getAttribute('aria-expanded')==='true'&&!${toggle}.hidden&&${shown}.length>1`));
   check(tag+' expanded bar has only its title',await A.js(`!${toggle}.querySelector('.dock-next').getClientRects().length`));
   check(tag+' toggle is a 48px target',await A.js(`${toggle}.getBoundingClientRect().height>=48&&${toggle}.getBoundingClientRect().width>=${width-40}`));
   check(tag+' expanded clears last row',await A.js(clears(LAST[name])));
   check(tag+' expanded fits width',await A.js(`document.documentElement.scrollWidth<=${width}`));
   console.log('  expanded dock height',await A.js(`Math.round(${dock}.getBoundingClientRect().height)`),'padding',await A.js(`getComputedStyle(document.querySelector('.table-page')).paddingBottom`));
   await A.shot(`dock-${name}-${width}-expanded`);
   await A.click(toggle);
   check(tag+' collapsed shows only the bar',await A.js(`${toggle}.getAttribute('aria-expanded')==='false'&&${shown}.length===1&&!document.querySelector('.next-action').getClientRects().length`));
   check(tag+' collapsed bar is small',await A.js(`${dock}.getBoundingClientRect().height<=${name==='long'?96:name==='counting'?76:72}`));
   check(tag+' collapsed bar names the state',await A.js(`${toggle}.querySelector('.dock-next').getClientRects().length>0`));
   check(tag+' collapsed clears last row',await A.js(clears(LAST[name])));
   check(tag+' collapsed fits width',await A.js(`document.documentElement.scrollWidth<=${width}`));
   console.log('  collapsed dock height',await A.js(`Math.round(${dock}.getBoundingClientRect().height)`));
   await A.shot(`dock-${name}-${width}-collapsed`);
   await A.go(`/s/${id}/`);
   check(tag+' collapsed survives reload',await A.js(`${toggle}.getAttribute('aria-expanded')==='false'&&${shown}.length===1`));
   await A.click(toggle);
   check(tag+' expands again',await A.js(`${toggle}.getAttribute('aria-expanded')==='true'&&${shown}.length>1&&localStorage.getItem('rack-dock')===null`));
  }
 }
 await size(A,390);
 // Keyboard: focus ring, activation, and focus kept across a live update made by another session.
 await A.go('/s/3/');await A.js(`${toggle}.focus()`);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9,modifiers:8},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9,modifiers:8},A.s);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);
 check('toggle keyboard focus visible',await A.js(`document.activeElement===${toggle}&&getComputedStyle(${toggle}).outlineWidth==='3px'`));
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r'},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13},A.s);await sleep(200);
 check('Enter collapses',await A.js(`document.documentElement.classList.contains('dock-collapsed')&&${toggle}.getAttribute('aria-expanded')==='false'`));
 const before=await A.js(`document.getElementById('live').dataset.version`);
 const B=await user('hana');await B.go('/s/3/');
 await B.js(`(()=>{const f=document.querySelector('form[action$="/buyins/add/"]');f.querySelector('[name=amount]').value='500';f.submit()})()`);await sleep(6000);
 check('live update arrived',await A.js(`document.getElementById('live').dataset.version`)!==before);
 check('collapsed survives live update',await A.js(`${toggle}.getAttribute('aria-expanded')==='false'&&!${toggle}.hidden&&${shown}.length===1`));
 check('toggle keeps focus across live update',await A.js(`document.activeElement===${toggle}`));
 // Motion: the dock slides between heights; closing keeps the content until the slide ends.
 await A.go('/s/3/');await A.js(`document.activeElement.blur()`);
 check('expanding animates the dock height',await A.js(`(()=>{${toggle}.click();const d=${dock};return d.getAnimations().length===1&&${shown}.length>1&&d.getBoundingClientRect().height<120})()`));await sleep(600);
 check('expanded at rest',await A.js(`${dock}.getAnimations().length===0&&${dock}.style.overflow===''&&${dock}.getBoundingClientRect().height>120`));
 check('collapsing keeps content while sliding',await A.js(`(()=>{${toggle}.click();const d=${dock};return d.getAnimations().length===1&&document.documentElement.classList.contains('dock-closing')&&${shown}.length>1&&${toggle}.getAttribute('aria-expanded')==='false'})()`));await sleep(600);
 check('collapsed at rest',await A.js(`${dock}.getAnimations().length===0&&!document.documentElement.classList.contains('dock-closing')&&${shown}.length===1`));
 check('quick double tap ends expanded',await A.js(`(()=>{${toggle}.click();${toggle}.click();${toggle}.click();return true})()`)&&(await sleep(600),await A.js(`${dock}.getAnimations().length===0&&!document.documentElement.classList.contains('dock-closing')&&${shown}.length>1&&${toggle}.getAttribute('aria-expanded')==='true'`)));
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
 check('reduced motion: no slide, immediate state',await A.js(`(()=>{${toggle}.click();return ${dock}.getAnimations().length===0&&${shown}.length===1&&getComputedStyle(${toggle}.querySelector('.icon')).transitionDuration==='0s'})()`));
 await send('Emulation.setEmulatedMedia',{features:[]},A.s);
 // Options under More host controls are buttons.
 await A.click(toggle);await A.click(`document.querySelector('.host-more > summary')`);
 check('more-controls options are 48px bordered buttons',await A.js(`(()=>{const items=[...document.querySelectorAll('.host-more > a.btn, .host-more > details > summary')];return items.length>=2&&items.every(el=>{const r=el.getBoundingClientRect(),c=getComputedStyle(el);return r.height>=48&&c.borderTopWidth==='1px'&&r.width>=${390-40}})})()`));
 check('options are spaced apart',await A.js(`(()=>{const items=[...document.querySelector('.host-more').children].filter(el=>el.tagName!=='SUMMARY'&&el.getClientRects().length);return items.every((el,i)=>!i||el.getBoundingClientRect().top-items[i-1].getBoundingClientRect().bottom>=8)})()`));
 await A.shot('dock-more-controls-390');
 await A.click(`[...document.querySelectorAll('.host-more details > summary')][0]`);await A.shot('dock-more-cancel-open-390');
 await A.click(`[...document.querySelectorAll('.host-more details > summary')][0]`);await A.click(`document.querySelector('.host-more > summary')`);await A.click(toggle);
 // Collapsed choice carries across states: open set → start → end play.
 await A.go(`/s/${M.default.set}/`);
 check('open set collapsed, next step named',await A.js(`${shown}.length===1&&${toggle}.textContent.includes('Next: Start the set')`));
 await A.click(toggle);await A.click(`document.querySelector('button[value=start]')`);await A.click(toggle);
 check('running names end play',await A.js(`${shown}.length===1&&${toggle}.textContent.includes('Next: End play and count up')`));
 await A.click(toggle);await A.click(`document.querySelector('button[value=end]')`);await A.click(toggle);
 check('count-up collapsed after end play',await A.js(`${shown}.length===1&&!!document.querySelector('[data-dock-status]')`));
 // Count-up: the collapsed bar follows the typed counts.
 await A.go(`/s/${C.php}/`);const saved=await A.js(`document.querySelector('[data-dock-status]').textContent`);
 await A.js(`(()=>{const f=[...document.querySelectorAll('[data-count-input]')].find(f=>f.dataset.saved==='');f.value='1000';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('bar verdict follows typing',await A.js(`document.querySelector('[data-dock-status]').textContent==='All counts match buy-ins.'&&document.querySelector('[data-dock-coverage]').textContent==='0 still to count.'`)&&saved!=='All counts match buy-ins.');
 check('bar verdict equals full preview',await A.js(`document.querySelector('[data-dock-status]').textContent===document.querySelector('[data-count-preview] [data-count-status]').textContent`));
 await A.shot('dock-counting-typed-collapsed');
 await A.js(`(()=>{const f=[...document.querySelectorAll('[data-count-input]')].find(f=>f.dataset.saved==='');f.value='9x';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('bar shows invalid preview',await A.js(`document.querySelector('[data-dock-status]').textContent.startsWith('Preview unavailable')`));
 // Desktop: no toggle, and a stored collapsed choice changes nothing.
 await size(A,1280);await A.go('/s/3/');
 check('desktop has no toggle and full controls',await A.js(`localStorage.getItem('rack-dock')==='collapsed'&&!${toggle}.getClientRects().length&&!!document.querySelector('.next-action').getClientRects().length&&!!document.querySelector('.host-more').getClientRects().length`));
 await A.shot('dock-running-1280');
 await size(A,390);await A.go('/s/3/');await A.click(toggle);
 // Reduced motion and storage refusal.
 const {identifier}=await send('Page.addScriptToEvaluateOnNewDocument',{source:`Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})`},A.s);
 await A.go('/s/3/');await A.click(toggle);
 check('works with storage refused',await A.js(`${toggle}.getAttribute('aria-expanded')==='false'&&${shown}.length===1`));
 await A.go('/s/3/');check('refused storage forgets',await A.js(`${toggle}.getAttribute('aria-expanded')==='true'`));
 await send('Page.removeScriptToEvaluateOnNewDocument',{identifier},A.s);
 // Without JavaScript: no toggle, expanded dock, native action works.
 await A.go('/s/3/');await A.click(toggle);
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go('/s/3/');
 check('no JavaScript: no toggle, dock expanded',await A.js(`!${toggle}.getClientRects().length&&!!document.querySelector('.next-action').getClientRects().length`));
 check('no JavaScript: last row clears dock',await A.js(clears('.player-list')));
 await A.shot('dock-running-390-nojs');
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
 // iPhone keyboard: a stand-in visual viewport reports a 336px keyboard over the 844px page.
 const fake=await send('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const v=new EventTarget();Object.assign(v,{width:innerWidth,height:844,offsetTop:0,offsetLeft:0,scale:1});Object.defineProperty(window,'visualViewport',{value:v,configurable:true});window.__kb=h=>{v.height=844-h;v.dispatchEvent(new Event('resize'))}})()`},A.s);
 const bottom=`Math.round(${dock}.getBoundingClientRect().bottom)`,field=`[...document.querySelectorAll('[data-count-input]')].find(f=>f.dataset.saved==='')`;
 const kb=async h=>{await A.js(`__kb(${h})`);await sleep(150)};
 await A.go(`/s/${C.php}/`);await A.js(`localStorage.removeItem('rack-dock')`);await A.go(`/s/${C.php}/`);
 check('keyboard closed: dock at the bottom, expanded',await A.js(`${bottom}===844&&${shown}.length>1&&!document.documentElement.classList.contains('kb-open')`));
 await A.js(`${field}.focus()`);await kb(336);
 check('keyboard up: dock sits on the keyboard',await A.js(`${bottom}===508`));
 check('keyboard up: dock is the bar',await A.js(`${shown}.length===1&&${toggle}.getAttribute('aria-expanded')==='false'&&${dock}.getBoundingClientRect().height<=72`));
 check('keyboard up: bar shows the live count and verdict',await A.js(`!!document.querySelector('[data-dock-accounted]').getClientRects().length&&!!document.querySelector('[data-dock-status]').getClientRects().length`));
 check('keyboard up: typed field is not covered',await A.js(`${field}.getBoundingClientRect().bottom<=${dock}.getBoundingClientRect().top`));
 check('keyboard up: saved choice untouched',await A.js(`localStorage.getItem('rack-dock')===null&&!document.documentElement.classList.contains('dock-collapsed')`));
 const typedBefore=await A.js(`document.querySelector('[data-dock-accounted]').textContent`);
 await A.js(`(()=>{const f=${field};f.value='1000';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('keyboard up: live count follows typing',await A.js(`document.querySelector('[data-dock-accounted]').textContent===document.querySelector('[data-count-preview] [data-count-accounted]').textContent`)&&typedBefore!==await A.js(`document.querySelector('[data-dock-accounted]').textContent`));
 await A.shot('dock-counting-keyboard');
 const last=`[...document.querySelectorAll('[data-count-input]')].pop()`;await A.js(`window.scrollTo(0,0);${last}.focus({preventScroll:true});${last}.scrollIntoView({block:'end'})`);await sleep(250);
 check('keyboard up: a field under the bar is moved clear',await A.js(`${last}.getBoundingClientRect().bottom<=${dock}.getBoundingClientRect().top`));
 await A.click(toggle);
 check('keyboard up: tapping the bar leaves the field and keeps the choice',await A.js(`!document.activeElement.matches('[data-count-input]')&&localStorage.getItem('rack-dock')===null`));
 await kb(0);
 check('keyboard closed again: back at the bottom, expanded',await A.js(`${bottom}===844&&${shown}.length>1&&${toggle}.getAttribute('aria-expanded')==='true'&&!document.documentElement.style.getPropertyValue('--kb')`));
 await A.click(toggle);await A.js(`${field}.focus()`);await kb(336);
 check('collapsed dock also rides the keyboard',await A.js(`${bottom}===508&&${shown}.length===1`));
 await kb(0);check('collapsed dock returns collapsed',await A.js(`${bottom}===844&&${shown}.length===1&&localStorage.getItem('rack-dock')==='collapsed'`));
 await A.click(toggle);
 await A.js(`${field}.focus();visualViewport.scale=2`);await kb(336);check('zoomed page: dock does not move',await A.js(`${bottom}===844`));
 await A.js(`visualViewport.scale=1`);await kb(50);check('a 50px change is not a keyboard',await A.js(`${bottom}===844&&!document.documentElement.classList.contains('kb-open')`));
 await kb(0);
 // Typing in a field inside the dock keeps the dock expanded, above the keyboard and on screen.
 await A.go('/s/3/');await A.js(`${dock}.querySelectorAll('details').forEach(d=>d.open=true)`);await sleep(200);
 const inner=`${dock}.querySelector('input:not([type=hidden]):not([type=checkbox]),select,textarea')`;
 if(await A.js(`!!${inner}`)){await A.js(`${inner}.focus()`);await kb(336);
  check('field in the dock: dock expanded above the keyboard',await A.js(`${bottom}===508&&${shown}.length>1&&${dock}.getBoundingClientRect().top>=0`));
  await A.shot('dock-running-keyboard-inner');await kb(0);} else check('field in the dock exists',false);
 // Leaving the set page clears the keyboard state; coming back works once.
 await A.go(`/s/${C.php}/`);await A.js(`${field}.focus()`);await kb(336);
 await A.js(`Turbo.visit('/')`);await sleep(900);
 check('leaving clears the keyboard state',await A.js(`!document.documentElement.classList.contains('kb-open')&&!document.documentElement.classList.contains('kb-bar')&&!document.documentElement.style.getPropertyValue('--kb')`));
 await A.js(`__kb(0);Turbo.visit('/s/${C.php}/')`);await sleep(900);await A.js(`${field}.focus()`);await kb(336);
 check('returning: dock rides the keyboard again',await A.js(`${bottom}===508&&${shown}.length===1`));
 await kb(0);await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:fake.identifier},A.s);
 const none=await send('Page.addScriptToEvaluateOnNewDocument',{source:`Object.defineProperty(window,'visualViewport',{value:undefined});window.__errors=[];addEventListener('error',e=>__errors.push(e.message))`},A.s);
 await A.go(`/s/${C.php}/`);await A.click(toggle);await A.click(toggle);
 check('no visual viewport: no error, dock as before',await A.js(`__errors.length===0&&${bottom}===844&&${shown}.length>1`));
 await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:none.identifier},A.s);
 // A player has no dock.
 const P=await user('ben');await P.go('/s/3/');check('player has no dock or toggle',await P.js(`!document.querySelector('.host-controls')&&!document.querySelector('.dock-toggle')`));
 writeFileSync(`${OUT}/dock.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
