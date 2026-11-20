// The session finale (finale.js, DESIGN.md "Session finale"). Seed a fresh temporary SQLite database with
// seed_finale.py alone, serve it on 127.0.0.1:8765, then run. The host's close consumes the "ready" session.
// A sampler, installed before the page's scripts, reads every animation frame: the stage while it is on the
// page, then when the recap card rises. Since 2026-11-20 no sheet opens by itself: any open sheet is noted.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-finale-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const N=JSON.parse(readFileSync('/private/tmp/pn-finale-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-finale-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir=/private/tmp/pn-finale-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'').slice(0,200));return}
 if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Each frame while the stage is up: the ground, each chip, the ring, the words. Then when the recap card rose,
// and whether a sheet ever opened (it must not).
const SAMPLER=`window.__fi={n:0,first:null,last:null,gaps:[],shots:[],ring:0,opened:null,rose:null,stages:0};(()=>{let prev=0,seen=null;
 const at=c=>{const r=c.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,l:r.left,r:r.right,t:r.top,b:r.bottom,o:+getComputedStyle(c).opacity,text:c.textContent.trim(),top:c.classList.contains('fi-top')}};
 const tick=now=>{const o=document.querySelector('.finale:not(.is-gone)');
  if(o){if(o!==seen){seen=o;__fi.stages++}if(prev)__fi.gaps.push(now-prev);prev=now;const call=o.querySelector('.ov-call'),cr=call.getBoundingClientRect();
   const f={t:now,ground:+getComputedStyle(o.querySelector('.ov-ground')).opacity,chips:[...o.querySelectorAll('.ov-chip')].map(at),ring:+getComputedStyle(o.querySelector('.ov-ring')).opacity,words:call.textContent.trim(),call:{l:cr.left,r:cr.right,o:+getComputedStyle(call).opacity},figure:(document.querySelector('[data-still-to-pay]')||document.querySelector('.night-overview')||{}).textContent,dialog:!!document.querySelector('dialog.sheet[open]')};
   __fi.ring=Math.max(__fi.ring,f.ring);if(!__fi.first)__fi.first=f;__fi.last=f;__fi.n++;__fi.shots.push(f)}else prev=0;
  if(document.querySelector('dialog.sheet[open]')&&__fi.opened===null)__fi.opened=now;if(document.querySelector('[data-recap-card].is-rising')&&__fi.rose===null)__fi.rose=now;
  requestAnimationFrame(tick)};requestAnimationFrame(tick)})()`;
async function page({width=390,height=844,reduce=false,block=false,nojs=false}={}){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:SAMPLER},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 if(block){await send('Network.enable',{},s);await send('Network.setBlockedURLs',{urls:['*vendor/motion-*']},s);}
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}};
 const go=async(path,pause=300)=>{await send('Page.navigate',{url:BASE+path},s);await sleep(pause);await settle()};
 const login=async user=>{await go('/accounts/login/',600);await js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300);await settle();if(nojs)await send('Emulation.setScriptExecutionDisabled',{value:true},s)};
 const until=async(expr,ms=7000)=>{for(let t=0;t<ms;t+=40){if(await js(expr).catch(()=>false))return true;await sleep(40)}return false};
 const shot=async name=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const tap=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 return {s,js,go,login,until,shot,tap};}
