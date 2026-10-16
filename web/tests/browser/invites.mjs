// Group settings → Invite players: links shown again, Copy and Share, the new link's arrival, a revoke, Past invites.
// Seed a fresh temporary database with seed_invites.py, serve it on 127.0.0.1:8765, then run.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-invites-manifest.json','utf8'));
const SETTINGS=`/g/${M.group}/?view=settings`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const UA={phone:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
 desktop:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'};
rmSync('/private/tmp/pn-invites-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-invites-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BOOT=({share})=>`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__copied=[];window.__shared=[];
 try{Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>(__copied.push(t),Promise.resolve())},configurable:true})}catch(e){}
 try{Object.defineProperty(navigator,'share',{value:${share?`d=>(__shared.push(d),Promise.resolve())`:'undefined'},configurable:true})}catch(e){}`;
async function user(kind,width,{share=true,reduced=false,height=844}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:2,mobile:kind==='phone'},s);
 await send('Emulation.setUserAgentOverride',{userAgent:UA[kind]},s);if(kind==='phone')await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 if(reduced)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT({share})},s);
 const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const settle=async()=>{await sleep(400);for(let i=0;i<30;i++){if(await ev('document.readyState')==='complete')break;await sleep(100)}};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await settle()};
 const shot=async(n,full)=>{const p={format:'png'};if(full){const m=await send('Page.getLayoutMetrics',{},s);p.clip={x:0,y:0,width,height:Math.ceil(m.cssContentSize.height),scale:1};p.captureBeyondViewport=true}const{data}=await send('Page.captureScreenshot',p,s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=4000)=>{for(let t=0;t<ms;t+=50){if(await ev(expression))return true;await sleep(50)}return false};
 const login=async()=>{await go('/accounts/login/');await ev(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(500);await settle()};
 return {s,js:ev,go,shot,until,login,settle};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const S=`document.getElementById('invites')`;
const tidy=w=>`[...${S}.querySelectorAll('.btn,summary,input[readonly]')].filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=48)&&document.documentElement.scrollWidth<=${w}`;
const address=`${BASE}/join/${M.token}/`;
try{
 const A=await user('phone',390);await A.login();await A.go(SETTINGS);
 await A.js(`${S}.scrollIntoView()`);await sleep(300);
 const rows=await A.js(`[...${S}.querySelectorAll('.invite-row')].map(r=>({id:+r.dataset.invite,who:r.querySelector('.invite-who').textContent.trim(),field:r.querySelector('input[readonly]')?.value||null,share:!!r.querySelector('[data-invite-share]:not([hidden])'),old:!!r.querySelector('.invite-old')}))`);
 check('The active link is shown with its address and Share',rows[0].id===M.shown&&rows[0].field===address&&rows[0].share&&/^Created by hana · /.test(rows[0].who),rows);
 check('The link from before says it cannot be shown, with no field',rows[1].id===M.old&&rows[1].old&&rows[1].field===null,rows[1]);
 check('Two active rows; the button reads Create another link under them',rows.length===2&&await A.js(`[...${S}.querySelectorAll('button')].some(b=>b.textContent.trim()==='Create another link'&&!b.classList.contains('btn-primary'))`));
 const past=await A.js(`({open:${S}.querySelector('.invites-past').open,summary:${S}.querySelector('.invites-past summary').textContent.trim(),items:[...${S}.querySelectorAll('.invite-past')].map(e=>e.textContent.trim())})`);
 check('Past invites is closed, counts 3, and says how each ended',!past.open&&past.summary==='Past invites (3)'&&past.items.some(t=>/revoked/.test(t))&&past.items.some(t=>/expired/.test(t))&&past.items.some(t=>/used up/.test(t)),past);
 check('Targets are 48px, nothing overflows',await A.js(tidy(390)));
 await A.js(`${S}.querySelector('[data-copy="invite-link-${M.shown}"]').click()`);await sleep(80);
 const copy=await A.js(`({copied:__copied,button:${S}.querySelector('[data-copy="invite-link-${M.shown}"]').textContent,flash:document.getElementById('invite-link-${M.shown}').getAnimations().map(a=>a.animationName)})`);
 check('Copy copies the link, says Copied, and the address flashes Brass',copy.copied[0]===address&&copy.button==='Copied'&&copy.flash.includes('invite-copied'),copy);
 await A.js(`${S}.querySelector('[data-invite-share]').click()`);await sleep(50);
 const shared=await A.js('__shared');
 check('Share hands the link and one line to the share sheet',shared[0]&&shared[0].url===address&&/^Join Kamuning Friday Night Card Club on PokerNights$/.test(shared[0].text),shared);
 await A.js(`${S}.querySelector('.invites-past summary').click()`);await sleep(30);
 check('Past invites eases open',await A.js(`${S}.querySelector('.invites-past').open&&document.getAnimations().length>0`));
 await sleep(500);await A.shot('invites-390-1-rows',true);

 // Create: the new link drops into the top row, marked New.
 await A.js(`[...${S}.querySelectorAll('button')].find(b=>b.textContent.trim()==='Create another link').click()`);
 await A.until(`!!document.querySelector('#invites [data-arrived]')`,4000);await sleep(60);
 const arrival=await A.js(`(()=>{const r=document.querySelector('#invites .invite-row');return{arrived:r.hasAttribute('data-arrived'),newTag:r.querySelector('.invite-new')?.textContent,moving:r.getAnimations().length>0||r.style.transform!=='',rule:getComputedStyle(r.querySelector('.invite-who'),'::after').animationName,field:!!r.querySelector('input[readonly]'),count:document.querySelectorAll('#invites .invite-row').length}})()`);
 check('After Create the new link is the top row, marked New, and drops in',arrival.arrived&&arrival.newTag==='New'&&arrival.moving&&arrival.rule==='mark-draw'&&arrival.field&&arrival.count===3,arrival);
 await sleep(900);
 check('At rest nothing runs and no inline style is left',await A.js(`document.getAnimations().filter(a=>a.playState==='running').length===0&&!document.querySelector('#invites .invite-row').getAttribute('style')`));
 await A.shot('invites-390-2-new');
 await A.go(SETTINGS);
 check('The New mark is once; the link stays',await A.js(`!document.querySelector('#invites [data-arrived]')&&document.querySelectorAll('#invites .invite-row input[readonly]').length===2`));

 // Revoke: the row goes to Past invites, whose summary is marked.
 await A.js(`document.querySelector('#invites .invite-row:last-child .invite-revoke').click()`);
 await A.until(`!!document.querySelector('#invites .invites-past[data-changed]')`,4000);await sleep(60);
 const revoked=await A.js(`({rows:document.querySelectorAll('#invites .invite-row').length,mark:document.querySelector('#invites .invites-past > summary').classList.contains('just-changed'),summary:document.querySelector('#invites .invites-past > summary').textContent.trim()})`);
 check('Revoke moves the link to Past invites and marks it',revoked.rows===2&&revoked.mark&&revoked.summary==='Past invites (4)',revoked);
 check('No script errors',(await A.js('__errors')).length===0,await A.js('__errors'));

 // A phone without a share sheet; 320px.
 const N=await user('phone',320,{share:false,height:568});await N.login();await N.go(SETTINGS);await N.js(`${S}.scrollIntoView()`);
 check('Without a share sheet there is no Share button',await N.js(`[...${S}.querySelectorAll('[data-invite-share]')].every(b=>b.hidden)`));
 check('320px: targets 48px, nothing overflows',await N.js(tidy(320)));await N.shot('invites-320-1-rows');

 // Desktop.
 const D=await user('desktop',1280,{height:900});await D.login();await D.go(SETTINGS);await D.js(`${S}.scrollIntoView()`);await sleep(200);
 check('1280px: nothing overflows',await D.js(`document.documentElement.scrollWidth<=1280`));await D.shot('invites-1280-1-rows');

 // Reduced motion.
 const R=await user('phone',390,{reduced:true});await R.login();await R.go(SETTINGS);
 await R.js(`[...${S}.querySelectorAll('button')].find(b=>b.textContent.trim()==='Create another link').click()`);
 await R.until(`!!document.querySelector('#invites [data-arrived]')`,4000);await sleep(40);
 check('Reduced motion: the new row is in place at once, no rule drawing',await R.js(`(()=>{const r=document.querySelector('#invites [data-arrived]');return r.getAnimations().length===0&&!r.style.transform&&getComputedStyle(r.querySelector('.invite-who'),'::after').animationName==='none'})()`));
}finally{
 const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed} of ${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed?1:0;
}
