// Results that read at a glance: a final set of six at 320, 390 and 1280 px, with touch on the phones.
// Seed a fresh temporary database with seed.py and seed_results.py, serve it on 127.0.0.1:8765, then run. It writes nothing.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-results-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const PROFILE='/private/tmp/pn-results-chrome';rmSync(PROFILE,{recursive:true,force:true});
const seeded=JSON.parse(readFileSync('/private/tmp/pn-results-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9471',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<60&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9471/json/version')).json()).webSocketDebuggerUrl}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const[ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok,detail)=>{results.push({name,ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name}${detail===undefined?'':' '+JSON.stringify(detail)}`)};
const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
await send('Page.enable',{},s);await send('Runtime.enable',{},s);
const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,300));return r.result.value};
const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await sleep(700);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const shot=async name=>{const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'jpeg',quality:70,captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.jpg`,Buffer.from(data,'base64'))};
const size=async width=>{await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);await send('Emulation.setTouchEmulationEnabled',{enabled:width<900,maxTouchPoints:5},s)};
const NETS=`[...document.querySelectorAll('.result-amount')].map(a=>Number(a.textContent.replace(/[^0-9−-]/g,'').replace('−','-'))||0)`;
try {
await size(390);await go('/accounts/login/');await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
for(const width of [320,390,1280]){
 await size(width);await go(`/s/${seeded.set}/`);await shot(`final-${width}`);
 const nets=await js(NETS);
 check(`${width}: results run best to worst`,nets.length===6&&nets.every((n,i)=>i===0||nets[i-1]>=n),nets);
 check(`${width}: no sideways scroll`,await js(`document.documentElement.scrollWidth<=${width}`));
 const heights=await js(`[...document.querySelectorAll('.result-row')].filter(r=>!r.textContent.includes('very long name')).map(r=>Math.round(r.getBoundingClientRect().height))`);
 check(`${width}: a row is 72 px or less`,heights.every(h=>h<=72),heights);
 const tall=await js(`Math.round([...document.querySelectorAll('.result-row')].find(r=>r.textContent.includes('very long name')).getBoundingClientRect().height)`);
 check(`${width}: a long name wraps beside its result`,await js(`(()=>{const r=[...document.querySelectorAll('.result-summary')].find(r=>r.textContent.includes('very long name'));return r.querySelector('.player-name').getBoundingClientRect().right<=r.querySelector('.result-amount').getBoundingClientRect().left+1})()`),tall);
 if(width<900)check(`${width}: the set fits within two screens`,await js(`document.querySelector('.final-results').getBoundingClientRect().bottom+scrollY<=innerHeight*2`),await js(`Math.round(document.querySelector('.final-results').getBoundingClientRect().bottom+scrollY)`));
 check(`${width}: a loss has no extra emphasis`,await js(`(()=>{const f=s=>{const c=getComputedStyle(document.querySelector('.result-amount'+s));return [c.fontSize,c.fontWeight,c.fontStretch].join()};return f('.plus')===f('.minus')})()`));
 check(`${width}: each row has a 48 px target and a chevron`,await js(`[...document.querySelectorAll('.result-summary')].every(r=>r.getBoundingClientRect().height>=48&&!!r.querySelector(':scope > svg.icon'))`));
 check(`${width}: the facts wait behind the row`,await js(`[...document.querySelectorAll('.result-line')].every(l=>!l.checkVisibility())`));
 await js(`document.querySelector('.result-summary').click()`);await sleep(350);
 check(`${width}: a tap on the row opens the facts and the records`,await js(`(()=>{const d=document.querySelector('.result-details');return d.open&&d.querySelector('.result-line').checkVisibility()&&d.textContent.includes('Final cash-out')})()`));
 check(`${width}: the chevron turns`,await js(`getComputedStyle(document.querySelector('.result-details[open] .result-summary > .icon')).transform!=='none'`));
 await shot(`final-open-${width}`);await js(`document.querySelector('.result-summary').click()`);await sleep(250);
 await go(`/n/${seeded.night}/`);await shot(`session-${width}`);
 const standing=await js(`[...document.querySelectorAll('.night-results .amount')].map(a=>Number(a.textContent.replace(/[^0-9−-]/g,'').replace('−','-'))||0)`);
 check(`${width}: session results run best to worst`,standing.length===6&&standing.every((n,i)=>i===0||standing[i-1]>=n),standing);
 const rows=await js(`[...document.querySelectorAll('.night-results .result-row')].filter(r=>!r.textContent.includes('very long name')).map(r=>Math.round(r.getBoundingClientRect().height))`);
 check(`${width}: a session row is 72 px or less`,rows.every(h=>h<=72),rows);
}
await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);await size(390);await go(`/s/${seeded.set}/`);
check('reduced motion: the chevron does not move',await js(`getComputedStyle(document.querySelector('.result-summary > .icon')).transitionDuration==='0s'||getComputedStyle(document.querySelector('.result-summary > .icon')).transitionProperty==='none'`));
await send('Emulation.setEmulatedMedia',{features:[]},s);
await send('Emulation.setScriptExecutionDisabled',{value:true},s);await go(`/s/${seeded.set}/`);
check('without JavaScript the row is still a disclosure',await js(`document.querySelectorAll('details.result-details > summary').length===6`));
await send('Emulation.setScriptExecutionDisabled',{value:false},s);
writeFileSync(`${OUT}/results.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill();}
if(results.some(x=>!x.ok))process.exitCode=1;
