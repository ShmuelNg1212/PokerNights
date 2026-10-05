// The mark on a changed row and its "Rebuy added" badge must not cover anything: not a neighbouring
// row, not another mark, not a name, an amount or a button. Seed a fresh temporary database with
// seed.py and seed_flow.py and serve it; PN_BROWSER_URL names it (default http://127.0.0.1:8765).
// The script only reads: it marks rows in the page the way changes.js does and measures them.
import {spawn} from 'node:child_process';
import {rmSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const SET=JSON.parse(readFileSync('/private/tmp/pn-flow-manifest.json','utf8')).still.set;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-marks-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9365','--user-data-dir=/private/tmp/pn-marks-chrome','--no-first-run','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9365/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const size=width=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 await size(390);await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1000);
 return {js,go,size,shot};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||!note?'':'  '+note}`)};
// Marks three neighbouring rows, optionally with a long name and a large amount, and reports what crosses what.
const MEASURE=long=>`(()=>{
 const hit=(a,b)=>a.left<b.right-.5&&b.left<a.right-.5&&a.top<b.bottom-.5&&b.top<a.bottom-.5;
 const text=el=>{const r=document.createRange();r.selectNodeContents(el);return [...r.getClientRects()]};
 const rows=[...document.querySelectorAll('#live .player-row')].slice(0,3),problems=[];
 if(rows.length<3)return 'fewer than three rows';
 rows.forEach((row,i)=>{
  if(${long}&&i===1){row.querySelectorAll('.player-name > span:first-child, .fallback-name').forEach(n=>n.firstChild.textContent='Maria Clara Esperanza de los Santos-Villanueva');row.querySelector('.player-figure').firstChild.textContent='₱1,250,000.50';}
  row.classList.add('just-changed');
  row.querySelectorAll('.change-label').forEach(b=>{b.textContent=i===1?'Updated':'Rebuy added';b.hidden=false});
 });
 rows.forEach((row,i)=>{
  const box=row.getBoundingClientRect(),style=getComputedStyle(row),mark=getComputedStyle(row,'::before');
  // The mark: no outline outside the row; a box drawn inside it, top and bottom.
  if(style.outlineStyle!=='none'&&parseFloat(style.outlineWidth)>0&&parseFloat(style.outlineOffset)>=0)problems.push('row '+i+': the mark is an outline outside the row');
  else if(style.outlineStyle==='none'&&(mark.content==='none'||parseFloat(mark.borderTopWidth)<2||parseFloat(mark.top)<0||parseFloat(mark.bottom)<0))problems.push('row '+i+': no mark inside the row');
  const badges=[...row.querySelectorAll('.change-label')].filter(b=>b.getClientRects().length);
  if(badges.length!==1){problems.push('row '+i+': '+badges.length+' badges showing');return}
  const badge=badges[0].getBoundingClientRect();
  if(badge.top<box.top-.5||badge.bottom>box.bottom+.5||badge.left<box.left-.5||badge.right>box.right+.5)problems.push('row '+i+': the badge leaves its row');
  if(badge.right>innerWidth)problems.push('row '+i+': the badge leaves the screen');
  const things=[];
  row.querySelectorAll('.player-figure, .player-actions .btn, .chip, .buy-stack').forEach(el=>{if(el.getClientRects().length)things.push([el.className.split(' ')[0],el.getBoundingClientRect()])});
  row.querySelectorAll('.player-name > span:first-child, .fallback-name').forEach(el=>text(el).forEach(r=>things.push(['name',r])));
  const meta=badges[0].parentElement;[...meta.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).forEach(n=>text(n).forEach(r=>things.push(['buy-ins',r])));
  things.forEach(([what,r])=>{if(hit(badge,r))problems.push('row '+i+': the badge covers the '+what)});
 });
 if(document.documentElement.scrollWidth>innerWidth)problems.push('the page scrolls sideways');
 return problems.join('; ')||'ok';
})()`;
try {
 for (const [who,label] of [['hana','host'],['ben','player']]) {
  const A=await user(who);
  for (const width of [320,390,1280]) for (const long of [false,true]) {
   await A.size(width);await A.go(`/s/${SET}/`);
   const heights=`[...document.querySelectorAll('#live .player-row')].map(r=>Math.round(r.getBoundingClientRect().height)).join()`;
   const before=await A.js(heights),found=await A.js(MEASURE(long)),after=await A.js(heights);
   const tag=`${label} ${width}px${long?' long name, large amount':''}`;
   check(`${tag}: marks and badges cover nothing`,found==='ok',found);
   if(!long)check(`${tag}: the badge does not change a row's height`,before===after,before+' -> '+after);
   if(width!==1280||long)await A.shot(`marks-${label}-${width}${long?'-long':''}`);
  }
 }
} finally { await send('Browser.close').catch(()=>{});ws.close();chrome.kill(); }
const failed=results.filter(r=>!r.ok);console.log(`${results.length-failed.length}/${results.length} checks passed`);process.exit(failed.length?1:0);
