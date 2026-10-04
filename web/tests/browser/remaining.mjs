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
const A=await user('hana'),P=await user('ben'),N=await user(''),E=await user('empty-user'),F=await user(process.env.PN_EMPTY_ACCOUNT || 'unattached');
const extra=JSON.parse(readFileSync('/private/tmp/pn-slice4-manifest.json','utf8'));
const submit=async(U,selector,values)=>{await U.js(`(()=>{const f=document.querySelector(${JSON.stringify(selector)});for(const [k,v] of Object.entries(${JSON.stringify(values)})){f.elements[k].value=v;}f.requestSubmit();})()`);await sleep(700)};
try {
await A.go('/');const group=await A.js(`document.querySelector('a[href^="/g/"]').getAttribute('href')`);
await A.go(group);const preset=await A.js(`document.querySelector('a[href*=presets]:not([href$="/new/"])')?.getAttribute('href')`);
const newSession=await A.js(`document.querySelector('a[href$="/new/"][href*=sessions]')?.getAttribute('href')`);
for(const [name,U,path] of [['home',A,'/'],['empty-home',F,'/'],['empty-group',E,'/g/'+extra.empty_group+'/'],['canceled',A,'/s/'+extra.canceled+'/'],['group-host',A,group],['group-player',P,group],['login',N,'/accounts/login/'],['signup',N,'/accounts/signup/'],['invite-invalid',A,'/join/invalid/'],['new-session',A,newSession],['preset',A,preset],['picker',A,'/s/3/players/add-several/'],['settings',A,'/s/3/settings/'],['log',A,'/s/1/log/']]) {
 if(!path)throw Error('missing route '+name);
 for(const width of [390,1280]) {await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},U.s);await U.go(path);check(name+' loads '+width,await U.js(`!document.body.textContent.includes('Page not found')&&!document.body.textContent.includes('Traceback')`));check(name+' action targets '+width,await U.js(`[...document.querySelectorAll('main a,.brand')].every(a=>a.getBoundingClientRect().height>=48)`));check(name+' fits '+width,await U.js(`document.documentElement.scrollWidth<=${width}`));await U.shot(name+'-'+width)}
}
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},A.s);await A.go(group);
check('sessions first viewport',await A.js(`document.querySelector('a[href^="/n/"]').getBoundingClientRect().bottom<844&&document.querySelector('a[href*=sessions][href$="/new/"]').getBoundingClientRect().bottom<844`));
check('clean title',await A.js(`!document.title.includes('<form')`));
await P.go(group);check('player tools hidden',await P.js(`!document.querySelector('form[action*=members]')&&!document.querySelector('form[action*=invites]')`));
await A.js(`document.querySelector('form[action$="/tables/new/"]')?.closest('details').setAttribute('open','')`);
// Fetch follows the redirect and consumes the one-use draft. Use native POST instead for visible evidence.
await A.js(`const f=document.querySelector('form[action$="/tables/new/"]');f.noValidate=true;f.elements.name.value='Kitchen invalid';f.elements.seat_count.value='13';f.requestSubmit()`);await sleep(700);
check('table refusal retained',await A.js(`document.querySelector('[name=name][id^=table]').value==='Kitchen invalid'&&document.querySelector('[name=seat_count]').value==='13'&&document.querySelector('form[action$="/tables/new/"]').closest('details').open`));await A.shot('group-table-error-390');
await A.js(`const f=document.querySelector('form[action$="/members/add/"]');f.closest('details').open=true;f.elements.name.value='Ben';f.requestSubmit()`);await sleep(700);
check('duplicate roster retained',await A.js(`document.querySelector('#add_name').value==='Ben'&&!!document.querySelector('form[action$="/members/add/"] .errors')`));await A.shot('group-roster-error-390');
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},N.s);await N.go('/accounts/login/?next='+encodeURIComponent(group));await submit(N,'form.form-section',{username:'wrong-user',password:'wrong-password'});check('login refusal retains username and next',await N.js(`document.querySelector('[name=username]').value==='wrong-user'&&document.querySelector('[name=password]').value===''&&document.querySelector('[name=next]').value===${JSON.stringify(group)}`));await N.shot('login-error-390');
await N.go('/accounts/signup/');await submit(N,'form.form-section',{username:'hana',password1:'tablestakes-91',password2:'different-91'});check('signup errors retained',await N.js(`document.querySelector('[name=username]').value==='hana'&&!!document.querySelector('.errors')&&document.querySelector('[name=password1]').value===''`));await N.shot('signup-error-390');
await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go(group);await A.js(`const f=document.querySelector('form[action$="/members/add/"]');f.closest('details').open=true;f.elements.name.value='No script player';f.requestSubmit()`);await sleep(700);check('native roster write works',await A.js(`document.body.textContent.includes('No script player')`));await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
for(const path of [group,'/s/1/log/','/accounts/login/']) {await send('Emulation.setDeviceMetricsOverride',{width:320,height:844,deviceScaleFactor:1,mobile:true},A.s);await A.go(path);check('edge320 '+path,await A.js(`document.documentElement.scrollWidth<=320`));await A.shot('edge-'+path.replaceAll('/','-')+'320')}
writeFileSync(`${OUT}/remaining.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
