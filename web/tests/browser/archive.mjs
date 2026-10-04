import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-archive-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
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

// Archive and delete sessions and groups. Run after seed.py, seed_end_set.py, seed_night.py and seed_archive.py.
const M=JSON.parse(readFileSync('/private/tmp/pn-archive-manifest.json','utf8'));
const size=(A,width)=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main summary, main input:not([type=hidden])')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
async function look(A,name,path,widths=[320,390,1280]){for(const width of widths){await size(A,width);await A.go(path);await A.js(`document.querySelectorAll('details.night-manage, details.archived-sessions, details.home-archived').forEach(d=>d.open=true)`);check(`${name} fits ${width}`,await A.js(`document.documentElement.scrollWidth<=${width}`));check(`${name} 48px targets ${width}`,await A.js(targets));await A.shot(`archive-${name}-${width}`);}await size(A,390);}
try {
 const A=await user('hana'),P=await user('ben');
 // Session: manage section, confirmation with unpaid transfers, archive, read-only page, restore.
 await look(A,'night-manage',`/n/${M.unpaid}/`);
 check('manage offers archive, not delete, when money exists',await A.js(`!!document.querySelector('.night-manage a[href$="/archive/"]')&&!document.querySelector('.night-manage a[href$="/delete/"]')&&${text('cannot be deleted')}`));
 await P.go(`/n/${M.unpaid}/`);check('player has no manage section',await P.js(`!document.querySelector('.night-manage')`));
 await look(A,'night-archive-confirm',`/n/${M.unpaid}/archive/`);
 check('confirmation names unpaid transfers',await A.js(`${text('not marked paid')}&&${text('Archive with unpaid transfers')}`));
 const stats=`document.querySelector('main').textContent.replace(/\\s+/g,' ')`;await A.go(`/g/${M.group}/?view=stats`);const before=await A.js(stats);
 await A.go(`/n/${M.unpaid}/archive/`);await A.click(`document.querySelector('form.form-section button')`);
 check('archive lands on the group with a message',await A.js(`location.pathname==='/g/${M.group}/'&&${text('Session archived')}`));
 check('archived list shows it',await A.js(`!!document.querySelector('.archived-sessions a[href="/n/${M.unpaid}/"]')&&!document.querySelector('.group-sessions:not(.archived-sessions) a[href="/n/${M.unpaid}/"]')`));
 await look(A,'group-sessions-archived',`/g/${M.group}/`);
 await P.go(`/g/${M.group}/`);check('player sees no archived list',await P.js(`!document.querySelector('.archived-sessions')`));
 await look(A,'night-archived',`/n/${M.unpaid}/`);
 check('archived page: notice, restore, no payment action',await A.js(`${text('This session is archived')}&&!!document.querySelector('form[action$="/restore/"] button')&&!document.querySelector('form[action*="/transfers/"]')`));
 await A.go(`/s/${M.unpaid_set}/`);check('archived set page shows the notice and no host dock',await A.js(`${text('This session is archived')}&&!document.querySelector('.host-controls')`));await A.shot('archive-set-archived-390');
 await A.go(`/g/${M.group}/?view=stats`);check('stats changed while archived',await A.js(stats)!==before);await A.shot('archive-stats-while-archived-390');
 await A.go(`/n/${M.unpaid}/`);await A.click(`document.querySelector('form[action$="/restore/"] button')`);
 check('restore returns actions',await A.js(`${text('Session restored')}&&!!document.querySelector('form[action*="/transfers/"]')`));
 await A.go(`/g/${M.group}/?view=stats`);check('stats return to their earlier figures',await A.js(stats)===before);
 // Session with a set in play: neither action.
 await A.go(`/n/${M.live}/`);await A.js(`document.querySelector('.night-manage').open=true`);
 check('live session offers neither action',await A.js(`!document.querySelector('.night-manage a.btn')&&${text('finish or cancel every set first')}`));await A.shot('archive-night-live-390');
 // Session without money: delete, with keyboard and focus.
 await look(A,'night-delete-confirm',`/n/${M.empty}/delete/`);
 await A.js(`document.querySelector('form.form-section button').focus()`);
 check('delete button is the danger style',await A.js(`document.querySelector('form.form-section button').classList.contains('btn-danger')`));
 await A.click(`document.querySelector('form.form-section button')`);
 check('delete lands on the group with a message',await A.js(`location.pathname==='/g/${M.group}/'&&${text('Deleted the session')}`));
 await A.go(`/n/${M.empty}/`);check('deleted session is not found',await A.js(`document.title.includes('Not Found')||${text('Not Found')}||${text('not found')}`));
 // Without JavaScript: delete the second empty session through native forms.
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
 await A.go(`/n/${M.second}/`);check('no JavaScript: manage disclosure is a native details',await A.js(`document.querySelector('.night-manage').tagName==='DETAILS'`));
 await A.go(`/n/${M.second}/delete/`);await A.click(`document.querySelector('form.form-section button')`);
 check('no JavaScript: delete works',await A.js(`location.pathname==='/g/${M.group}/'&&${text('Deleted the session')}`));
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
 // Group settings and confirmation pages.
 await look(A,'group-manage',`/g/${M.group}/?view=settings`);
 check('group settings has the manage section',await A.js(`!!document.querySelector('#manage a[href$="/archive/"]')&&!!document.querySelector('#manage a[href$="/delete/"]')`));
 await P.go(`/g/${M.group}/?view=settings`);check('player has no group manage section',await P.js(`!document.querySelector('#manage')`));
 await look(A,'group-archive-blocked',`/g/${M.group}/archive/`,[390]);
 check('group with a live set cannot be archived',await A.js(`${text('Finish or cancel every set first')}&&!document.querySelector('form.form-section')`));
 await look(A,'group-delete-confirm',`/g/${M.club}/delete/`);
 await look(A,'group-delete-long',`/g/${M.long}/delete/`,[320]);
 await A.go(`/g/${M.club}/delete/`);await A.js(`document.querySelector('[name=confirm_name]').value='empty club'`);await A.click(`document.querySelector('form.form-section button')`);
 check('wrong name is refused and kept',await A.js(`${text('Type the group name exactly')}&&document.querySelector('[name=confirm_name]').value==='empty club'&&document.querySelector('[name=confirm_name]').labels.length===1`));await A.shot('archive-group-delete-refused-390');
 // Archive a group, see it on home, restore, then delete it.
 await look(A,'group-archive-confirm',`/g/${M.club}/archive/`);
 await A.click(`document.querySelector('form.form-section button')`);
 check('group archive lands on home',await A.js(`location.pathname==='/'&&${text('Empty Club is archived')}&&!document.querySelector('.home-groups a[href="/g/${M.club}/"]')`));
 await look(A,'home-archived','/');
 check('home lists the archived group with restore',await A.js(`!!document.querySelector('.home-archived form[action="/g/${M.club}/restore/"] button')`));
 await A.go(`/g/${M.club}/`);check('archived group page is not found',await A.js(`${text('Not Found')}||${text('not found')}`));
 await A.go('/');await A.js(`document.querySelector('.home-archived').open=true`);await A.click(`document.querySelector('.home-archived form[action="/g/${M.club}/restore/"] button')`);
 check('restore opens the group',await A.js(`location.pathname==='/g/${M.club}/'&&${text('Empty Club is restored')}`));
 await A.go(`/g/${M.club}/delete/`);await A.js(`document.querySelector('[name=confirm_name]').value='Empty Club'`);await A.click(`document.querySelector('form.form-section button')`);
 check('group delete lands on home',await A.js(`location.pathname==='/'&&${text('Deleted the group Empty Club')}`));
 // Keyboard focus is visible on the danger link.
 await A.go(`/g/${M.group}/?view=settings`);await A.js(`document.querySelector('#manage a.btn-danger').focus()`);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9,modifiers:8},A.s);await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);
 check('danger link shows keyboard focus',await A.js(`document.activeElement.matches('#manage a.btn-danger')&&getComputedStyle(document.activeElement).outlineWidth==='3px'`));
 writeFileSync(`${OUT}/archive.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
