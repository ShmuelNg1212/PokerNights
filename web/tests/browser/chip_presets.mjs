// Group chip presets, from an empty list to a chip count that uses preset values. Run after seed_chip_presets.py on a fresh temporary database.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-chip-presets-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-chip-presets-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir=/private/tmp/pn-chip-presets-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 // A phone: a finger is the main pointer. A computer: a mouse.
 const phone=async(width=390,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:true},s);await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s)};
 const computer=async()=>{await send('Emulation.setTouchEmulationEnabled',{enabled:false},s);await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},s)};
 const point=async expr=>js(`(()=>{const el=${expr};el.scrollIntoView({block:'center'});const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 const down=async expr=>{const p=await point(expr);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},s);return p};
 const up=async()=>{await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},s)};
 const tap=async(expr,pause=40)=>{await down(expr);await up();await sleep(pause)};
 const shot=async name=>{await js('document.fonts.ready.then(()=>1)');const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await phone();
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,phone,computer,tap,down,up,shot};
}

const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${detail===undefined?'':' '+JSON.stringify(detail)}`)};
const ids=JSON.parse(readFileSync('/private/tmp/pn-chip-presets-manifest.json','utf8'));
const errors=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push([d.text,d.exception&&d.exception.description,d.url,d.lineNumber].join(' | '))}});
const H=await user('hana'),P=await user('ben');await send('Runtime.enable',{},H.s);await send('Runtime.enable',{},P.s);
const key=(scope,k)=>`document.querySelector('${scope} .numpad-key[data-key="${k}"]')`;
const choose=(U,sel,value)=>U.js(`(()=>{const f=document.querySelector(${JSON.stringify(sel)});f.value=${JSON.stringify(value)};f.dispatchEvent(new Event('change',{bubbles:true}));})()`);
const settings=`/g/${ids.group}/?view=settings`;
const fits=async(U,path,name)=>{for(const w of [320,390,1280]){await U.phone(w,w<900?844:900);await U.go(path);check(`${name} fits ${w}`,await U.js(`document.documentElement.scrollWidth<=${w}`));if(name==='settings')await U.js(`document.querySelector('#chip-presets').scrollIntoView({block:'start'})`);await U.shot(`${name}-${w}`);}await U.phone();};
try {
 await H.go(settings);
 check('settings: the group starts with no chip presets',await H.js(`document.querySelector('#chip-presets').textContent.includes('No chip presets yet')`));
 await H.go(`/g/${ids.group}/chip-presets/new/`);
 await H.js(`document.querySelector('[name=name]').value='Home set'`);
 await choose(H,'[name=chips-0-colour]','red');
 const V=n=>`document.querySelector('[name=chips-${n}-value]')`;
 await H.tap(V(0));await sleep(300);
 check('preset: values use the number keys',await H.js(`${V(0)}.getAttribute('inputmode')==='none'&&!!document.querySelector('.numpad-panel')`));
 check('preset: a pesos preset has a decimal point',await H.js(`${key('.numpad-panel','alt')}.textContent==='.'`));
 for(const k of ['2','5']) await H.tap(key('.numpad-panel',k),80);
 await H.js(`document.querySelector('[name=unit]').focus()`);await sleep(100); // a tap on the select takes the focus, as on a phone
 await choose(H,'[name=unit]','chips');await H.tap(V(0));await sleep(200);
 check('preset: the keys follow the unit choice',await H.js(`${key('.numpad-panel','alt')}.textContent==='00'`));
 await choose(H,'[name=unit]','php');
 await H.js(`document.querySelector('[data-chip-add]').click()`);await sleep(300);
 await choose(H,'[name=chips-1-colour]','green');
 await H.tap(V(1));await sleep(200);for(const k of ['1','0','0']) await H.tap(key('.numpad-panel',k),80);
 check('preset: keys wrote both values',await H.js(`${V(0)}.value==='25'&&${V(1)}.value==='100'`),await H.js(`[${V(0)}.value,${V(1)}.value]`));
 await H.js(`document.querySelector('[data-chip-values] .btn-primary').click()`);await sleep(900);
 check('preset: saved and listed in group settings',await H.js(`location.search.includes('view=settings')&&(t=>t.includes('Home set')&&t.includes('₱25')&&t.includes('₱100'))(document.querySelector('#chip-presets').textContent)`));
 // Fill a session in place, then save.
 await H.go(`/n/${ids.night}/chip-values/`);await H.js(`window.__stay=1`);
 check('session: the picker offers the preset',await H.js(`[...document.querySelectorAll('#chip-preset option')].some(o=>o.textContent==='Home set')`));
 await H.js(`document.querySelector('[data-chip-preset-form] [type=submit]').click()`);await sleep(500);
 check('session: Fill works in place',await H.js(`window.__stay===1`));
 check('session: rows hold the preset',await H.js(`document.querySelector('[name=chips-0-colour]').value==='red'&&${V(0)}.value==='25'&&document.querySelector('[name=chips-1-colour]').value==='green'&&${V(1)}.value==='100'`));
 check('session: the note names the preset',await H.js(`document.querySelector('[data-chip-preset-note]').textContent.startsWith('Filled from Home set')&&!!document.querySelector('[data-chip-from-preset]').value`));
 check('session: row movement settles',await H.js(`new Promise(r=>setTimeout(()=>r([...document.querySelectorAll('[data-chip-value-row]')].every(x=>!x.style.transform)),600))`));
 await H.js(`document.querySelector('[data-chip-values] .btn-primary').click()`);await sleep(900);
 check('session: saved values show on the session',await H.js(`location.pathname==='/n/${ids.night}/'&&(t=>t.includes('₱25')&&t.includes('₱100'))(document.querySelector('.session-chip-values').textContent)`));
 // The player counts with the preset's values.
 await P.go(`/s/${ids.set}/`);
 await P.tap(`document.querySelector('#own-count')`);await sleep(500);
 await P.tap(`document.querySelector('.numpad-panel [data-numpad-chips]:not([hidden])')`);await sleep(800);
 const D=`document.querySelector('dialog[open]')`;
 check('count: the sheet uses the preset values',await P.js(`${D}.textContent.includes('₱25 each')&&${D}.textContent.includes('₱100 each')`));
 await P.tap(`${D}.querySelector('[name=qty_red]')`);await P.tap(key('dialog[open]','4'),80);
 check('count: total from preset values',await P.js(`${D}.querySelector('[data-chip-total]').textContent==='₱100'`));
 await P.js(`${D}.querySelector('.chip-count-send [type=submit]:not([name])').scrollIntoView({block:'center'})`);
 await P.tap(`document.querySelector('dialog[open] .chip-count-send [type=submit]:not([name])')`);await sleep(1500);
 check('count: the count reaches the server',await P.js(`document.querySelector('.own-count').textContent.includes('You entered ₱100')`));
 // A chips session is not offered a pesos preset.
 await H.go(`/n/${ids.chips}/chip-values/`);
 check('chips session: no pesos preset offered',await H.js(`!document.querySelector('[data-chip-preset-form]')`));
 // Save a session's rows as a new preset with Enter.
 await H.go(`/n/${ids.native}/chip-values/`);
 await choose(H,'[name=chips-0-colour]','blue');await H.js(`${V(0)}.value='5'`);
 await H.js(`document.querySelector('.chip-save-preset').open=true;document.querySelector('[data-chip-preset-name]').value='Blues';document.querySelector('[data-chip-preset-name]').focus()`);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r'},H.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13},H.s);await sleep(1000);
 check('save as preset: Enter saves the preset and keeps the rows',await H.js(`document.body.textContent.includes('Saved Blues as a group preset')&&${V(0)}.value==='5'&&document.querySelectorAll('[data-chip-value-row]:not([hidden])').length===1`));
 await H.go(`/n/${ids.native}/`);
 check('save as preset: the session did not change',await H.js(`!document.querySelector('.chip-value-reference')`));
 // Without JavaScript.
 const N=await user('hana');await send('Emulation.setScriptExecutionDisabled',{value:true},N.s);
 await N.go(`/n/${ids.native}/chip-values/`);
 await N.js(`(()=>{const s=document.querySelector('#chip-preset');s.value=[...s.options].find(o=>o.textContent==='Home set').value})()`);
 await N.js(`document.querySelector('[data-chip-preset-form] [type=submit]').click()`);await sleep(900);
 check('no script: Fill fills by a page',await N.js(`document.body.textContent.includes('Filled from Home set')&&document.querySelector('[name=chips-0-value]').value==='25'`));
 await N.js(`document.querySelector('[data-chip-values] .btn-primary').click()`);await sleep(900);
 check('no script: Save copies the values',await N.js(`location.pathname==='/n/${ids.native}/'&&document.querySelector('.session-chip-values').textContent.includes('₱25')`));
 // Players read, hosts edit.
 await P.go(settings);
 check('player: reads presets without edit links',await P.js(`(s=>s.textContent.includes('Home set')&&s.textContent.includes('Blues')&&!s.querySelector('a[href*="chip-presets"]'))(document.querySelector('#chip-presets'))`));
 await fits(H,settings,'settings');await fits(H,`/g/${ids.group}/chip-presets/new/`,'preset-new');
 await H.go(settings);const edit=await H.js(`document.querySelector('#chip-presets a[href*="chip-presets/"]').getAttribute('href')`);await fits(H,edit,'preset-edit');
 await fits(H,`/n/${ids.native}/chip-values/`,'session-values');
 check('no script errors',errors.length===0,errors);
} catch(e) { check('run completed: '+e.message,false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
