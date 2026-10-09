// The set page while a set is prepared and in play (DESIGN.md, "Set page").
// Seed a fresh temporary database with seed.py, seed_end_set.py, seed_night.py and seed_opening.py: set 3 is
// in play with eight players, set 4 is an empty draft, sets 19 to 22 are open. PN_OFF_URL, when set, is a
// second server on the same database started with TABLE_REVAMP=False. The script consumes its fixtures.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-table-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-table-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'').slice(0,160)+' after '+results.length+' checks');return}
 if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765', OFF=process.env.PN_OFF_URL || '';
async function page(opts={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const size=(width,height=844)=>send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}};
 const go=async(path,pause=1100,base=BASE)=>{await send('Page.navigate',{url:base+path},s);await sleep(pause);await settle()};
 const login=async(user,base=BASE)=>{await go('/accounts/login/',600,base);await js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300);await settle()};
 const click=async(expr,pause=650)=>{await js(expr+'.click()');await sleep(pause)};
 const until=async(expr,ms=7000)=>{for(let t=0;t<ms;t+=50){if(await js(expr).catch(()=>false))return true;await sleep(50)}return false};
 const shot=async(name,full=false)=>{const p={format:'png'};if(full){const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);p.captureBeyondViewport=true;p.clip={x:0,y:0,width:c.width,height:c.height,scale:1}}const{data}=await send('Page.captureScreenshot',p,s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const tab=async()=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},s)};
 await size(390);return {s,js,go,login,click,until,shot,size,tab};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const shown=sel=>`[...document.querySelectorAll(${JSON.stringify(sel)})].filter(el=>el.getClientRects().length)`;
