// Share results: the sheet, the drawn card and the three ways out. Seed a fresh temporary database
// with seed_share.py, serve it on 127.0.0.1:8765, then run. It writes nothing, so it can be rerun.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-share-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-share-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-share-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// The recap opens by itself once per browser; these checks are about the share sheet, so it is marked seen.
// "phone" gives the page a share sheet that takes files and records what it was handed; mode 'cancel' closes it as a person would.
const BOOT=phone=>`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));
 const _set=Storage.prototype.getItem;Storage.prototype.getItem=function(k){return String(k).startsWith('rack-recap:')?'1':_set.call(this,k)};
 window.__copied=[];try{Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>(window.__clipFail?Promise.reject(new Error('no')):(__copied.push(t),Promise.resolve()))},configurable:true})}catch(e){}
 ${phone?`window.__shared=[];navigator.canShare=d=>!!(d&&d.files&&d.files.length);navigator.share=d=>{if(window.__shareMode==='cancel')return Promise.reject(new DOMException('x','AbortError'));if(window.__shareMode==='fail')return Promise.reject(new Error('no'));__shared.push({text:d.text,files:(d.files||[]).map(f=>({name:f.name,type:f.type,size:f.size}))});return Promise.resolve()};`:`try{delete Navigator.prototype.share;delete Navigator.prototype.canShare}catch(e){}`}`;
async function user(name,width,{phone=false,reduced=false,noFont=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 if(reduced)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT(phone)+(noFont?`;document.fonts.load=()=>Promise.reject(new Error('blocked'));`:'')},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=5000)=>{for(let t=0;t<ms;t+=50){if(await js(expression))return true;await sleep(50)}return false};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(900);
 // The card as a file, exactly as it would be shared.
 const card=async n=>{const b64=await js(`fetch(document.querySelector('[data-share-preview]').src).then(r=>r.blob()).then(b=>new Promise(ok=>{const f=new FileReader();f.onload=()=>ok(f.result.split(',')[1]);f.readAsDataURL(b)}))`);writeFileSync(`${OUT}/${n}.png`,Buffer.from(b64,'base64'))};
 const open=async night=>{await go(`/n/${night}/`);await js(`document.querySelector('[data-sheet-open=share]').scrollIntoView({block:'center'});window.__t=performance.now();document.querySelector('[data-sheet-open=share]').click()`);};
 return {s,js,go,shot,until,card,open,width};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const D=`document.querySelector('dialog.sheet')`,Q=s=>`${D}.querySelector(${JSON.stringify(s)})`;
const ready=`${D}&&${D}.open&&!${Q('[data-share-stage]')}.hidden&&${Q('[data-share-preview]')}.naturalWidth>0`;
const shown=sel=>`[...${D}.querySelectorAll(${JSON.stringify(sel)})].filter(e=>e.getClientRects().length)`;
const data=`JSON.parse(document.getElementById('share-card').textContent)`;
// What the picture is made of, read from the picture: its size, how many distinct colours, and whether the page's font drew it.
const facts=`(async()=>{const img=${Q('[data-share-preview]')};const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;const x=c.getContext('2d');x.drawImage(img,0,0);const d=x.getImageData(0,0,c.width,c.height).data;const seen=new Set();for(let i=0;i<d.length;i+=4*97)seen.add(d[i]+','+d[i+1]+','+d[i+2]);return {w:c.width,h:c.height,colours:seen.size,archivo:document.fonts.check('800 64px Archivo')}})()`;

