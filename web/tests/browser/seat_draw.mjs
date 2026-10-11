// The seat draw (seats.js). Seed a fresh temporary database with seed_seat_draw.py alone, serve it
// on 127.0.0.1:8765, then run. PN_DB names the SQLite file: some host actions are made through the
// real services while the pages watch. A host and two players sit side by side.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-seat-draw-check.sqlite3';
const M=JSON.parse(readFileSync('/private/tmp/pn-seat-draw-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const py=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid, json, datetime
from django.utils import timezone
from groups.models import Member
from groups import services as groups
from games import services as games, seats
from games.models import GameSession, SeatDraw, Participant
host=Member.objects.get(user__username='hana',role='host')
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-900));return r.stdout.trim().split('\n').pop()};
const server=set=>JSON.parse(py(`s=seats.seating(GameSession.objects.get(pk=${set}))
print(json.dumps(None if s is None else {'state':s.state,'dealer':s.dealer.member.display_name if s.seats else None,'order':[x.participant.member.display_name for x in s.seats],'by_seat':[x.participant.member.display_name for x in s.by_seat],'draw':s.draw.pk}))`));
rmSync('/private/tmp/pn-seats-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-seats-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,{width=390,height=844,reduce=false,scripts=true}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async file=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${file}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=8000)=>{const from=Date.now();while(Date.now()-from<ms){if(await js(expression))return Math.max(1,Date.now()-from);await sleep(80)}return 0};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(700);
 if(!scripts)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,until,name};}
