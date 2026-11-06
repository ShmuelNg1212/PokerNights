// The set start overture (overture.js, DESIGN.md "Set start overture"). Seed a fresh temporary SQLite
// database with seed_overture.py alone, serve it on 127.0.0.1:8765, then run. Each start consumes its set.
// A sampler reads every animation frame while the stage is on the page: the first frame, the last frame
// before it goes (where each chip must sit on its row token), and the frame times.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-overture-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const SET=JSON.parse(readFileSync('/private/tmp/pn-overture-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-overture-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9343','--user-data-dir=/private/tmp/pn-overture-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9343/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'').slice(0,200));return}
 if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function page({width=390,height=844,reduce=false,block=false}={}){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 if(block){await send('Network.enable',{},s);await send('Network.setBlockedURLs',{urls:['*vendor/motion-*']},s);}
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}};
 const go=async(path,pause=1100)=>{await send('Page.navigate',{url:BASE+path},s);await sleep(pause);await settle()};
 const login=async user=>{await go('/accounts/login/',600);await js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300);await settle()};
 const until=async(expr,ms=7000)=>{for(let t=0;t<ms;t+=40){if(await js(expr).catch(()=>false))return true;await sleep(40)}return false};
 const shot=async name=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const tap=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 return {s,js,go,login,until,shot,tap};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
