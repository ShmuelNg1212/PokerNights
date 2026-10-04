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
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section button').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
try{const A=await user('hana'),N=await user('unattached');const extra=JSON.parse(readFileSync('/private/tmp/pn-slice4-manifest.json','utf8'));
for(const [name,path] of [['long-log','/s/'+extra.long_log+'/log/'],['override-log','/s/10/log/']]){for(const width of [390,1280,320]){await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);await A.go(path);check(name+' fit'+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot(name+'-'+width)}}
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},A.s);await A.go('/g/1/');await A.click(`document.querySelector('form[action$="/invites/new/"] button')`);const link=await A.js(`document.querySelector('input[aria-label="Invite link"]').value`);check('invite shown',!!link);await A.shot('group-invite-390');await send('Emulation.setDeviceMetricsOverride',{width:1280,height:844,deviceScaleFactor:1,mobile:false},A.s);await A.shot('group-invite-1280');
for(const width of [390,1280]){await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},N.s);await N.go(new URL(link).pathname);await N.shot('join-'+width)}
await N.click(`document.querySelector('form.form-section button')`);check('invite accepted',await N.js(`document.body.textContent.includes('Kamuning Card Club')&&location.pathname==='/g/1/'`));
await A.go('/g/1/');check('invite consumed once',await A.js(`!document.querySelector('input[aria-label="Invite link"]')`));await A.click(`document.querySelector('form[action$="/revoke/"] button')`);await N.go(new URL(link).pathname);check('revoked invite invalid',await N.js(`document.body.textContent.includes('not valid')`));
writeFileSync(`${OUT}/supplement.json`,JSON.stringify(results,null,2));}finally{await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