const targets=`${shown('#live a.btn, #live button, #live summary, #live input:not([type=hidden]), #live .link-button')}.every(el=>Math.round(el.getBoundingClientRect().height*100)/100>=48)`;
// WCAG contrast of an element's text against a named surface colour, via canvas so oklch resolves.
const contrast=(sel,surface)=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.documentElement).getPropertyValue(${JSON.stringify(surface)})));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
const steps=`Object.fromEntries([...document.querySelectorAll('.prep-step')].map(s=>[s.dataset.step,s.dataset.state]))`;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
try {
 // ===== In play, as the host.
 const H=await page();await H.login('hana');await H.go('/s/3/');
 check('in play: the new page, felt, the badge says In play',await H.js(`!!document.querySelector('.table-v2 .felt:not(.hero)')&&document.querySelector('.felt .badge').textContent==='In play'`));
 check('in play: the menu starts folded and names the next step',await H.js(`document.documentElement.classList.contains('dock-collapsed')&&document.querySelector('.dock-toggle').getAttribute('aria-expanded')==='false'&&document.querySelector('.dock-next').textContent.includes('Next: End play and count up')`));
 const first=await H.js(`(()=>{const dock=document.querySelector('.host-controls').getBoundingClientRect().top,felt=document.querySelector('.felt').getBoundingClientRect();const rows=[...document.querySelectorAll('.player-row')].map(r=>r.getBoundingClientRect());return {felt:Math.round(felt.height),feltWhole:felt.bottom<=dock,whole:rows.filter(r=>r.top>=0&&r.bottom<=dock).length,row:Math.round(rows[0].height),page:document.documentElement.scrollHeight}})()`);
 check('first screen at 390x844: the whole panel and at least five whole rows above the menu',first.feltWhole&&first.whole>=5,JSON.stringify(first));
 check('a row is at most 72px tall',first.row<=72,`${first.row}px`);
 check('the panel is at most 260px tall',first.felt<=260,`${first.felt}px`);
 check('every control is at least 48px',await H.js(targets));
 check('one written action on a row below 900px: Rebuy',await H.js(`${shown('.player-row .player-actions .btn')}.every(b=>b.matches('.buy-opener'))&&${shown('.player-row .buy-opener')}.length===7&&${shown('.cash-opener')}.length===0`));
 check('the host finds Join under the list, not above it',await H.js(`(()=>{const j=document.querySelector('.join-row-quiet'),rows=document.querySelectorAll('.player-row');return !!j&&j.getBoundingClientRect().top>rows[rows.length-1].getBoundingClientRect().bottom-1})()`));
 check('contrast: the line on felt',await H.js(contrast('.facts-line','--felt'))>=4.5&&await H.js(contrast('.facts-more','--felt'))>=4.5);
 check('contrast: a row on the ground',await H.js(contrast('.player-meta','--ground'))>=4.5&&await H.js(contrast('.player-opens .icon','--ground'))>=3);
 await H.shot('table-play-390');
 // The facts behind one line.
 check('the line states bought in and cashed out',await H.js(`/₱12,500 bought in · ₱2,650 cashed out/.test(document.querySelector('.facts-line').textContent)&&!document.querySelector('.set-facts').open`));
 await H.click(`document.querySelector('.set-facts > summary')`,60);const fading=await H.js(`document.querySelector('.facts-body').getAnimations().length`);await sleep(450);
 check('Details opens the rest, and they fade in',fading>0&&await H.js(`document.querySelector('.set-facts').open&&${text('Total bought in')}&&${text('(10 buy-ins)')}&&${text('Rake is Off.')}&&!document.querySelector('.facts-body').getAttribute('style')`),`${fading} movement`);
 check('no rake rows on a set without rake',await H.js(`!${text('Collected rake')}`));
 // The row opens the player's sheet; Cash out is inside it.
 const amountAt=await H.js(`(()=>{const r=document.querySelector('.player-row .player-figure').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()`);
 check('the whole row is the target: the amount belongs to it',await H.js(`document.elementFromPoint(${amountAt[0]},${amountAt[1]}).matches('.player-opener')`));
 await H.js(`document.elementFromPoint(${amountAt[0]},${amountAt[1]}).click()`);await sleep(650);
 check("the player's sheet leads with Cash out and has the focus there",await H.js(`document.querySelector('dialog.sheet').open&&document.querySelector('#sheet-title').textContent.startsWith('Miguel')&&document.activeElement.matches('[data-sheet-swap]')&&${text('Bought in ₱1,000')}&&!!document.querySelector('dialog .list')`));
 await H.shot('table-sheet-player-390');
 await H.click(`document.querySelector('dialog [data-sheet-swap]')`,60);const swapping=await H.js(`document.querySelector('.sheet-body').getAnimations().length`);await sleep(550);
 check('Cash out takes over the same sheet, with the amount ready',swapping>0&&await H.js(`document.querySelector('dialog.sheet').open&&document.querySelector('#sheet-title').textContent==='Cash out · Miguel'&&document.activeElement.name==='amount'&&!document.querySelector('.sheet-body').style.opacity&&!document.querySelector('.sheet-body').style.transform`));
 await H.js(`document.querySelector('dialog [name=amount]').value='750'`);await H.click(`document.querySelector('dialog form [type=submit]')`,100);
 check('the cash-out is recorded and the page answers in place',await H.until(`!document.querySelector('dialog.sheet').open&&document.querySelector('.player-row .player-figure').textContent.includes('Cashed out ₱750')`)&&await H.js(`/₱3,400/.test(document.querySelector('.set-totals').textContent)&&document.querySelector('.set-facts').open`));
 check('focus returns to the row',await H.js(`document.activeElement.matches('.player-row .player-opener')`));
 await H.click(`document.querySelectorAll('.player-row .player-opener')[1]`);
 check("the next player's sheet is whole again",await H.js(`document.querySelector('#sheet-title').textContent.startsWith('Carlo')&&document.querySelectorAll('dialog [data-sheet-swap]').length===1`));
 await H.click(`document.querySelector('dialog .sheet-head button')`,500);
 // Rebuy from the row.
 await H.click(`document.querySelectorAll('.player-row .buy-opener')[1]`);
 check('Rebuy opens its own sheet from the row',await H.js(`document.querySelector('#sheet-title').textContent==='Rebuy · Carlo'&&!!document.querySelector('dialog [name=amount]')`));
 await H.js(`document.querySelector('dialog [name=amount]').value='1000'`);await H.click(`document.querySelector('dialog form [type=submit]')`,100);
 check('the rebuy is recorded and the row says so',await H.until(`!document.querySelector('dialog.sheet').open&&document.querySelectorAll('.player-row')[1].textContent.includes('₱3,000')`)&&await H.js(`document.querySelectorAll('.player-row')[1].classList.contains('just-changed')`));
 // A change from another device.
 await H.js(`window.scrollTo(0,120);window.__doc=1`);const B=await page();await B.login('hana');await B.go('/s/3/');
 await B.click(`document.querySelectorAll('.player-row .buy-opener')[2]`);await B.js(`document.querySelector('dialog [name=amount]').value='500'`);await B.click(`document.querySelector('dialog form [type=submit]')`,300);
 check('a change from another device arrives in place',await H.until(`document.querySelectorAll('.player-row')[2].textContent.includes('₱2,500')`,9000)&&await H.js(`window.__doc===1&&window.scrollY===120&&document.querySelector('.set-facts').open&&document.querySelectorAll('.player-row')[2].classList.contains('just-changed')`));
 check('a live update does not replay the fade of Details',await H.js(`document.querySelector('.facts-body').getAnimations().length===0&&!document.querySelector('.facts-body').getAttribute('style')`));
 // The menu: opening it is remembered while in play.
 await H.js('window.scrollTo(0,0)');await H.click(`document.querySelector('.dock-toggle')`,600);await H.go('/s/3/');
 check('opened by the host, the menu stays open on the next visit',await H.js(`!document.documentElement.classList.contains('dock-collapsed')&&${shown('.host-controls .next-action')}.length===1`));
 await H.click(`document.querySelector('.dock-toggle')`,600);
 // Keyboard.
 await H.js(`document.querySelector('.section-heading a').focus()`);await H.tab();const k1=await H.js(`document.activeElement.className`);const ring=await H.js(`getComputedStyle(document.activeElement,'::after').outlineWidth`);await H.tab();const k2=await H.js(`document.activeElement.className`);
 check('keyboard: the row, then its Rebuy; the ring is drawn round the row',k1.includes('player-opener')&&ring==='3px'&&k2.includes('buy-opener'),`${k1} | ${ring} | ${k2}`);
 // Widths.
 await H.size(320,568);await H.go('/s/3/');
 check('320px: no overflow, 48px controls, the amount under the name',await H.js(`document.documentElement.scrollWidth<=320`)&&await H.js(targets)&&await H.js(`(()=>{const row=document.querySelector('.player-row'),f=row.querySelector('.player-figure').getBoundingClientRect(),n=row.querySelector('.player-opens').getBoundingClientRect();return f.top>=n.bottom-1})()`));
 await H.js(`document.querySelector('.player-opens').firstChild.textContent='AnExtraordinarilyLongUnbrokenPlayerNameThatMustWrap'`);
 check('320px: a long unbroken name wraps inside its row',await H.js(`document.documentElement.scrollWidth<=320&&document.querySelector('.player-row .buy-opener').getBoundingClientRect().right<=320`));await H.shot('table-play-320',true);
 await H.size(1280,800);await H.go('/s/3/');
 check('1280px: two columns, both actions written, the facts open with no line',await H.js(`document.documentElement.scrollWidth<=1280&&${shown('.cash-opener')}.length>=5&&document.querySelector('.set-facts').open&&!document.querySelector('.set-facts > summary').getClientRects().length&&document.querySelector('.table-left').getBoundingClientRect().right<document.querySelector('.table-players').getBoundingClientRect().left`));
 await H.shot('table-play-1280');await H.size(390);
 // As a player.
 const P=await page();await P.login('ben');await P.go('/s/3/');
 check("a player sees their own row first, with Rebuy, and no host menu",await P.js(`document.querySelector('.player-row').textContent.includes('(you)')&&!!document.querySelector('.player-row .buy-opener')&&document.querySelectorAll('.player-row .buy-opener').length===1&&!document.querySelector('.host-controls')&&!document.querySelector('.join-row')`));
 check("a player's page has no cash-out and no reversal",await P.js(`!document.querySelector('[data-sheet-swap]')&&!document.querySelector('.cash-opener')&&!document.querySelector('.btn-danger')`));
 await P.shot('table-play-player-390');

 // ===== Preparing: a draft, walked to the start.
 await H.go('/s/4/');
 check('draft: four steps, players next; no totals',same(await H.js(steps),{players:'next',stakes:'done',open:'later',start:'later'})&&await H.js(`document.querySelector('.prep .badge').textContent==='Draft'&&!${text('Still in play')}&&!${text('Set timer')}&&!${text('Cashed out')}&&!document.querySelector('.felt')`));
 check('draft: the main button is Add players; Open is offered beside it',await H.js(`document.querySelector('.host-controls .next-action').textContent==='Add players'&&!!document.querySelector('.host-controls button[value=open]')&&document.querySelectorAll('.host-controls .btn-primary').length===1`));
 check('draft: 48px controls, no overflow, the list is not under the menu',await H.js(targets)&&await H.js(`document.documentElement.scrollWidth<=390&&document.querySelector('.prep').getBoundingClientRect().bottom<=document.querySelector('.host-controls').getBoundingClientRect().top+1`));
 check('contrast: a step on the rail',await H.js(contrast('.prep-line','--rail'))>=4.5&&await H.js(contrast('.prep-step[data-state=later] .prep-name','--rail'))>=4.5);
 check('each step says its state in words',await H.js(`[...document.querySelectorAll('.prep-step .visually-hidden')].map(e=>e.textContent).join(' ')==='Next: Done: Later: Later:'`));
 await H.shot('table-draft-390');
 await H.size(320,568);await H.go('/s/4/');check('draft at 320px: no overflow, 48px controls',await H.js(`document.documentElement.scrollWidth<=320`)&&await H.js(targets));await H.shot('table-draft-320',true);await H.size(390);await H.go('/s/4/');
 // Add two players from the menu, in place.
 for(const n of [0,1]){await H.js(`document.querySelector('details.host-more').open=true;document.querySelector('details[data-key="add-one"]').open=true`);await H.click(`document.querySelector('details[data-key="add-one"] button[type=submit]')`,50);
  if(n===0){const ok=await H.until(`document.querySelector('[data-step=players]').dataset.state==='done'`);const moved=await H.until(`document.querySelector('[data-step=players] .prep-mark').getAnimations().length>0||!!document.querySelector('[data-step=players] .prep-mark').style.transform`,400);
   check('a completed step: the mark lands with its tick, and the next step is pointed at',ok&&moved&&same(await H.js(steps),{players:'done',stakes:'done',open:'next',start:'later'}));}
  else await H.until(`document.querySelectorAll('.player-row').length===2`);await sleep(700);}
 check('at rest the steps keep no inline style',await H.js(`[...document.querySelectorAll('.prep-mark')].every(m=>!m.getAttribute('style'))&&document.getAnimations().length===0`));
 check('with players, Open for players is the one main button',await H.js(`document.querySelector('.host-controls .next-action').textContent==='Open for players'&&document.querySelector('.dock-next').textContent.includes('Next: Open for players')&&${text('2 added')}`));
 await H.click(`document.querySelector('.host-controls button[value=open]')`,50);
 check('opening is answered in place: the step is done, Start is next',await H.until(`document.querySelector('.prep .badge').textContent==='Open'`)&&same(await H.js(steps),{players:'done',stakes:'done',open:'done',start:'next'})&&await H.js(`document.querySelector('.host-controls .next-action').textContent==='Start the set'&&${text('Players can see it and join.')}`));
 await sleep(600);
 check('open: the menu holds the option and Start; Back to draft waits under More',await H.js(`!!document.querySelector('#opening-buy-ins')&&${shown('.host-controls > form button[value=close], .host-controls > button[value=close]')}.length===0&&!!document.querySelector('.host-more button[value=close]')`));
 const dockH=await H.js(`Math.round(document.querySelector('.host-controls').getBoundingClientRect().height)`);check('open: the menu is at most 260px tall',dockH<=260,`${dockH}px`);await H.shot('table-open-390');
 // Start: the one moment.
 await H.js(`window.__seen=null;new MutationObserver(()=>{const f=document.querySelector('.table-v2 .felt');if(f&&!window.__seen){const a=document.getAnimations();window.__seen={figure:document.querySelector('.display-amount').textContent.trim(),clip:getComputedStyle(f).clipPath,styled:f.style.clipPath,timer:document.querySelector('.pot-side strong').textContent.trim()}}}).observe(document.getElementById('live'),{childList:true,subtree:true})`);
 await H.click(`document.querySelector('.host-controls button[value=start]')`,50);
 const started=await H.until(`document.getElementById('live').dataset.state==='running'&&!!window.__seen`);await sleep(120);
 const run=await H.js(`(()=>{const f=document.querySelector('.table-v2 .felt'),a=f.getAnimations();return {n:a.length,end:Math.max(0,...document.getAnimations().map(x=>x.effect.getComputedTiming().endTime))}})()`);const seen=await H.js('window.__seen');
 check('the set starts: felt sweeps across the panel',started&&run.n>0,JSON.stringify({seen,run}));
 check('the start is over within 900ms',run.end>0&&run.end<=900,`${Math.round(run.end)}ms`);await sleep(950);
 check('the figure was at its value on the first frame, and nothing is left at rest',await H.js(`document.querySelector('.display-amount').textContent.trim()===${JSON.stringify(seen.figure)}&&!document.querySelector('.table-v2 .felt').getAttribute('style')&&!document.querySelector('.pot-side').getAttribute('style')&&document.getAnimations().length===0`),seen.figure);
 check('started: the usual buy-in went to both players, the timer runs',await H.js(`document.querySelector('.felt .badge').textContent==='In play'&&/₱/.test(document.querySelector('.display-amount').textContent)&&document.querySelectorAll('.player-row .buy-opener').length===2`));
 await H.go('/s/4/');check('opening the page again does not replay the start',await H.js(`document.getAnimations().length===0&&!document.querySelector('.table-v2 .felt').getAttribute('style')`));
 // An open set as a player.
 await P.go('/s/19/');
 check('a player on an open set: the stakes, Join first, no checklist',await P.js(`!document.querySelector('.prep-step')&&${text('The host starts the set.')}&&${text('Blinds')}&&document.querySelector('.player-list > li').matches('.join-row')&&!!document.querySelector('.join-row .btn-primary')`));
 await P.shot('table-open-player-390');await P.click(`document.querySelector('.join-row button')`,100);
 check('Join seats the player, first in their own list',await P.until(`!document.querySelector('.join-row')&&document.querySelector('.player-row').textContent.includes('(you)')`));
 // Desktop preparation.
 await H.size(1280,800);await H.go('/s/19/');check('1280px open set: checklist in the left column, no overflow',await H.js(`document.documentElement.scrollWidth<=1280&&document.querySelector('.prep').getBoundingClientRect().right<document.querySelector('.table-players').getBoundingClientRect().left`));await H.shot('table-open-1280');await H.size(390);

 // ===== Fail safe.
 const R=await page();await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await R.login('hana');await R.go('/s/21/');
 await R.click(`document.querySelector('.host-controls button[value=start]')`,50);await R.until(`document.getElementById('live').dataset.state==='running'`);
 check('reduced motion: the set starts and nothing moves',await R.js(`document.getAnimations().length===0&&!document.querySelector('.table-v2 .felt').getAttribute('style')&&document.querySelector('.felt .badge').textContent==='In play'`));
 await R.click(`document.querySelector('.player-row .player-opener')`,400);
 check('reduced motion: the row still opens the sheet',await R.js(`document.querySelector('dialog.sheet').open`));
 const X=await page();await send('Network.enable',{},X.s);await send('Network.setBlockedURLs',{urls:['*vendor/motion-*']},X.s);const before=errors.length;await X.login('hana');await X.go('/s/3/');
 await X.click(`document.querySelectorAll('.player-row .player-opener')[3]`,500);await X.click(`document.querySelector('dialog [data-sheet-swap]')`,500);
 check('Motion blocked: rows, sheets and the page work, with no script error',await X.js(`!window.Motion&&document.querySelector('dialog.sheet').open&&document.querySelector('#sheet-title').textContent.startsWith('Cash out')`)&&errors.length===before,errors.slice(before).join('; '));
 const N=await page();await N.login('hana');await send('Emulation.setScriptExecutionDisabled',{value:true},N.s);await N.go('/s/20/');
 check('no JavaScript, open set: the steps, the option and Start are all there',await N.js(`document.querySelectorAll('.prep-step').length===4&&!!document.querySelector('#opening-buy-ins')&&!!document.querySelector('button[value=start]')`));
 await N.click(`document.querySelector('.host-controls button[value=start]')`,1500);
 check('no JavaScript: Start works and the page in play is whole',await N.js(`location.pathname==='/s/20/'&&!!document.querySelector('.table-v2 .felt')&&document.querySelector('.felt .badge').textContent==='In play'`));
 check('no JavaScript: each row offers Rebuy, Cash out and Details as native disclosures',await N.js(`(()=>{const row=document.querySelector('.player-row');const s=[...row.querySelectorAll('summary')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim());return s.join('|')==='Rebuy|Cash out|Details'&&!row.querySelector('.player-opens .icon').getClientRects().length})()`),await N.js(`[...document.querySelector('.player-row').querySelectorAll('summary')].map(e=>e.textContent.trim()).join('|')`));
 await N.js(`(()=>{const d=[...document.querySelectorAll('.player-row details')].find(x=>x.querySelector('summary').textContent.trim()==='Rebuy');d.open=true;d.querySelector('[name=amount]').value='500'})()`);
 await N.click(`[...document.querySelectorAll('.player-row details')].find(x=>x.querySelector('summary').textContent.trim()==='Rebuy').querySelector('[type=submit]')`,1500);
 check('no JavaScript: a rebuy from the native form is recorded',await N.js(`location.pathname==='/s/20/'&&/1 rebuy/.test(document.querySelector('.player-row').textContent)`));
 check('no JavaScript: Details on the panel is a native disclosure',await N.js(`document.querySelector('.set-facts > summary').getClientRects().length>0&&!document.querySelector('.set-facts').open`));
 // Late frames on the start, with the processor slowed four times.
 const L=await page();await L.login('hana');await L.go('/s/22/');await send('Emulation.setCPUThrottlingRate',{rate:4},L.s);
 await L.js(`window.__frames=[];let last=0;const tick=n=>{if(last)window.__frames.push(n-last);last=n;requestAnimationFrame(tick)};requestAnimationFrame(tick)`);
 await L.click(`document.querySelector('.host-controls button[value=start]')`,50);await L.until(`document.getElementById('live').dataset.state==='running'`,12000);await L.js('window.__mark=window.__frames.length');await sleep(1000);
 const frames=(await L.js('window.__frames.slice(window.__mark)'));const worst=Math.round(Math.max(...frames)),late=frames.filter(d=>d>34).length;
 check('slowed four times: the sweep itself drops at most two frames',late<=2,`${frames.length} frames, ${late} over 34ms, worst ${worst}ms`);
 if(OFF){const O=await page();await O.login('hana',OFF);await O.go('/s/3/',1100,OFF);
  check('switch off, in play: the page as it was',await O.js(`!document.querySelector('.table-v2')&&!document.querySelector('.set-facts')&&document.querySelector('.felt .badge').textContent==='Running'&&${shown('.cash-opener')}.length>=5&&!document.documentElement.classList.contains('dock-collapsed')&&!!document.querySelector('.join-row:not(.join-row-quiet)')`));
  await O.go('/s/19/',1100,OFF);check('switch off, open set: the panel of totals and the menu as they were',await O.js(`!!document.querySelector('.felt.hero')&&!document.querySelector('.prep-step')&&${text('Still in play')}&&${shown('.host-controls > form button[value=close]')}.length===1`));
  await O.click(`document.querySelector('.player-row .player-opener')`,500);check('switch off: sheets still work',await O.js(`document.querySelector('dialog.sheet').open&&!document.querySelector('dialog [data-sheet-swap]')`));
 } else console.log('SKIP the switch: PN_OFF_URL is not set');
 check('no script error anywhere',errors.length===0,errors.join('; '));
 writeFileSync(`${OUT}/table.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
