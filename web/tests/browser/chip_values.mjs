import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9343',`--user-data-dir=/private/tmp/pn-chip-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9343/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
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
const ids=JSON.parse(readFileSync('/private/tmp/pn-chip-manifest.json','utf8'));
const A=await user('hana'),P=await user('ben');
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails)});await send('Runtime.enable',{},A.s);
const type=async(U,selector,value)=>U.js(`(()=>{const f=document.querySelector(${JSON.stringify(selector)});f.value=${JSON.stringify(value)};f.dispatchEvent(new Event('input',{bubbles:true}));})()`);
const fit=async(U,width,name)=>{await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},U.s);check(name+' fits '+width,await U.js(`document.documentElement.scrollWidth<=${width}`));};
try {
await A.go(`/n/${ids.setup}/chip-values/`);
for(const width of [320,390,1280]) {await fit(A,width,'Setup');await A.shot('setup-empty-'+width);}
await type(A,'[name=chips-0-colour]','red');await A.js(`document.querySelector('[name=chips-0-colour]').dispatchEvent(new Event('change',{bubbles:true}))`);
await type(A,'[name=chips-0-value]','25.50');await type(A,'[name=chips-0-label]','Small');
await A.click(`document.querySelector('[data-chip-add]')`);
check('add row preserves values and focuses colour',await A.js(`document.querySelector('[name=chips-0-value]').value==='25.50'&&document.activeElement.name==='chips-1-colour'`));
check('row motion settles',await A.js(`!document.querySelector('[name=chips-1-colour]').closest('fieldset').style.transform`));
await type(A,'[name=chips-1-colour]','green');await type(A,'[name=chips-1-value]','100');
await type(A,'[name=chips-1-label]','AlexandriaDeLaCruzWithAVeryLongChipNameXX');
await fit(A,320,'Long setup');await A.shot('setup-long-320');
await A.js(`document.querySelector('[name=chips-1-DELETE]').click()`);
check('remove hides only removed row',await A.js(`document.querySelector('[name=chips-1-DELETE]').closest('fieldset').hidden&&document.querySelector('[name=chips-0-value]').value==='25.50'`));
await A.click(`document.querySelector('[data-chip-add]')`);
check('add reuses removed row',await A.js(`document.querySelector('[name=chips-TOTAL_FORMS]').value==='2'&&!document.querySelector('[name=chips-1-DELETE]').closest('fieldset').hidden`));
await type(A,'[name=chips-1-colour]','green');await type(A,'[name=chips-1-value]','100');
await A.click(`document.querySelector('[data-chip-values] button.btn-primary')`);
check('setup saves through real POST',await A.js(`location.pathname==='/n/${ids.setup}/'&&document.body.textContent.includes('₱25.50')&&document.body.textContent.includes('₱100')`));
await A.go(`/n/${ids.other}/`);check('same colour has another session value',await A.js(`document.querySelector('.session-chip-values').textContent.includes('₱50')`));
await A.go(`/n/${ids.chips}/`);check('chips unit has no peso conversion',await A.js(`document.querySelector('.session-chip-values').textContent.includes('25 chips')&&!document.querySelector('.session-chip-values').textContent.includes('₱')`));
await P.go(`/s/${ids.set}/`);
await P.click(`document.querySelector('.own-count [data-sheet-open="chip-count-${ids.player}"]')`);
check('sheet opens with focus and initial blank total',await P.js(`document.querySelector('dialog[open]')!==null&&document.activeElement.name==='qty_white'&&document.querySelector('dialog [data-chip-total]').textContent==='—'`));
await type(P,'dialog [name=qty_red]','4');await type(P,'dialog [name=qty_green]','9');
check('exact live total',await P.js(`document.querySelector('dialog [data-chip-total]').textContent==='₱1,000'`));
for(const width of [320,390,1280]) {await fit(P,width,'Count sheet');await P.shot('count-sheet-'+width);}
check('quantity target and font',await P.js(`Array.from(document.querySelectorAll('dialog [data-chip-quantity]')).every(el=>el.getBoundingClientRect().height>=48&&parseFloat(getComputedStyle(el).fontSize)>=16)`));
await type(P,'dialog [name=qty_red]','1.5');check('invalid quantity never shows a valid total',await P.js(`document.querySelector('dialog [data-chip-total]').textContent==='Check quantities'`));
await type(P,'dialog [name=qty_red]','4');
await P.js(`document.querySelector('dialog').dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(450);
check('close restores opener focus',await P.js(`!document.querySelector('dialog[open]')&&document.activeElement.dataset.sheetOpen==='chip-count-${ids.player}'`));
await P.click(`document.querySelector('.own-count [data-sheet-open="chip-count-${ids.player}"]')`);
check('reopened sheet keeps draft',await P.js(`document.querySelector('dialog [name=qty_red]').value==='4'&&document.querySelector('dialog [name=qty_green]').value==='9'`));
await P.click(`document.querySelector('dialog .btn-primary')`);
check('player submits and accepted sheet closes',await P.js(`!document.querySelector('dialog[open]')&&document.body.textContent.includes('You entered')&&document.body.textContent.includes('₱1,000')`));
await A.go(`/n/${ids.night}/chip-values/`);check('first submission locks setup',await A.js(`document.body.textContent.includes('Chip values are locked')&&document.querySelector('.chip-value-fields').disabled`));
await A.go(`/s/${ids.set}/`);
await A.click(`document.querySelector('button[form=counts-form].confirm-all')`);
check('host accepts player count',await A.js(`document.body.textContent.includes('1 count confirmed')`));
await A.click(`document.querySelector('[data-sheet-open="player-${ids.player}"]')`);
check('host reviews original breakdown',await A.js(`document.querySelector('dialog').textContent.includes('Chip breakdown')&&document.querySelector('dialog').textContent.includes('4 × ₱25')`));
await A.js(`document.querySelector('dialog').dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(400);
await A.click(`document.querySelector('[data-sheet-open="chip-count-${ids.a}"]')`);
await type(A,'dialog [name=qty_green]','10');
await A.click(`document.querySelector('dialog .btn-primary')`);
check('host confirms own chip count',await A.js(`!document.querySelector('dialog[open]')&&document.body.textContent.includes('Count confirmed.')`));
await A.go(`/s/${ids.set}/cash-out-counted/`);
check('cash-out review balances with breakdowns',await A.js(`document.body.textContent.includes('After this batch the books balance.')&&document.querySelectorAll('.chip-breakdown').length===2`));
await A.click(`document.querySelector('.batch-review button[type=submit]')`);
check('real cash-out preserves balanced books',await A.js(`document.body.textContent.includes('All counts match buy-ins.')`));
// A closed draft keeps its original revision across another host's edit.
await P.go(`/s/${ids.stale}/`);
await P.click(`document.querySelector('.own-count [data-sheet-open="chip-count-${ids.stale_player}"]')`);
await type(P,'dialog [name=qty_red]','4');
await P.js(`document.querySelector('dialog').dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(400);
await A.go(`/n/${ids.stale_night}/chip-values/`);await type(A,'[name=chips-1-value]','50');
await A.click(`document.querySelector('[data-chip-values] button.btn-primary')`);await sleep(4600);
await P.click(`document.querySelector('.own-count [data-sheet-open="chip-count-${ids.stale_player}"]')`);
check('closed draft preserves old revision and warns after live update',await P.js(`document.querySelector('dialog [name=qty_red]').value==='4'&&document.querySelector('dialog [name=chip_revision]').value==='1'&&!document.querySelector('dialog [data-chip-stale]').hidden&&document.querySelector('dialog .btn-primary').disabled`));
await P.shot('stale-draft-390');
await P.go(`/s/${ids.stale}/counts/${ids.stale_player}/chips/`);
check('explicit reload starts a recount at current values',await P.js(`document.querySelector('[name=chip_revision]').value==='2'&&document.querySelector('[name=qty_red]').value===''`));
// The next set uses the session's same denominations. Reduced motion keeps it still.
await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
await A.go(`/s/${ids.second}/`);
await A.click(`document.querySelector('[data-sheet-open="chip-count-${ids.second_player}"]')`);
check('second set shares values and reduced motion opens without movement',await A.js(`document.querySelector('dialog').textContent.includes('₱25 each')&&document.querySelector('dialog').getAnimations().length===0`));
await A.js(`document.querySelector('dialog').dispatchEvent(new Event('cancel',{cancelable:true}))`);await sleep(100);
// Without JavaScript, the same setup form can add a row and the count form can write.
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
await A.go(`/n/${ids.setup}/chip-values/`);
await A.click(`document.querySelector('[data-chip-add]')`);
check('no-JS add colour',await A.js(`document.querySelector('[name=chips-2-colour]')!==null`));
await A.go(`/s/${ids.second}/counts/${ids.second_player}/chips/`);
await type(A,'[name=qty_green]','10');
await A.click(`document.querySelector('.chip-count-form .btn-primary')`);
check('no-JS chip count writes the exact total',await A.js(`location.pathname==='/s/${ids.second}/'&&document.body.textContent.includes('Count confirmed.')&&document.body.textContent.includes('₱1,000')`));
check('no-JS count page keeps sheet sources hidden',await A.js(`Array.from(document.querySelectorAll('[data-sheet-source^="chip-count-"]')).every(el=>el.hidden)`));
await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
// Reduced motion must remove the sheet's movement without hiding the form.
await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
await A.go(`/s/${ids.set}/`);
check('no runtime exceptions',errors.length===0,errors);
writeFileSync(`${OUT}/chip-values.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill();}
if(results.some(x=>!x.ok))process.exitCode=1;
