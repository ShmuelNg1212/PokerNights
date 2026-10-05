// Stage 3 trial probe: what happens when a host records a rebuy from a sheet on the set page.
import {spawn} from 'node:child_process';import {rmSync} from 'node:fs';
const BASE='http://127.0.0.1:8765';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-spike/chrome',{recursive:true,force:true});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9357','--user-data-dir=/private/tmp/pn-spike/chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9357/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();let events=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)events.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async e=>{const r=await send('Runtime.evaluate',{expression:e,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)return 'EXC '+JSON.stringify(r.exceptionDetails.exception?.description||r.exceptionDetails.text).slice(0,160);return r.result.value};
const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await sleep(900)};
async function action(label,amount){
 await go('/s/3/');
 await js(`document.querySelector('.host-more').open=true;document.querySelector('#cancel-reason').value='draft kept?';window.scrollTo(0,500);window.__mark=1`);
 const before=await js(`document.querySelector('[data-watch=in-play]').dataset.value`);
 await js(`[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1).click()`);await sleep(500);
 await js(`document.querySelector('dialog [name=amount]').value=${JSON.stringify(amount)}`);
 events=[];const t=Date.now();await js(`document.querySelector('dialog form [type=submit]').click()`);
 let ms=null;for(let i=0;i<50;i++){await sleep(60);const now=await js(`document.querySelector('[data-watch=in-play]')?.dataset.value`);const msg=await js(`!!document.querySelector('.message, .toast, .sheet-error')`);if((now&&now!==before)||(amount==='abc'&&msg)){ms=Date.now()-t;break}}
 await sleep(900);
 const reqs=events.filter(e=>e.method==='Network.requestWillBeSent').map(e=>e.params.type+':'+e.params.request.method+':'+new URL(e.params.request.url).pathname);
 const errors=events.filter(e=>e.method==='Runtime.exceptionThrown'||(e.method==='Runtime.consoleAPICalled'&&e.params.type==='error')).length;
 console.log(label,JSON.stringify({ms,reloaded:await js(`window.__mark!==1`),scrollY:await js(`Math.round(window.scrollY)`),total:[before,await js(`document.querySelector('[data-watch=in-play]').dataset.value`)],
  toast:await js(`(document.querySelector('.toast, .message-success')||{}).textContent||null`),errorShown:await js(`(document.querySelector('.sheet-error, .message-error')||{}).textContent||null`),sheetOpen:await js(`!!document.querySelector('dialog[open]')`),
  draftKept:await js(`(document.querySelector('#cancel-reason')||{}).value==='draft kept?'`),moreOpen:await js(`!!document.querySelector('.host-more[open]')`),requests:reqs.length,docs:reqs.filter(r=>r.startsWith('Document')).length,jsErrors:errors,list:reqs.slice(0,14).join(' ')}));
}
try{await go('/accounts/login/');await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1000);
 await action('rebuy ',"500");await action('badamt',"abc");
}finally{await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
