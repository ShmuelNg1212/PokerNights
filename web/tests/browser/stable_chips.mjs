// One chip per member in a group (ADR 0015). Seed a fresh database with seed.py, seed_end_set.py,
// seed_night.py, seed_opening.py and seed_home.py (its group 2 has 14 players and group 4 a 60-character name), serve it on 127.0.0.1:8765 (PN_BROWSER_URL), then run.
// Reads every chip that names a member (data-m) on eleven pages and fails when one member is drawn two ways.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-stable-chips';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const PORT=process.env.PN_CDP_PORT || '9351';const PROFILE=`/private/tmp/pn-stable-chips-chrome-${PORT}`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,width=390){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const h=await js('Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)');await send('Emulation.setDeviceMetricsOverride',{width,height:Math.min(h,5200),deviceScaleFactor:1,mobile:width<900},s);await sleep(150);const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'));await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {js,go,shot};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,600)}`)};
// Each chip that names a member: its colour class and its label. Clones made by motion scripts drop data-m.
const READ=`[...document.querySelectorAll('.chip[data-m]')].filter(c=>c.dataset.m).map(c=>[c.dataset.m,[...c.classList].find(k=>/^k\\d+$/.test(k)),c.textContent.trim()])`;
const seen={};const note=(page,chips)=>{for(const [m,k,label] of chips){(seen[m] ||= new Map()).set(`${k} ${label}`,(seen[m].get(`${k} ${label}`)||[]).concat(page))}};
try{
 const pages=[['hana','/s/3/'],['hana','/s/2/'],['hana','/s/1/'],['hana','/n/1/'],['hana','/n/12/'],['hana','/g/1/?view=players'],['hana','/g/1/?view=stats'],['ben','/'],['mara','/'],['mara','/g/2/?view=players'],['mara','/g/4/?view=players']];
 const who={};
 for(const [name,path] of pages){who[name] ||= await user(name);const A=who[name];await A.go(path);const chips=await A.js(READ);note(`${name} ${path}`,chips);
  check(`${name} ${path}: chips that name a member are drawn`,chips.length>0,chips.length);
  await A.shot(`${name}${path.replace(/[\/?=]+/g,'_')}`);}
 const split=Object.entries(seen).filter(([,ways])=>ways.size>1).map(([m,ways])=>({member:m,ways:Object.fromEntries(ways)}));
 check(`each member has one colour and one label on all eleven pages (${Object.keys(seen).length} members)`,split.length===0,split.slice(0,4));
 const wide=await user('hana',1280);await wide.go('/s/3/');note('hana 1280 /s/3/',await wide.js(READ));await wide.shot('hana_1280_s_3');
 check('at 1280 px the set page draws the same chips as at 390 px',Object.values(seen).every(w=>w.size===1),Object.entries(seen).filter(([,w])=>w.size>1).map(([m,w])=>[m,[...w.keys()]]).slice(0,4));
}finally{
 const failed=results.filter(r=>!r.ok).length;console.log(`${results.length-failed}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed?1:0;
}
