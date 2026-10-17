// Table alerts in the header (2026-10-16): the bell, its panel and the once-per-window reminder
// (alerts.js). Uses the arrivals fixtures: on a fresh temporary database seeded with
// seed_arrivals.py, serve it on 127.0.0.1:8765 with VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY set,
// then run. A phone's push service is stubbed in the page (PushManager); real delivery is
// checked on a phone. Each browser context is a new window, so a new app session.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-alerts-bell-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-arrivals.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-arrivals-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const py=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`from notify.models import PushSubscription
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-600));return r.stdout.trim().split('\n').at(-1)};
rmSync('/private/tmp/pn-alerts-bell-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9343','--user-data-dir=/private/tmp/pn-alerts-bell-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9343/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call and error is logged; so is each start of the bell's swing.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];window.__errors=[];window.__swings=0;addEventListener('error',e=>__errors.push(e.message));
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className&&el.className.baseVal===undefined?el.className:el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}
 document.addEventListener('animationstart',e=>{if(e.animationName==='alerts-swing')__swings++})});
 window.__morphs=0;document.addEventListener('turbo:render',e=>{if(e.detail.renderMethod==='morph')__morphs++})`;
// A phone's push service, stubbed: the subscription and the permission live in localStorage.
const PUSH=`(()=>{if(!window.PushManager)return;const S='__fake_sub',P='__fake_perm';
 const perm=()=>localStorage.getItem(P)||'default';
 Object.defineProperty(Notification,'permission',{configurable:true,get:perm});
 const fake=()=>({endpoint:'https://push.example.com/send/bell-check',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'BPhoneKey',auth:'secret'}}},unsubscribe(){localStorage.removeItem(S);return Promise.resolve(true)}});
 PushManager.prototype.subscribe=function(){if(perm()==='denied')return Promise.reject(new DOMException('denied','NotAllowedError'));localStorage.setItem(P,'granted');localStorage.setItem(S,'1');return Promise.resolve(fake())};
 PushManager.prototype.getSubscription=function(){return Promise.resolve(localStorage.getItem(S)?fake():null)};})()`;
// An iPhone's browser: no PushManager outside the Home Screen app.
const IPHONE='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const ANDROID='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36';
async function user(name,width=390,{reduce=false,push=true,agent=null,noPush=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:1,mobile:width<900},s);
 if(agent)await send('Emulation.setUserAgentOverride',{userAgent:agent},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 if(noPush)await send('Page.addScriptToEvaluateOnNewDocument',{source:'delete window.PushManager'},s);
 else if(push)await send('Page.addScriptToEvaluateOnNewDocument',{source:PUSH},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // Through the real form: the login lands on Your groups as a new arrival.
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(300);
 for(let i=0;i<30;i++){if(await js(`location.pathname==='/'&&document.readyState==='complete'`))break;await sleep(100)}
 return {s,js,go,shot};}
const only=`__runs.filter(r=>!r.el.includes('toast')).every(r=>r.keys.every(k=>['transform','opacity'].includes(k)))`;
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const bell=`(()=>{const b=document.getElementById('alerts');if(!b||b.hidden)return null;const p=b.querySelector('.alerts-panel'),s=p.querySelector('[data-alerts-state]:not([hidden])');
 const glyph=[...b.querySelectorAll('.alerts-glyphs .icon')].find(g=>getComputedStyle(g).opacity==='1');
 return {state:b.dataset.state,label:b.querySelector('[data-alerts-bell]').getAttribute('aria-label'),expanded:b.querySelector('[data-alerts-bell]').getAttribute('aria-expanded'),open:!p.hidden,
  shown:s?s.dataset.alertsState:null,later:!b.querySelector('[data-alerts-later]').hidden,glyph:glyph?[...glyph.classList].find(c=>c.startsWith('icon-')):null}})()`;
const until=async(P,test,ms=3000)=>{for(let t=0;t<ms;t+=100){const v=await P.js(bell);if(v&&test(v))return v;await sleep(100)}return await P.js(bell)};
const targets=`[...document.querySelectorAll('#alerts .alerts-panel button:not([hidden]), #alerts [data-alerts-bell]')].filter(b=>b.getClientRects().length).every(b=>b.getBoundingClientRect().height>=48||b.classList.contains('link-button')&&b.getBoundingClientRect().height>=44)`;
const inside=`(()=>{const r=document.querySelector('#alerts .alerts-panel').getBoundingClientRect();return r.left>=8&&r.right<=innerWidth-8})()`;
const noOverflow=`document.documentElement.scrollWidth<=innerWidth`;
const focusIs=sel=>`document.activeElement&&document.activeElement.matches(${JSON.stringify(sel)})`;

// --- 390: the reminder after a login, Not now, once per window -------------------------------------
{const W='390 reminder';const P=await user('cal',390);
 let b=await until(P,v=>v.open,4000);
 check(`${W}: the panel opens by itself in the ask state, with Not now`,b&&b.open&&b.shown==='ask'&&b.later&&b.expanded==='true');
 check(`${W}: the bell is the outline one, named "Table alerts, off"`,b.glyph==='icon-bell'&&b.label==='Table alerts, off');
 check(`${W}: the bell swung once`,await P.js('__swings')===1);
 check(`${W}: the panel grew from the bell (Motion)`,await P.js(`__runs.some(r=>r.el.includes('alerts-panel'))`));
 check(`${W}: focus stays where it was`,!(await P.js(`document.getElementById('alerts').contains(document.activeElement)`)));
 check(`${W}: screen readers hear it`,(await P.js(`document.getElementById('route-announcer').textContent`)).startsWith('Table alerts are off.'));
 await sleep(500);
 check(`${W}: 48px targets`,await P.js(targets));
 check(`${W}: inside the screen`,await P.js(inside));
 check(`${W}: no horizontal scroll`,await P.js(noOverflow));
 check(`${W}: the caret points at the bell`,await P.js(`(()=>{const p=document.querySelector('#alerts .alerts-panel'),b=document.querySelector('[data-alerts-bell]').getBoundingClientRect(),c=p.getBoundingClientRect().right-parseFloat(p.style.getPropertyValue('--caret'));return Math.abs(c-(b.left+b.width/2))<2})()`));
 await sleep(700);await P.shot('reminder-390');
 await P.js(`document.querySelector('[data-alerts-later]').click()`);await sleep(400);
 b=await P.js(bell);
 check(`${W}: Not now closes it and puts focus on the bell`,!b.open&&b.expanded==='false'&&await P.js(focusIs('[data-alerts-bell]')));
 await P.go(`/g/${py(`from groups.models import GameGroup;print(GameGroup.objects.get(name='Quiet room').pk)`)}/`);await P.go('/');await sleep(2000);
 check(`${W}: not again in this window`,!(await P.js(bell)).open);

 // --- The bell by hand: open, Escape, outside tap, Turn on, Turn off ------------------------------------
 const V='390 bell';
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(350);
 b=await P.js(bell);
 check(`${V}: a tap opens the panel without Not now and focuses Turn on`,b.open&&!b.later&&await P.js(focusIs('[data-alerts-on]')));
 await P.js(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))`);await sleep(350);
 check(`${V}: Escape closes it and focus returns to the bell`,!(await P.js(bell)).open&&await P.js(focusIs('[data-alerts-bell]')));
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(300);
 await P.js(`document.querySelector('.page-heading h1').click()`);await sleep(350);
 check(`${V}: a tap outside closes it`,!(await P.js(bell)).open);
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(300);
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(350);
 check(`${V}: the bell again closes it`,!(await P.js(bell)).open);
 // Open, then something changes for cal: Your groups redraws in place and the panel stays open.
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(300);
 const morphs=await P.js('__morphs');
 py(`from games import services as games;from groups.models import Member;games.transition(${M.draft.set},Member.objects.get(pk=${M.draft.host_member}),'open')`);
 let redrawn=false;for(let i=0;i<60&&!redrawn;i++){await sleep(250);redrawn=await P.js(`__morphs>${morphs}&&!!document.querySelector('[data-added]')`)}
 check(`${V}: Your groups still refreshes while the panel is open, and the panel stays open`,redrawn&&(await P.js(bell)).open);
 await P.js(`document.querySelector('[data-alerts-on]').click()`);await sleep(700);
 b=await P.js(bell);
 check(`${V}: Turn on shows "On for this phone." with focus on Turn off`,b.shown==='on'&&await P.js(focusIs('[data-alerts-off]'))&&await P.js(`document.querySelector('[data-alerts-state=on]').textContent.includes('On for this phone.')`));
 check(`${V}: the bell is filled and named "Table alerts, on"`,b.glyph==='icon-bell-filled'&&b.label==='Table alerts, on');
 check(`${V}: the server holds the phone`,py(`print(PushSubscription.objects.filter(user__username='cal').count())`)==='1');
 check(`${V}: the tick sprang`,await P.js(`__runs.some(r=>r.el.includes('alerts-tick'))`));
 await P.shot('on-390');
 // On another page the bell keeps its state; Turn off from there.
 await P.go(`/g/${py(`from groups.models import GameGroup;print(GameGroup.objects.get(name='Quiet room').pk)`)}/`);
 check(`${V}: the next page's bell is still on`,(await P.js(bell)).state==='on');
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(300);
 await P.js(`document.querySelector('[data-alerts-off]').click()`);await sleep(700);
 b=await P.js(bell);
 check(`${V}: Turn off asks again and the server forgets the phone`,b.shown==='ask'&&b.glyph==='icon-bell'&&py(`print(PushSubscription.objects.filter(user__username='cal').count())`)==='0');
 check(`${V}: no script error`,(await P.js('__errors')).length===0);
 check(`${V}: Motion animates only transform and opacity`,await P.js(only));
}

