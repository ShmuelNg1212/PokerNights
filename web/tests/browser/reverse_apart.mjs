// Cash out and Reverse apart (doc/plan/1795144795_cash_out_and_reverse.md).
// Seed a fresh temporary SQLite database with seed_sheet_drag.py alone and serve it on 127.0.0.1:8765.
// The probe reverses one buy-in in the set in play: reseed before a repeat.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const M=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-drag-manifest.json','utf8'));
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-reverse-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-reverse-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9353','--user-data-dir=/private/tmp/pn-reverse-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9353/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'').slice(0,160)+' after '+results.length+' checks');return}
 if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
async function page(opts={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const size=(width,height=844)=>send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}};
 const go=async(path,pause=1100,base=BASE)=>{await send('Page.navigate',{url:base+path},s);await sleep(pause);await settle()};
 const login=async(user,base=BASE)=>{await go('/accounts/login/',600,base);await js(`document.querySelector('[name=username]').value=${JSON.stringify(user)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300);await settle()};
 const click=async(expr,pause=650)=>{await js(expr+'.click()');await sleep(pause)};
 const until=async(expr,ms=7000)=>{for(let t=0;t<ms;t+=50){if(await js(expr).catch(()=>false))return true;await sleep(50)}return false};
 const shot=async(name,full=false)=>{const p={format:'png'};if(full){const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);p.captureBeyondViewport=true;p.clip={x:0,y:0,width:c.width,height:c.height,scale:1}}const{data}=await send('Page.captureScreenshot',p,s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const tab=async()=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},s)};
 await size(390);return {s,js,go,login,click,until,shot,size,tab};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const shown=sel=>`[...document.querySelectorAll(${JSON.stringify(sel)})].filter(el=>el.getClientRects().length)`;
const sheet=`document.querySelector('dialog.sheet[open]')`;
const visible=sel=>`[...${sheet}.querySelectorAll(${JSON.stringify(sel)})].filter(el=>el.checkVisibility({visibilityProperty:true,opacityProperty:true}))`;
const openPlayer=async(P,name)=>{await P.click(`[...document.querySelectorAll('[data-sheet-open^="player-"]')].find(b=>b.getAttribute('aria-label')==='Details for '+${JSON.stringify(name)})`,900);return P.until(`!!${sheet}`)};
const closeSheet=async P=>{await P.click(`${sheet}.querySelector('.sheet-head button')`,700)};
try {
 const H=await page();await H.login('hana');
 for(const w of [390,320]){
  await H.size(w,w===320?568:844);await H.go(`/s/${M.play}/`);
  check(`${w}px: the tap hint shows`,await H.js(`!!${shown('.row-hint')}.length`));
  check(`${w}px: the player sheet opens`,await openPlayer(H,w===390?'Miguel':'Carlo'));
  check(`${w}px: no red button and no reason field on open`,await H.js(`${visible('.btn-danger')}.length===0&&${visible('input[name=reason]')}.length===0`));
  check(`${w}px: the records sit under a hairline and a heading`,await H.js(`(()=>{const r=${sheet}.querySelector('.records');return !!r&&parseFloat(getComputedStyle(r).borderTopWidth)>=1&&r.querySelector('h3').textContent.trim()==='Records and corrections'})()`));
  const gap=await H.js(`(()=>{const a=${sheet}.querySelector('.sheet-swap').getBoundingClientRect(),b=${sheet}.querySelector('.reverse-entry > summary').getBoundingClientRect();return Math.round(b.top-a.bottom)})()`);
  check(`${w}px: the first Reverse… is 48px or more below Cash out`,gap>=48,`${gap}px`);
  check(`${w}px: Reverse… is a 48px quiet target`,await H.js(`(()=>{const s=${sheet}.querySelector('.reverse-entry > summary');return s.getBoundingClientRect().height>=48&&!s.classList.contains('btn-danger')})()`));
  await H.click(`${sheet}.querySelector('.reverse-entry > summary')`,600);
  check(`${w}px: opened, it shows the reason and "Reverse ₱1,000"`,await H.js(`${visible('input[name=reason]')}.length===1&&${visible('.btn-danger')}.map(b=>b.textContent.trim()).join()==='Reverse ₱1,000'`));
  check(`${w}px: nothing in the sheet is wider than the sheet`,await H.js(`(()=>{const d=${sheet}.getBoundingClientRect();return [...${sheet}.querySelectorAll('.records *')].every(el=>{const r=el.getBoundingClientRect();return !r.width||r.right<=d.right+0.5})})()`));
  await H.shot(`sheet-${w}`);
  if(w===390){
   // An empty reason is refused by the form itself: nothing is reversed.
   await H.click(`${sheet}.querySelector('.reverse-entry .btn-danger')`,900);
   check('an empty reason reverses nothing',await H.js(`!document.body.textContent.includes('Reversed:')`));
   await H.js(`${sheet}.querySelector('.reverse-entry input[name=reason]').value='probe: typed twice'`);
   await H.click(`${sheet}.querySelector('.reverse-entry .btn-danger')`,1800);
   check('with a reason it reverses, and the entry shows struck with the reason',await H.until(`[...document.querySelectorAll('.struck')].length>0&&document.body.textContent.includes('Reversed: probe: typed twice')`));
   await H.go(`/s/${M.play}/`);
  } else await closeSheet(H);
 }
 await H.size(1280,900);await H.go(`/s/${M.play}/`);
 check('1280px: the tap hint is gone',await H.js(`${shown('.row-hint')}.length===0`));
 check('1280px: each row has its own Cash out',await H.js(`${shown('.cash-opener')}.length>=3`));
 // Counting up: the same list, the same fold.
 await H.size(390);await H.go(`/s/${M.count}/`);
 check('count-up: the player sheet opens',await openPlayer(H,'Ben'));
 check('count-up: no red button on open, a Reverse… is there',await H.js(`${visible('.btn-danger')}.length===0&&${visible('.reverse-entry > summary')}.length>0`));
 await closeSheet(H);
 // A player sees the records, with no corrections.
 const P=await page();await P.login('ben');await P.go(`/s/${M.play}/`);
 const opened=await P.js(`!!document.querySelector('[data-mine] [data-sheet-open^="player-"]')`);
 if(opened){await P.click(`document.querySelector('[data-mine] [data-sheet-open^="player-"]')`,900)}
 check("a player's sheet has records and no Reverse…",await P.js(`!document.querySelector('.reverse-entry')&&!document.body.textContent.includes('Records and corrections')`));
 check('no script errors',errors.length===0,errors.join(' | '));
} finally {await send('Browser.close');ws.close();chrome.kill()}
const failed=results.filter(r=>!r.ok);console.log(`${results.length-failed.length}/${results.length} passed`);process.exit(failed.length?1:0);
