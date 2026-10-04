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
const ids=JSON.parse(readFileSync('/private/tmp/pn-late-manifest.json','utf8'));
const picker=id=>`/s/${id}/players/add/`;
try {
await A.go(`/s/${ids.running}/`);await B.go(`/s/${ids.running}/`);
const path=await A.js(`document.querySelector('.section-heading a').getAttribute('href')`);
const before=await A.js(`document.querySelector('[data-watch=in-play]').dataset.value`);
check('Add players visible with every roster member seated',path.includes('players'));
for(const width of [390,1280]) {await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);await A.go(path);check('picker no overflow '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));check('new name offered with no eligible roster',await A.js(`!!document.querySelector('[name=name]')&&!document.querySelector('[data-pick]')&&document.body.textContent.includes('Every player of this group')`));await A.shot('late-picker-'+width);}
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},A.s);
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
await A.js(`document.querySelector('[name=name]').value='Late arrival'`);await A.click(`document.querySelector('form.form-section [type=submit]')`);
check('native creation returns running set',await A.js(`location.pathname==='/s/${ids.running}/'&&document.body.textContent.includes('Late arrival')&&document.querySelector('.next-action').textContent.includes('End play')`));
check('no automatic late buy-in',await A.js(`document.querySelector('[data-watch=in-play]').dataset.value===${JSON.stringify(before)}&&[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Late arrival')).textContent.includes('No buy-in yet')`));
await sleep(4600);check('second host sees live arrival',await B.js(`document.body.textContent.includes('Late arrival')`));
check('new join timer shown',await A.js(`[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Late arrival')).textContent.includes('Played')`));
await A.go(path);await A.js(`document.querySelector('[name=name]').value='late ARRIVAL'`);await A.click(`document.querySelector('form.form-section [type=submit]')`);
check('duplicate bound name and seated recovery',await A.js(`document.querySelector('[name=name]').value==='late ARRIVAL'&&document.querySelector('[name=name]').getAttribute('aria-invalid')==='true'&&document.body.textContent.includes('already at the table. Return to the set.')`));await A.shot('late-duplicate-390');
await A.go(`/g/1/`);check('new identity saved to group roster',await A.js(`document.body.textContent.includes('Late arrival')`));
await A.go(`/s/${ids.full}/`);const fullPath=await A.js(`document.querySelector('.section-heading a').getAttribute('href')`);await A.go(fullPath);
check('full table explains disabled new action',await A.js(`document.body.textContent.includes('The table is full')&&document.querySelector('[name=name]').matches(':disabled')&&document.querySelector('form.form-section button').matches(':disabled')`));
await A.go(`/s/${ids.stale}/`);const stalePath=await A.js(`document.querySelector('.section-heading a').getAttribute('href')`);await A.go(stalePath);await A.js(`document.querySelector('[name=name]').value='After end'`);
await B.go(`/s/${ids.stale}/`);const endPath=await B.js(`document.querySelector('.next-action').closest('form').getAttribute('action')`);await post(B,endPath,{action:'end'});await A.click(`document.querySelector('form.form-section [type=submit]')`);
check('ended race retains name and disables add',await A.js(`document.querySelector('[name=name]').value==='After end'&&document.querySelector('[name=name]').matches(':disabled')&&document.body.textContent.includes('Players cannot be added now')`));
await B.go(`/s/${ids.stale}/`);check('ended race added no player',await B.js(`!document.body.textContent.includes('After end')`));
await A.go(`/s/${ids.chips}/`);const chipsPath=await A.js(`document.querySelector('.section-heading a').getAttribute('href')`);await A.go(chipsPath);await A.js(`document.querySelector('[name=name]').value='Chip newcomer'`);await A.click(`document.querySelector('form.form-section [type=submit]')`);
check('chips late join keeps native unit and no money',await A.js(`!document.body.textContent.includes('₱')&&[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Chip newcomer')).textContent.includes('0 chips')`));
await A.js(`window.row=[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Chip newcomer'));row.querySelector('details').open=true;row.querySelector('input[name=amount]').value='1000'`);await A.click(`row.querySelector('form button')`);
check('native manual buy-in after late arrival',await A.js(`[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Chip newcomer')).textContent.includes('1,000 chips')`));
await B.go(chipsPath);check('new group identity appears in other set picker',await B.js(`document.body.textContent.includes('Late arrival')`));
await P.go(`/s/${ids.running}/`);check('player sees arrival without host add action',await P.js(`document.body.textContent.includes('Late arrival')&&!document.querySelector('.section-heading a')`));
await A.go('/s/3/');const existingPath=await A.js(`document.querySelector('.section-heading a').getAttribute('href')`);await A.go(existingPath);
await A.js(`document.querySelector('[data-pick] input[data-label="Late arrival"]').checked=true;document.querySelector('[data-pick]').dispatchEvent(new Event('change',{bubbles:true}))`);await A.click(`document.querySelector('[data-pick-submit]')`);
check('existing roster selection still joins without money',await A.js(`location.pathname==='/s/3/'&&[...document.querySelectorAll('.player-row')].find(r=>r.textContent.includes('Late arrival')).textContent.includes('No buy-in yet')`));
await A.go(path);check('new form has48px target and label',await A.js(`document.querySelector('form.form-section button').getBoundingClientRect().height>=48&&document.querySelector('[name=name]').labels.length===1`));
check('no runtime errors',errors.length===0,errors);writeFileSync(`${OUT}/late-player.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill();}
if(results.some(x=>!x.ok))process.exitCode=1;
