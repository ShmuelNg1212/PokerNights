import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rake-review';mkdirSync(OUT,{recursive:true});
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
await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];function check(name,ok,detail){results.push({name,ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const A=await user('hana'),B=await user('ben');
const ids=JSON.parse(readFileSync('/private/tmp/pn-rake-manifest.json','utf8'));
const post=async(U,path,data)=>U.js(`(async()=>{const body=new URLSearchParams(${JSON.stringify(data)});body.set('csrfmiddlewaretoken',document.querySelector('[name=csrfmiddlewaretoken]').value);const r=await fetch(${JSON.stringify(path)},{method:'POST',body});return {status:r.status,text:await r.text()};})()`);
const type=async(index,value)=>A.js(`(()=>{const f=document.querySelectorAll('[data-count-input]')[${index}];f.value=${JSON.stringify(value)};f.dispatchEvent(new Event('input',{bubbles:true}));})()`);
const total=()=>A.js(`document.querySelector('[data-count-preview] [data-count-accounted]').textContent`);
async function capture(name){for(const width of [390,1280]){await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);check(name+' fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot(name+'-'+width);}}
try {
if (!process.env.PN_RAKE_CONTINUE) {
await A.go(`/s/${ids.percent}/settings/`);await capture('rake-settings');
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
await A.js(`document.querySelector('[name=rake_mode][value=percent]').checked=true;document.querySelector('[name=rake_percentage]').value='5.001';document.querySelector('form.form-section').noValidate=true`);await A.click(`document.querySelector('form.form-section button')`);
check('native invalid precision keeps input and error',await A.js(`document.querySelector('[name=rake_percentage]').value==='5.001'&&document.querySelector('[role=alert]')!==null`));await A.shot('rake-error-1280');
await A.js(`document.querySelector('[name=rake_percentage]').value='5'`);await A.click(`document.querySelector('form.form-section button')`);
check('native percentage settings saved',await A.js(`location.pathname==='/s/${ids.percent}/'&&document.body.textContent.includes('5% rake deducted')`));
await A.click(`document.querySelector('.next-action')`);check('native opening deducts rake exactly once',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='190000'&&document.body.textContent.includes('₱100')`));await capture('rake-active');
await A.go(`/s/${ids.percent}/settings/`);check('accepted money locks rake controls',await A.js(`document.querySelector('[name=rake_mode]').disabled&&document.querySelector('[name=rake_percentage]').disabled`));
await A.go(`/s/${ids.percent}/`);await A.js(`document.querySelector('details[data-key=player-'+document.querySelector('[name=participant_id]').value+']')?.setAttribute('open','')`);
const buyAction=await A.js(`document.querySelector('form.buy-form').getAttribute('action')`);const participant=await A.js(`document.querySelector('form.buy-form [name=participant_id]').value`);
await post(A,buyAction,{participant_id:participant,amount:'1000',request_id:crypto.randomUUID()});await A.go(`/s/${ids.percent}/`);
check('rebuy deducts same percentage',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='285000'&&document.body.textContent.includes('Collected rake')`));
await A.go(`/s/${ids.percent}/players/add-several/`);await A.js(`document.querySelector('[name=name]').value='Late rake'`);await A.click(`document.querySelector('form.form-section button')`);
const late=await A.js(`[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Late rake')).querySelector('[name=participant_id]').value`);
await post(A,buyAction,{participant_id:late,amount:'1000',request_id:crypto.randomUUID()});await A.go(`/s/${ids.percent}/`);
check('late player buy-in uses agreed deduction',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='380000'`));
}
await A.go(`/s/${ids.count}/`);await B.go(`/s/${ids.count}/`);await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);await A.go(`/s/${ids.count}/`);
await type(0,'950');await type(1,'950');check('live preview adds accepted rake exactly once',await total()==='₱2,000');await capture('rake-count');
await type(1,'oops');check('invalid draft has no false balance',await total()==='Unavailable');await type(1,'950');
await A.js(`document.querySelectorAll('[data-count-input]')[1].focus()`);
const firstName=await B.js(`document.querySelectorAll('[data-count-input]')[0].name`);
await post(B,`/s/${ids.count}/counts/confirm/`,{[firstName]:'900',request_id:crypto.randomUUID()});await sleep(4600);await A.js('document.activeElement.blur()');await sleep(300);
check('another host redraw preserves draft with rake',await total()==='₱2,000');await type(0,'');check('saved fallback plus rake is exact',await total()==='₱1,950');await type(0,'950');
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.click(`document.querySelector('button[form=counts-form].btn-block')`);
check('native confirms counts',await A.js(`document.querySelectorAll('[data-status=ready]').length===2`));
await A.click(`document.querySelector('a.next-action')`);check('review shows rake and playable',await A.js(`document.body.textContent.includes('Collected rake')&&document.body.textContent.includes('₱1,900')`));await capture('rake-review');
await A.click(`document.querySelector('form.batch-review button')`);check('rake-aware books balance',await A.js(`document.body.textContent.includes('Cash-outs plus rake equal gross buy-ins')`));await A.click(`document.querySelector('.next-action')`);await capture('rake-final');
check('frozen result includes collected fee',await A.js(`document.body.textContent.includes('Results include rake already collected')&&document.body.textContent.includes('−₱50')`));
const nightPath=await A.js(`document.querySelector('.session-next a').getAttribute('href')`);await A.go(nightPath);
await A.click(`document.querySelector('form[action$="/close/"] button')`);check('equal rake losses owe no further transfer',await A.js(`document.body.textContent.includes('Nobody owes anything')&&document.body.textContent.includes('No positive result after rake')&&!document.body.textContent.includes('Everyone broke even')`));await capture('rake-night');
await A.go(`/s/${ids.flat}/settings/`);await A.js(`document.querySelector('[name=rake_mode][value=flat]').checked=true;document.querySelector('[name=rake_flat]').value='20'`);await A.click(`document.querySelector('form.form-section button')`);await A.click(`document.querySelector('.next-action')`);
check('native flat chips start',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='1960'&&document.body.textContent.includes('20 chips rake deducted')`));await capture('rake-flat');
await A.go(`/s/${ids.off}/`);check('Off default visible',await A.js(`document.body.textContent.includes('Rake is Off')`));await A.click(`document.querySelector('.next-action')`);check('Off opening preserves gross playable',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='200000'`));
await A.go(`/g/${ids.group}/`);await A.js(`document.querySelector('[aria-label="Accumulated rake"] details').open=true`);check('group lifetime includes live finalized and separate units',await A.js(`document.querySelector('[aria-label="Accumulated rake"]').textContent.includes('₱300')&&document.querySelector('[aria-label="Accumulated rake"]').textContent.includes('40 chips')`));await capture('rake-group');
check('group account excludes player identity',await A.js(`![...document.querySelectorAll('.roster-person')].some(r=>r.textContent.includes('Rake'))`));
writeFileSync(OUT+'/rake-results.json',JSON.stringify(results,null,2));if(results.some(r=>!r.ok))process.exitCode=1;
} finally {ws.close();chrome.kill();}
