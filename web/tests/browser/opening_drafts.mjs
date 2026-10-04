import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-rack-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:(process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765')+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

const M=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
try {
 const A=await user('hana'),B=await user('hana');
 const path='/s/'+M.live.set+'/';
 await A.go(path);await B.go(path);
 await A.js(`document.querySelector('[name=opening_buy_ins]').click();document.querySelector('[name=opening_buy_ins]').blur()`);
 const version=await A.js(`document.querySelector('#live').dataset.version`);
 await send('Emulation.setScriptExecutionDisabled',{value:true},B.s);
 await B.js(`document.querySelector('form[action$="/buyins/add/"]').requestSubmit()`);
 await sleep(5200);
 check('live snapshot arrived',await A.js(`document.querySelector('#live').dataset.version!==${JSON.stringify(version)}`));
 check('unchecked opening option survives live redraw',await A.js(`!document.querySelector('[name=opening_buy_ins]').checked`));
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
 await A.click(`document.querySelector('button[value=start]')`);
 check('retained opt-out submits with existing-only total',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent==='₱1,000'`));
 writeFileSync(`${OUT}/opening-drafts.json`,JSON.stringify(results,null,2));
}finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
