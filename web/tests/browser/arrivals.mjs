// Table alerts (2026-10-15): a player who arrives on another phone's set page (arrivals.js), the
// "added you" line on Your groups and the table alerts panel (alerts.js). On a fresh temporary
// database seeded with seed_arrivals.py, serve it on 127.0.0.1:8765 with VAPID_PUBLIC_KEY and
// VAPID_PRIVATE_KEY set, then run. PN_DB names the SQLite file: the other host writes to it
// through the real services, and the pages learn of it by polling. A phone's push service is
// stubbed in the page (PushManager); real delivery is checked on a phone.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-arrivals-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-arrivals.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-arrivals-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const py=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from games import services as games
from ledger import services as ledger
from groups.models import Member
from games.models import Participant
from notify.models import PushSubscription
host=Member.objects.get(user__username='ari',group__name='Arrivals')
u=uuid.uuid4
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-600));return r.stdout.trim().split('\n').at(-1)};
rmSync('/private/tmp/pn-arrivals-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-arrivals-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call and error is logged; each redraw of the set page is counted.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];window.__errors=[];window.__redraws=0;addEventListener('error',e=>__errors.push(e.message));
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className&&el.className.baseVal===undefined?el.className:el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}
 document.addEventListener('live:updated',()=>{__redraws++})})`;
// A phone's push service, stubbed: the subscription and the permission live in localStorage.
const PUSH=`(()=>{if(!window.PushManager)return;const S='__fake_sub',P='__fake_perm';
 const perm=()=>localStorage.getItem(P)||'default';
 Object.defineProperty(Notification,'permission',{configurable:true,get:perm});
 const fake=()=>({endpoint:'https://push.example.com/send/browser-check',toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'BPhoneKey',auth:'secret'}}},unsubscribe(){localStorage.removeItem(S);return Promise.resolve(true)}});
 PushManager.prototype.subscribe=function(){if(perm()==='denied')return Promise.reject(new DOMException('denied','NotAllowedError'));localStorage.setItem(P,'granted');localStorage.setItem(S,'1');return Promise.resolve(fake())};
 PushManager.prototype.getSubscription=function(){return Promise.resolve(localStorage.getItem(S)?fake():null)};})()`;
async function user(name,width=390,{reduce=false,push=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:1,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);if(push)await send('Page.addScriptToEvaluateOnNewDocument',{source:PUSH},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // The next redraw of the set page; the poll is asked at once instead of after 4s.
 const redraw=async(poke=true)=>{const n=await js('__redraws');if(poke)await js(`window.dispatchEvent(new Event('online'))`);for(let i=0;i<120;i++){if(await js('__redraws')>n){await sleep(120);return true}await sleep(50)}return false};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 return {s,js,go,shot,redraw};}
// Toasts keep their separate y (DESIGN.md, motion stage 2, rule 4); everything new moves by transform and opacity.
const only=`__runs.filter(r=>!r.el.includes('toast')).every(r=>r.keys.every(k=>['transform','opacity'].includes(k)))`;
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const row=n=>`document.querySelector('#live li.player-row[data-name="${n}"]')`;
const marked=n=>`(()=>{const r=${row(n)};if(!r)return null;const b=[...r.querySelectorAll('.change-label')].find(b=>b.getClientRects().length);return {mark:r.classList.contains('just-changed'),badge:b?b.textContent:null,before:getComputedStyle(r,'::before').borderTopColor}})()`;
const toasts=`[...document.querySelectorAll('.message-arrival:not(.leaving)')].map(t=>t.querySelector('span').textContent)`;
const inView=n=>`(()=>{const b=${row(n)}.getBoundingClientRect();return b.top>=0&&b.bottom<=innerHeight})()`;

// --- 390: the arrival out of view, a toast with Show, two at once ---------------------------------
{const S=M.narrow,[a,b,c]=S.names,W='390px';
 const P=await user('bea',390);await P.go(`/s/${S.set}/`);
 check(`${W} first sight: nothing marked, no toast`,await P.js(`!document.querySelector('.just-changed')&&!document.querySelector('.message-arrival')`));
 py(`games.add_participants(${S.set},host,[${S.spare[0]}],u())`);
 check(`${W} the poll brings the new row`,await P.redraw());
 const m=await P.js(marked(a));
 check(`${W} the new row carries the brass mark and "Joined"`,m&&m.mark&&m.badge==='Joined');
 check(`${W} the row rose and its badge sprang (Motion)`,await P.js(`__runs.some(r=>r.el.includes('player-row'))&&__runs.some(r=>r.el.includes('change-label'))`));
 check(`${W} the players count draws its line`,await P.js(`!!document.querySelector('[data-player-count].count-arrived')`));
 check(`${W} the row is below the fold, so a toast names it`,!(await P.js(inView(a)))&&JSON.stringify(await P.js(toasts))===JSON.stringify([`${a} joined`]));
 check(`${W} the toast has Show and Dismiss, and the hidden line stays empty (the toast speaks)`,await P.js(`(()=>{const t=document.querySelector('.message-arrival');return [...t.querySelectorAll('button')].map(b=>b.textContent).join()==='Show,Dismiss'&&t.closest('[role=status]')!==null&&document.getElementById('arrival-news').textContent===''})()`));
 await P.shot('arrival-toast-390');
 await P.js(`[...document.querySelectorAll('.message-arrival button')].find(b=>b.textContent==='Show').click()`);await sleep(900);
 check(`${W} Show brings the row into view`,await P.js(inView(a)));
 check(`${W} Show marks the row again`,(await P.js(marked(a))).mark);
 check(`${W} Show puts focus on the row`,await P.js(`document.activeElement.closest('li')===${row(a)}`));
 check(`${W} Show dismisses the toast`,(await P.js(toasts)).length===0);
 await P.shot('arrival-show-390');
 await sleep(3300);
 check(`${W} after three seconds the mark and badge are gone`,await P.js(`(()=>{const r=${row(a)};return !r.classList.contains('just-changed')&&[...r.querySelectorAll('.change-label')].every(b=>b.hidden)})()`));
 await P.js(`scrollTo(0,0)`);await sleep(200);
 py(`games.add_participants(${S.set},host,[${S.spare[1]},${S.spare[2]}],u())`);
 await P.redraw();
 check(`${W} two at once: one toast names both`,JSON.stringify(await P.js(toasts))===JSON.stringify([`${b} and ${c} joined`]));
 check(`${W} two at once: both rows marked`,(await P.js(marked(b))).badge==='Joined'&&(await P.js(marked(c))).badge==='Joined');
 check(`${W} no script error`,(await P.js('__errors')).length===0);
 check(`${W} Motion animates only transform and opacity`,await P.js(only));
}

// --- 1280: in view, so no toast but a line for screen readers; a redraw keeps the mark --------------
{const S=M.wide,[a,b,c]=S.names,W='1280px';
 const P=await user('bea',1280);await P.go(`/s/${S.set}/`);
 py(`games.add_participants(${S.set},host,[${S.spare[0]}],u())`);await P.redraw();
 check(`${W} the new row is in view: no toast`,await P.js(inView(a))&&(await P.js(toasts)).length===0);
 await sleep(100);
 check(`${W} screen readers hear who joined`,await P.js(`document.getElementById('arrival-news').textContent`)===`${a} joined the set.`);
 await P.shot('arrival-inview-1280');
 // A buy-in for someone else redraws the page within the three seconds: the new row stays marked.
 py(`p=Participant.objects.get(session_id=${S.set},member__user__username='bea');ledger.record_buy_in(${S.set},host,p.pk,100000,u())`);await P.redraw();
 check(`${W} a redraw within the hold keeps the new row's mark`,(await P.js(marked(a))).badge==='Joined');
 // The host's own add, sent in place: the row is marked, nothing is announced as someone else's.
 const H=await user('ari',1280);await H.go(`/s/${S.set}/`);
 await H.js(`(()=>{const f=document.querySelector('form[action$="/players/add/"] select#add-player').form;f.querySelector('select').value='${S.spare[1]}';f.requestSubmit()})()`);
 await H.redraw(false);await sleep(200);
 check(`${W} the host's own add: the row is marked`,(await H.js(marked(b)))?.badge==='Joined');
 check(`${W} the host's own add: no toast and no announcement`,(await H.js(toasts)).length===0&&await H.js(`document.getElementById('arrival-news').textContent`)==='');
 check(`${W} no script error`,(await P.js('__errors')).length+(await H.js('__errors')).length===0);
}

