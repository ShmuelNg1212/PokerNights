// Count-up as the host works through it. Run after seed.py and seed_count_flow.py on a fresh temporary database.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-count-flow-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir=/private/tmp/pn-count-flow-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 // A phone: a finger is the main pointer. A computer: a mouse.
 const phone=async(width=390,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:true},s);await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s)};
 const computer=async()=>{await send('Emulation.setTouchEmulationEnabled',{enabled:false},s);await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},s)};
 const point=async expr=>js(`(()=>{const el=${expr};el.scrollIntoView({block:'center'});const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 const down=async expr=>{const p=await point(expr);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},s);return p};
 const up=async()=>{await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},s)};
 const tap=async(expr,pause=40)=>{await down(expr);await up();await sleep(pause)};
 const shot=async name=>{await js('document.fonts.ready.then(()=>1)');const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await phone();
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,phone,computer,tap,down,up,shot};
}
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const M=JSON.parse(readFileSync('/private/tmp/pn-count-flow-manifest.json','utf8'));
const R=`document.documentElement`,DOCK=`document.querySelector('.host-controls')`,PANEL=`document.querySelector('.numpad-panel')`,PAD=`document.querySelector('.numpad')`;
const fields=`[...document.querySelectorAll('[data-count-input]')]`,field=i=>`${fields}[${i}]`;
const key=k=>`${PAD}.querySelector('[data-key="${k}"]')`;
const shownIn=sel=>`[...document.querySelectorAll(${JSON.stringify(sel)})].filter(e=>e.getClientRects().length&&(!e.checkVisibility||e.checkVisibility()))`;
const primaries=`${shownIn('#live .btn-primary')}.map(e=>e.textContent.trim().replace(/\\s+/g,' '))`;
// Text against the nearest painted background, through a canvas so any colour syntax is read.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d',{willReadFrequently:true});const rgb=v=>{c.clearRect(0,0,1,1);c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)};return .2126*f(r)+.7152*f(g)+.0722*f(b)};
 const el=document.querySelector(${JSON.stringify(sel)});if(!el)return null;let bg=null,n=el;while(n&&n.nodeType===1){const v=rgb(getComputedStyle(n).backgroundColor);if(v[3]>250){bg=v;break}n=n.parentElement}bg=bg||rgb(getComputedStyle(document.body).backgroundColor);const a=lum(rgb(getComputedStyle(el).color)),b=lum(bg);return Math.round((Math.max(a,b)+.05)/(Math.min(a,b)+.05)*100)/100})()`;
try {
 const A=await user('hana');
 const type=async keys=>{for(const k of keys)await A.tap(key(k))};
 await A.go(`/s/${M.eight}/`);await A.js(`localStorage.removeItem('rack-dock');sessionStorage.clear()`);await A.go(`/s/${M.eight}/`);

 // --- The screen: players first, one total.
 check('document order: overview, players, host action, totals, balance',await A.js(`[...document.querySelector('.count-layout').children].map(e=>e.className.split(' ')[0]).join()`)==='felt,count-workspace,host-controls,count-facts,end-balance');
 check('headings go down one level at a time',await A.js(`(()=>{const l=${shownIn('#live h1,#live h2,#live h3,#live h4')}.map(h=>+h.tagName[1]);return l[0]===1&&l.every((v,i)=>!i||v<=l[i-1]+1)})()`));
 check('eight count fields, none with a button of its own',await A.js(`${fields}.length===8&&!document.querySelector('.count-row [type=submit][form=counts-form]')`));
 check('the first count field is in the first screen, above the bar',await A.js(`${field(0)}.getBoundingClientRect().bottom<=${DOCK}.getBoundingClientRect().top`));
 const rowsAbove=edge=>`[...document.querySelectorAll('.count-row')].filter(r=>{const b=r.getBoundingClientRect();return b.top>=document.querySelector('.site-header').getBoundingClientRect().bottom-1&&b.bottom<=${edge}}).length`;
 const dockTop=`${DOCK}.getBoundingClientRect().top`;
 console.log('  dock height expanded',await A.js(`Math.round(${DOCK}.getBoundingClientRect().height)`),'row height',await A.js(`Math.round(document.querySelector('.count-row').getBoundingClientRect().height)`),'first field top',await A.js(`Math.round(${field(0)}.getBoundingClientRect().top)`));
 check('one running total is shown, in the bar',await A.js(`${shownIn('[data-count-accounted],[data-dock-accounted]')}.length`)===1);
 check('nothing typed, nobody counted: no main button, and the line that says why',await A.js(`${primaries}.length===0&&/Type each player/.test(document.getElementById('batch-why').textContent)`));
 check('"Confirm all counts" is the fallback only',await A.js(`!document.querySelector('.confirm-all').getClientRects().length`));
 check('rake rows are left out when rake is off',await A.js(`!/Collected rake/.test(document.getElementById('live').textContent)`));
 check('a count field is right-aligned like the figures',await A.js(`getComputedStyle(${field(0)}).textAlign`)==='right');
 check('fits 390 wide',await A.js(`${R}.scrollWidth<=390`));
 await sleep(300);await A.shot('count-flow-top-390');
 await A.tap(`document.querySelector('.dock-toggle')`,600);
 check('bar folded: at least three whole rows in the first screen',await A.js(rowsAbove(dockTop))>=3);
 console.log('  dock height folded',await A.js(`Math.round(${DOCK}.getBoundingClientRect().height)`),'rows',await A.js(rowsAbove(dockTop)));
 check('folded bar still shows the total and verdict',await A.js(`${shownIn('.dock-count,.dock-next')}.length===2`));
 await A.tap(`document.querySelector('.dock-toggle')`,600);

 // --- The numpad panel.
 check('count fields no longer call the phone keyboard',await A.js(`${fields}.every(f=>f.getAttribute('inputmode')==='none')`));
 await A.tap(field(0),700);
 check('tapping a field raises the panel and hides the dock',await A.js(`!!${PANEL}&&${R}.classList.contains('numpad-open')&&!${DOCK}.getClientRects().length&&document.activeElement===${field(0)}`));
 check('the panel names the field',await A.js(`${PANEL}.querySelector('[data-numpad-label]').textContent`)==='Final count of Miguel');
 check('the panel shows the running total',await A.js(`/₱100 of ₱9,000 · 8 to count/.test(${PANEL}.querySelector('[data-numpad-note]').textContent)`));
 check('panel keys and buttons are at least 48px',await A.js(`[...${PANEL}.querySelectorAll('button')].every(b=>b.getBoundingClientRect().height>=48&&b.getBoundingClientRect().width>=44)`));
 check('the field is clear of the panel',await A.js(`${field(0)}.getBoundingClientRect().bottom<=${PANEL}.getBoundingClientRect().top`));
 check('numpad open: at least two whole rows above it',await A.js(rowsAbove(`${PANEL}.getBoundingClientRect().top`))>=2);
 console.log('  panel height',await A.js(`Math.round(${PANEL}.getBoundingClientRect().height)`),'rows above',await A.js(rowsAbove(`${PANEL}.getBoundingClientRect().top`)));
 check('the page reserves room for the panel',await A.js(`parseFloat(getComputedStyle(document.querySelector('.page')).paddingBottom)>=${PANEL}.getBoundingClientRect().height`));
 await sleep(300);await A.shot('count-flow-pad-390');
 await type(['9','0','0']);
 check('keys write the count',await A.js(`${field(0)}.value`)==='900');
 check('the panel total follows, labelled Preview',await A.js(`/^Preview · ₱1,000 of ₱9,000 · 7 to count/.test(${PANEL}.querySelector('[data-numpad-note]').textContent)`));
 await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,500);
 check('Next moves to the next player still to count',await A.js(`document.activeElement===${field(1)}&&${PANEL}.querySelector('[data-numpad-label]').textContent==='Final count of Carlo'`));
 await type(['2','0','0','0']);
 await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,200);await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,200);await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,200);await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,200);await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,200);await A.tap(`${PANEL}.querySelector('[data-numpad-next]')`,700);
 check('Next reaches the last player, scrolled clear of the panel',await A.js(`document.activeElement===${field(7)}&&${field(7)}.getBoundingClientRect().bottom<=${PANEL}.getBoundingClientRect().top&&${field(7)}.getBoundingClientRect().top>=document.querySelector('.site-header').getBoundingClientRect().bottom`));
 check('on the last field there is no Next',await A.js(`${PANEL}.querySelector('[data-numpad-next]').hidden`));
 await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,500);
 check('Done puts the panel away and brings the dock back',await A.js(`!${PANEL}&&!${R}.classList.contains('numpad-open')&&${DOCK}.getClientRects().length>0&&document.activeElement!==${field(7)}`));
 check('typed counts: the one main button confirms them',await A.js(`JSON.stringify(${primaries})`)==='["Confirm 2 counts"]');
 check('typed counts: the bar says Preview',await A.js(`document.querySelector('.dock-count').textContent.replace(/\\s+/g,' ').trim()`)==='Preview · ₱3,000 of ₱9,000 bought in');
 check('typed counts: the hint says they are not saved',await A.js(`/not saved until you confirm/.test(document.getElementById('batch-why').textContent)`));
 await A.js(`window.scrollTo(0,0)`);await sleep(300);await A.shot('count-flow-typed-390');
 // An invalid count (from a physical keyboard) blocks the confirm.
 await A.js(`${field(2)}.focus()`);await send('Input.insertText',{text:'9x'},A.s);await A.js(`document.activeElement.blur()`);await sleep(400);
 check('an invalid count disables the confirm and marks the verdict',await A.js(`document.querySelector('[data-confirm-typed]').disabled&&document.querySelector('[data-dock-status]').dataset.tone==='warn'&&${field(2)}.getAttribute('aria-invalid')==='true'`));
 check('the verdict has a mark as well as a colour',await A.js(`getComputedStyle(document.querySelector('[data-dock-status]'),'::before').content!=='none'`));
 await A.js(`${field(2)}.value='';${field(2)}.dispatchEvent(new Event('input',{bubbles:true}))`);
 // Typed counts survive leaving the page.
 await A.js(`Turbo.visit('/')`);await sleep(1000);await A.js(`Turbo.visit('/s/${M.eight}/')`);await sleep(1300);
 check('typed counts survive leaving the page and coming back',await A.js(`${field(0)}.value==='900'&&${field(1)}.value==='2000'`)&&await A.js(`JSON.stringify(${primaries})`)==='["Confirm 2 counts"]');
 // A live update from another host does not disturb the open panel.
 const B=await user('hana');await B.go(`/s/${M.eight}/`);
 await A.tap(field(3),600);await type(['5','0','0']);
 const version=await A.js(`document.getElementById('live').dataset.version`);
 await B.js(`(()=>{const f=document.getElementById('counts-form'),i=document.querySelectorAll('[data-count-input]')[7];i.value='1000';f.requestSubmit()})()`);await sleep(6500);
 check('while a count is typed the live update waits; the panel and the count stay',await A.js(`!!${PANEL}&&${field(3)}.value==='500'&&document.activeElement===${field(3)}`));
 await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,5500);
 check('after Done the update arrives and the typed counts are kept',await A.js(`document.getElementById('live').dataset.version`)!==version&&await A.js(`${field(0)}.value==='900'&&${field(1)}.value==='2000'&&${field(3)}.value==='500'`));
 check('the other host\'s confirmed count shows in its field',await A.js(`${field(7)}.placeholder==='1000'&&${field(7)}.dataset.saved==='100000'&&${field(7)}.getAttribute('inputmode')==='none'`));
 // Tapping away from the field puts the panel away.
 await A.tap(field(4),600);await A.tap(`document.querySelector('.felt h1')`,600);
 check('tapping elsewhere puts the panel away',await A.js(`!${PANEL}`));
 // Confirm the typed counts with the main button.
 await A.tap(`document.querySelector('[data-confirm-typed]')`,1800);
 check('confirming records the counts and the main button becomes the cash-out',await A.js(`JSON.stringify(${primaries})`)==='["Cash out counted players (4)"]'&&await A.js(`${field(0)}.value===''&&${field(0)}.placeholder==='900'`));
 check('nothing typed: the bar is no longer a preview',await A.js(`document.querySelector('[data-dock-prefix]').textContent`)==='');
 check('confirmed fields are still served by the numpad',await A.js(`${fields}.every(f=>f.getAttribute('inputmode')==='none')`));
 await A.js(`window.scrollTo(0,0)`);await sleep(6500);await A.shot('count-flow-ready-390');
 for(const [name,sel] of [['label','.count-entry label'],['confirmed count in its field','.count-entry input'],['row state','.count-state .num'],['bar verdict','[data-dock-status]'],['hint','#batch-why'],['progress','.count-progress']]) {
  const ratio=await A.js(contrast(sel));check(`contrast of the ${name} is at least 4.5 (${ratio})`,ratio>=4.5);
 }
 check('a confirmed count in its field is readable (placeholder colour)',await A.js(`(()=>{const c=document.createElement('canvas').getContext('2d');c.fillStyle=getComputedStyle(${field(0)},'::placeholder').color;return c.fillStyle!==''})()`));

 // --- Motion.
 await A.tap(field(4),60);
 check('the panel rises by transform only',await A.js(`${PANEL}.getAnimations().length===1&&${PANEL}.getAnimations()[0].effect.getKeyframes().every(k=>Object.keys(k).filter(p=>!['offset','easing','composite','computedOffset'].includes(p)).join()==='transform')`));
 await sleep(600);await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,60);
 check('the panel leaves by transform',await A.js(`!!${PANEL}&&${PANEL}.getAnimations().length===1`));
 await sleep(500);check('and is then gone',await A.js(`!${PANEL}`));
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
 await A.tap(field(4),80);
 check('reduced motion: the panel appears at once',await A.js(`!!${PANEL}&&${PANEL}.getAnimations().length===0&&document.getAnimations().length===0`));
 await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,80);
 check('reduced motion: and goes at once',await A.js(`!${PANEL}`));
 await send('Emulation.setEmulatedMedia',{features:[]},A.s);
 // Leaving the page with the panel open.
 await A.tap(field(4),500);await A.js(`Turbo.visit('/')`);await sleep(1000);
 check('leaving the page removes the panel',await A.js(`!${PANEL}&&!${R}.classList.contains('numpad-open')&&!${R}.style.getPropertyValue('--pad-h')`));

 // --- Chips.
 await A.go(`/s/${M.chips}/`);await A.tap(field(1),600);
 check('chips: double zero in place of the decimal point',await A.js(`${key('alt')}.textContent`)==='00');
 await type(['1','5','alt']);
 check('chips: keys write whole chips',await A.js(`${field(1)}.value`)==='1500');
 check('chips: the panel total is in chips',await A.js(`/^Preview · 1,600 chips of 9,000 chips · 7 to count/.test(${PANEL}.querySelector('[data-numpad-note]').textContent)`));
 await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,500);await A.js(`sessionStorage.clear()`);

 // --- The end states.
 await A.go(`/s/${M.off}/`);
 check('books off: the main button leads to the difference',await A.js(`${shownIn('#live .next-action')}.map(e=>e.textContent.trim()).join()`)==='See the ₱100 difference'&&await A.js(`${primaries}.length`)===0);
 check('books off: the balance check is directly under the overview, its red panel in the first screen',await A.js(`(()=>{const a=document.querySelector('.felt').getBoundingClientRect(),e=document.querySelector('.end-balance').getBoundingClientRect(),b=document.querySelector('.discrepancy').getBoundingClientRect();return e.top>=a.bottom&&e.top<a.bottom+40&&b.bottom<=${DOCK}.getBoundingClientRect().top+2})()`));
 check('books off: the verdict is marked',await A.js(`document.querySelector('[data-dock-status]').dataset.tone==='warn'&&/₱100 missing/.test(document.querySelector('[data-dock-status]').textContent)`));
 check('books off: no disabled button',await A.js(`!${DOCK}.querySelector('button:disabled')`));
 await sleep(300);await A.shot('count-flow-off-390');
 await A.tap(`${DOCK}.querySelector('a.next-action')`,700);
 check('books off: the button shows the panel',await A.js(`(()=>{const b=document.querySelector('.discrepancy').getBoundingClientRect();return b.top>=0&&b.top<${DOCK}.getBoundingClientRect().top})()`));
 await A.go(`/s/${M.balanced}/`);
 check('books balance: Finalize is the one main button',await A.js(`JSON.stringify(${primaries})`)==='["Finalize results"]');
 check('books balance: the verdict is green with its mark',await A.js(`document.querySelector('[data-dock-status]').dataset.tone==='good'&&getComputedStyle(document.querySelector('[data-dock-status]'),'::before').content!=='none'`));
 check('books balance: the balance line is directly under the overview',await A.js(`(()=>{const a=document.querySelector('.felt').getBoundingClientRect(),b=document.querySelector('.books-balanced').getBoundingClientRect();return b.top>a.bottom&&b.bottom<${DOCK}.getBoundingClientRect().top})()`));
 await sleep(300);await A.shot('count-flow-balanced-390');
 await A.go(`/s/${M.override}/`);
 check('override: the verdict says it is covered, and Finalize is offered',await A.js(`document.querySelector('[data-dock-status]').textContent==='Off by ₱100, covered by an override.'&&document.querySelector('[data-dock-status]').dataset.tone===''`)&&await A.js(`JSON.stringify(${primaries})`)==='["Finalize results"]');
 await A.go(`/s/${M.empty}/`);
 check('no buy-in: no main button, and the line that says why',await A.js(`${shownIn('#live .next-action')}.length===0&&/nothing to finalize/.test(document.getElementById('batch-why').textContent)`));

 // --- Review, cash out, finalize, final results.
 const SHEET=`document.querySelector('dialog.sheet')`,TOAST=`document.querySelector('.toast')`;
 const confirmCounts=async values=>{await A.js(`(()=>{const f=${fields};${JSON.stringify(values)}.forEach((v,i)=>{if(v!==null){f[i].value=v;f[i].dispatchEvent(new Event('input',{bubbles:true}))}})})()`);await A.tap(`document.querySelector('[data-confirm-typed]')`,1800)};
 await A.go(`/s/${M.finish}/`);await confirmCounts(['1000','950']);
 check('a success message sits above the bottom bar, never on it',await A.js(`!!${TOAST}&&${TOAST}.getBoundingClientRect().bottom<=${DOCK}.getBoundingClientRect().top`));
 await sleep(300);await A.shot('count-flow-toast-390');
 await A.go(`/s/${M.finish}/cash-out-counted/`);
 const verdict=`document.querySelector('.review-verdict')`;
 check('review, ₱50 short: a warning directly above the button',await A.js(`/the books are ₱50 short/.test(${verdict}.textContent)&&${verdict}.querySelector('.verdict').dataset.tone==='warn'&&${verdict}.nextElementSibling.matches('button[type=submit]')`));
 check('review: the verdict has a mark as well as a colour',await A.js(`getComputedStyle(${verdict}.querySelector('.verdict'),'::before').content!=='none'`));
 check('review: the verdict is readable',await A.js(contrast('.review-verdict .verdict'))>=4.5);
 check('review: the button is 48px and the page fits 390 wide',await A.js(`${verdict}.nextElementSibling.getBoundingClientRect().height>=48&&${R}.scrollWidth<=390`));
 await A.js(`document.querySelector('.review-verdict').scrollIntoView({block:'center'})`);await sleep(300);await A.shot('count-flow-review-short-390');
 await A.go(`/s/${M.finish}/`);await confirmCounts([null,'1000']);
 await A.go(`/s/${M.finish}/cash-out-counted/`);
 check('review, balanced: says the books will balance',await A.js(`${verdict}.textContent.trim()==='After this batch the books balance.'&&${verdict}.querySelector('.verdict').dataset.tone==='good'`));
 await A.js(`document.querySelector('.review-verdict').scrollIntoView({block:'center'})`);await sleep(300);await A.shot('count-flow-review-balanced-390');
 await A.tap(`${verdict}.nextElementSibling`,2000);
 check('after the cash-outs: the message is above the bar and Finalize is clear of it',await A.js(`!!${TOAST}&&${TOAST}.getBoundingClientRect().bottom<=${DOCK}.getBoundingClientRect().top`)&&await A.js(`JSON.stringify(${primaries})`)==='["Finalize results"]');
 await sleep(300);await A.shot('count-flow-finalize-ready-390');
 await A.tap(`document.querySelector('.finalize-opener')`,800);
 check('Finalize asks first: a sheet restates the books',await A.js(`${SHEET}.open&&${SHEET}.querySelector('h2').textContent==='Finalize set 1?'&&/Players\\s*2/.test(${SHEET}.textContent)&&/Total bought in\\s*₱2,000/.test(${SHEET}.textContent)&&/Total cashed out\\s*₱2,000/.test(${SHEET}.textContent)&&/The books balance\\./.test(${SHEET}.textContent)`));
 check('Finalize asks first: nothing is finalized yet, and focus is on "Not yet"',await A.js(`document.getElementById('live').dataset.state==='reconciliation'&&document.activeElement.matches('[data-sheet-close]')`));
 check('Finalize sheet: its two buttons are 48px and it fits the screen',await A.js(`[...${SHEET}.querySelectorAll('.sheet-content .btn')].filter(b=>b.getClientRects().length).length===2&&[...${SHEET}.querySelectorAll('.sheet-content .btn')].every(b=>b.getBoundingClientRect().height>=48)&&${SHEET}.scrollHeight<=${SHEET}.clientHeight`));
 await sleep(400);await A.shot('count-flow-finalize-sheet-390');
 await A.tap(`${SHEET}.querySelector('[data-sheet-close]')`,700);
 check('"Not yet" closes the sheet and the set is still counting',await A.js(`!${SHEET}.open&&document.getElementById('live').dataset.state==='reconciliation'&&!!document.querySelector('.finalize-opener')`));
 await A.tap(`document.querySelector('.finalize-opener')`,800);await A.tap(`${SHEET}.querySelector('form [type=submit]')`,2200);
 check('the second tap finalizes: the final page arrives and the sheet is gone',await A.js(`document.getElementById('live').dataset.state==='finalized'&&!!document.querySelector('.final-layout')&&!${SHEET}.open`));
 check('final page: the proof is in the first screen',await A.js(`(()=>{const p=document.querySelector('.final-proof');return /2 players · ₱2,000 in · ₱2,000 out/.test(p.textContent)&&/The books balance\\./.test(p.textContent)&&p.getBoundingClientRect().bottom<=844&&p.querySelector('.verdict').dataset.tone==='good'})()`));
 check('final page: no live status on a set that cannot change',await A.js(`!document.getElementById('live-status').getClientRects().length`));
 check('final page: an even result reads Even',await A.js(`[...document.querySelectorAll('.result-amount')].every(e=>e.textContent.trim()==='Even')&&!/Available to play/.test(document.getElementById('live').textContent)`));
 check('final page: the proof is readable and the page fits 390 wide',await A.js(contrast('.final-proof'))>=4.5&&await A.js(`${R}.scrollWidth<=390`));
 await A.js(`window.scrollTo(0,0)`);await sleep(6500);await A.shot('count-flow-final-390');

 // --- Widths.
 await A.phone(320,568);await A.go(`/s/${M.eight}/`);
 check('fits 320 wide',await A.js(`${R}.scrollWidth<=320`));
 await A.tap(field(5),700);
 check('320 by 568: the panel fits, its keys are 48px and the field is clear of it',await A.js(`${PANEL}.getBoundingClientRect().height<=568-180&&[...${PANEL}.querySelectorAll('button')].every(b=>b.getBoundingClientRect().height>=48)&&${field(5)}.getBoundingClientRect().bottom<=${PANEL}.getBoundingClientRect().top&&${R}.scrollWidth<=320`));
 await sleep(300);await A.shot('count-flow-pad-320');
 await A.tap(`${PANEL}.querySelector('[data-numpad-done]')`,400);
 await A.phone();

 // --- A computer: two columns, the action beside the fields' top, no panel.
 await A.computer();await A.go(`/s/${M.eight}/`);
 check('computer: players at the right, the action directly under the overview',await A.js(`(()=>{const f=document.querySelector('.felt').getBoundingClientRect(),w=document.querySelector('.count-workspace').getBoundingClientRect(),d=${DOCK}.getBoundingClientRect(),t=document.querySelector('.count-facts').getBoundingClientRect();return w.left>f.right&&Math.abs(w.top-f.top)<4&&d.top>=f.bottom&&d.top<f.bottom+40&&t.top>=d.bottom&&d.left===f.left})()`));
 check('computer: one total, and the cash-out button',await A.js(`${shownIn('[data-count-accounted],[data-dock-accounted]')}.length===1`)&&await A.js(`JSON.stringify(${primaries})`)==='["Cash out counted players (4)"]');
 await A.js(`${field(4)}.focus()`);await send('Input.insertText',{text:'750'},A.s);await sleep(300);
 check('computer: typing with the keyboard, no panel, the button confirms',await A.js(`!${PANEL}&&${field(4)}.getAttribute('inputmode')==='decimal'`)&&await A.js(`JSON.stringify(${primaries})`)==='["Confirm 1 count"]');
 check('computer: focus goes from the fields to the action',await A.js(`(()=>{const order=[...document.querySelectorAll('#live input:not([type=hidden]), #live button, #live a[href], #live summary')].filter(e=>e.getClientRects().length);return order.indexOf(${field(0)})<order.indexOf(document.querySelector('[data-confirm-typed]'))})()`));
 await sleep(300);await A.shot('count-flow-1280');
 await A.js(`sessionStorage.clear()`);

 // --- A player.
 const P=await user('ben');await P.go(`/s/${M.eight}/`);
 check('player: no fields, no dock, no keys',await P.js(`!document.querySelector('[data-count-input]')&&!document.querySelector('.host-controls')&&!document.querySelector('.numpad-panel')`));
 check('player: one read-only total and no host instructions',await P.js(`[...document.querySelectorAll('[data-count-accounted]')].length===1&&!/Confirm each player|Type what each player/.test(document.getElementById('live').textContent)`));
 await P.shot('count-flow-player-390');
} catch(e) { check('run completed: '+e.message.slice(0,300),false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