// Every frame while the stage is on the page: the ground, each chip, the disc, the row tokens, the badge.
// The felt's light after the landing: when data-felt-lit comes and goes, the ring's origin against the badge, the
// properties its layers animate, and the frame times while it is lit.
const SAMPLER=`window.__lit={on:null,off:null,stage:null,origin:null,badge:null,props:[],names:[],gaps:[]};window.__ov={n:0,first:null,last:null,gaps:[],shots:[]};(()=>{let prev=0,litPrev=0;
 const litTick=now=>{const h=document.documentElement,on=h.hasAttribute('data-felt-lit');if(on){if(litPrev)__lit.gaps.push(now-litPrev);litPrev=now;if(__lit.on===null){__lit.on=now;__lit.stage=!!document.querySelector('.overture:not(.is-gone)');const felt=document.querySelector('#live .felt').getBoundingClientRect(),b=document.querySelector('#live .badge-live').getBoundingClientRect(),cs=getComputedStyle(h);__lit.origin={x:felt.left+parseFloat(cs.getPropertyValue('--lit-x')),y:felt.top+parseFloat(cs.getPropertyValue('--lit-y')),r:parseFloat(cs.getPropertyValue('--lit-r'))};__lit.badge={x:b.left+b.width/2,y:b.top+b.height/2};__lit.felt={w:felt.width,h:felt.height};const a=document.getAnimations().filter(x=>x.effect&&x.effect.pseudoElement&&x.effect.target.matches('#live .felt'));__lit.names=a.map(x=>x.animationName+x.effect.pseudoElement);__lit.props=[...new Set(a.flatMap(x=>x.effect.getKeyframes().flatMap(k=>Object.keys(k).filter(n=>!['offset','easing','composite','computedOffset'].includes(n)))))]}}else if(__lit.on!==null&&__lit.off===null){__lit.off=now;litPrev=0}};const at=c=>{if(!c)return null;const r=c.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height,l:r.left,r:r.right,t:r.top,b:r.bottom,o:+getComputedStyle(c).opacity,text:c.textContent}};
 const tick=now=>{const o=document.querySelector('.overture:not(.is-gone)');if(o){if(prev)__ov.gaps.push(now-prev);prev=now;const f={t:now,ground:+getComputedStyle(o.querySelector('.ov-ground')).opacity,chips:[...o.querySelectorAll('.ov-chip')].map(at),disc:at(o.querySelector('.ov-disc')),
  tokens:[...document.querySelectorAll('#live .player-row .chip')].map(at),badge:at(document.querySelector('#live .badge-live')),words:[...o.querySelectorAll('p')].map(p=>p.textContent.trim()).join(' '),figure:(document.querySelector('#live .display-amount')||{}).textContent};if(!__ov.first)__ov.first=f;__ov.last=f;__ov.n++;__ov.shots.push(f)}else prev=0;litTick(now);requestAnimationFrame(tick)};requestAnimationFrame(tick)})()`;
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
// Each chip still visible at the end sits on a row token; the others were hidden under the dock.
const landed=(f,floor)=>{const shown=f.tokens.filter(t=>t.y<floor-12);const on=f.chips.filter(c=>c.o>0.5).map(c=>Math.min(...f.tokens.map(t=>dist(c,t))));return {shown:shown.length,visible:on.length,worst:Math.max(0,...on)}};
const floorOf=P=>P.js(`(()=>{const d=document.querySelector('.host-controls');return d&&getComputedStyle(d).position==='fixed'?d.getBoundingClientRect().top:innerHeight})()`);
// A seat draw this browser has not watched opens its stage on arrival; the host closes it, as after watching.
async function start(P,set,{arm=true}={}){await P.go(`/s/${set}/`);await P.js(`document.querySelector('dialog[open]')?.close()`);await sleep(200);if(arm)await P.js(SAMPLER);await P.js(`document.querySelector('.host-controls button[value=start]').click()`);return P.until(`document.getElementById('live').dataset.state==='running'`,8000)}
const rest=`!document.querySelector('.overture')&&!document.documentElement.hasAttribute('data-overture')&&!document.documentElement.hasAttribute('data-felt-lit')&&!document.documentElement.style.getPropertyValue('--lit-r')&&[...document.querySelectorAll('#live .player-row .chip, #live [data-carry=title] small, #live .badge-live')].every(e=>!e.getAttribute('style')&&getComputedStyle(e).opacity==='1')`;
try {
 // ===== Eight players, no draw, with a player's phone watching and a poll landing mid-overture.
 const B=await page();await B.login('ben');await B.go(`/s/${SET.eight}/`);await B.js(SAMPLER);
 const H=await page();await H.login('hana');
 check('eight: the start is accepted',await start(H,SET.eight));
 check('eight: the overture appears on the host phone',await H.until(`__ov.n>0`,1500));
 await sleep(700);await H.shot('eight-orbit-390');
 // A poll's morph, as live.js does it, while the stage plays: the stage is outside #live and keeps going.
 const morphed=await H.js(`(async()=>{const r=document.getElementById('live');const v=r.dataset.version;const s=await (await fetch(r.dataset.url+'?v=0',{headers:{'X-Requested-With':'fetch'},cache:'no-store'})).json();r.dispatchEvent(new Event('live:updating',{bubbles:true}));const n=document.createElement('div');n.innerHTML=s.html;Turbo.morphChildren(r,n,{ignoreActiveValue:true});r.dispatchEvent(new CustomEvent('live:updated',{bubbles:true,detail:{poll:true}}));return !!document.querySelector('.overture')&&document.documentElement.hasAttribute('data-overture')})()`);
 check('eight: a poll during the overture leaves the stage playing and the tokens hidden',morphed);
 check('eight: the overture ends by itself',await H.until(`__ov.n>0&&!document.querySelector('.overture')`,4000));
 const e8=await H.js('({first:__ov.first,last:__ov.last,n:__ov.n,span:__ov.last.t-__ov.first.t})');const floor8=await floorOf(H);const l8=landed(e8.last,floor8);
 check('eight: the first frame is the dark ground arriving, with no chip at rest and the tokens hidden',e8.first.ground<0.6&&e8.first.chips.every(c=>c.o<0.1)&&e8.first.tokens.every(t=>t.o===0),JSON.stringify({ground:e8.first.ground,chips:e8.first.chips.map(c=>c.o)}));
 check('eight: the words are the set, the call and the facts from the page',/^Set 1 Shuffle up and deal 8 players · Blinds ₱10 \/ ₱20 Tap to skip/.test(e8.first.words),e8.first.words);
 check('eight: each chip ends on its row token; the rest went under the dock',l8.visible===l8.shown&&l8.worst<=1.5&&e8.last.chips.length===8,JSON.stringify(l8));
 check('eight: without a draw the button goes into the In play badge',dist(e8.last.disc,e8.last.badge)<=2&&e8.last.disc.o<0.3,JSON.stringify({disc:e8.last.disc,badge:e8.last.badge}));
 check('eight: about two seconds from first to last frame',e8.span>=1650&&e8.span<=2300,`${Math.round(e8.span)}ms`);
 await H.until(`__lit.off!==null`,2000);const lit8=await H.js('({lit:__lit,end:__ov.last.t})');const L8=lit8.lit;
 check('eight: the felt lights once the button is home, while the stage is still leaving',L8.on!==null&&L8.stage&&L8.on<lit8.end,JSON.stringify({on:L8.on,end:lit8.end,stage:L8.stage}));
 check('eight: the ring starts on the In play badge and reaches the farthest corner of the felt',dist(L8.origin,L8.badge)<=1.5&&L8.origin.r>=Math.hypot(L8.felt.w,L8.felt.h)/2,JSON.stringify(L8.origin));
 check('eight: two layers, the light and the ring, moving only transform and opacity',L8.names.sort().join()==='felt-light::before,felt-ring::after'&&L8.props.every(n=>n==='transform'||n==='opacity'),JSON.stringify({names:L8.names,props:L8.props}));
 check('eight: the light is over within about 700ms',L8.off-L8.on>=650&&L8.off-L8.on<=850,`${Math.round(L8.off-L8.on)}ms`);
 check('eight: no animation is left on the felt',await H.js(`document.getAnimations().filter(a=>a.effect&&a.effect.target&&a.effect.target.matches&&a.effect.target.matches('#live .felt')).length===0`));
 check('eight: at rest nothing is left, and every token, the label and the badge show',await H.js(rest));
 const figureAfter=await H.js(`document.querySelector('.display-amount').textContent`);
 check('eight: money is at its accepted value from the first frame to the last',e8.first.figure===figureAfter&&e8.last.figure===figureAfter&&/₱8,000/.test(figureAfter),JSON.stringify([e8.first.figure,e8.last.figure,figureAfter]));
 await H.shot('eight-rest-390');
 check("eight: the player's phone plays it after its poll",await B.until(`__ov.n>0`,8000)&&await B.until(`!document.querySelector('.overture')`,4000));
 const b8=await B.js('__ov.last');const lb=landed(b8,await floorOf(B));
 check("eight: on the player's phone the chips land on their tokens too",lb.visible===lb.shown&&lb.worst<=1.5,JSON.stringify(lb));
 await B.go(`/s/${SET.eight}/`);await B.js(SAMPLER);await sleep(2500);
 check("eight: a reload does not replay it",await B.js(`__ov.n===0&&!document.querySelector('.overture')`));
 await H.go(`/s/${SET.eight}/`);await H.js(SAMPLER);await sleep(2500);check('eight: the host page opened again does not replay it',await H.js(`__ov.n===0`));

 // ===== Six players with a seated draw: the seat order, and the button to the first dealer.
 // Ben watches the same set at 1280px, where every row is on the screen; at 390px the host's dealer row may be under the dock.
 const D=await page({width:1280,height:800});await D.login('ben');await D.go(`/s/${SET.drawn}/`);await D.js(`document.querySelector('dialog[open]')?.close()`);await D.js(SAMPLER);
 // Ben has a player's sheet open when the start arrives: the overture waits until he closes it.
 await sleep(300);await D.js(`document.querySelector('.player-row .player-opener').click()`);await sleep(500);const sheetOpen=await D.js(`!!document.querySelector('dialog[open]')`);
 const homeOf=`(()=>{const li=[...document.querySelectorAll('[data-seats] .seat-order > li .chip')];const by={};document.querySelectorAll('#live .player-row .chip').forEach(c=>by[c.dataset.m]=c);const d=by[li[0].dataset.m].getBoundingClientRect();return {order:li.map(c=>c.textContent.trim()),home:{x:d.left+d.width/2+d.width*.42,y:d.top+d.height/2-d.height*.36}}})()`;
 const dealerCheck=async(P,f,label)=>{const seat=await P.js(homeOf),floor=await floorOf(P),under=seat.home.y>floor-12;
  check(`${label}: the chips come in clockwise from the dealer`,JSON.stringify(f.first.chips.map(c=>c.text.trim()))===JSON.stringify(seat.order),JSON.stringify({chips:f.first.chips.map(c=>c.text),seat:seat.order}));
  check(`${label}: the dealer button ${under?'goes behind the dock over the dealer':'rests on the first dealer at 22px'}`,under?(Math.abs(f.last.disc.y-(floor+10))<=2&&Math.abs(f.last.disc.x-seat.home.x)<=2&&f.last.disc.o<0.3):(dist(f.last.disc,seat.home)<=2&&Math.abs(f.last.disc.w-22)<=1.5&&f.last.disc.o>0.9),JSON.stringify({under,floor,disc:f.last.disc,home:seat.home}));
  return under};
 check('drawn: the start is accepted',await start(H,SET.drawn));
 await H.until(`__ov.n>0&&!document.querySelector('.overture')`,5000);
 const underHost=await dealerCheck(H,await H.js('({first:__ov.first,last:__ov.last})'),'drawn at 390px');
 await D.until(`document.getElementById('live').dataset.state==='running'`,8000);await sleep(600);
 check("drawn at 1280px: with a sheet open, the player's phone waits",sheetOpen&&await D.js(`__ov.n===0&&!document.querySelector('.overture')&&!!document.querySelector('dialog[open]')`));
 await D.js(`document.querySelector('dialog[open]').close()`);
 check("drawn at 1280px: closing the sheet plays it",await D.until(`__ov.n>0`,2000)&&await D.until(`!document.querySelector('.overture')`,4000));
 const underWide=await dealerCheck(D,await D.js('({first:__ov.first,last:__ov.last})'),'drawn at 1280px');
 check('drawn: the fixture checks both ends: behind the dock at 390px, at rest on the dealer at 1280px',underHost&&!underWide,JSON.stringify({underHost,underWide}));
 check('drawn: at rest nothing is left',await H.js(rest));

 // ===== The skip: a tap on top of a Rebuy at 600ms ends it at once and does not press the Rebuy.
 check('two: the start is accepted',await start(H,SET.two));await H.until(`__ov.n>0`,1500);await sleep(600);
 const target=await H.js(`(()=>{const b=document.querySelector('.player-row .buy-opener').getBoundingClientRect();return {x:b.left+b.width/2,y:b.top+b.height/2}})()`);
 await H.tap(target.x,target.y);
 check('two: the tap ends it in the same frame: tokens, label and badge show',await H.js(`!document.documentElement.hasAttribute('data-overture')&&!document.querySelector('.overture:not(.is-gone)')`));
 await sleep(700);
 check('two: the skipping tap did not open a sheet, and the stage is gone',await H.js(`!document.querySelector('dialog[open]')&&${rest}`));
 await sleep(1200);check('two: a skipped overture does not light the felt',await H.js(`__lit.on===null`));
 await H.js(`document.querySelector('.player-row .buy-opener').click()`);await sleep(500);
 check('two: the next tap works: Rebuy opens its sheet',await H.js(`!!document.querySelector('dialog.sheet[open]')`));

 // ===== The key skip: Enter on a focused Rebuy ends it and does not press the Rebuy.
 check('keys: the start is accepted',await start(H,SET.keys));await H.until(`__ov.n>0`,1500);await sleep(500);
 await H.js(`document.querySelector('.player-row .buy-opener').focus()`);
 for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:'Enter',code:'Enter',windowsVirtualKeyCode:13,...(type==='keyDown'?{text:'\r'}:{})},H.s);
 check('keys: Enter ends it in the same frame',await H.js(`!document.querySelector('.overture')&&!document.documentElement.hasAttribute('data-overture')`));await sleep(500);
 check('keys: Enter did not also press the focused Rebuy',await H.js(`!document.querySelector('dialog[open]')&&document.activeElement.matches('.buy-opener')`));
 // ===== Twelve players at 320 × 568: every chip stays on the screen while it circles.
 const T=await page({width:320,height:568});await T.login('hana');
 check('twelve: the start is accepted',await start(T,SET.twelve));await T.until(`__ov.n>0`,1500);await sleep(800);await T.shot('twelve-orbit-320');
 // live.js without Turbo replaces #live outright while the felt is lit: the light stops, it does not start again.
 await T.until(`document.documentElement.hasAttribute('data-felt-lit')`,4000);
 const relit=await T.js(`(async()=>{const r=document.getElementById('live');const s=await (await fetch(r.dataset.url+'?v=0',{headers:{'X-Requested-With':'fetch'},cache:'no-store'})).json();r.innerHTML=s.html;r.dispatchEvent(new CustomEvent('live:updated',{bubbles:true}));await new Promise(f=>requestAnimationFrame(()=>requestAnimationFrame(f)));return {lit:document.documentElement.hasAttribute('data-felt-lit'),anims:document.getAnimations().filter(a=>a.effect&&a.effect.pseudoElement).length}})()`);
 check('twelve: a full replacement of the felt while it is lit stops the light',!relit.lit&&relit.anims===0,JSON.stringify(relit));
 await T.until(`__ov.n>0&&!document.querySelector('.overture')`,4000);
 const inside=await T.js(`(()=>{const f=__ov.shots.filter(s=>s.t-__ov.first.t>700&&s.t-__ov.first.t<1250);return {frames:f.length,out:f.flatMap(s=>s.chips.filter(c=>c.o>0.5&&(c.l<0||c.r>innerWidth||c.t<0||c.b>innerHeight))).length,words:__ov.first.words}})()`);
 check('twelve at 320px: twelve chips circle inside the screen',inside.frames>5&&inside.out===0,JSON.stringify(inside));
 const ov=await T.js(`(()=>{const f=__ov.shots.find(s=>s.t-__ov.first.t>800);return f?f.chips.length:0})()`);check('twelve: a chip for each player',ov===12,`${ov}`);
 check('twelve: at rest nothing is left, and the page does not scroll sideways',await T.js(`${rest}&&document.documentElement.scrollWidth<=320`));

 // ===== 1280 × 800: the rows are in the right column.
 const W=await page({width:1280,height:800});await W.login('hana');
 check('wide: the start is accepted',await start(W,SET.wide));await W.until(`__ov.n>0`,1500);await sleep(700);await W.shot('wide-orbit-1280');
 // live.js without Turbo replaces #live outright: every node captured at the start is gone when the chips fly.
 const replaced=await W.js(`(async()=>{const r=document.getElementById('live');const s=await (await fetch(r.dataset.url+'?v=0',{headers:{'X-Requested-With':'fetch'},cache:'no-store'})).json();const old=r.querySelector('.player-row .chip');r.innerHTML=s.html;return !old.isConnected&&!!document.querySelector('.overture')})()`);
 check('wide: a full replacement of the set during the overture leaves the stage playing',replaced);
 await W.until(`__ov.n>0&&!document.querySelector('.overture')`,4000);const lw=landed(await W.js('__ov.last'),await floorOf(W));
 check('wide at 1280px: each chip ends on its row token, found again after the replacement',lw.visible===lw.shown&&lw.shown>0&&lw.worst<=1.5,JSON.stringify(lw));
 check('wide: after the replacement the felt still lights, and then goes out',await W.until(`__lit.off!==null`,2000)&&await W.js(`__lit.on!==null`));
 check('wide: at rest nothing is left',await W.js(rest));await W.shot('wide-rest-1280');

 // ===== Fail safe.
 const R=await page({reduce:true});await R.login('hana');check('reduced motion: the start is accepted',await start(R,SET.calm));await sleep(2500);
 check('reduced motion: no overture, the running set at once',await R.js(`__ov.n===0&&__lit.on===null&&${rest}&&document.querySelector('.felt .badge').textContent==='In play'`));
 const X=await page({block:true});await X.login('hana');const errorsBefore=errors.length;check('Motion blocked: the start is accepted',await start(X,SET.blocked));await sleep(2500);
 check('Motion blocked: no overture, no script error',await X.js(`!window.Motion&&__ov.n===0&&${rest}`)&&errors.length===errorsBefore,errors.slice(errorsBefore).join('; '));

 // ===== Frames with the processor slowed four times, over the whole overture.
 const L=await page();await L.login('hana');await L.go(`/s/${SET.slow}/`);await send('Emulation.setCPUThrottlingRate',{rate:4},L.s);await L.js(SAMPLER);
 await L.js(`document.querySelector('.host-controls button[value=start]').click()`);await L.until(`__ov.n>0`,12000);await L.until(`!document.querySelector('.overture')`,8000);
 await L.until(`__lit.off!==null`,4000);const gaps=await L.js('__ov.gaps.concat(__lit.gaps)');const worst=Math.round(Math.max(...gaps)),late=gaps.filter(g=>g>50).length;
 check('slowed four times: no frame over 50ms while it plays and the felt is lit',late===0,`${gaps.length} frames, ${late} over 50ms, worst ${worst}ms`);
 check('no script error anywhere',errors.length===0,errors.join('; '));
 writeFileSync(`${OUT}/overture.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
process.exit(results.every(x=>x.ok)?0:1);
