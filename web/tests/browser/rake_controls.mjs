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
try {
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
async function capture(name){for(const width of [390,1280]){await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);check(name+' fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot(name+'-'+width);}}
async function choose(mode,flat,percent){await A.js(`document.querySelector('[name=rake_mode][value=${mode}]').checked=true;document.querySelector('[name=rake_flat]').value=${JSON.stringify(flat)};document.querySelector('[name=rake_percentage]').value=${JSON.stringify(percent)}`);}
async function fillNew(unit){await A.go(`/g/${ids.group}/sessions/new/`);await A.js(`document.querySelector('[name=table_id]').value='1';document.querySelector('[name=game_date]').value='2026-10-04';document.querySelector('[name=game_type]').value='nlh';document.querySelector('[name=unit]').value='${unit}';for(const [name,value] of Object.entries({small_blind:'10',big_blind:'20',min_buy_in:'500',max_buy_in:'2000',default_buy_in:'1000'}))document.querySelector('[name='+name+']').value=value`);}
await fillNew('php');await capture('rake-new');
check('three native choices with Off selected',await A.js(`document.querySelectorAll('[name=rake_mode]').length===3&&document.querySelector('[name=rake_mode]:checked').value==='off'`));
await choose('percent','oops','5.001');await A.click(`document.querySelector('form.form-section button')`);
check('native active percentage rejects precision and retains radio',await A.js(`document.querySelector('[name=rake_mode]:checked').value==='percent'&&document.querySelector('[name=rake_percentage]').value==='5.001'&&document.querySelector('#id_rake_percentage_error')!==null`));await capture('rake-new-error');
await choose('flat','20','oops');await A.click(`document.querySelector('form.form-section button')`);
check('native creation flat ignores malformed percentage',await A.js(`location.pathname.startsWith('/s/')&&document.body.textContent.includes('₱20 rake deducted')`));
const firstPath=await A.js('location.pathname');await A.go(firstPath+'settings/');await capture('rake-choice');
await choose('percent','oops','5');await A.click(`document.querySelector('form.form-section button')`);
check('native switch to percentage ignores malformed flat',await A.js(`location.pathname===${JSON.stringify(firstPath)}&&document.body.textContent.includes('5% rake deducted')`));
await A.go(firstPath+'settings/');await choose('off','oops','oops');await A.click(`document.querySelector('form.form-section button')`);
check('native Off ignores both values',await A.js(`document.body.textContent.includes('Rake is Off')`));
await A.go(firstPath+'settings/');await choose('flat','20','0');await A.click(`document.querySelector('form.form-section button')`);
check('native flat ignores percentage zero',await A.js(`document.body.textContent.includes('₱20 rake deducted')`));
await A.click(`document.querySelector('.next-action')`);
check('empty open set has pre-start rake choice',await A.js(`document.body.textContent.includes('Choose rake before buy-ins')`));await capture('rake-prestart');
const addPath=firstPath+'players/add-several/';await A.go(addPath);await A.js(`document.querySelector('[name=name]').value='Opening rake'`);await A.click(`document.querySelector('form.form-section button')`);await A.click(`document.querySelector('.next-action')`);
check('selected creation rake applies before opening buy-ins',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value==='98000'`));await A.go(firstPath+'settings/');
check('accepted money disables every radio and both value inputs',await A.js(`[...document.querySelectorAll('[name=rake_mode],[name=rake_flat],[name=rake_percentage]')].every(f=>f.disabled)&&document.body.textContent.includes('Default opening buy-ins also lock the rule')`));await capture('rake-locked');
await A.go(`/s/${ids.count}/`);const nightPath=await A.js(`document.querySelector('a[href^="/n/"]').getAttribute('href')`);await A.go(nightPath);await A.click(`document.querySelector('form[action$="/next-set/"] button')`);
check('next set exposes inherited rake and pre-start choice',await A.js(`document.body.textContent.includes('Choose rake before buy-ins')&&document.body.textContent.includes('5% rake deducted')`));
const nextPath=await A.js('location.pathname');await A.go(nextPath+'settings/');await choose('flat','20','0');await A.click(`document.querySelector('form.form-section button')`);
check('next set rule can change before opening money',await A.js(`document.body.textContent.includes('₱20 rake deducted')`));
await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
await fillNew('chips');await choose('flat','1.5','0');await A.click(`document.querySelector('form.form-section button')`);
check('chips active flat rejects fractions with scripts enabled',await A.js(`document.querySelector('#id_rake_flat_error')!==null&&document.querySelector('[name=rake_flat]').value==='1.5'`));
await choose('percent','oops','5');await A.click(`document.querySelector('form.form-section button')`);
check('chips creation percentage with scripts enabled',await A.js(`document.body.textContent.includes('5% rake deducted')&&document.body.textContent.includes('chips')`));
await A.go(await A.js('location.pathname')+'settings/');
await A.js(`document.querySelector('[name=rake_mode][value=off]').focus()`);await send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowDown',code:'ArrowDown',windowsVirtualKeyCode:40},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowDown',code:'ArrowDown',windowsVirtualKeyCode:40},A.s);
check('keyboard radio changes to Flat amount',await A.js(`document.querySelector('[name=rake_mode]:checked').value==='flat'`));
check('48px radio label targets and labeled inputs',await A.js(`[...document.querySelectorAll('.rake-settings .check')].every(e=>e.getBoundingClientRect().height>=48)&&[...document.querySelectorAll('.rake-settings input')].every(e=>e.labels.length===1)`));
writeFileSync(OUT+'/rake-controls-results.json',JSON.stringify(results,null,2));if(results.some(r=>!r.ok))process.exitCode=1;
} finally {ws.close();chrome.kill();}
