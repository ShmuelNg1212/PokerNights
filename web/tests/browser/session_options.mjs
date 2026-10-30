// New session options, from the form to what a player sees. Run after seed_session_options.py on a fresh temporary database.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-session-options-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765',PROFILE='/private/tmp/pn-session-options-chrome',PORT=9351;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok,detail)=>{results.push(ok);console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,300)}`)};
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const settle=async()=>{await sleep(600);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(200)};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await settle()};
 const size=async width=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const shot=async name=>{await js('document.fonts.ready.then(()=>1)');const m=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:m.cssContentSize.width,height:m.cssContentSize.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await size(390);await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await settle();
 return {s,js,go,size,shot,settle};
}
const {group}=JSON.parse(readFileSync('/private/tmp/pn-session-options-manifest.json','utf8'));
const NEW=`/g/${group}/sessions/new/`,FORM=`document.querySelector('form.form-groups')`,CHOOSER=`document.querySelector('[name=chip_preset_id]')`;
const names=`[...${CHOOSER}.options].map(o=>o.textContent)`,submit=`${FORM}.requestSubmit(${FORM}.querySelector('[type=submit]'))`;
const setUnit=unit=>`(()=>{const u=document.querySelector('[name=unit]');u.value='${unit}';u.dispatchEvent(new Event('change',{bubbles:true}))})()`;
try{
 const A=await user('hana'),B=await user('ben');
 // The form
 await A.go(NEW);
 check('the options start off',await A.js(`${CHOOSER}.value===''&&!document.querySelector('[name=announce]').checked`));
 check('the start time is off the page until the box is ticked',await A.js(`getComputedStyle(document.querySelector('[name=start_time]').closest('.field')).display==='none'`));
 for(const width of [320,390,1280]){await A.size(width);
  check('fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));
  check('48px targets '+width,await A.js(`document.querySelector('.session-options .check').getBoundingClientRect().height>=48&&${CHOOSER}.getBoundingClientRect().height>=48`));
  await A.js(`document.querySelector('[name=announce]').checked=true`);check('the start time is a 48px field '+width,await A.js(`(()=>{const t=document.querySelector('[name=start_time]').getBoundingClientRect(),c=${CHOOSER}.getBoundingClientRect();return t.height>=48&&Math.round(t.width)===Math.round(c.width)})()`));await A.shot('form-'+width);await A.js(`document.querySelector('[name=announce]').checked=false`);}
 await A.size(390);
 check('the list starts with the pesos presets',JSON.stringify(await A.js(names))==='["Set later","Home set"]',await A.js(names));
 await A.js(`${CHOOSER}.selectedIndex=1`);await A.js(setUnit('chips'));
 check('changing the unit replaces the list and clears a choice that no longer fits',JSON.stringify(await A.js(names))==='["Set later","Tournament set (Chips)"]'&&await A.js(`${CHOOSER}.value===''`),await A.js(names));
 await A.js(setUnit('php'));await A.js(`document.querySelector('[name=preset]').selectedIndex=0;document.querySelector('[name=preset]').dispatchEvent(new Event('change',{bubbles:true}))`);
 check('a stakes preset does not choose a chip preset',await A.js(`${CHOOSER}.value===''`));
 // Without the options: hidden from the player
 await A.js(submit);await A.settle();
 const plain=await A.js('location.pathname');
 check('creating lands on the session page with both cards',/^\/n\/\d+\/$/.test(plain)&&await A.js(`!!document.querySelector('#announce')&&!!document.querySelector('.session-chip-values')`),plain);
 check('Announce is the one primary action',await A.js(`document.querySelectorAll('main .btn-primary').length===1&&document.querySelector('main .btn-primary').textContent.trim()==='Announce to the group'`),await A.js(`[...document.querySelectorAll('main .btn-primary')].map(b=>b.textContent.trim())`));
 check('the Announce card start time is a 48px field',await A.js(`document.querySelector('#announce-time').getBoundingClientRect().height>=48`));await A.shot('session-page');
 await B.go(plain);check('a session without the options stays hidden from the player',await B.js(`document.title.includes('Not found')||!document.querySelector('.night-layout')`));
 // A refusal: the chips preset on a pesos game, as a page without the script could send it
 await A.go(NEW);const chipsId=await A.js(`(()=>{const c=document.createElement('option');return fetch(location.href).then(r=>r.text()).then(t=>new DOMParser().parseFromString(t,'text/html').querySelector('option[data-unit=chips]').value)})()`);
 await A.js(`(()=>{const o=document.createElement('option');o.value='${chipsId}';${CHOOSER}.appendChild(o);${CHOOSER}.value='${chipsId}';document.querySelector('[name=announce]').checked=true;document.querySelector('[name=location]').value='Kept place'})()`);
 await A.js(submit);await A.settle();
 check('the other unit is refused and the typed text stays',await A.js(`location.pathname==='${NEW}'&&document.body.textContent.includes('uses another unit')&&document.querySelector('[name=location]').value==='Kept place'&&document.querySelector('[name=announce]').checked`));
 await A.shot('refused');
 // With both options: the player is told and sees it
 await A.js(`${CHOOSER}.selectedIndex=1;document.querySelector('[name=start_time]').value='20:30'`);
 check('a ticked box shows the start time',await A.js(`getComputedStyle(document.querySelector('[name=start_time]').closest('.field')).display!=='none'`));
 await A.js(submit);await A.settle();
 const both=await A.js('location.pathname');
 check('both options apply',/^\/n\/\d+\/$/.test(both)&&await A.js(`!!document.querySelector('#coming')&&!document.querySelector('#announce')&&!!document.querySelector('.chip-value-reference')&&document.body.textContent.includes('Starts 8:30 PM')`),both);
 check('after announcing, Open set 1 leads',await A.js(`[...document.querySelectorAll('main .btn-primary')].some(b=>b.textContent.trim()==='Open set 1')`));
 await A.shot('session-page-announced');
 await B.go('/');check('the player is asked on the home page',await B.js(`document.body.textContent.includes('Are you in?')`));
 await B.go(both);check('the player sees the session and its chip values',await B.js(`!!document.querySelector('#coming')&&!!document.querySelector('.chip-value-reference')`));
 await B.shot('player-session');
 // Without JavaScript
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go(NEW);
 check('without the script both units are listed',JSON.stringify(await send('Runtime.evaluate',{expression:names,returnByValue:true},A.s).then(r=>r.result.value))==='["Set later","Home set","Tournament set (Chips)"]');
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
}catch(error){check('script ran to the end',false,String(error))}
writeFileSync(`${OUT}/session_options.json`,JSON.stringify(results));
console.log(`${results.filter(Boolean).length}/${results.length} passed`);chrome.kill();ws.close();process.exit(results.every(Boolean)?0:1);