// --- A new window reminds again; never on a set page; never when on or blocked -------------------------
{const W='new window';const P=await user('bea',390);
 check(`${W}: the reminder comes again`,(await until(P,v=>v.open,4000)).open);
 await P.js(`document.querySelector('[data-alerts-later]').click()`);await sleep(300);
 await P.js(`sessionStorage.removeItem('pn-alerts-reminded')`);
 await P.go(`/s/${M.narrow.set}/`);await sleep(2000);
 const b=await P.js(bell);
 check(`${W}: the set page has the bell but never reminds`,b&&b.state==='ask'&&!b.open);
 await P.shot('set-page-390');
 await P.js(`localStorage.setItem('__fake_perm','denied')`);await P.go('/');await sleep(2000);
 const d=await P.js(bell);
 check(`${W}: blocked: slashed bell, "Table alerts, blocked", no reminder`,d.state==='blocked'&&d.glyph==='icon-bell-off'&&d.label==='Table alerts, blocked'&&!d.open);
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(350);
 check(`${W}: blocked: the panel says where to change it`,(await P.js(`document.querySelector('[data-alerts-state=blocked]').textContent`)).includes('phone’s settings'));
 await P.shot('blocked-390');
 await P.js(`localStorage.removeItem('__fake_perm');localStorage.setItem('__fake_sub','1');sessionStorage.removeItem('pn-alerts-reminded')`);await P.go('/');await sleep(2000);
 check(`${W}: on: no reminder`,(await P.js(bell)).state==='on'&&!(await P.js(bell)).open);
 check(`${W}: no script error`,(await P.js('__errors')).length===0);
}

