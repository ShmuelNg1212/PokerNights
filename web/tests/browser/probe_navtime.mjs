// Time from tap to the next screen being ready, on an emulated slow connection, for two modes.
import {spawn} from 'node:child_process';import {rmSync} from 'node:fs';
const BASE='http://127.0.0.1:8765';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-spike/chrome-n',{recursive:true,force:true});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9361','--user-data-dir=/private/tmp/pn-spike/chrome-n','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9361/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();let ev=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}else if(m.method)ev.push(m)};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
await send('ServiceWorker.enable',{},s).catch(()=>{});await send('Network.setBypassServiceWorker',{bypass:true},s);
const js=async e=>{const r=await send('Runtime.evaluate',{expression:e,awaitPromise:true,returnByValue:true},s);return r.exceptionDetails?'EXC':r.result.value};
try{await send('Page.navigate',{url:BASE+'/accounts/login/'},s);await sleep(900);await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 await send('Page.navigate',{url:BASE+'/g/1/'},s);await sleep(1500);
 await send('Network.emulateNetworkConditions',{offline:false,latency:400,downloadThroughput:200000,uploadThroughput:93750},s);
 const times=[];
 for(let i=0;i<4;i++){
  const want=i%2===0?'/n/':'/g/';const sel=i%2===0?`[...document.querySelectorAll('a.session-link')].find(a=>a.textContent.includes('Friday table'))`:`document.querySelector('.table-bar a')`;
  const m=ev.length;const t=Date.now();await js(sel+'.click()');let done=null;
  for(let k=0;k<200;k++){await sleep(25);const p=await js('location.pathname+"|"+document.readyState+"|"+(document.querySelector("main h1")?1:0)');if(typeof p==='string'&&p.startsWith(want)&&p.endsWith('complete|1')){done=Date.now()-t;break}}
  await sleep(700);const net=ev.slice(m).filter(e=>e.method==='Network.requestWillBeSent').length;times.push(done+'ms/'+net+'req');}
 console.log(process.argv[2]||'', times.join('  '));
}finally{await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