const why=`JSON.stringify({stage:!!document.querySelector('.finale'),anims:document.getAnimations().filter(a=>a.playState==='running'&&a.effect&&a.effect.target&&!(a.effect.target.closest&&a.effect.target.closest('.sheet-body'))).map(a=>(a.animationName||a.transitionProperty||'waapi')+' on '+(a.effect.target.className||a.effect.target.tagName)),style:(document.querySelector('dialog.sheet')||{getAttribute:()=>null}).getAttribute('style')})`;
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const RECAP=`!!document.querySelector('dialog.sheet[open] .recap')`;
const CARD=`!!document.querySelector('[data-recap-card].is-rising')`;
const NOSHEET=`(__fi.opened===null&&!document.querySelector('dialog[open]'))`;
const done=`__fi.n>0&&!document.querySelector('.finale')&&${CARD}`;
// The money and the card are on the first screen: nothing scrolled the page, nothing covers the figure.
const FIRST=`(()=>{const a=document.querySelector('.night-overview .display-amount').getBoundingClientRect(),c=document.querySelector('[data-recap-card]').getBoundingClientRect();return scrollY===0&&a.top>=0&&a.bottom<=innerHeight&&c.height>=48&&c.bottom<=innerHeight})()`;
const rest=`!document.querySelector('.finale')&&!pokerStage.taken()&&document.getAnimations().filter(a=>a.playState==='running'&&a.effect&&a.effect.target&&!(a.effect.target.closest&&a.effect.target.closest('.sheet-body'))).length===0&&!(document.querySelector('dialog.sheet')||{style:{}}).style.transform`;
const facts=`({under:__fi.shots.filter(s=>s.dialog).length,held:(f=>f.length?f[f.length-1].t-f[0].t:0)(__fi.shots.filter(s=>s.ground>=0.99&&s.call.o>=0.99&&s.chips.length&&s.chips.every(c=>c.o>=0.99))),ringEarly:Math.max(0,...__fi.shots.filter(s=>s.t-__fi.first.t<300).map(s=>s.ring)),n:__fi.n,stages:__fi.stages,first:__fi.first,last:__fi.last,ring:__fi.ring,span:__fi.last.t-__fi.first.t,noSheet:__fi.opened===null,rose:__fi.rose-__fi.first.t,chips:__fi.shots[Math.max(0,__fi.shots.length-12)].chips})`;
// The chips in the order they were dealt onto the stack: each later one sits higher.
const stacked=chips=>chips.every((c,i)=>i===0||c.y<chips[i-1].y+0.5);
try {
 // ===== The host closes a session of eight, with a player's phone on the session page.
 const B=await page();await B.login('ben');await B.go(`/n/${N.ready}/`);
 const H=await page();await H.login('hana');await H.go(`/n/${N.ready}/`);
 check('ready: no finale on an open session',await H.js(`__fi.n===0&&!document.querySelector('dialog[open]')`));
 const figureBefore=await H.js(`document.querySelector('form[action$="/close/"]')?true:false`);
 check('ready: the host has the close form',figureBefore);
 await H.js(`document.querySelector('form[action$="/close/"]').requestSubmit()`);
 check('ready: the close plays the finale, then the recap card rises',await H.until(done,8000));
 await sleep(700);
 const h=await H.js(facts);
 check('ready: the first frame is the dark ground arriving with no chip at rest',h.first.ground<0.7&&h.first.chips.every(c=>c.o<0.2)&&!h.first.dialog,JSON.stringify({ground:h.first.ground,chips:h.first.chips.map(c=>c.o)}));
 check('ready: the words are "That’s the night"',h.first.words==='That’s the night',h.first.words);
 check('ready: a chip for each of the eight players, in one stack',h.chips.length===8&&stacked(h.chips)&&h.chips.every(c=>Math.abs(c.x-195)<=1),JSON.stringify(h.chips.map(c=>[c.text,Math.round(c.y)])));
 check('ready: the top result (Miguel) is the last to land and has the Brass edge',h.chips[7].top&&h.chips[7].text===await H.js(`document.querySelector('.recap-ranking>li[data-top] .chip').textContent.trim()`)&&await H.js(`document.querySelector('.recap-ranking>li[data-top]').textContent.includes('Miguel')`)&&h.chips.filter(c=>c.top).length===1,JSON.stringify(h.chips.map(c=>c.text+(c.top?'*':''))));
 check('ready: the others are not in result order',JSON.stringify(h.chips.slice(0,7).map(c=>c.text))!==JSON.stringify(await H.js(`[...document.querySelectorAll('.recap-ranking>li:not([data-top]) .chip')].map(c=>c.textContent.trim())`)),JSON.stringify(h.chips.map(c=>c.text)));
 check('ready: one Brass ring opens, and not before the top chip is on its way',h.ring>0.3&&h.ringEarly===0,JSON.stringify({ring:h.ring,early:h.ringEarly}));
 check('ready: the whole picture holds for half a second or more',h.held>=500,`${Math.round(h.held)}ms`);
 check('ready: the card rises only when the stage has gone, and no sheet opens',h.rose>=h.span-20&&h.under===0&&h.noSheet,`stage ${Math.round(h.span)}ms, card rose ${Math.round(h.rose)}ms`);
 check('ready: "Still to pay" and the card are on the first screen, at the top of the page',await H.js(FIRST));
 check('ready: one stage only',h.stages===1,`${h.stages}`);
 check('ready: at rest nothing is left: no stage, no animation, no inline style on the sheet',await H.js(rest),await H.js(why));
 await H.shot('ready-card-390');
 await H.js(`document.querySelector('[data-recap-card] [data-sheet-open=recap]').click()`);await sleep(700);
 check('ready: a tap on the card opens the recap, with focus on its Close',await H.js(`${RECAP}&&document.activeElement.matches('dialog.sheet .sheet-head button')`));
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27},H.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27},H.s);await sleep(600);
 check('ready: closing the recap gives focus back to the card, and the page stays at the top',await H.js(`!document.querySelector('dialog[open]')&&document.activeElement.matches('[data-recap-card] button')&&scrollY===0`));
 check("ready: the player's phone plays it once after its redraw",await B.until(done,9000));await sleep(700);
 const b=await B.js(facts);
 check("ready: on the player's phone no sheet opens, and the card rises after the stage",b.stages===1&&b.under===0&&b.noSheet&&b.rose>=b.span-20,`card rose ${Math.round(b.rose)}ms`);
 check("ready: on the player's phone their part and the card are on the first screen",await B.js(FIRST));
 await B.go(`/n/${N.ready}/`);await sleep(1800);
 check('ready: a reload does not replay it: no sheet, the card is still',await B.js(`__fi.n===0&&!document.querySelector('dialog[open]')&&!${CARD}`));
 await B.js(`document.querySelector('[data-sheet-open=recap]').click()`);await sleep(700);
 check('ready: the card opens the sheet with no finale',await B.js(`__fi.n===0&&${RECAP}`));

 // ===== Two players, twelve, a tie and an even session: each in a fresh browser.
 const first=async(name,options)=>{const P=await page(options);await P.login('hana');await P.go(`/n/${N[name]}/`);const ok=await P.until(done,6000);await sleep(700);return {P,ok,f:ok?await P.js(facts):null}};
 const two=await first('two');
 check('two: the finale plays with two chips, the winner on top',two.ok&&two.f.chips.length===2&&two.f.chips[1].top&&!two.f.chips[0].top&&two.f.under===0&&two.f.noSheet,two.ok?JSON.stringify(two.f.chips.map(c=>c.text+(c.top?'*':''))):'');
 const twelve=await first('twelve',{width:320,height:568});
 check('twelve at 320px: twelve chips in a stack inside the screen',twelve.ok&&twelve.f.chips.length===12&&stacked(twelve.f.chips)&&twelve.f.chips.every(c=>c.l>=0&&c.r<=320&&c.t>=0&&c.b<=568),twelve.ok?JSON.stringify(twelve.f.chips.map(c=>Math.round(c.y))):'');
 check('twelve at 320px: the words fit and the page does not scroll sideways',twelve.ok&&twelve.f.last.call.l>=0&&twelve.f.last.call.r<=320&&await twelve.P.js(`document.documentElement.scrollWidth<=320`));
 check('twelve at 320px: no sheet opens, and the money and the card are on the first screen',twelve.ok&&twelve.f.under===0&&twelve.f.noSheet&&await twelve.P.js(FIRST));
 const tied=await first('tied');
 check('tied: both top results land last, with one ring',tied.ok&&tied.f.chips.slice(-2).every(c=>c.top)&&tied.f.chips.filter(c=>c.top).length===2&&tied.f.ring>0.3&&tied.f.ringEarly===0&&await tied.P.js(`document.querySelectorAll('.recap-ranking>li[data-top]').length===2`),tied.ok?JSON.stringify(tied.f.chips.map(c=>c.text+(c.top?'*':''))):'');
 const even=await first('even');
 check('even: the finale plays with no ring and no marked chip',even.ok&&even.f.ring===0&&even.f.chips.length===3&&even.f.chips.every(c=>!c.top),even.ok?JSON.stringify({ring:even.f.ring}):'');
 const wide=await first('eight',{width:1280,height:800});
 check('wide at 1280px: the stack is in the middle, no sheet opens, the card is on the first screen',wide.ok&&wide.f.chips.every(c=>Math.abs(c.x-640)<=1)&&wide.f.under===0&&wide.f.noSheet&&await wide.P.js(FIRST));
 check('wide: at rest nothing is left',await wide.P.js(rest),await wide.P.js(why));await wide.P.shot('wide-card-1280');

 // ===== The skip: a tap over a control ends it, raises the card and presses nothing.
 const S=await page();await S.login('hana');await S.go(`/n/${N.eight}/`,0);await S.until(`__fi.n>0`,5000);await sleep(200);
 const aim=await S.js(`(()=>{const el=[...document.querySelectorAll('main a[href], main button')].find(e=>{const r=e.getBoundingClientRect();return r.width&&r.top>80&&r.bottom<innerHeight-20});if(!el)return null;const r=el.getBoundingClientRect();window.__clicked=0;el.addEventListener('click',()=>__clicked++);return {x:r.left+r.width/2,y:r.top+r.height/2,dialog:!!document.querySelector('dialog[open]')}})()`);
 const where=await S.js('location.pathname');
 await S.tap(aim.x,aim.y);
 check('skip: the tap ends the stage in that frame, before the recap was due',!aim.dialog&&await S.js(`!document.querySelector('.finale:not(.is-gone)')`));
 await sleep(700);
 check('skip: the card has risen and no sheet opened',await S.js(`${CARD}&&${NOSHEET}`));
 check('skip: the tap pressed nothing under the stage',await S.js(`__clicked===0&&location.pathname===${JSON.stringify(where)}`));
 check('skip: at rest nothing is left',await S.js(rest),await S.js(why));
 // ===== The key skip: Enter on a focused link ends it and does not follow the link.
 const K=await page();await K.login('hana');await K.go(`/n/${N.eight}/`,0);await K.until(`__fi.n>0`,5000);await sleep(150);
 await K.js(`document.querySelector('main a[href]').focus()`);const kwhere=await K.js('location.pathname');
 const enter=(type,more={})=>send('Input.dispatchKeyEvent',{type,key:'Enter',code:'Enter',windowsVirtualKeyCode:13,...(type==='keyDown'?{text:'\r'}:{}),...more},K.s);
 await enter('keyDown');
 check('keys: Enter ends the stage, and the screen stays taken while the key is down',await K.js(`!document.querySelector('.finale')&&pokerStage.taken()&&!document.querySelector('dialog[open]')`));
 await enter('keyDown',{autoRepeat:true});
 check('keys: the held key repeats and still follows no link',await K.js(`location.pathname===${JSON.stringify(kwhere)}&&pokerStage.taken()`));
 await enter('keyUp');await sleep(700);
 check('keys: the card has risen, no sheet, and Enter followed no link',await K.js(`${CARD}&&${NOSHEET}&&location.pathname===${JSON.stringify(kwhere)}`));
 // ===== A hidden tab ends it; the card is there for the return.
 const V=await page();await V.login('hana');await V.go(`/n/${N.eight}/`,0);await V.until(`__fi.n>0`,5000);await sleep(150);
 await V.js(`Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))`);
 check('hidden tab: the stage ends, the card has risen, no sheet',await V.js(`!document.querySelector('.finale')&&${CARD}&&${NOSHEET}`));
 // ===== A redraw of the session page waits for the stage (nightlive.js).
 const Q=await page();await Q.login('hana');await Q.go(`/n/${N.eight}/`,0);await Q.until(`__fi.n>0`,5000);
 check('the screen is taken while the stage plays, so the page does not redraw and no other sheet opens',await Q.js(`pokerStage.taken()&&!document.querySelector('dialog[open]')`));
 await Q.until(done,3000);await sleep(600);
 check('the screen is free again at rest, with no sheet open',await Q.js(`!pokerStage.taken()&&${CARD}&&${NOSHEET}`));
 // ===== Reached by a tap on a session card: a screen change in the same document. A tap during it ends it on that session.
 const T=await page();await T.login('hana');await T.go('/');await T.go(await T.js(`document.querySelector('main a[href^="/g/"]').getAttribute('href')`));
 const card=await T.js(`(()=>{const a=document.querySelector('main a[href="/n/${N.tied}/"]');if(!a)return false;window.__same=1;a.click();return true})()`);
 check('turbo: the group page links to the session',card);
 check('turbo: the finale plays after a screen change in the same document',await T.until(`__fi.n>0`,5000)&&await T.js(`window.__same===1`));
 await sleep(120);await T.tap(195,300);await sleep(900);
 check('turbo: a tap during it leaves the card risen on that session, no sheet',await T.js(`${CARD}&&${NOSHEET}&&location.pathname==='/n/${N.tied}/'&&!pokerStage.taken()`));

 // ===== Fail safe.
 const R=await page({reduce:true});await R.login('hana');await R.go(`/n/${N.eight}/`);await sleep(1200);
 check('reduced motion: no finale, no sheet, the card is there and does not move',await R.js(`__fi.n===0&&!document.querySelector('.finale')&&${NOSHEET}&&document.querySelector('[data-recap-card]').getAnimations().length===0`)&&await R.js(FIRST));
 const before=errors.length;const X=await page({block:true});await X.login('hana');await X.go(`/n/${N.eight}/`);await sleep(1200);
 check('Motion blocked: no finale, no sheet, the card is there, no script error',await X.js(`!window.Motion&&__fi.n===0&&${NOSHEET}&&${CARD}`)&&errors.length===before,errors.slice(before).join('; '));
 const J=await page({nojs:true});await J.login('hana');await J.go(`/n/${N.eight}/`);await sleep(600);
 await send('Emulation.setScriptExecutionDisabled',{value:false},J.s);
 check('no JavaScript: the recap facts are in the page, and the card is hidden',await J.js(`!document.querySelector('.finale')&&!document.querySelector('dialog[open]')&&document.querySelector('.recap-source .recap').getClientRects().length>0&&document.querySelector('[data-recap-card]').getClientRects().length===0`));

 // ===== Frames with the processor slowed four times.
 const L=await page();await L.login('hana');await send('Emulation.setCPUThrottlingRate',{rate:4},L.s);await L.go(`/n/${N.eight}/`,0);
 await L.until(done,12000);await sleep(1500);const slow=await L.js(`({gaps:__fi.gaps})`);const worst=Math.round(Math.max(...slow.gaps)),late=slow.gaps.filter(g=>g>50).length;
 check('slowed four times: no frame over 50ms while the stage plays',late===0,`${slow.gaps.length} frames, ${late} over 50ms, worst ${worst}ms`);
 check('no script error anywhere',errors.length===0,errors.join('; '));
 writeFileSync(`${OUT}/finale.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
process.exit(results.every(x=>x.ok)?0:1);