// --- An Android phone's browser: the home-screen sheet goes first --------------------------------------
{const W='Android';const P=await user('dan',390,{agent:ANDROID});
 await sleep(2200);
 check(`${W}: the home-screen sheet opened and the reminder gave way`,await P.js(`!!document.querySelector('#install-sheet[open]')`)&&!(await P.js(bell)).open);
 await P.js(`document.querySelector('[data-install-close]').click()`);await sleep(500);
 await P.go(`/s/${M.still.set}/`);await P.go('/');
 check(`${W}: the next visit to Your groups reminds`,(await until(P,v=>v.open,3000)).open);
 check(`${W}: no script error`,(await P.js('__errors')).length===0);
}

// --- An iPhone's browser: the bell offers the home-screen sheet ---------------------------------------
{const W='iPhone Safari';const P=await user('bea',390,{agent:IPHONE,noPush:true});
 await sleep(2200);
 let b=await P.js(bell);
 check(`${W}: the bell shows in the install state, outline, and does not remind`,b&&b.state==='install'&&b.glyph==='icon-bell'&&!b.open);
 if(await P.js(`!!document.querySelector('#install-sheet[open]')`)){await P.js(`document.querySelector('[data-install-close]').click()`);await sleep(500)}
 await P.js(`document.querySelector('[data-alerts-bell]').click()`);await sleep(350);
 check(`${W}: its panel says alerts work from the Home Screen app`,(await P.js(`document.querySelector('[data-alerts-state=install]').textContent`)).includes('Home Screen app')&&await P.js(focusIs('[data-alerts-install]')));
 await P.shot('install-390');
 await P.js(`document.querySelector('[data-alerts-install]').click()`);await sleep(700);
 check(`${W}: Add to Home Screen closes the panel and opens the sheet`,!(await P.js(bell)).open&&await P.js(`!!document.querySelector('#install-sheet[open]')`));
 await P.js(`document.querySelector('[data-install-close]').click()`);await sleep(500);
 check(`${W}: closing the sheet returns focus to the bell`,await P.js(focusIs('[data-alerts-bell]')));
 check(`${W}: no script error`,(await P.js('__errors')).length===0);
}