const results=[];function check(name,ok,detail){results.push({name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const OPEN=`!!document.querySelector('dialog.seat-stage[open]')`,LINE=`document.querySelector('.stage-line').textContent`,SUB=`document.querySelector('.stage-sub').textContent`;
const tableNames=`[...document.querySelectorAll('#live .seat-table .seat-spot.is-taken .seat-name')].map(e=>e.textContent)`;
// The players on the stage in seat order: each token's place is matched to the nearest seat ring.
const stageNames=`(()=>{const seats=[...document.querySelectorAll('.stage-seats .seat-spot')].map(e=>{const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]});const out=[];document.querySelectorAll('.stage-token').forEach(t=>{const r=t.querySelector('.chip').getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;let best=0,d=1e9;seats.forEach((s,i)=>{const q=Math.hypot(s[0]-x,s[1]-y);if(q<d){d=q;best=i}});out[best]=t.querySelector('.stage-name').textContent});return out})()`;
try {
const six='/s/'+M.six+'/';
const H=await user('hana'),B=await user('ben'),C=await user('cara');
await H.go(six);await B.go(six);await C.go(six);
check('host is offered the draw as an optional step; Start the set stays the one main button',await H.js(`!!document.querySelector('.prep-step[data-step=seats][data-state=optional] form[action$="/draw/"] .btn-quiet')&&!document.querySelector('.host-controls form[action$="/draw/"]')&&document.querySelector('.host-controls .next-action').textContent.trim()==='Start the set'`));
check('a player is offered no draw and sees no table yet',await B.js(`!document.querySelector('form[action$="/draw/"]')&&!document.querySelector('[data-seats]')`));
check('the stage is closed before a draw',!(await H.js(OPEN))&&!(await B.js(OPEN)));

// --- The draw reaches every phone.
await H.js(`window.__t={};setInterval(()=>{const d=document.querySelector('dialog.seat-stage[open]');if(d&&!__t.open)__t.open=performance.now();if(d&&!__t.named&&d.querySelector('.stage-line').textContent.includes('has the dealer seat'))__t.named=performance.now()},30);document.querySelector('.prep-step[data-step=seats] form button').click()`);
const opened=[await H.until(OPEN,3000),await B.until(OPEN,7000),await C.until(OPEN,7000)];
check('the stage opens on the host and on both players by itself',opened.every(Boolean),opened);
await sleep(700);await H.shot('seats-draw-ring');
check('Motion moves only transform and opacity on the stage',await H.js(`document.getAnimations().filter(a=>!(a instanceof CSSTransition)&&a.effect&&a.effect.target&&a.effect.target.closest('.seat-stage')).every(a=>a.effect.getKeyframes().every(k=>Object.keys(k).every(p=>['transform','opacity','offset','easing','composite','computedOffset'].includes(p))))`));
let truth=server(M.six);
const named=[await H.until(`${LINE}.includes('has the dealer seat')`,9000),await B.until(`${LINE}.includes('has the dealer seat')`,9000),await C.until(`${LINE}.includes('has the dealer seat')`,9000)];
check('every phone names the dealer the server drew',named.every(Boolean)&&(await H.js(LINE))===truth.dealer+' has the dealer seat'&&(await B.js(LINE))===(await H.js(LINE))&&(await C.js(LINE))===(await H.js(LINE)),[truth.dealer,await B.js(LINE)]);
await sleep(900);await H.shot('seats-choose-host');
const took=await H.js(`Math.round(__t.named-__t.open)`);
check('the draw runs between three and five seconds before it names the dealer',took>3000&&took<5000,took);
const players={Ben:B,Cara:C},winner=players[truth.dealer]||null,other=truth.dealer==='Ben'?C:B;
check('the host can tap a seat; seats are 48px targets',await H.js(`(()=>{const b=[...document.querySelectorAll('.stage-seats button')];return b.length===6&&b.every(e=>{const r=e.getBoundingClientRect();return r.width>=48&&r.height>=48})})()`));
check('a player who is not the dealer has no seat to tap and reads who is choosing',await other.js(`!document.querySelector('.stage-seats button')&&document.querySelectorAll('.stage-seats span.seat-spot').length===6`)&&(await other.js(SUB))===truth.dealer+' is choosing a seat');
if(winner)check('the dealer can tap a seat on their own phone',await winner.js(`document.querySelectorAll('.stage-seats button').length===6`)&&(await winner.js(SUB))==='Tap the seat you want.');
check('the page asks more often while the seat is awaited',await other.js(`!!document.querySelector('#live [data-poll-fast]')`));
const refused=await other.js(`(async()=>{const r=await fetch('/s/${M.six}/draw/seat/',{method:'POST',headers:{'X-Requested-With':'fetch'},body:new URLSearchParams({csrfmiddlewaretoken:document.querySelector('[name=csrfmiddlewaretoken]').value,seat:'1',request_id:crypto.randomUUID()})});return [r.status,(await r.json()).error]})()`);
check('a seat sent by another player is refused',refused[0]===409&&/has the dealer seat and chooses/.test(refused[1]),refused);

// --- The seat is chosen; everyone is seated the same way.
const chooser=winner||H;
await chooser.js(`document.querySelectorAll('.stage-seats button')[3].click()`);
await sleep(350);await chooser.shot('seats-deal-flight');
const set=[await H.until(`${LINE}==='Seats are set'`,7000),await B.until(`${LINE}==='Seats are set'`,7000),await C.until(`${LINE}==='Seats are set'`,7000)];
truth=server(M.six);
check('every phone plays the seating within a few seconds of the tap',set.every(Boolean),set);
check('the dealer sits in the tapped seat and the others follow clockwise in the drawn order',truth.state==='seated'&&truth.by_seat[3]===truth.dealer&&truth.by_seat[4]===truth.order[1]&&truth.by_seat[2]===truth.order[5],truth);
const staged=[await H.js(stageNames),await B.js(stageNames),await C.js(stageNames)];
check('the stage seats the same players in the same seats on every phone',staged.every(s=>JSON.stringify(s)===JSON.stringify(truth.by_seat)),staged[1]);
check('each token shows its first-hand position and the viewer is marked',await B.js(`[...document.querySelectorAll('.stage-token.is-seated .stage-pos')].map(e=>e.textContent).sort().join()==='BB,CO,D,HJ,SB,UTG'&&document.querySelectorAll('.stage-token.is-you').length===1&&document.querySelector('.stage-token.is-you .stage-name').textContent==='Ben'`));
check('the player is told their own seat and position',/^You are in seat \d: .+ on the first hand\.$/.test(await B.js(SUB)),await B.js(SUB));
await H.shot('seats-set-host');await B.shot('seats-set-player');
check('Done has the focus and closes the stage',await H.js(`document.activeElement===document.querySelector('[data-stage-done]')`));
await H.js(`document.querySelector('[data-stage-done]').click()`);await B.js(`document.querySelector('[data-stage-done]').click()`);await C.js(`document.querySelector('[data-stage-close]').click()`);await sleep(300);
check('the stage is closed and does not come back on the next updates',!(await H.js(OPEN))&&!(await B.js(OPEN)));
await H.until(`document.querySelectorAll('#live .seat-table .seat-spot.is-taken').length===6`,6000);await B.until(`document.querySelectorAll('#live .seat-table .seat-spot.is-taken').length===6`,6000);
check('the page keeps the table: same seats, the dealer disc, the viewer ringed',JSON.stringify(await B.js(tableNames))===JSON.stringify(truth.by_seat)&&await B.js(`document.querySelectorAll('#live .seat-table .seat-disc').length===1&&document.querySelector('#live .seat-spot.is-me .seat-name').textContent==='Ben'`),await B.js(tableNames));
check('the list gives each first-hand position',await B.js(`[...document.querySelectorAll('#live .seat-order .seat-what')].map(e=>e.textContent).join('|')==='Dealer|Small blind|Big blind|Under the gun|Hijack|Cutoff'`));
check('the host\'s step is done and the main button is still Start the set',await H.js(`document.querySelector('.prep-step[data-step=seats]').dataset.state==='done'&&document.querySelector('.host-controls .next-action').textContent.trim()==='Start the set'&&!document.querySelector('.host-controls form[action$="/draw/"]')`));
await H.js(`document.querySelector('.seats').scrollIntoView()`);await H.shot('seats-page-host');
check('no page scrolls sideways',await H.js(`document.documentElement.scrollWidth<=390`)&&await B.js(`document.documentElement.scrollWidth<=390`));
await sleep(4600);
check('still closed after another update',!(await B.js(OPEN)));

// --- Watch the draw again; a tap skips.
await B.js(`document.querySelector('[data-seat-replay]').click()`);await sleep(250);
check('Watch the draw replays it',await B.js(OPEN)&&(await B.js(LINE))==='Drawing the dealer seat');
await B.js(`document.querySelector('.stage-table').click()`);await sleep(120);await B.js(`document.querySelector('.stage-table').click()`);await sleep(120);await B.js(`document.querySelector('.stage-table').click()`);await sleep(120);await B.js(`document.querySelector('.stage-table').click()`);
const skipped=await B.until(`${LINE}==='Seats are set'`,1500);
check('taps skip to the end within a second',skipped>0&&skipped<1500,skipped);
check('a skipped draw ends in the same seats',JSON.stringify(await B.js(stageNames))===JSON.stringify(truth.by_seat));
await B.js(`document.querySelector('[data-stage-done]').click()`);

// --- A phone that arrives long after the draw sees the table, not the show.
py(`SeatDraw.objects.filter(session_id=${M.six}).update(created_at=timezone.now()-datetime.timedelta(minutes=10),chosen_at=timezone.now()-datetime.timedelta(minutes=9))`);
const L=await user('cara');await L.go(six);await sleep(1200);
check('a later phone gets no replay and has the table and the button',!(await L.js(OPEN))&&await L.js(`document.querySelectorAll('#live .seat-table .seat-spot.is-taken').length===6&&!document.querySelector('[data-seat-replay]').hidden`));

// --- Draw again; then the table changes.
await H.js(`document.querySelector('.seats-again').open=true;document.querySelector('.seats-again form button').click()`);
const again=[await H.until(OPEN,3000),await B.until(OPEN,7000)];
const second=server(M.six);
check('Draw again plays a new draw on every phone',again.every(Boolean)&&second.draw!==truth.draw&&second.state==='choosing',again);
check('the set log keeps both draws',py(`print(SeatDraw.objects.filter(session_id=${M.six}).count(), SeatDraw.objects.filter(session_id=${M.six},is_current=True).count())`)==='2 1');
await H.until(`${LINE}.includes('has the dealer seat')`,9000);await B.until(`${LINE}.includes('has the dealer seat')`,9000);
py(`games.add_participants(${M.six}, host, [${M.late}], uuid.uuid4())`);
const changed=[await B.until(`${LINE}==='The table changed'`,7000),await H.until(`${LINE}==='The table changed'`,7000)];
check('a player joining makes the open stage say the table changed',changed.every(Boolean),changed);
await B.js(`document.querySelector('[data-stage-done]').click()`);await H.js(`document.querySelector('[data-stage-done]').click()`);
check('the page says so and offers the host a new draw',await B.js(`document.querySelector('#live [data-seats]').dataset.state==='stale'&&!document.querySelector('#live .seat-table')&&/A host can draw again/.test(document.querySelector('.seats-line').textContent)`)&&await H.js(`!!document.querySelector('#live .seats form[action$="/draw/"]')`));

// --- Start with a draw nobody chose a seat for; a late player.
py(`games.draw_seats(${M.six}, host, uuid.uuid4())`);
await B.until(OPEN,7000);await B.until(`${LINE}.includes('has the dealer seat')`,9000);
py(`games.transition(${M.six}, host, 'start', opening_buy_ins=False)`);
const started=await B.until(`${LINE}==='Seats are set'`,8000);
const running=server(M.six);
check('starting the set seats the dealer at the top and the waiting stage plays it',started>0&&running.state==='seated'&&running.by_seat[0]===running.dealer&&running.by_seat.length===7,started);
await B.js(`document.querySelector('[data-stage-done]').click()`);await H.js(`if(document.querySelector('dialog.seat-stage[open]'))document.querySelector('[data-stage-close]').click()`);
await H.go(six);await sleep(600);await H.js(`if(document.querySelector('dialog.seat-stage[open]'))document.querySelector('[data-stage-close]').click()`);
await H.go(six);await sleep(900);
check('a stage closed part-way does not come back on the next visit',!(await H.js(OPEN)));
check('in play the seats fold into one line that names the first dealer',await H.js(`(()=>{const d=document.querySelector('#live details.seats-fold');return !!d&&d.querySelector('summary').textContent.includes(${JSON.stringify(running.dealer)}+' dealt first')})()`));
py(`m=groups.add_roster_player(host,'Very Late')
games.add_participants(${M.six}, host, [m.pk], uuid.uuid4())`);
await H.until(`!!document.querySelector('#live .seat-late form')`,7000);
await H.js(`document.querySelector('#live details.seats-fold').open=true`);
check('the host is offered a seat for the late player; a player is told they have none',await H.js(`/Seat Very Late after/.test(document.querySelector('.seat-late label').textContent)`)&&await B.until(`/Very Late joined after the draw and has no seat yet/.test((document.querySelector('#live .seats-note')||{}).textContent||'')`,7000));
await H.js(`(()=>{const f=document.querySelector('.seat-late form');f.querySelector('select').selectedIndex=1;f.querySelector('button').click()})()`);
await H.until(`document.querySelectorAll('#live .seat-table .seat-spot.is-taken').length===8`,6000);
const late=server(M.six);
check('the late player sits after the chosen player and nobody else changes order',late.order.length===8&&late.order[2]==='Very Late'&&JSON.stringify(late.order.filter(n=>n!=='Very Late'))===JSON.stringify(running.order),late.order);
await H.js(`document.querySelector('.seats').scrollIntoView()`);await H.shot('seats-running-host');

// --- Reduced motion.
const R=await user('ben',{reduce:true});await R.go(six);await sleep(500);
await R.js(`document.querySelector('#live details.seats-fold').open=true;document.querySelector('[data-seat-replay]').click()`);
const still=await R.until(`${LINE}==='Seats are set'`,600);
check('reduced motion shows the result at once with nothing running',still>0&&await R.js(`document.getAnimations().filter(a=>a.effect&&a.effect.target&&a.effect.target.closest('.seat-stage')).length===0&&document.querySelectorAll('.stage-token.is-seated').length===8&&document.querySelector('[data-stage-hint]').hidden`),still);
await R.shot('seats-reduced');

// --- Twelve players on the smallest phone, with the processor slowed four times.
py(`games.draw_seats(${M.twelve}, host, uuid.uuid4())`);
const S=await user('hana',{width:320,height:568});
await send('Emulation.setCPUThrottlingRate',{rate:4},S.s);
await S.js(`window.__gaps=[];(function tick(last){requestAnimationFrame(now=>{if(last)__gaps.push(now-last);tick(now)})})(0)`);
await S.go('/s/'+M.twelve+'/');
await S.js(`window.__gaps=[];(function tick(last){requestAnimationFrame(now=>{if(last)__gaps.push(now-last);tick(now)})})(0)`);
const twelve=await S.until(`${LINE}.includes('has the dealer seat')`,12000);
await S.until(`/Tap a seat/.test(${SUB})`,8000);await sleep(300);await S.shot('seats-twelve-choose-320');
check('twelve seats fit 320px: all on screen, 48px each, none overlapping',await S.js(`(()=>{const b=[...document.querySelectorAll('.stage-seats button')].map(e=>e.getBoundingClientRect());return b.length===12&&b.every(r=>r.width>=48&&r.height>=48&&r.left>=0&&r.right<=320&&r.top>=0&&r.bottom<=568)&&b.every((r,i)=>b.every((q,j)=>i===j||Math.hypot(r.x-q.x,r.y-q.y)>=48))})()`),twelve);
await S.until(`/Tap a seat/.test(${SUB})`,6000);
await S.js(`document.querySelectorAll('.stage-seats button')[7].click()`);
await S.until(`${LINE}==='Seats are set'`,9000);await sleep(300);await S.shot('seats-twelve-set-320');
const gaps=await S.js(`({n:__gaps.length,long:__gaps.filter(g=>g>50).length,worst:Math.round(Math.max(...__gaps))})`);
check('with the processor slowed four times few frames run late',gaps.n>100&&gaps.long<=gaps.n*0.05,gaps);
check('twelve players seated at 320px: every chip on screen and clear of Done',await S.js(`(()=>{const done=document.querySelector('[data-stage-done]').getBoundingClientRect();return [...document.querySelectorAll('.stage-token')].every(t=>{const c=t.querySelector('.chip').getBoundingClientRect(),n=t.querySelector('.stage-name').getBoundingClientRect();return c.left>=0&&c.right<=320&&c.top>=0&&n.bottom<=done.top+1})&&document.querySelector('.seat-stage').scrollWidth<=320})()`));
await send('Emulation.setCPUThrottlingRate',{rate:1},S.s);
await S.js(`document.querySelector('[data-stage-done]').click()`);await sleep(4500);
check('the page table fits 320px with twelve players',await S.js(`document.documentElement.scrollWidth<=320&&document.querySelectorAll('#live .seat-table .seat-spot.is-taken').length===12`));
await S.js(`document.querySelector('.seat-table').scrollIntoView({block:'center'})`);await S.shot('seats-twelve-page-320');

// --- Desktop.
const W=await user('hana',{width:1280,height:800});await W.go('/s/'+M.twelve+'/');await sleep(400);
await W.js(`document.querySelector('[data-seat-replay]').click()`);await W.until(`${LINE}==='Seats are set'`,12000);await sleep(300);await W.shot('seats-twelve-1280');
check('at 1280px the stage is a centred panel and the table sits in the left column',await W.js(`(()=>{const d=document.querySelector('.seat-stage').getBoundingClientRect(),t=document.querySelector('#live .seats').getBoundingClientRect();return d.width<=520&&d.left>300&&t.right<640})()`));

// --- Without scripts: ordinary forms and a still table.
const N=await user('hana',{scripts:false});await N.go('/s/'+M.two+'/');
await N.js(`document.querySelector('.prep-step[data-step=seats] form button').click()`);await sleep(900);
check('without scripts Draw seats answers with the table and two seat buttons',await N.js(`document.querySelectorAll('form[data-seat-pick] button.seat-free').length===2&&/has the dealer seat/.test(document.querySelector('.seats-line').textContent)&&[...document.querySelectorAll('.seat-order .seat-what')].map(e=>e.textContent).join('|')==='Dealer and small blind|Big blind'`));
await N.shot('seats-noscript-choose');
await N.js(`document.querySelectorAll('form[data-seat-pick] button.seat-free')[1].click()`);await sleep(900);
const pair=server(M.two);
check('without scripts a tapped seat seats both players',pair.state==='seated'&&pair.by_seat[1]===pair.dealer&&JSON.stringify(await N.js(tableNames))===JSON.stringify(pair.by_seat),pair);
check('no script error',errors.length===0,errors);
} finally {
const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length} of ${results.length} passed`);
chrome.kill();process.exit(failed.length?1:0);
}
