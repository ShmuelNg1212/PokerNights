// Payments at the table (ADR 0002). Seed a fresh temporary database with seed_table_payments.py alone,
// serve it on 127.0.0.1:8765, then run. Captures 320, 390 and 1280px and the page without JavaScript.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-table-pay-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-table-pay-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-table-pay-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,{width=390,height=844,scripts=true}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async(file,full=false)=>{let clip;if(full){const m=await send('Page.getLayoutMetrics',{},s);clip={x:0,y:0,width,height:Math.ceil(m.cssContentSize.height),scale:1}}const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:full,...(clip?{clip}:{})},s);writeFileSync(`${OUT}/${file}.png`,Buffer.from(data,'base64'))};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(800);
 if(!scripts)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,width};}
const results=[];function check(name,ok,detail){results.push({name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const targets=`[...document.querySelectorAll('.table-pay button:not([hidden]), .table-pay summary.btn, .table-pay select, .table-pay input:not([type=hidden])')].filter(e=>e.offsetParent).map(e=>Math.round(e.getBoundingClientRect().height))`;
const night='/n/'+M.tonight+'/',closed='/n/'+M.closed+'/';
try {
const H=await user('hana');
await H.go(night);
check('the open session lists one payment and one undone',await H.js(`document.querySelectorAll('.table-pay-row').length===2&&document.querySelectorAll('.table-pay-row.is-undone').length===1`));
check('the undone row is struck and gives the reason',await H.js(`/undone: Wrong player/.test(document.querySelector('.table-pay-row.is-undone').textContent)&&!!document.querySelector('.table-pay-row.is-undone .struck')`));
check('controls in the section are 48px',(await H.js(targets)).every(h=>h>=48),await H.js(targets));
check('390: no sideways scroll',await H.js(fits(390)));
await H.js(`document.querySelector('.table-pay').scrollIntoView()`);await H.shot('table-pay-open-390');
await H.js(`document.querySelector('.table-pay-opener').click()`);await sleep(600);
check('the opener shows a sheet titled Paid at the table',await H.js(`!!document.querySelector('dialog[open]')&&document.querySelector('dialog[open] h2').textContent==='Paid at the table'`));
check('the sheet has two players, an amount and one primary action',await H.js(`(()=>{const d=document.querySelector('dialog[open]');return d.querySelectorAll('select').length===2&&!!d.querySelector('input[name=amount]')&&d.querySelectorAll('.btn-primary').length===1})()`));
await H.shot('table-pay-sheet-390');
await H.js(`(()=>{const d=document.querySelector('dialog[open]');const o=[...d.querySelectorAll('select[name=payer] option')];d.querySelector('select[name=payer]').value=o.find(x=>x.textContent==='Ana').value;d.querySelector('select[name=payee]').value=o.find(x=>x.textContent==='Ben').value;d.querySelector('input[name=amount]').value='4250.50';d.querySelector('button[type=submit]').click()})()`);
await sleep(1500);
check('recording returns to the session page with a third row',await H.js(`location.pathname===${JSON.stringify(night)}&&document.querySelectorAll('.table-pay-row').length===3&&/Ana.*Ben.*₱4,250\\.50/.test(document.querySelector('.table-pay-row:last-child').textContent.replace(/\\s+/g,' '))`),await H.js(`[...document.querySelectorAll('.table-pay-row')].map(r=>r.textContent.replace(/\\s+/g,' ').trim())`));
// The set page: Ben left; his sheet offers the link, which fills the form.
await H.go('/s/'+M.set+'/');
await H.js(`document.querySelector('[data-sheet-open="player-${M.ben_participant}"]').click()`);await sleep(600);
check('a left winner\'s sheet asks who paid him and links to the form',await H.js(`/Up ₱4,250\\.50 in this set\\. Did someone pay Ben/.test(document.querySelector('dialog[open] .leaver-pay').textContent)&&!!document.querySelector('dialog[open] .leaver-pay a.btn')`));
await H.shot('table-pay-leaver-sheet-390');
await H.js(`document.querySelector('dialog[open] .leaver-pay a').click()`);await sleep(1200);
check('the form page has Ben as payee and the amount filled',await H.js(`document.querySelector('select[name=payee] option:checked').textContent==='Ben'&&document.querySelector('select[name=payer]').value===''&&document.querySelector('input[name=amount]').value==='4250.50'`));
await H.shot('table-pay-form-390');
// Closed session with a large table payment.
await H.go(closed);await sleep(300);
if(await H.js(`!!document.querySelector('dialog[open]')`)){await H.js(`document.querySelector('.sheet-head button').click()`);await sleep(450)}
check('closed: the explanation names table payments',await H.js(`/subtracts the payments made at the table/.test(document.querySelector('.night-how').textContent)`));
await H.js(`document.querySelector('.night-records summary').click()`);
check('closed: the record says At the table',await H.js(`/At the table · recorded by hana/.test(document.querySelector('.payment-records').textContent)&&/paid Ben ₱1,234,567/.test(document.querySelector('.payment-records').textContent)`));
check('closed: no Paid at the table form',await H.js(`!document.querySelector('.table-pay')`));
await H.shot('table-pay-closed-390',true);
// Player.
const B=await user('ben');await B.go(night);
check('a player sees the list and own line but no form or undo',await B.js(`!!document.querySelector('.table-pay')&&!document.querySelector('.table-pay-opener, .table-pay-fallback, .table-pay-undo')&&/Ana paid you ₱4,250\\.50 at the table\\./.test(document.querySelector('.night-mine').textContent)`));
await B.shot('table-pay-player-390',true);
// Widths.
const N=await user('hana',{width:320,height:700});await N.go(night);
check('320: no sideways scroll, the long name wraps inside its row',await N.js(fits(320)+`&&[...document.querySelectorAll('.table-pay-row')].every(r=>r.scrollWidth<=r.clientWidth+1)`));
await N.js(`document.querySelector('.table-pay').scrollIntoView()`);await N.shot('table-pay-open-320');
const W=await user('hana',{width:1280,height:900});await W.go(night);
check('1280: no sideways scroll',await W.js(fits(1280)));await W.shot('table-pay-open-1280',true);
// Without JavaScript the disclosure holds the form.
const X=await user('hana',{scripts:false});await X.go(night);
check('no JavaScript: the opener is hidden and the disclosure shows',await X.js(`document.querySelector('.table-pay-opener').hidden&&getComputedStyle(document.querySelector('.table-pay-fallback')).display!=='none'`));
check('no runtime errors',errors.length===0,errors);
} finally { ws.close();chrome.kill(); }
const failed=results.filter(r=>!r.ok);writeFileSync(`${OUT}/table_payments.json`,JSON.stringify(results,null,1));
console.log(`${results.length-failed.length} of ${results.length} pass`);process.exit(failed.length?1:0);