// --- Reduced motion: the mark without movement -----------------------------------------------------
{const S=M.still,[a]=S.names,W='390px reduced motion';
 const P=await user('dan',390,{reduce:true});await P.go(`/s/${S.set}/`);
 py(`games.add_participants(${S.set},host,[${S.spare[0]}],u())`);await P.redraw();
 const m=await P.js(marked(a));
 check(`${W}: the row is marked "Joined"`,m&&m.mark&&m.badge==='Joined');
 check(`${W}: nothing moved`,await P.js(`__runs.length===0&&getComputedStyle(${row(a)}).transform==='none'`));
 check(`${W}: the toast still names the row`,(await P.js(toasts)).length===1);
}

// --- Your groups: "added you" arrives with a refresh and leaves once the set is opened ---------------
{const S=M.draft,W='Your groups';
 const P=await user('cal',390,{push:true});await P.go('/');
 check(`${W}: no line before the set opens`,await P.js(`!document.querySelector('[data-added]')`));
 py(`h=Member.objects.get(pk=${S.host_member});games.transition(${S.set},h,'open')`);
 let line=null;for(let i=0;i<60&&!line;i++){await sleep(250);line=await P.js(`(()=>{const l=document.querySelector('[data-added]');return l?{text:l.textContent,primary:l.closest('section').querySelector('a.btn').classList.contains('btn-primary')}:null})()`)}
 check(`${W}: the refresh brings "ari added you" with the set's button leading`,line&&line.text==='ari added you'&&line.primary);
 await sleep(100);
 check(`${W}: the line rose and its dot sprang`,await P.js(`__runs.some(r=>r.el.includes('band-added'))&&__runs.some(r=>r.el.includes('added-dot'))`));
 await sleep(600);
 check(`${W}: at rest, no inline style left`,await P.js(`(()=>{const l=document.querySelector('[data-added]');return !l.getAttribute('style')&&getComputedStyle(l).opacity==='1'})()`));
 await P.shot('added-you-390');
 await P.go(`/s/${S.set}/`);await P.go('/');
 check(`${W}: gone once the set was opened`,await P.js(`!document.querySelector('[data-added]')`));

 // --- The alerts panel, with the push service stubbed -----------------------------------------------
 const shown=async()=>{for(let i=0;i<40;i++){const v=await P.js(`(()=>{const p=document.getElementById('alerts');if(!p||p.hidden)return null;const s=p.querySelector('[data-alerts-state]:not([hidden])');return s?s.dataset.alertsState:null})()`);if(v)return v;await sleep(100)}return null};
 const W2='Alerts panel';
 check(`${W2}: asks, with two 48px buttons`,await shown()==='ask'&&await P.js(`[...document.querySelectorAll('#alerts .alerts-ask button')].every(b=>b.getBoundingClientRect().height>=48)`));
 await P.js(`document.getElementById('alerts').scrollIntoView({block:'center'})`);await sleep(150);await P.shot('alerts-ask-390');
 await P.js(`document.querySelector('[data-alerts-later]').click()`);await sleep(600);
 check(`${W2}: Not now hides it`,await P.js(`document.getElementById('alerts').hidden`));
 await P.go('/');await sleep(800);
 check(`${W2}: and it stays hidden on the next visit`,await P.js(`document.getElementById('alerts').hidden`));
 await P.js(`localStorage.removeItem('pn-alerts-later')`);await P.go('/');
 check(`${W2}: asks again when Not now is forgotten`,await shown()==='ask');
 await P.js(`document.querySelector('[data-alerts-on]').click()`);await sleep(900);
 check(`${W2}: Turn on shows the on line with focus on Turn off`,await shown()==='on'&&await P.js(`document.activeElement.matches('[data-alerts-off]')`));
 check(`${W2}: the server holds the phone`,py(`print(PushSubscription.objects.filter(user__username='cal').count())`)==='1');
 check(`${W2}: the tick sprang`,await P.js(`__runs.some(r=>r.el.includes('alerts-tick'))`));
 await P.js(`document.getElementById('alerts').scrollIntoView({block:'center'})`);await sleep(150);await P.shot('alerts-on-390');
 await P.js(`document.querySelector('[data-alerts-off]').click()`);await sleep(900);
 check(`${W2}: Turn off asks again and the server forgets the phone`,await shown()==='ask'&&py(`print(PushSubscription.objects.count())`)==='0');
 await P.js(`localStorage.setItem('__fake_perm','denied')`);await P.go('/');
 check(`${W2}: blocked in the phone's settings says so`,await shown()==='blocked');
 await P.js(`document.getElementById('alerts').scrollIntoView({block:'center'})`);await sleep(150);await P.shot('alerts-blocked-390');
 check(`${W2}: no script error`,(await P.js('__errors')).length===0);
 check(`${W2}: Motion animates only transform and opacity`,await P.js(only));
}

const failed=results.filter(r=>!r.ok);
console.log(`\n${results.length-failed.length} of ${results.length} passed`);
ws.close();chrome.kill();process.exit(failed.length?1:0);