async function phone(width){
 const W=`${width}px phone`,A=await user('hana',width,{phone:true});
 await A.go(`/n/${M.small}/`);
 check(`${W} Share results sits with the recap opener, 48px, page fits`,await A.js(`(()=>{const b=document.querySelector('.night-after [data-sheet-open=share]');return !!b&&b.getBoundingClientRect().height>=48&&b.previousElementSibling.classList.contains('recap-opener')&&document.documentElement.scrollWidth<=${width}})()`));
 await A.open(M.small);
 // The first frames of the deal, before it lands.
 await A.until(`${ready}`);
 const first=await A.js(`(()=>{const s=${Q('[data-share-stage]')},d=s.querySelector('.share-deal');return {dealt:s.classList.contains('is-dealt'),names:d.getAnimations().map(a=>a.animationName),clip:getComputedStyle(s.querySelector('img')).clipPath,ms:performance.now()-__t}})()`);
 check(`${W} the card is drawn and dealt: it lands with the arrive spring and is uncovered from the top`,first.dealt&&first.names.includes('share-deal'),first);
 check(`${W} the card is ready within a second of the tap`,first.ms<1000,first.ms);
 await A.shot(`share-${width}-1-dealing`);
 await sleep(900);
 check(`${W} at rest: no transform, no clip, nothing running`,await A.js(`(()=>{const d=${Q('.share-deal')},i=d.querySelector('img');return getComputedStyle(d).transform==='none'&&getComputedStyle(i).clipPath==='none'&&document.getAnimations().filter(a=>a.playState==='running').length===0})()`));
 const f=await A.js(facts);
 check(`${W} the picture is 1080px wide, in the page's font, and not blank`,f.w===1080&&f.h>900&&f.colours>40&&f.archivo,f);
 check(`${W} the sheet: Share is the one primary and comes first; Save image and Copy text follow; all 48px`,await A.js(`(()=>{const b=${shown('[data-share-actions] .btn')};b.sort((p,q)=>p.getBoundingClientRect().top-q.getBoundingClientRect().top);return b.map(e=>e.textContent.trim()).join('|')==='Share|Save image|Copy text'&&b.filter(e=>e.classList.contains('btn-primary')).length===1&&b[0].classList.contains('btn-primary')&&b.every(e=>e.getBoundingClientRect().height>=48)})()`));
 check(`${W} focus starts on Share; the text is folded away; the sheet does not overflow sideways`,await A.js(`document.activeElement.dataset.shareDo==='share'&&!${Q('[data-share-text]')}.open&&${D}.scrollWidth<=${D}.clientWidth`));
 check(`${W} the whole card and all three actions are in view together`,await A.js(`(()=>{const i=${Q('[data-share-preview]')}.getBoundingClientRect(),b=${Q('[data-share-actions] [data-share-do=copy]')}.getBoundingClientRect();return i.top>=0&&b.bottom<=innerHeight&&i.height<=innerHeight*.47})()`));
 await A.shot(`share-${width}-2-sheet`);await A.card(`share-card-small`);
 // Share: the file and the server's text, straight from the tap.
 await A.js(`${Q('[data-share-do=share]')}.click()`);await sleep(150);
 const sent=await A.js(`({s:__shared,text:${data}.text,file:${data}.file,label:${Q('[data-share-do=share]')}.textContent,status:${Q('[data-share-status]')}.textContent})`);
 check(`${W} Share hands over one PNG named for the session and the server's text`,sent.s.length===1&&sent.s[0].files.length===1&&sent.s[0].files[0].type==='image/png'&&sent.s[0].files[0].name===sent.file&&sent.s[0].files[0].size>20000&&sent.s[0].text===sent.text,sent.s);
 check(`${W} the button says Shared and a status says it`,sent.label==='Shared'&&sent.status==='Shared.',sent);
 await sleep(2100);
 check(`${W} the label returns after two seconds`,await A.js(`${Q('[data-share-do=share]')}.textContent==='Share'`));
 await A.js(`window.__shareMode='cancel';${Q('[data-share-status]')}.textContent='';${Q('[data-share-do=share]')}.click()`);await sleep(150);
 check(`${W} closing the phone's sheet says nothing and keeps ours`,await A.js(`${D}.open&&${Q('[data-share-status]')}.textContent===''&&${Q('[data-share-do=share]')}.textContent==='Share'`));
 await A.js(`window.__shareMode='fail';${Q('[data-share-do=share]')}.click()`);await sleep(150);
 check(`${W} a refused share says what to do next`,await A.js(`/Save the image or copy the text/.test(${Q('[data-share-status]')}.textContent)`));
 await A.js(`${Q('[data-share-do=copy]')}.click()`);await sleep(150);
 check(`${W} Copy text puts the server's text on the clipboard and says Copied`,await A.js(`__copied.length===1&&__copied[0]===${data}.text&&${Q('[data-share-actions] [data-share-do=copy]')}.textContent==='Copied'`));
 await A.js(`window.__clipFail=true;${Q('[data-share-actions] [data-share-do=copy]')}.click()`);await sleep(200);
 check(`${W} a refused copy opens the text and selects it`,await A.js(`(()=>{const t=${Q('textarea')};return ${Q('[data-share-text]')}.open&&document.activeElement===t&&t.selectionEnd===t.value.length&&/selected/.test(${Q('[data-share-status]')}.textContent)})()`));
 await A.shot(`share-${width}-3-text`);
 // Close and reopen: the card is not drawn twice, and focus returned to the opener in between.
 await A.js(`${Q('.sheet-head button')}.click()`);await sleep(500);
 check(`${W} closing returns focus to Share results`,await A.js(`!${D}.open&&document.activeElement.dataset.sheetOpen==='share'`));
 await A.js(`window.__url=document.querySelector('.share-source [data-share-preview]').src;document.querySelector('[data-sheet-open=share]').click()`);await A.until(ready);
 check(`${W} reopening shows the same picture again`,await A.js(`${Q('[data-share-preview]')}.src===__url`));
 await A.js(`${Q('.sheet-head button')}.click()`);await sleep(500);
 // From the recap's foot, in the same sheet.
 await A.js(`document.querySelector('[data-sheet-open=recap]').click()`);await sleep(500);
 check(`${W} the recap ends with Share results`,await A.js(`(()=>{const b=${Q('[data-sheet-swap=share]')};return !!b&&b.getClientRects().length>0&&b.getBoundingClientRect().height>=48})()`));
 await A.js(`${Q('[data-sheet-swap=share]')}.click()`);
 check(`${W} it turns the recap's sheet into the share sheet`,await A.until(ready)&&await A.js(`${Q('h2')}.textContent==='Share results'`));
 // Twelve players, long names, six-figure amounts.
 await A.open(M.big);await A.until(ready);await sleep(900);
 const g=await A.js(facts);
 check(`${W} twelve players: the card grows taller, stays 1080 wide, and its preview stays within the sheet`,g.w===1080&&g.h>2000&&await A.js(`${Q('[data-share-preview]')}.getBoundingClientRect().width<=${D}.clientWidth&&${D}.scrollWidth<=${D}.clientWidth`),g);
 await A.shot(`share-${width}-4-big`);await A.card(`share-card-big`);
 await A.open(M.even);await A.until(ready);await sleep(900);await A.card(`share-card-even`);
 check(`${W} a chips game where nobody owes still draws`,(await A.js(facts)).colours>20&&await A.js(`${data}.transfers.length===0`));
 check(`${W} no script error`,await A.js(`__errors.length===0`),await A.js('__errors'));
}

