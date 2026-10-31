// The people's journeys through the app, counted: the Targets table of doc/plan/1793431937_ui_revamp.md.
// A new host from sign-up to a marked payment, and a repeat game from an idle Your groups, at 390 x 844
// with touch. Each tap and field is counted. Seed a fresh temporary database with seed.py, seed_end_set.py,
// seed_night.py, seed_remaining.py, seed_opening.py and seed_journey.py, serve it on 127.0.0.1:8765, run.
// Prints the table, then its checks; exits 1 if a check fails. It writes to the database: reset it for a repeat.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-journey-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const PROFILE='/private/tmp/pn-journey-chrome';rmSync(PROFILE,{recursive:true,force:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9461',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<60&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9461/json/version')).json()).webSocketDebuggerUrl}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const[ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

// Every control a person could press. Used for the seeded settings count too.
const CONTROLS=`[...document.querySelectorAll('main a,main button,main summary,main input:not([type=hidden]),main select,main textarea')].filter(e=>e.getClientRects().length).length`;
async function person(){
 const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,300));return r.result.value};
 const settle=async ms=>{await sleep(ms);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await settle(1000)};
 const shot=async name=>{const{data}=await send('Page.captureScreenshot',{format:'jpeg',quality:70},s);writeFileSync(`${OUT}/${name}.jpg`,Buffer.from(data,'base64'))};
 const P={s,js,go,shot,settle,taps:0,fields:0,scrolled:0,
  // The visible control whose words match, within an open sheet when there is one. One tap.
  async tap(words,wait=1200){
   const find=`(()=>{const re=new RegExp(${JSON.stringify(words)},'i');const v=[...document.querySelectorAll('a,button,summary')].filter(e=>e.getClientRects().length&&re.test((e.textContent.trim()||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ')));const d=document.querySelector('dialog[open]');const inside=d?v.filter(e=>d.contains(e)):v;return (inside.length?inside:v)[0]})()`;
   await js('scrollTo(0,0)');
   const seen=await js(`(()=>{const e=${find};if(!e)return null;const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight})()`);
   if(seen===null)throw Error(`nothing to tap: ${words} on ${await js('location.pathname')}`);
   P.taps++;if(!seen)P.scrolled++;
   await js(`(()=>{const e=${find};e.scrollIntoView({block:'center'});e.click()})()`);await settle(wait);
  },
  async type(field,value){await js(`(()=>{const e=document.querySelector(${JSON.stringify(field)});e.scrollIntoView({block:'center'});e.focus();e.value=''})()`);await send('Input.insertText',{text:String(value)},s);P.fields++},
  async tick(field){await js(`document.querySelector(${JSON.stringify(field)}).click()`);await sleep(80)},
  async login(name){await go('/accounts/login/');await sleep(600);await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await settle(1500)},
 };
 return P;
}

