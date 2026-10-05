// Screen changes without a reload (Turbo link navigation). Seed a fresh temporary database with seed.py,
// seed_end_set.py, seed_night.py and seed_opening.py. The script restarts the Django server on
// 127.0.0.1:8765 itself to produce a failed send (PN_DB names the SQLite file; PN_PORT another port).
import {spawn,execSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-navigate-review';mkdirSync(OUT,{recursive:true});
const DB=process.env.PN_DB||'/private/tmp/pn-dock-check.sqlite3';const PORT=process.env.PN_PORT||'8765';const BASE='http://127.0.0.1:'+PORT;
const M=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function stopServer(){try{execSync(`pkill -f "runserver 127.0.0.1:${PORT}"`)}catch{}}
async function startServer(){stopServer();await sleep(700);spawn('.venv/bin/python',['manage.py','runserver','127.0.0.1:'+PORT,'--noreload'],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},stdio:'ignore',detached:true}).unref();for(let i=0;i<40;i++){try{if((await fetch(BASE+'/healthz')).ok)return}catch{}await sleep(250)}throw Error('server did not start')}
rmSync('/private/tmp/pn-navigate-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9362','--user-data-dir=/private/tmp/pn-navigate-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9362/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const events=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)events.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await js('window.__mark=1')};
 const click=async(expr,ms=900)=>{await js(expr+'.click()');await sleep(ms)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const reqs=(since,type)=>events.slice(since).filter(e=>e.sessionId===s&&e.method==='Network.requestWillBeSent'&&(!type||e.params.type===type)).map(e=>e.params.request.method+' '+new URL(e.params.request.url).pathname);
 const errors=since=>events.slice(since).filter(e=>e.sessionId===s&&e.method==='Runtime.exceptionThrown').length;
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,click,shot,reqs,errors};}
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const docs=(A,since)=>A.reqs(since,'Document').length;
const pollCount=(A,since)=>events.slice(since).filter(e=>e.sessionId===A.s&&e.method==='Network.requestWillBeSent'&&e.params.request.url.includes('/state/')).length;
const friday=`[...document.querySelectorAll('a.session-link')].find(a=>a.textContent.includes('Friday table'))`;
const toSet=`document.querySelector('.night-overview a.btn-primary[href^="/s/"], .night-sets a.set-link')`;
const back=`document.querySelector('.table-bar a')`;
const total=`Number(document.querySelector('[data-watch=in-play]').dataset.value)`;
const opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1)`;
try {
 await startServer();const A=await user('hana');let mark;
 // 1. A walk through the app with no document load.
 await A.go('/');mark=events.length;
 await A.click(`document.querySelector('.home-links a[href="/g/1/"], a[href="/g/1/"]')`);
 check('home -> group by tap',await A.js(`location.pathname==='/g/1/'&&window.__mark===1`));
 await A.click(`document.querySelector('a[href$="?view=stats"]')`);await A.click(`document.querySelector('a[href$="?view=settings"]')`);
 check('group tabs by tap',await A.js(`location.search==='?view=settings'&&!!document.querySelector('#manage')&&window.__mark===1`));
 await A.click(`document.querySelector('a[href$="?view=sessions"], .pills a, nav a[href="/g/1/"]')`);await A.go('/g/1/');mark=events.length;
 await A.click(friday);check('group -> session by tap',await A.js(`location.pathname.startsWith('/n/')&&!!document.querySelector('.night-layout')&&window.__mark===1`));
 await A.click(toSet);check('session -> set by tap',await A.js(`location.pathname==='/s/3/'&&!!document.getElementById('live')&&window.__mark===1`));
 await A.click(`document.querySelector('a[href="/s/3/log/"]')`);check('set -> log by tap',await A.js(`location.pathname==='/s/3/log/'&&window.__mark===1`));
 await A.click(`document.querySelector('.table-bar a, p.small a')`);await A.click(back);await A.click(back);await A.click(`document.querySelector('.table-bar a, a.brand')`);
 check('and back to Your groups',await A.js(`location.pathname==='/'&&window.__mark===1`));
 console.log('  document loads during the walk:',docs(A,mark));
 check('the whole walk made no document load',docs(A,mark)===0&&A.errors(mark)===0);
 // 1b. A tapped link answers at once and keeps the look while its screen is on the way.
 await A.go('/g/1/');
 const lit=el=>`(()=>{const el=${el};return getComputedStyle(el).backgroundColor!=='rgba(0, 0, 0, 0)'})()`;
 check('a session row at rest has no pressed look',!(await A.js(lit(friday))));
 const at=JSON.parse(await A.js(`(()=>{${friday}.scrollIntoView({block:'center'});const b=${friday}.getBoundingClientRect();return JSON.stringify({x:b.left+b.width/2,y:b.top+b.height/2})})()`));
 await send('Input.dispatchMouseEvent',{type:'mousePressed',x:at.x,y:at.y,button:'left',clickCount:1},A.s);
 check('held down: the row looks pressed on the first frame',await A.js(`${friday}.matches(':active')`)&&await A.js(lit(friday)));
 await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:5,y:5,button:'left',buttons:1},A.s);await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:5,y:5,button:'left',clickCount:1},A.s);await sleep(200);
 check('let go elsewhere: nothing pressed, same screen',await A.js(`location.pathname==='/g/1/'`)&&!(await A.js(lit(friday))));
 await send('Network.emulateNetworkConditions',{offline:false,latency:700,downloadThroughput:-1,uploadThroughput:-1},A.s);
 await A.js(`${friday}.click()`);await sleep(250);
 check('tapped, screen on its way: the row stays pressed',await A.js(`location.pathname==='/g/1/'&&${friday}.classList.contains('is-going')`)&&await A.js(lit(friday)));
 await sleep(2200);
 check('arrived: nothing is marked',await A.js(`location.pathname.startsWith('/n/')&&!document.querySelector('.is-going,[aria-busy=true]')`));
 await A.js(`${toSet}.click()`);await sleep(250);
 check('a button link shows the busy line while its screen is on the way',await A.js(`(()=>{const el=${toSet};return !el.matches('.btn')||el.getAttribute('aria-busy')==='true'})()`));
 await sleep(2200);
 await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1},A.s);
 await A.js('history.back()');await sleep(1200);
 check('after Back: nothing is marked',await A.js(`location.pathname.startsWith('/n/')&&!document.querySelector('.is-going,[aria-busy=true]')`));
 for(const [name,el] of [['back link',back],['set link',`document.querySelector('.set-link')`]]){await A.js(`(()=>{const el=${el};if(el)el.classList.add('is-going')})()`);check(name+' has a pressed look',await A.js(`!${el}`)||await A.js(lit(el)));await A.js(`(()=>{const el=${el};if(el)el.classList.remove('is-going')})()`)}
 await A.go('/g/1/');await A.js(`document.querySelector('.tabs a:not([aria-current])').classList.add('is-going')`);
 check('a tab has a pressed look',await A.js(lit(`document.querySelector('.tabs a.is-going')`)));
 await A.go('/');await A.js(`document.querySelector('.group-home-head h2 a').classList.add('is-going')`);
 check('a group name has a pressed look',await A.js(lit(`document.querySelector('.group-home-head h2 a')`)));
 // 2. No leak after 20 screen changes.
 await A.go('/g/1/');mark=events.length;
 for(let i=0;i<5;i++){await A.click(friday,600);await A.click(toSet,600);await A.click(back,600);await A.click(back,600)}
 await A.click(friday,600);await A.click(toSet,900);
 check('after 22 screen changes: on the set page, one sheet dialog, page not reloaded',await A.js(`location.pathname==='/s/3/'&&document.querySelectorAll('dialog.sheet').length===1&&window.__mark===1`));
 let p=events.length;await sleep(8500);const onSet=pollCount(A,p);
 await A.click(back,900);p=events.length;await sleep(8500);const offSet=pollCount(A,p);
 console.log('  polls in 8.5 s on the set page:',onSet,'| after leaving it:',offSet,'| script errors:',A.errors(mark));
 check('exactly one poll loop on the set page',[2,3].includes(onSet));
 check('no poll after leaving the set page',offSet===0);
 check('no script error in 22 screen changes',A.errors(mark)===0&&docs(A,mark)===0);
 // 3. A page reached by a tap behaves as after a fresh load.
 await A.click(toSet,900);
 check('tapped-in set: dock toggle shown and collapses once per tap',await A.js(`(()=>{const t=document.querySelector('.dock-toggle');if(!t||t.hidden)return false;const b=document.documentElement.classList.contains('dock-collapsed');t.click();const ok=document.documentElement.classList.contains('dock-collapsed')!==b;t.click();return ok})()`));
 await A.click(opener,500);check('tapped-in set: one tap opens one sheet',await A.js(`document.querySelectorAll('dialog[open]').length===1`));
 // 5. In-place actions on a set reached by a tap.
 let t0=await A.js(total);await A.js(`document.querySelector('dialog [name=amount]').value='500'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('tapped-in set: a rebuy updates in place',await A.js(total)===t0+50000&&await A.js(`window.__mark===1&&!document.querySelector('dialog[open]')`));
 await A.click(opener,500);await A.js(`document.querySelector('dialog [name=amount]').value='abc'`);await A.click(`document.querySelector('dialog form [type=submit]')`,1300);
 check('tapped-in set: a refused amount keeps the sheet open',await A.js(`!!document.querySelector('dialog[open] .sheet-error')`)&&await A.js(total)===t0+50000);
 await A.click(`document.querySelector('dialog .sheet-head button')`,500);
 await A.click(`document.querySelector('a[href$="/players/add-several/"]')`,900);
 check('tapped-in Add players: the picker started',await A.js(`location.pathname.endsWith('/players/add-several/')&&(!document.querySelector('[data-pick-search-box]')||!document.querySelector('[data-pick-search-box]').hidden)&&window.__mark===1`));
 await A.go('/g/1/');await A.click(`[...document.querySelectorAll('a.session-link')].find(a=>a.textContent.includes('Rooftop table'))`);await A.click(toSet,900);
 await A.js(`(()=>{const f=document.querySelector('[data-count-input]');f.value='5';f.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('tapped-in count-up: the preview follows typing',await A.js(`document.querySelector('[data-count-preview] [data-count-label]').textContent.includes('unsaved')&&window.__mark===1`));
 // 4. Back shows a fresh page and restores the scroll position.
 await A.go('/g/1/');await A.click(friday);await A.click(toSet,900);t0=await A.js(total);await A.click(back,900);
 const B=await user('hana');await B.go('/s/3/');await B.click(opener,500);await B.js(`document.querySelector('dialog [name=amount]').value='700'`);await B.click(`document.querySelector('dialog form [type=submit]')`,1300);
 mark=events.length;await A.js('history.back()');await sleep(1300);
 check('Back returns to the set with the figure another host just changed',await A.js(`location.pathname==='/s/3/'`)&&await A.js(total)===t0+70000&&await A.js('window.__mark===1'));
 check('Back fetched the page again (nothing came from a page cache)',A.reqs(mark).some(r=>r==='GET /s/3/'));
 await A.js('history.forward()');await sleep(1200);check('Forward works',await A.js(`location.pathname.startsWith('/n/')&&window.__mark===1`));
 await A.go('/s/3/');await A.js(`window.scrollTo(0,600)`);await sleep(200);const y=await A.js('Math.round(window.scrollY)');await A.click(`document.querySelector('a[href="/s/3/log/"]')`,900);
 check('a new screen starts at the top',await A.js('Math.round(window.scrollY)')===0);
 await A.js('history.back()');await sleep(1300);console.log('  scroll before/after Back:',y,await A.js('Math.round(window.scrollY)'));
 check('Back restores the scroll position',Math.abs(await A.js('Math.round(window.scrollY)')-y)<=40);
 // 8. Announcement and focus.
 await A.go('/g/1/');await A.click(friday);
 check('the new title is announced once and focus is at the start of the content',await A.js(`document.getElementById('route-announcer').textContent===document.title&&document.querySelectorAll('#route-announcer').length===1&&document.activeElement===document.getElementById('main')`));
 // 9. A loading line for a slow screen.
 await send('Network.emulateNetworkConditions',{offline:false,latency:1500,downloadThroughput:-1,uploadThroughput:-1},A.s);
 await A.js(back+'.click()');await sleep(1100);
 check('a slow screen shows the loading line in brass',await A.js(`(()=>{const b=document.querySelector('.turbo-progress-bar');return !!b&&getComputedStyle(b).height==='3px'})()`));
 await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1},A.s);await sleep(2500);
 // 10. Anchors and leaving the app.
 await A.go('/g/1/archive/');await A.click(`document.querySelector('a[href*="#manage"]')`,900);
 check('a link with an anchor lands on its section',await A.js(`location.hash==='#manage'&&location.search==='?view=settings'&&(()=>{const t=document.getElementById('manage').getBoundingClientRect().top;return t>=0&&t<innerHeight})()&&window.__mark===1`));
 await A.js(`(()=>{const a=document.createElement('a');a.href='/admin/login/';a.id='to-admin';a.textContent='admin';document.getElementById('main').append(a)})()`);await A.click(`document.getElementById('to-admin')`,1500);
 check('a page outside the app loads the ordinary way',await A.js(`location.pathname==='/admin/login/'&&window.__mark!==1`));
 // 6. Forms that lead elsewhere, from a page reached by a tap.
 await A.go('/g/1/');await A.click(`document.querySelector('a[href$="/sessions/new/"]')`,900);
 check('tapped-in New session: the form is there',await A.js(`location.pathname.endsWith('/sessions/new/')&&window.__mark===1&&!!document.querySelector('form.form-groups')`));
 await A.js(`(()=>{const v={small_blind:'10',big_blind:'20',min_buy_in:'500',max_buy_in:'2000',default_buy_in:'1000',location:'By tap'};for(const k in v)document.querySelector('[name='+k+']').value=v[k]})()`);await A.click(`document.querySelector('form.form-groups [type=submit]')`,1500);
 check('New session posts natively and lands on a working set page',await A.js(`/^\\/s\\/\\d+\\/$/.test(location.pathname)&&window.__mark!==1&&window.pokerPage.running()&&!!document.querySelector('.host-controls')`));
 await A.go('/g/1/');await A.click(friday);await A.click(`document.querySelector('form[action$="/logout/"] button')`,1500);
 check('Log out from a tapped-in page reaches Log in',await A.js(`location.pathname==='/accounts/login/'&&!document.querySelector('.site-header')`));
 await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await A.click(`document.querySelector('form.form-section [type=submit]')`,1500);
 check('Log in works after it',await A.js(`location.pathname==='/'&&!!document.querySelector('.site-header')`));
 // Signed out: links between the entry pages, and the Show button on a tapped-in page.
 const C=await user('');await C.go('/accounts/login/');await C.js('window.__mark=1');await C.click(`document.querySelector('.entry-alt a')`,900);
 check('signed out: Log in -> Sign up by tap',await C.js(`location.pathname==='/accounts/signup/'&&window.__mark===1`));
 await C.click(`document.querySelector('[data-password-toggle]')`,300);
 check('tapped-in Sign up: Show reveals both fields, once',await C.js(`document.querySelector('[name=password1]').type==='text'&&document.querySelector('[name=password2]').type==='text'&&!document.querySelector('[data-password-toggle]').hidden`));
 // 11. An expired login during a tap.
 await A.go('/g/1/');await send('Network.clearBrowserCookies',{},A.s);await A.click(friday,1500);
 check('a tap with an expired login leads to Log in',await A.js(`location.pathname==='/accounts/login/'&&!!document.querySelector('[name=password]')`));
 await A.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91'`);await A.click(`document.querySelector('form.form-section [type=submit]')`,1500);
 check('and logging in returns to where the tap was going',await A.js(`location.pathname.startsWith('/n/')`));
 // 7. A screen change with the server unreachable shows the offline page.
 await A.go('/g/1/');await A.js(`navigator.serviceWorker.ready.then(()=>true)`);await A.go('/g/1/');stopServer();await sleep(900);
 await A.click(friday,2200);
 check('offline: a tap shows the offline page',await A.js(`document.title.startsWith("You're offline")&&!!document.getElementById('retry')`));
 await startServer();await A.click(`document.getElementById('retry')`,1500);
 check('offline: Try again reaches the screen',await A.js(`location.pathname.startsWith('/n/')&&!!document.querySelector('.night-layout')`));
 // 12. Without JavaScript a link is a link.
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go('/g/1/');mark=events.length;await A.click(friday,1200);
 check('no JavaScript: the link loads a page',await A.js(`location.pathname.startsWith('/n/')`)&&docs(A,mark)>=1);
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
 writeFileSync(`${OUT}/navigate.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close').catch(()=>{});ws.close();chrome.kill();stopServer()}
if(results.some(x=>!x.ok))process.exitCode=1;
