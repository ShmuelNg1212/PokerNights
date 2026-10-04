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
await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section button').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];function check(name,ok,detail){results.push({name,ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const A=await user('hana'),B=await user('hana'),P=await user('ben');
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text)});await send('Runtime.enable',{},A.s);
const post=async(U,path,data)=>U.js(`(async()=>{const body=new URLSearchParams(${JSON.stringify(data)});body.set('csrfmiddlewaretoken',document.querySelector('[name=csrfmiddlewaretoken]').value);const r=await fetch(${JSON.stringify(path)},{method:'POST',body});return {status:r.status,text:await r.text()};})()`);
const ids=JSON.parse(readFileSync('/private/tmp/pn-counts-manifest.json','utf8'));
const state=()=>A.js(`(()=>{const b=document.querySelector('[data-count-preview]');return {label:b.querySelector('[data-count-label]').textContent,total:b.querySelector('[data-count-accounted]').textContent,status:b.querySelector('[data-count-status]').textContent,coverage:b.querySelector('[data-count-coverage]').textContent}})()`);
const type=async(index,value)=>A.js(`(()=>{const f=document.querySelectorAll('[data-count-input]')[${index}];f.value=${JSON.stringify(value)};f.dispatchEvent(new Event('input',{bubbles:true}));})()`);
try {
await A.go(`/s/${ids.php}/`);await B.go(`/s/${ids.php}/`);
let q=await state();check('confirmed fallback plus earlier cash-out',q.total==='₱1,000'&&q.coverage==='1 still to count.',q);
await type(1,'1,000');q=await state();check('typing matches with saved fallback',q.total==='₱2,000'&&q.status==='All counts match buy-ins.'&&q.label.includes('unsaved'),q);
await type(0,'0');q=await state();check('zero replaces saved count',q.total==='₱1,100'&&q.status==='₱900 missing.',q);
await type(0,'');await type(1,'1000.50');q=await state();check('centavos exact',q.total==='₱2,000.50'&&q.status==='₱0.50 extra.',q);
await type(1,'oops');q=await state();check('invalid never falls back or claims match',q.total==='Unavailable'&&q.status.includes('unavailable'),q);check('invalid entry identified',await A.js(`document.querySelectorAll('[data-count-input]')[1].getAttribute('aria-invalid')==='true'&&!document.querySelectorAll('[data-count-error]')[1].hidden`));
for(const bad of ['-1','1.005','1000000001','Infinity','1e3']) {await type(1,bad);check('unsupported draft '+bad,(await state()).total==='Unavailable');}
await type(0,'1900');await type(1,'');q=await state();check('equal partial sum never claims complete',q.total==='₱2,000'&&q.status.includes('finish counting')&&q.coverage==='1 still to count.',q);
await type(0,'900');await type(1,'1000');
const name=await B.js(`document.querySelectorAll('[data-count-input]')[0].name`);
await A.js(`document.querySelectorAll('[data-count-input]')[1].focus()`);
await post(B,`/s/${ids.php}/counts/confirm/`,{[name]:'800',request_id:crypto.randomUUID()});await sleep(4600);
check('typing defers poll and keeps preview', (await state()).total==='₱2,000');await A.js(`document.activeElement.blur()`);await sleep(250);
q=await state();check('post-restore event uses drafts',q.total==='₱2,000'&&q.label.includes('unsaved'),q);
await type(0,'');q=await state();check('clearing draft uses other host saved count',q.total==='₱1,900'&&q.status==='₱100 missing.',q);
await type(0,'900');await type(1,'1000');
for(const width of [390,1280]) {
 await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
 check('counter no overflow '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));
 if(width===390) {check('phone preview visible',await A.js(`(()=>{const r=document.querySelector('[data-count-preview]').getBoundingClientRect();return r.top>=0&&r.bottom<=844})()`));await A.js(`window.scrollTo(0,document.documentElement.scrollHeight)`);check('dock clears final confirm action',await A.js(`document.querySelector('button[form=counts-form].btn-block').getBoundingClientRect().bottom<=document.querySelector('.host-controls').getBoundingClientRect().top`));}
 await A.shot('counts-php-'+width);
}
await A.click(`document.querySelector('button[form=counts-form]')`);q=await state();check('confirmation makes authoritative baseline',q.total==='₱2,000'&&q.label==='Confirmed counts',q);
await P.go(`/s/${ids.php}/`);check('player sees saved baseline only',await P.js(`!document.querySelector('[data-count-preview]')&&!document.querySelector('[data-count-input]')&&document.querySelector('[data-count-accounted]').textContent==='₱2,000'`));
await A.go(`/s/${ids.php}/cash-out-counted/`);await A.click(`document.querySelector('.batch-review button[type=submit]')`);q=await state();check('cash-out transfers remaining count without double count',q.total==='₱2,000'&&q.status==='All counts match buy-ins.',q);check('server offers finalize after recorded cash-outs',await A.js(`document.body.textContent.includes('Finalize results')`));
await A.go(`/s/${ids.chips}/`);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},A.s);await type(1,'1,000 chips');q=await state();check('native chips match',q.total==='2,000 chips'&&q.status==='All counts match buy-ins.',q);await A.shot('counts-chips-390');
await type(1,'0');q=await state();check('zero chips counts completely',q.total==='1,000 chips'&&q.coverage==='0 still to count.'&&q.status==='1,000 chips missing.',q);
await type(1,'100000000000');q=await state();check('large integer chips exact',q.total==='100,000,001,000 chips',q);
await type(1,'1.5');check('fractional chips invalid',(await state()).total==='Unavailable');
await type(1,'bad');await A.click(`document.querySelector('button[form=counts-form]')`);q=await state();check('refused submission retains invalid preview',q.total==='Unavailable'&&await A.js(`document.querySelectorAll('[data-count-input]')[1].value==='bad'`),q);
await B.go(`/s/${ids.chips}/`);
const firstChipName=await B.js(`document.querySelector('[data-count-input]').name`);
await post(B,`/s/${ids.chips}/counts/confirm/`,{[firstChipName]:'800',request_id:crypto.randomUUID()});await sleep(4600);
q=await state();check('refused default drafts survive later poll',q.total==='Unavailable'&&await A.js(`document.querySelectorAll('[data-count-input]')[1].value==='bad'`),q);
await A.js(`window.dispatchEvent(new Event('pageshow'))`);check('page restoration recomputes invalid draft',(await state()).total==='Unavailable');
await send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:true},A.s);
check('invalid phone preview fits at320',await A.js(`document.documentElement.scrollWidth<=320&&document.querySelector('[data-count-preview]').getBoundingClientRect().top>=0`));
await B.go(`/s/${ids.chips}/`);await send('Emulation.setScriptExecutionDisabled',{value:true},B.s);await B.go(`/s/${ids.chips}/`);check('no JS keeps confirmed baseline',await B.js(`document.querySelector('[data-count-preview] [data-count-accounted]').textContent==='900 chips'&&document.body.textContent.includes('Confirm counts to update this total.')`));
await A.go('/s/10/');q=await state();check('override does not hide stack discrepancy',q.status==='₱100 missing.'&&await A.js(`document.querySelector('[data-count-preview]').textContent.includes('Overrides are excluded')`),q);
await A.go('/s/7/');check('no money never claims complete',(await state()).status==='No buy-ins recorded.');
check('no runtime errors',errors.length===0,errors);writeFileSync(`${OUT}/counts.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill();}
if(results.some(x=>!x.ok))process.exitCode=1;