const table={};
try{
 // A new host, from nothing to a marked payment.
 const H=await person();
 await H.go('/accounts/signup/');await sleep(900);
 await H.type('[name=username]','rosa'+Date.now()%100000);await H.type('input[type=password]','tablestakes-91');
 await H.tap('^Create account',1800);await sleep(1200);
 check('a new person is not asked about the home screen before any session',await H.js(`!document.querySelector('dialog[open]')`));
 await H.type('main [name=name]','Friday crew');await H.tap('^Create group',1500);
 const groupPath=await H.js('location.pathname');
 await H.go(groupPath+'?view=settings');table.settingsNew=await H.js('document.documentElement.scrollHeight');await H.go(groupPath);
 await H.tap('^New session');
 await H.type('[name=table_name]','Rosa kitchen');
 for(const[k,v]of[['small_blind',10],['big_blind',20],['min_buy_in',500],['max_buy_in',5000],['default_buy_in',1000]])await H.type(`[name=${k}]`,v);
 await H.tap('^Create session',1800);await sleep(1200);
 check('creating lands on the set',/^\/s\/\d+\/$/.test(await H.js('location.pathname')));
 check('the home-screen suggestion comes with the first session',await H.js(`!!document.querySelector('dialog[open]')`));
 if(await H.js(`!!document.querySelector('dialog[open]')`))await H.tap('^Not now',900);
 await H.tap('^Add players');
 await H.type('[name=names]','Ana\nBong\nCes\nDon');await sleep(300);await H.tap('^Add 4 players',1600);
 const rowsAbove=`(()=>{const dock=document.querySelector('.host-controls');const edge=dock?dock.getBoundingClientRect().top:innerHeight;return [...document.querySelectorAll('.player-row')].filter(r=>r.getBoundingClientRect().bottom<=edge).length})()`;
 table.rowsOpen=await H.js(rowsAbove);
 await H.shot('ready');
 await H.tap('^Start the set',500);await H.shot('started');
 check('start: no first buy-in is called a rebuy',await H.js(`![...document.querySelectorAll('.change-label')].some(b=>b.getClientRects().length&&b.textContent==='Rebuy added')`));
 check('start: no row is singled out with a box',await H.js(`![...document.querySelectorAll('.player-row')].some(r=>getComputedStyle(r,'::before').content!=='none'&&getComputedStyle(r,'::before').borderTopWidth==='2px')`));
 await H.settle(800);
 await H.tap('^Rebuy$',900);await H.tap('^Confirm rebuy',1300);
 check('rebuy: one row says Rebuy added',await H.js(`[...document.querySelectorAll('.change-label')].filter(b=>b.getClientRects().length&&b.textContent==='Rebuy added').length===1`));
 await H.tap('^End play and count up',1800);
 check('count-up reached in place shows one way to confirm',await H.js(`!document.querySelector('.confirm-all')?.getClientRects().length`));
 const names=await H.js(`[...document.querySelectorAll('main input[name^=count_]')].filter(e=>e.getClientRects().length).map(e=>e.name)`);
 const counts=[300,0,1500,3200];for(let i=0;i<names.length;i++)await H.type(`[name="${names[i]}"]`,counts[i]);
 await sleep(400);
 if(await H.js(`[...document.querySelectorAll('button')].some(b=>b.textContent.trim()==='Done'&&b.getClientRects().length)`))await H.tap('^Done$',500);
 const tapsBeforeEnd=H.taps;
 await H.tap('^Confirm (4 counts|all counts)',1700);await H.shot('confirmed');
 check('confirm: the rows are not boxed, and the ticks stay',await H.js(`![...document.querySelectorAll('.count-row')].some(r=>getComputedStyle(r,'::before').content!=='none'&&getComputedStyle(r,'::before').borderTopWidth==='2px')`));
 await H.tap('^Cash out counted',1600);await H.tap('^Cash out 4 players',1700);
 await H.tap('^Finalize results',1200);await H.tap('^Finalize set 1',1900);
 await H.tap('^Settle up',900);await H.tap('^Close session and settle up',2000);await sleep(1200);
 check('closing: the recap opens by itself',await H.js(`!!document.querySelector('dialog[open]')`));
 if(await H.js(`!!document.querySelector('dialog[open]')`))await H.tap('^Close',900);
 table.endOfGame=H.taps-tapsBeforeEnd;
 await H.shot('transfers');
 await H.tap('^Mark paid',1400);
 table.newHostTaps=H.taps;table.newHostFields=H.fields;table.scrolled=H.scrolled;
  check('the new group page was reached',/^\/g\/\d+\/$/.test(groupPath));

 // A repeat game with a preset, from an idle group on Your groups.
 const R=await person();await R.login('rena');
 if(await R.js(`!!document.querySelector('dialog[open]')`)){await R.js(`[...document.querySelectorAll('dialog[open] button')].find(b=>/^Not now/.test(b.textContent.trim())).click()`);await sleep(700)}
 await R.tap('^New session');await sleep(300);await R.shot('new-session');
 await R.tap('^Create session',1800);await sleep(1000);
 if(await R.js(`!!document.querySelector('dialog[open]')`)){await R.js(`[...document.querySelectorAll('dialog[open] button')].find(b=>/^Not now/.test(b.textContent.trim())).click()`);await sleep(700)}
 await R.tap('^Add players');
 const ticks=await R.js(`[...document.querySelectorAll('[name=member_id]')].filter(e=>e.getClientRects().length&&!e.disabled).slice(0,4).map(e=>e.value)`);
 for(const v of ticks)await R.tick(`[name=member_id][value="${v}"]`);
 await R.tap('^Add \\d+ players|^Add players',1600);
 await R.tap('^Start the set',1500);
 table.repeatTaps=R.taps;table.repeatScrolled=R.scrolled;
 check('the repeat game started',await R.js(`!!document.querySelector('#live[data-state=running]')`));

 // Seeded: a group with a long roster and a long history.
 const S=await person();await S.login('hana');
 await S.go('/g/1/?view=settings');table.settingsSeeded=await S.js(CONTROLS);
 await S.go('/g/1/?view=stats');table.statsRow=await S.js(`Math.round(document.querySelector('.stat-row').getBoundingClientRect().top)`);
}catch(e){check(`the walk finished: ${e.message}`,false)}
console.log('\nMeasure                                              Now');
const line=(a,b)=>console.log(a.padEnd(52),b);
line('New host, sign-up to a marked payment',`${table.newHostTaps} taps, ${table.newHostFields} fields`);
line('Typed counts to the transfer list, books balanced',`${table.endOfGame} taps`);
line('Repeat game with a preset, from an idle Home',`${table.repeatTaps} taps + 4 ticks, ${table.repeatScrolled} needing a scroll`);
line('Group settings, new group',`${table.settingsNew} px`);
line('Settings, seeded',`${table.settingsSeeded} controls`);
line('Player rows on the first screen, ready to start',`${table.rowsOpen}`);
line('First ranked row on Stats',`${table.statsRow} px`);
writeFileSync(`${OUT}/journey.json`,JSON.stringify(table));
ws.close();chrome.kill();
const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed} of ${results.length} checks passed`);process.exit(failed?1:0);
