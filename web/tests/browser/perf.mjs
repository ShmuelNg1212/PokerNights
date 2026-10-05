// The on-phone readout ("?perf=1", static/js/perf.js) and the Server-Timing header behind it.
// Seed a fresh temporary database with seed.py and seed_flow.py and start the server; PN_BROWSER_URL
// names it (default http://127.0.0.1:8765). The set used is "wide" from /private/tmp/pn-flow-manifest.json.
import {spawn} from 'node:child_process';
import {rmSync,readFileSync} from 'node:fs';
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const SET=JSON.parse(readFileSync('/private/tmp/pn-flow-manifest.json','utf8')).wide.set;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-perf-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9364','--user-data-dir=/private/tmp/pn-perf-chrome','--no-first-run','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9364/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const events=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)events.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:2,mobile:true},s);
const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(400);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const lines=`(document.querySelector('.perf-readout')||{textContent:''}).textContent.split('\\n')`;
const last=`${lines}.at(-1)`;
const SERVER=/server \d+ db \d+ \(\d+q\) open \d+/;
try {
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 // 1. Off unless asked for.
 await go('/');
 check('not asked for: no readout and nothing stored',await js(`!document.querySelector('.perf-readout')&&sessionStorage.getItem('pn-perf')===null`));
 const header=await js(`fetch('/').then(r=>r.headers.get('Server-Timing'))`);
 check('every page carries Server-Timing',/^app;dur=[\d.]+, db;dur=[\d.]+;desc="\d+ quer(y|ies)", connect;dur=[\d.]+$/.test(header));
 // 2. Asked for: the first line says how the document arrived.
 await go('/?perf=1');
 const first=await js(`${lines}[0]`);
 check('asked for: the load line has the server figures',/^load: first byte \d+ ready \d+ms \| /.test(first)&&SERVER.test(first));
 check('the readout is outside the body and takes no taps',await js(`document.querySelector('.perf-readout').parentElement===document.documentElement&&getComputedStyle(document.querySelector('.perf-readout')).pointerEvents==='none'`));
 // 3. A screen change: wait, draw, move, the server and the frames.
 await js(`document.querySelector('.group-home h2 a').click()`);await sleep(1800);
 let line=await js(last);
 check('screen change: one line with every figure',/^\/g\/\d+\/ wait (\d+|0 \(fetched ahead\)) draw \d+ move \d+ = \d+ms \| /.test(line)&&SERVER.test(line)&&/\| late \d+\/\d+ worst \d+$/.test(line));
 check('the readout survives the screen change, once',await js(`document.querySelectorAll('.perf-readout').length===1&&${lines}.length===2`));
 check('the choice lasts without the parameter',await js(`!/perf=/.test(location.search)&&sessionStorage.getItem('pn-perf')==='1'`));
 // 4. A tap that asks the server nothing: frames only.
 await go('/s/'+SET+'/');
 await js(`document.querySelector('[data-sheet-open^=buy]').click()`);await sleep(1600);
 line=await js(last);
 check('opening a sheet: frames only, no server figures',/\| late \d+\/\d+ worst \d+$/.test(line)&&!/wait|server/.test(line));
 // 5. An action sent in place.
 await js(`(()=>{const f=document.querySelector('dialog[open] form');const a=f.querySelector('[name=amount]');if(!a.value)a.value='1000';f.requestSubmit(f.querySelector('[type=submit]'))})()`);
 await js(`document.querySelector('dialog[open] form [type=submit]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}))`).catch(()=>{});
 await sleep(2200);
 const all=await js(`${lines}.join('\\n')`);
 check('rebuy in place: a line with the wait and the server figures',all.split('\n').some(l=>/wait \d+ draw \d+ move \d+ = \d+ms/.test(l)&&SERVER.test(l)));
 check('never more than five lines',all.split('\n').length<=5);
 // 6. Turned off again.
 await go('/?perf=0');
 check('turned off: no readout and nothing stored',await js(`!document.querySelector('.perf-readout')&&sessionStorage.getItem('pn-perf')===null`));
 const thrown=events.filter(e=>e.method==='Runtime.exceptionThrown').map(e=>(e.params.exceptionDetails.exception||{}).description||e.params.exceptionDetails.text);
 if(thrown.length)console.log('  script errors:',JSON.stringify(thrown).slice(0,900));
 check('no script errors',thrown.length===0);
} finally { await send('Browser.close').catch(()=>{});ws.close();chrome.kill(); }
const failed=results.filter(r=>!r.ok);console.log(`${results.length-failed.length}/${results.length} checks passed`);process.exit(failed.length?1:0);
