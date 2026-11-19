// The host dock before the start (_host_controls.html, _players.html, dock.js). Seed a fresh temporary
// SQLite database with seed_dock_before_start.py alone, serve it on 127.0.0.1:8765, then run. The Join
// check seats the host at the "join" set: reseed before a repeat.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-dock-start-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const SET=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-dock-start-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const PROFILE=process.env.PN_CHROME_PROFILE || '/private/tmp/pn-dock-start-chrome';rmSync(PROFILE,{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9347','--user-data-dir='+PROFILE,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9347/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;errors.push(d.text+' '+((d.exception&&d.exception.description)||'').slice(0,200));return}
 if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// One browser context: the fold chosen in play is in localStorage and the class on <html> follows it.
const {browserContextId}=await send('Target.createBrowserContext');
async function page(width,height){
 const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const settle=async()=>{for(let i=0;i<40;i++){if(await js('document.readyState').catch(()=>'')==='complete')break;await sleep(100)}await sleep(400)};
 const go=async(path,pause=900)=>{await send('Page.navigate',{url:BASE+path},s);await sleep(pause);await settle()};
 const shot=async name=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 const tap=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 return {js,go,shot,tap};}
const results=[];const check=(name,ok,note='')=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${note?'  ('+note+')':''}`)};
const visible=el=>`(e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden')(${el})`;
const DOCK=`(()=>{const d=document.querySelector('#live .host-controls'),r=d.getBoundingClientRect();
 const shown=[...d.querySelectorAll(':scope > *')].filter(e=>e.getClientRects().length);
 const primary=[...d.querySelectorAll('.btn-primary')].filter(e=>e.getClientRects().length&&!e.closest('details:not([open])'));
 const start=d.querySelector('[value=start]'),j=document.querySelector('#live .host-join button'),jr=j&&j.getBoundingClientRect();
 return {top:r.top,h:r.height,fixed:getComputedStyle(d).position==='fixed',scroll:d.scrollHeight-d.clientHeight,toggle:!!d.querySelector('.dock-toggle'),
  primary:primary.map(e=>e.textContent.trim()),start:!!start&&start.getClientRects().length>0&&start.getBoundingClientRect().height>=48,
  join:jr?{top:jr.top,bottom:jr.bottom,h:jr.height,name:j.getAttribute('aria-label')}:null,joinInDock:!!d.querySelector('.host-join'),
  overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,padTop:parseFloat(getComputedStyle(d).paddingTop)}})()`;
const login=async p=>{await p.go('/accounts/login/',600);await p.js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300)};

// 390 × 844, a joining set with eight of twelve seats taken.
const phone=await page(390,844);await login(phone);
await phone.go('/s/'+SET.eight+'/');let d=await phone.js(DOCK);await phone.shot('eight-390');
check('390: the dock before the start has no toggle',!d.toggle);
check('390: one bright button in the dock, Start the set',d.primary.length===1&&d.primary[0]==='Start the set',JSON.stringify(d.primary));
check('390: the dock fits without its own scroll',d.scroll<=0,`${d.scroll}px over`);
check('390: the dock is at most 200px high',d.h<=200,`${Math.round(d.h)}px`);
check('390: Join is not in the dock',!d.joinInDock);
check('390: Join is beside Players, on the first screen, clear of the dock',!!d.join&&d.join.top>=0&&d.join.bottom<=d.top,JSON.stringify(d.join));
check('390: Join is a 48px target named "Join this set"',!!d.join&&d.join.h>=48&&d.join.name==='Join this set');
check('390: the dock keeps its top padding',d.padTop>=8,`${d.padTop}px`);
check('390: no sideways scroll',d.overflow<=0);
// The page reserves the dock's height: the last row clears the dock at the end of the page.
await phone.js('window.scrollTo(0,document.documentElement.scrollHeight)');await sleep(300);
const clear=await phone.js(`(()=>{const rows=[...document.querySelectorAll('#live .player-row')],last=rows[rows.length-1].getBoundingClientRect(),dock=document.querySelector('#live .host-controls').getBoundingClientRect();return Math.round(dock.top-last.bottom)})()`);
check('390: the last row clears the dock at the end of the page',clear>=0,`${clear}px`);
// The page reserves the measured height (dock.js), not the 128px default, which is shorter than this dock.
const reserved=await phone.js(`(()=>{const h=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--dock-h')),d=document.querySelector('#live .host-controls').getBoundingClientRect().height;return {h,d:Math.ceil(d)}})()`);
check('390: the page reserves the measured dock height',Math.abs(reserved.h-reserved.d)<=1,JSON.stringify(reserved));
await phone.go('/s/'+SET.full+'/');d=await phone.js(DOCK);
check('390: a full set has no Join',!d.join&&!d.joinInDock);
await phone.go('/s/'+SET.draft+'/');d=await phone.js(DOCK);await phone.shot('draft-390');
check('390: a draft ready to start has no toggle and shows Start',!d.toggle&&d.start&&d.primary.length===1);

