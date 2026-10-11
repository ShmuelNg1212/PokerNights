// Reopening a finalized set and a closed session. Seed a fresh temporary database with seed_reopen.py,
// serve it on 127.0.0.1:8765, then run. The script consumes its fixture: use a fresh database per run.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-reopen-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-reopen-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-reopen-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__errors=[];addEventListener('error',e=>__errors.push(e.message))})`;
async function user(name,width,reduced){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 if(reduced)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=4000)=>{for(let t=0;t<ms;t+=50){if(await js(expression))return true;await sleep(50)}return false};
 const type=async text=>{for(const ch of text)await send('Input.dispatchKeyEvent',{type:'char',text:ch},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(900);
 return {s,js,go,shot,until,type,width};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const dialog=`document.querySelector('dialog.sheet')`;
// Compared with the requested width: mobile Chrome widens innerWidth when content overflows.
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const tall=sel=>`[...document.querySelectorAll(${JSON.stringify(sel)})].filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=48)`;
// Any CSS colour as [r,g,b], by painting it: the palette is written in oklch.
const lum=`(c=>{const x=document.createElement('canvas').getContext('2d');x.fillStyle=c;x.fillRect(0,0,1,1);const v=[...x.getImageData(0,0,1,1).data].slice(0,3).map(n=>{n/=255;return n<=.03928?n/12.92:((n+.055)/1.055)**2.4});return .2126*v[0]+.7152*v[1]+.0722*v[2]})`;

async function set(width,key,tag){
 const W=`${width}px ${tag}`,S=M[key];const A=await user('hana',width);
 await A.go(`/s/${S.sets[0]}/`);
 check(`${W} final page offers Reopen set, quietly, after the results' next step`,await A.js(`!!document.querySelector('.set-correct .reopen-opener')&&document.querySelector('.set-correct .reopen-opener').classList.contains('btn-quiet')&&${fits(width)}`));
 check(`${W} the opener is a 48px target`,await A.js(tall('.set-correct .btn')));
 await A.shot(`reopen-${width}-1-final`);
 await A.js(`document.querySelector('.reopen-opener').scrollIntoView({block:'center'});document.querySelector('.reopen-opener').click()`);await sleep(450);
 check(`${W} the sheet opens with its question, focus in the reason field`,await A.js(`${dialog}.open&&${dialog}.querySelector('h2').textContent==='Reopen set 1?'&&document.activeElement.id==='reopen-reason'`));
 check(`${W} sheet: three consequences, controls 48px, no overflow`,await A.js(`${dialog}.querySelectorAll('.reopen-effects li').length===3&&[...${dialog}.querySelectorAll('.btn, input[type=text]')].filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=48)&&${dialog}.scrollWidth<=${dialog}.clientWidth`));
 await A.shot(`reopen-${width}-2-sheet`);
 // An empty reason never leaves the browser.
 await A.js(`${dialog}.querySelector('form [type=submit]').click()`);await sleep(300);
 check(`${W} an empty reason is stopped in the sheet`,await A.js(`${dialog}.open&&document.querySelector('#live').dataset.state==='finalized'`));
 await A.js(`document.getElementById('reopen-reason').focus()`);await A.type('Miguel had ₱800, not ₱700');
 await A.js(`window.__t=performance.now();${dialog}.querySelector('form [type=submit]').click()`);
 check(`${W} the set is counting up again without a reload`,await A.until(`document.querySelector('#live').dataset.state==='reconciliation'&&!!document.querySelector('#live .correction')`));
 const first=await A.js(`(()=>{const c=document.querySelector('#live .correction');return {cls:c.classList.contains('reopen-arrived'),anim:getComputedStyle(c,'::before').animationName,text:c.textContent.replace(/\\s+/g,' ').trim(),running:document.getAnimations().length}})()`);
 check(`${W} the reason arrives once: the brass rule draws`,first.cls&&first.anim==='mark-draw',first);
 check(`${W} the line names the reason and who reopened`,/Reopened to correct\. Miguel had ₱800, not ₱700 hana/.test(first.text),first.text);
 await sleep(900);
 check(`${W} the sheet has closed and nothing is left running`,await A.js(`!${dialog}.open&&document.getAnimations().filter(a=>a.playState==='running'&&!(a.effect&&a.effect.getTiming().iterations===Infinity)).length===0`));
 const tone=await A.js(`(()=>{const L=${lum},c=document.querySelector('#live .correction'),bg=getComputedStyle(c.closest('.felt')).backgroundColor;const r=(a,b)=>(Math.max(a,b)+.05)/(Math.min(a,b)+.05);const b=L(bg);return [r(L(getComputedStyle(c.querySelector('strong')).color),b),r(L(getComputedStyle(c).color),b),r(L(getComputedStyle(c.querySelector('.correction-by')).color),b)]})()`);
 check(`${W} reason line contrast is at least 4.5:1 on the felt`,tone.every(x=>x>=4.5),tone.map(x=>x.toFixed(2)));
 check(`${W} count-up page fits`,await A.js(fits(width)));
 await A.shot(`reopen-${width}-3-counting`);
 await A.go(`/s/${S.sets[0]}/`);
 check(`${W} a reload does not replay the arrival`,await A.js(`!document.querySelector('#live .correction').classList.contains('reopen-arrived')`));
 // The missed buy-in sits in a player's sheet.
 await A.js(`document.querySelector('#live .player-opener').click()`);await sleep(450);
 check(`${W} a player's sheet offers Add a missed buy-in`,await A.js(`${dialog}.open&&!!${dialog}.querySelector('.missed-buy-in summary')&&${dialog}.querySelector('.missed-buy-in summary').getBoundingClientRect().height>=48`));
 await A.js(`${dialog}.querySelector('.missed-buy-in summary').click()`);await sleep(250);
 await A.shot(`reopen-${width}-4-missed`);
 check(`${W} no script error on the set pages`,await A.js(`__errors.length===0`),await A.js('__errors'));
 return A;
}

async function night(width){
 const W=`${width}px`,A=await user('hana',width);
 await A.go(`/n/${M.paid.night}/`);
 await A.js(`document.querySelector('#manage').open=true;document.querySelector('#manage').scrollIntoView()`);await sleep(200);
 check(`${W} a session with a paid mark says why it cannot reopen, with no button`,await A.js(`/1 transfer is marked paid\\. Mark it unpaid first\\./.test(document.querySelector('#manage').textContent)&&!document.querySelector('#manage [data-sheet-open=reopen-night]')`));
 await A.shot(`reopen-${width}-5-paid`);
 await A.go(`/s/${M.closed.sets[0]}/`);
 check(`${W} a set of a closed session points to the session`,await A.js(`/Reopen the session first/.test(document.querySelector('.set-correct').textContent)&&!document.querySelector('.set-correct [data-sheet-open]')&&${tall('.set-correct .btn')}`));
 await A.go(`/n/${M.closed.night}/`);await sleep(600);
 await A.js(`if(${dialog}&&${dialog}.open)${dialog}.querySelector('[data-sheet-close],.sheet-close,button').click()`);await sleep(500);
 await A.js(`document.querySelector('#manage').open=true;document.querySelector('#manage [data-sheet-open=reopen-night]').scrollIntoView({block:'center'})`);await sleep(200);
 check(`${W} Manage this session offers Reopen session at 48px`,await A.js(`!${dialog}.open&&${tall('#manage .btn')}&&${fits(width)}`));
 await A.shot(`reopen-${width}-6-manage`);
 await A.js(`document.querySelector('#manage [data-sheet-open=reopen-night]').click()`);await sleep(450);
 check(`${W} the session sheet opens with focus in the reason field`,await A.js(`${dialog}.open&&${dialog}.querySelector('h2').textContent==='Reopen this session?'&&document.activeElement.id==='reopen-night-reason'`));
 await A.shot(`reopen-${width}-7-night-sheet`);
 await A.type('One more set');
 await A.js(`${dialog}.querySelector('form [type=submit]').click()`);
 check(`${W} the session is open again and says why`,await A.until(`/Session open/.test(document.body.textContent)&&!!document.querySelector('.night-overview .correction')&&/One more set/.test(document.querySelector('.night-overview .correction').textContent)`));
 check(`${W} the earlier list is kept, struck, in its own disclosure; Start next set is back`,await A.js(`!!document.querySelector('[data-key=replaced-lists] .struck')&&/Start next set/.test(document.body.textContent)&&!document.querySelector('.transfer-list')&&${fits(width)}`));
 await A.shot(`reopen-${width}-8-night-open`);
 check(`${W} no script error on the session pages`,await A.js(`__errors.length===0`),await A.js('__errors'));
}

try{
 await set(390,'open','phone');
 await night(390);
 // Desktop and reduced motion reuse the sets that are still final.
 const B=await user('hana',1280,true);await B.go(`/s/${M.closed.sets[1]}/`);
 check('1280px final page of a reopened session offers Reopen set',await B.js(`!!document.querySelector('.set-correct .reopen-opener')&&${fits(1280)}`));
 await B.shot('reopen-1280-1-final');
 await B.js(`document.querySelector('.reopen-opener').click()`);await sleep(300);await B.shot('reopen-1280-2-sheet');
 await B.js(`document.getElementById('reopen-reason').focus()`);await B.type('Carlo cashed out 1,300');
 await B.js(`${dialog}.querySelector('form [type=submit]').click()`);
 check('reduced motion: the set comes back with the reason and nothing moves',await B.until(`document.querySelector('#live').dataset.state==='reconciliation'&&!!document.querySelector('#live .correction')`)&&await B.js(`getComputedStyle(document.querySelector('#live .correction'),'::before').animationName==='none'&&document.getAnimations().filter(a=>a.playState==='running').length===0`));
 await sleep(400);await B.shot('reopen-1280-3-counting');
 const P=await user('ben',390);await P.go(`/s/${M.closed.sets[1]}/`);
 check('a player sees the reason and no reopen control or missed buy-in',await P.js(`!!document.querySelector('#live .correction')&&!document.querySelector('.set-correct, .missed-buy-in, [data-sheet-open^=reopen]')`));
 await P.shot('reopen-390-9-player');
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
