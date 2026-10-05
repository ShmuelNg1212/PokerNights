// Stage 4 trial: navigate by tapping links with Turbo navigation on, and look for what the page scripts leak.
import {spawn} from 'node:child_process';import {rmSync} from 'node:fs';
const BASE='http://127.0.0.1:8765';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-spike/chrome-l',{recursive:true,force:true});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9360','--user-data-dir=/private/tmp/pn-spike/chrome-l','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9360/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();let ev=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)ev.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async e=>{const r=await send('Runtime.evaluate',{expression:e,awaitPromise:true,returnByValue:true},s);return r.exceptionDetails?'EXC '+(r.exceptionDetails.exception?.description||'').slice(0,120):r.result.value};
const tap=async sel=>{await js(`document.querySelector(${JSON.stringify(sel)}).click()`);await sleep(900)};
try{await send('Page.navigate',{url:BASE+'/accounts/login/'},s);await sleep(900);await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 await send('Page.navigate',{url:BASE+'/g/1/'},s);await sleep(900);await js('window.__mark=1');
 // group -> session (Friday table) -> set 3 -> back to session, three times, by tapping links.
 let docs=0,t=[];
 for(let i=0;i<3;i++){let m=ev.length,t0=Date.now();await js(`[...document.querySelectorAll('a.session-link')].find(a=>a.textContent.includes('Friday table')).click()`);await sleep(900);
  await tap('a.btn-primary[href^="/s/"], .night-sets a.set-link');await tap('.table-bar a');await tap('.table-bar a');
  docs+=ev.slice(m).filter(e=>e.method==='Network.requestWillBeSent'&&e.params.type==='Document').length;}
 console.log('after 3 round trips: page reloaded?',await js('window.__mark!==1'),'| document loads:',docs,'| at',await js('location.pathname'));
 await js(`[...document.querySelectorAll('a.session-link')].find(a=>a.textContent.includes('Friday table')).click()`);await sleep(900);await tap('a.btn-primary[href^="/s/"], .night-sets a.set-link');
 console.log('on set page:',await js('location.pathname'),'| sheet dialogs in the page:',await js(`document.querySelectorAll('dialog.sheet').length`),'| dock toggle shown:',await js(`!!document.querySelector('.dock-toggle')&&!document.querySelector('.dock-toggle').hidden`));
 let m=ev.length;await sleep(8500);const polls=ev.slice(m).filter(e=>e.method==='Network.requestWillBeSent'&&e.params.request.url.includes('/state/')).map(e=>new URL(e.params.request.url).pathname);
 console.log('poll requests in 8.5 s on the set page (expected 2):',polls.length,[...new Set(polls)].join(' '));
 await js(`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1).click()`);await sleep(500);console.log('open sheets after one tap:',await js(`document.querySelectorAll('dialog[open]').length`));
 await send('Page.navigate',{url:BASE+'/s/3/'},s);await sleep(900);await tap('.table-bar a');await tap('.table-bar a');
 m=ev.length;await sleep(8500);const stray=ev.slice(m).filter(e=>e.method==='Network.requestWillBeSent'&&e.params.request.url.includes('/state/')).length;
 console.log('poll requests in 8.5 s after leaving the set page (expected 0):',stray,'| at',await js('location.pathname'));
 console.log('script errors so far:',ev.filter(e=>e.method==='Runtime.exceptionThrown').length, ev.filter(e=>e.method==='Runtime.exceptionThrown').slice(0,2).map(e=>(e.params.exceptionDetails.exception?.description||'').slice(0,90)).join(' || '));
}finally{await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