// --- 320 and 1280: the header keeps one line; the panel fits ---------------------------------------------
{const P=await user('ari',320);await until(P,v=>v.open,4000);await sleep(500);
 check(`320: the brand, the bell and the account token share one line`,await P.js(`(()=>{const h=document.querySelector('.site-header'),t=[h.querySelector('.brand'),h.querySelector('[data-alerts-bell]'),h.querySelector('.account-button')].map(e=>e.getBoundingClientRect());return t.every(r=>Math.abs((r.top+r.bottom)/2-(t[0].top+t[0].bottom)/2)<4)})()`));
 check(`320: the panel is inside the screen with 48px targets, no horizontal scroll`,await P.js(inside)&&await P.js(targets)&&await P.js(noOverflow));
 await sleep(500);await P.shot('reminder-320');
 const Q=await user('cal',1280);await until(Q,v=>v.open,4000);await sleep(500);
 check(`1280: the panel sits under the bell, inside the screen`,await Q.js(`(()=>{const p=document.querySelector('#alerts .alerts-panel').getBoundingClientRect(),b=document.querySelector('[data-alerts-bell]').getBoundingClientRect();return p.top>=b.bottom&&p.right>=b.right-8&&p.right<=innerWidth})()`));
 await sleep(500);await Q.shot('reminder-1280');
 check(`320 and 1280: no script error`,(await P.js('__errors')).length+(await Q.js('__errors')).length===0);
}

// --- Reduced motion: the reminder without movement -----------------------------------------------------
{const W='390 reduced motion';const P=await user('bea',390,{reduce:true});
 const b=await until(P,v=>v.open,4000);
 check(`${W}: the reminder opens`,b.open&&b.later);
 check(`${W}: nothing moved and the bell did not swing`,await P.js(`__runs.length===0&&__swings===0`));
}

const failed=results.filter(r=>!r.ok);
console.log(`\n${results.length-failed.length} of ${results.length} passed`);
ws.close();chrome.kill();process.exit(failed.length?1:0);