try{
 await phone(390);
 // A browser that cannot share at all: Save image leads.
 const B=await user('hana',1280);await B.open(M.small);await B.until(ready);await sleep(900);
 check('1280px without a share sheet: Save image is the one primary and comes first; no Share button',await B.js(`(()=>{const b=${shown('[data-share-actions] .btn')};b.sort((p,q)=>p.getBoundingClientRect().top-q.getBoundingClientRect().top);return b.map(e=>e.textContent.trim()).join('|')==='Save image|Copy text'&&b[0].classList.contains('btn-primary')})()`));
 await B.js(`window.__clicks=[];HTMLAnchorElement.prototype.click=function(){__clicks.push({download:this.download,href:this.href.slice(0,5)})};${Q('[data-share-do=save]')}.click()`);await sleep(100);
 check('1280px Save image downloads the PNG under the session\'s name and says Saved',await B.js(`__clicks.length===1&&__clicks[0].download===${data}.file&&__clicks[0].href==='blob:'&&${Q('[data-share-do=save]')}.textContent==='Saved'`));
 check('1280px page and sheet fit',await B.js(`document.documentElement.scrollWidth<=1280&&${D}.scrollWidth<=${D}.clientWidth`));
 await B.shot('share-1280-1-sheet');
 const R=await user('hana',390,{phone:true,reduced:true});await R.open(M.small);await R.until(ready);
 check('reduced motion: the card is simply there',await R.js(`(()=>{const d=${Q('.share-deal')};return d.getAnimations({subtree:true}).length===0&&getComputedStyle(d).transform==='none'&&getComputedStyle(d.querySelector('img')).clipPath==='none'})()`));
 // The font cannot be confirmed: no card, the text and one Copy.
 const F=await user('hana',390,{phone:true,noFont:true});await F.open(M.small);
 check('no card without the font: the sheet is the text and Copy text',await F.until(`${D}&&${D}.open&&${Q('[data-share-stage]')}.hidden&&${Q('[data-share-actions]')}.hidden&&${Q('[data-share-text]')}.open&&!${Q('[data-share-plain]')}.hidden`));
 await F.js(`${Q('[data-share-plain]')}.click()`);await sleep(150);
 check('…and that Copy works',await F.js(`__copied.length===1&&__copied[0]===${data}.text`));
 await F.shot('share-390-5-text-only');
 const P=await user('ben',390,{phone:true});await P.open(M.small);
 check('a player can share too',await P.until(ready));
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
