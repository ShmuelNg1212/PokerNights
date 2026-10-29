// Filters on past sessions and a corrected end time (2026-10-29).
// Seed a fresh temporary database with seed_past_filters.py alone, serve it on 127.0.0.1:8765, then run.
// Reads ids from /private/tmp/pn-past-filters-manifest.json. Logs in as ben (player) and hana (host).
import {spawn,execSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-past-filters-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-past-filters-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-past-filters-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir=/private/tmp/pn-past-filters-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,width=390,{reduce=false,noJs=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:2,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__errors=[];addEventListener('error',e=>__errors.push(e.message))`},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const tapAt=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 const tap=async sel=>{const p=await js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await tapAt(p.x,p.y)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 if(noJs)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,tap,tapAt};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,400)}`)};
const rows=`[...document.querySelectorAll('.ledger .session-link')].map(a=>a.getAttribute('href'))`;
const pills=`(()=>{const n=document.querySelector('.past-filters');if(!n)return null;return [...n.querySelectorAll('a')].map(a=>({text:a.textContent.trim(),current:a.hasAttribute('aria-current'),h:Math.round(a.getBoundingClientRect().height),href:a.getAttribute('href')}))})()`;
const night=id=>`/n/${id}/`;

for(const width of [320,390,1280]){
 const B=await user('ben',width);await B.go(`/g/${M.group}/`);
 const tag=`${width} ben`;
 const p=await B.js(pills);
 check(`${tag} three chips, All marked`,p&&p.length===3&&p[0].current&&!p[1].current,p);
 check(`${tag} chips are at least 48px`,p&&p.every(x=>x.h>=48),p);
 check(`${tag} chip counts: 2 not settled, 2 played`,p&&/Not settled\s*2/.test(p[1].text)&&/I played\s*2/.test(p[2].text),p);
 check(`${tag} no horizontal overflow`,!(await B.js(`document.documentElement.scrollWidth>innerWidth`)));
 check(`${tag} all three nights listed`,(await B.js(rows)).length===3,await B.js(rows));
 await B.tap('.past-filters a:nth-child(2)');await sleep(1200);
 check(`${tag} Not settled: the URL carries the filter`,(await B.js('location.search'))==='?past=unsettled',await B.js('location.href'));
 const r=await B.js(rows);
 check(`${tag} Not settled: only the owing and missed nights`,JSON.stringify(r)===JSON.stringify([night(M.away),night(M.owing)]),r);
 check(`${tag} Not settled is marked`,(await B.js(pills))[1].current);
 await B.tap('.past-filters a:nth-child(3)');await sleep(1200);
 const m=await B.js(rows);
 check(`${tag} I played: only Ben's nights`,JSON.stringify(m)===JSON.stringify([night(M.owing),night(M.settled)]),m);
 check(`${tag} no script error`,(await B.js('window.__errors')).length===0,await B.js('window.__errors'));
 await B.shot(`filters-ben-${width}`);
}
{
 const N=await user('ben',390,{noJs:true});await N.go(`/g/${M.group}/?past=unsettled`);
 check('no JS: a filtered address shows only the unsettled nights',(await N.js(rows)).length===2,await N.js(rows));
}

// The host moves the end of play 30 minutes earlier on the counting page.
{
 const H=await user('hana',390);await H.go(`/s/${M.counting}/`);
 await H.tap('details.host-more > summary');await sleep(300);
 check('host: "Wrong end time?" is under More host controls',await H.js(`!!document.querySelector('details.host-more details[data-key=end-time]')`));
 await H.tap('details[data-key=end-time] > summary');await sleep(300);
 const before=await H.js(`document.querySelector('#end-time').value`);
 const target=new Date(Date.parse(before+':00Z')-30*60000).toISOString().slice(0,16);
 check('host: the field opens at the recorded end',/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(before),before);
 const field=await H.js(`(()=>{const r=document.querySelector('#end-time').getBoundingClientRect();return Math.round(r.height)})()`);
 check('host: the time field is at least 48px',field>=48,field);
 await H.shot('end-time-form-390');
 await H.js(`document.querySelector('#end-time').value=${JSON.stringify(target)};document.querySelector('#end-time-reason').value='Tapped late'`);
 await H.tap('details[data-key=end-time] button[type=submit]');await sleep(1500);
 const text=await H.js('document.body.innerText');
 check('host: a toast names the new time',/End time set to \d{1,2}:\d\d [AP]M\./.test(text),text.slice(0,300));
 await H.tap('details.host-more > summary');await sleep(200);await H.js(`document.querySelector('details[data-key=end-time]').open=true`);
 check('host: the form now opens at the new end',(await H.js(`document.querySelector('#end-time').value`))===target,[target,await H.js(`document.querySelector('#end-time').value`)]);
 await H.go(`/s/${M.counting}/log/`);
 check('host: the log records the correction',/Corrected the end of play from/.test(await H.js('document.body.innerText')));
 check('host: no script error',(await H.js('window.__errors')||[]).length===0);
 const P=await user('ben',390);await P.go(`/s/${M.counting}/`);
 check('player: no "Wrong end time?"',!(await P.js(`document.body.innerHTML.includes('Wrong end time?')`)));
}
const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed}/${results.length} passed`);
ws.close();chrome.kill();process.exit(failed?1:0);
