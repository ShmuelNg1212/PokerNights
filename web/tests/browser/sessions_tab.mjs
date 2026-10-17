// The Sessions tab (2026-10-17): table cards with your table first, then your past nights by month.
// Seed a fresh temporary database with seed_sessions_tab.py alone, serve it on 127.0.0.1:8765, then run.
// PN_DB names that SQLite file, for the live redraw check, which adds a session from the shell.
// Reads ids from /private/tmp/pn-sessions-tab-manifest.json. Logs in as ben (player) and hana (host).
import {spawn,execSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-sessions-tab-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-sessions-tab-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-sessions-tab-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9346','--user-data-dir=/private/tmp/pn-sessions-tab-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9346/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,width=390,{reduce=false,noJs=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:2,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__errors=[];addEventListener('error',e=>__errors.push(e.message))`},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const tapAt=async(x,y)=>{for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1},s)};
 const tap=async sel=>{const p=await js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);await tapAt(p.x,p.y)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 if(noJs)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,tap,tapAt};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,400)}`)};
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgba=v=>{c.clearRect(0,0,1,1);c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});if(!el)return null;let bg=el;while(bg.parentElement&&rgba(getComputedStyle(bg).backgroundColor)[3]===0)bg=bg.parentElement;const back=bg.matches('.felt')?rgba(getComputedStyle(document.documentElement).getPropertyValue('--felt').trim()):rgba(getComputedStyle(bg).backgroundColor);const a=lum(rgba(getComputedStyle(el).color)),b=lum(back);return Math.round((Math.max(a,b)+.05)/(Math.min(a,b)+.05)*100)/100})()`;
const facts=`(()=>{const cards=[...document.querySelectorAll('.table-card')];
 const small=[...document.querySelectorAll('main a, main button, main summary')].filter(e=>e.getClientRects().length).map(e=>[e.className||e.tagName,Math.round(e.getBoundingClientRect().height)]).filter(([,h])=>h<48);
 return {overflow:document.documentElement.scrollWidth>innerWidth,small,
  cards:cards.map(c=>({href:c.getAttribute('href'),mine:c.classList.contains('is-mine'),you:!!c.querySelector('.table-card-you'),felt:c.classList.contains('felt'),live:!!c.querySelector('.badge-live'),top:Math.round(c.getBoundingClientRect().top),h:Math.round(c.getBoundingClientRect().height)})),
  firstButtonBottom:(()=>{const b=document.querySelector('.table-card .btn');return b?Math.round(b.getBoundingClientRect().bottom+scrollY):null})(),
  years:[...document.querySelectorAll('.ledger-year')].map(d=>d.open),months:[...document.querySelectorAll('.ledger-month')].map(h=>h.textContent),
  titleLines:Math.round(document.querySelector('.ledger strong')&&Math.max(...[...document.querySelectorAll('.table-card-title')].map(t=>t.getBoundingClientRect().height/parseFloat(getComputedStyle(t).lineHeight)))),
  errors:window.__errors||[]}})()`;

for(const width of [320,390,1280]){
 for(const name of ['ben','hana']){
  const A=await user(name,width);await A.go(`/g/${M.group}/`);
  const f=await A.js(facts);
  const tag=`${width} ${name}`;
  check(`${tag} no horizontal overflow`,!f.overflow);
  check(`${tag} every target is at least 48px`,f.small.length===0,f.small);
  check(`${tag} no script error`,f.errors.length===0,f.errors);
  check(`${tag} felt only on cards in play`,f.cards.every(c=>c.felt===c.live),f.cards);
  check(`${tag} "You're …" only on the viewer's cards`,f.cards.every(c=>c.you===c.mine),f.cards);
  check(`${tag} a card title takes two lines at most`,f.titleLines<=2,f.titleLines);
  check(`${tag} this year is open and last year is closed`,JSON.stringify(f.years)==='[false]'&&f.months[0].endsWith(String(new Date().getFullYear())),[f.years,f.months]);
  if(name==='ben'){
   check(`${tag} Ben's table in play is first, then the other in play, then his open set`,JSON.stringify(f.cards.map(c=>c.href))===JSON.stringify([`/s/${M.mine_live}/`,`/s/${M.other_live}/`,`/s/${M.mine_open}/`]),f.cards.map(c=>c.href));
   if(width<900)check(`${tag} Open the table is in the first viewport`,f.firstButtonBottom<=844,f.firstButtonBottom);
  }else{
   check(`${tag} the host gets the draft last`,f.cards.at(-1).href===`/s/${M.draft}/`,f.cards.map(c=>c.href));
  }
  if(width===1280)check(`${tag} two columns: the first two cards share a row`,f.cards[0].top===f.cards[1].top,f.cards);
  else check(`${tag} one column on a phone`,f.cards[1].top>f.cards[0].top,f.cards);
  for(const sel of ['.table-card.felt .table-card-when','.table-card.felt .table-card-facts','.table-card:not(.felt) .table-card-when','.table-card:not(.felt) .table-card-facts','.ledger-month','.ledger-meta','.ledger-debt.plus','.ledger-debt.minus','.ledger-year summary .muted'])
   {const r=await A.js(contrast(sel));check(`${tag} contrast ${sel}`,r===null||r>=4.5,r)}
  await A.shot(`tab-${name}-${width}`);
  if(width===390&&name==='ben'){
   // The year opens with a tap and shows its months.
   await A.tap('.ledger-year summary');await sleep(300);
   check(`${tag} a tap opens last year`,await A.js(`document.querySelector('.ledger-year').open&&document.querySelectorAll('.ledger-year .ledger-month').length===2`));
   // Held down, the whole card looks pressed.
   await A.js(`scrollTo(0,0)`);await sleep(200);
   const at=await A.js(`(()=>{const r=document.querySelector('.table-cards > li:nth-child(2) .table-card .table-card-when').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
   await send('Input.dispatchMouseEvent',{type:'mousePressed',x:at.x,y:at.y,button:'left',clickCount:1},A.s);
   check(`${tag} held down, the card looks pressed`,await A.js(`getComputedStyle(document.querySelector('.table-cards > li:nth-child(2) .table-card')).boxShadow!=='none'`));
   await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:5,y:5,button:'left',buttons:1},A.s);await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:5,y:5,button:'left',clickCount:1},A.s);await sleep(200);
   check(`${tag} let go elsewhere, the card is at rest`,await A.js(`location.pathname==='/g/${M.group}/'&&getComputedStyle(document.querySelector('.table-cards > li:nth-child(2) .table-card')).boxShadow==='none'`));
   // A tap on a card away from its title and button opens the card's set.
   await A.js(`scrollTo(0,0)`);await sleep(200);
   await A.tap(`.table-cards > li:nth-child(2) .table-card .table-card-facts`);await sleep(1500);
   check(`${tag} a tap anywhere on a card opens its set`,await A.js(`location.pathname`)===`/s/${M.other_live}/`,await A.js('location.pathname'));
  }
 }
}

// Reduced motion: the year's chevron does not turn.
{const A=await user('ben',390,{reduce:true});await A.go(`/g/${M.group}/`);
 check('reduced motion: no transition on the year chevron',await A.js(`parseFloat(getComputedStyle(document.querySelector('.ledger-year summary .icon')).transitionDuration)===0`),await A.js(`getComputedStyle(document.querySelector('.ledger-year summary .icon')).transitionDuration`));}

// Without JavaScript: the cards and the rows are plain links, and the clock shows the server's value.
{const A=await user('ben',390,{noJs:true});await A.go(`/g/${M.group}/`);
 check('no JavaScript: the clock has its server value',await A.js(`document.querySelector('[data-clock]').textContent.trim().length>0`));
 await A.tap('.table-cards > li:nth-child(1) .table-card .table-card-when');await sleep(1500);
 check('no JavaScript: a tap on a card opens its set',await A.js('location.pathname')===`/s/${M.mine_live}/`,await A.js('location.pathname'));}

// A live redraw: another session opens while Ben reads the past list. The page morphs in place and keeps its scroll.
if(process.env.PN_DB){const A=await user('ben',390);await A.go(`/g/${M.group}/`);
 const before=await A.js(`document.querySelectorAll('.table-card').length`);
 await A.js(`window.__mark=1;scrollTo(0,900)`);await sleep(300);const y=await A.js('Math.round(scrollY)');
 execSync(`.venv/bin/python manage.py shell -c "from games.models import Table; from groups.models import Member; from games.tests.helpers import make_session; host=Member.objects.get(group_id=${M.group}, user__username='hana'); make_session(host, table=Table.objects.get(group_id=${M.group}, name='Garage'), state='open')"`,{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+process.env.PN_DB},stdio:'ignore'});
 await sleep(7000);
 const after=await A.js(`({cards:document.querySelectorAll('.table-card').length,mark:window.__mark,y:Math.round(scrollY)})`);
 check('live redraw: the new session arrives without a reload and the scroll stays',after.cards===before+1&&after.mark===1&&Math.abs(after.y-y)<=40,{before,y,after});
}else console.log('SKIP live redraw: set PN_DB');

chrome.kill();
const failed=results.filter(r=>!r.ok);
console.log(`${results.length-failed.length}/${results.length} passed`);
process.exit(failed.length?1:0);