// A fold chosen in play must not empty the dock of the next set.
await phone.go('/s/'+SET.running+'/');
// In play the dock starts folded with no choice saved; unfold and fold again, so "collapsed" is the host's own choice.
const folded=await phone.js(`(async()=>{const t=document.querySelector('#live .dock-toggle');if(!t)return 'no toggle';for(let i=0;i<2&&localStorage.getItem('rack-dock')!=='collapsed';i++){t.click();await new Promise(r=>setTimeout(r,400))}return document.documentElement.classList.contains('dock-collapsed')&&localStorage.getItem('rack-dock')==='collapsed'})()`);
check('in play the dock still folds',folded===true,String(folded));
await phone.go('/s/'+SET.eight+'/');d=await phone.js(DOCK);await phone.shot('eight-after-fold-390');
check('after a fold in play, a joining set still shows Start the set',d.start&&await phone.js(`document.documentElement.classList.contains('dock-collapsed')`),`start ${d.start}`);
await phone.go('/s/'+SET.running+'/');
check('back in play the dock is still folded',await phone.js(`document.querySelector('#live .dock-toggle').getAttribute('aria-expanded')==='false'`));

// A tap on Join seats the host.
await phone.go('/s/'+SET.join+'/');
const before=await phone.js(`document.querySelectorAll('#live .player-row').length`);
const at=await phone.js(`(()=>{const r=document.querySelector('#live .host-join button').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
await phone.tap(at.x,at.y);await sleep(1500);
const after=await phone.js(`({rows:document.querySelectorAll('#live .player-row').length,join:!!document.querySelector('#live .host-join'),hana:!!document.querySelector('#live .player-row[data-name="hana"]')})`);
check('a tap on Join seats the host, and Join goes',after.rows===before+1&&!after.join&&after.hana,JSON.stringify({before,...after}));

// 320 × 568, eleven of twelve seats.
const small=await page(320,568);
await small.go('/s/'+SET.twelve+'/');d=await small.js(DOCK);await small.shot('eleven-320');
check('320: no toggle, one bright button',!d.toggle&&d.primary.length===1);
check('320: the dock fits without its own scroll',d.scroll<=0,`${d.scroll}px over`);
// At 568px the set's panel alone reaches the dock, so Join is one short scroll away: the first control after the panel.
check('320: Join is the first control after the set panel',await small.js(`(()=>{const p=document.querySelector('#live .prep'),all=[...document.querySelectorAll('#live button,#live a')].filter(e=>e.getClientRects().length&&!p.contains(e)&&!e.closest('.host-controls'));return !!all[0]&&!!all[0].closest('.host-join')})()`));
await small.js(`document.querySelector('#live .host-join button').scrollIntoView({block:'center'})`);await sleep(300);d=await small.js(DOCK);
check('320: scrolled to, Join is clear of the dock',!!d.join&&d.join.top>=0&&d.join.bottom<=d.top,JSON.stringify(d.join)+' dock '+Math.round(d.top));
check('320: no sideways scroll',d.overflow<=0);

// 1280 px: the dock is a column, not fixed; Join sits beside Players there too.
const wide=await page(1280,900);
await wide.go('/s/'+SET.eight+'/');d=await wide.js(DOCK);await wide.shot('eight-1280');
check('1280: the dock is not fixed and Start shows',!d.fixed&&d.start);
check('1280: Join is beside Players',!!d.join&&!d.joinInDock);
check('1280: no sideways scroll',d.overflow<=0);

check('no script errors',errors.length===0,errors.join(' | '));
const passed=results.filter(r=>r.ok).length;console.log(`\n${passed}/${results.length} passed. Captures: ${OUT}`);
chrome.kill();process.exit(passed===results.length?0:1);
