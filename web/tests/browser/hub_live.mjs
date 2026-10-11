// Your groups and a group's Sessions tab update by themselves (nightlive.js). Seed a fresh temporary
// database with seed.py alone, serve it on 127.0.0.1:8765, then run. PN_DB names the SQLite file:
// the "host" writes to it through the real services while a player's pages watch.
import {spawn,spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const DB=process.env.PN_DB || '/private/tmp/pn-hublive-check.sqlite3';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const host=code=>{const r=spawnSync('.venv/bin/python',['manage.py','shell','-c',`import uuid
from django.utils import timezone
from games import services as games
from games.models import GameSession, Participant
from groups.models import Member
from settlement import services as settlement
from settlement.models import Transfer, Payment
host=Member.objects.get(user__username='hana',role='host')
ben=Member.objects.get(group=host.group,user__username='ben')
def live(): return GameSession.objects.get(table__name='Live table')
${code}`],{env:{...process.env,DEBUG:'True',DATABASE_URL:'sqlite:///'+DB},encoding:'utf8'});if(r.status!==0)throw Error(r.stderr.slice(-700));return r.stdout.trim().split('\n').pop()};
const GROUP=host(`print(host.group_id)`);
rmSync('/private/tmp/pn-hublive-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-hublive-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Counts the questions asked and the redraws in place, and marks the document so a reload would show.
const BOOT=`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__asked=[];window.__renders=0;
 const _f=window.fetch;window.fetch=function(u,o){if(/\\/state\\//.test(String(u)))__asked.push(String(u));return _f.apply(this,arguments)};
 document.addEventListener('turbo:render',e=>{if(e.detail.renderMethod==='morph')__renders++});
 addEventListener('DOMContentLoaded',()=>{window.__loaded=(window.__loaded||0)+1})`;
async function user(name,path){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await sleep(400);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=9000)=>{const t0=Date.now();while(Date.now()-t0<ms){if(await js(expression))return Math.max(1,Date.now()-t0);await sleep(100)}return 0};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('[name=password]').form.submit()`);await sleep(900);
 if(path){await go(path);await sleep(300)}
 return {s,js,go,shot,until};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const text=`document.getElementById('main').innerText.replace(/\\s+/g,' ')`;
const fresh=`window.__mark==='same document'&&__loaded===1`;

try{
 const H=await user('ben','/'),G=await user('ben',`/g/${GROUP}/`);
 check('both pages ask once as they start',await H.until(`__asked.length>=1`,3000)>0&&await G.until(`__asked.length>=1`,3000)>0&&await H.js(`__asked[0].endsWith('/state/?v=')`)&&await G.js(`__asked[0].includes('/g/${GROUP}/state/?v=')`),[await H.js('__asked'),await G.js('__asked')]);
 await sleep(600);
 for(const p of [H,G])await p.js(`window.__mark='same document';scrollTo(0,140);window.__y=scrollY`);
 const more=Number((await H.js(text)).match(/More open sessions (\d+)/)?.[1]||0);
 check('the starting answer redraws nothing',await H.js(`__renders===0`)&&await G.js(`__renders===0`));
 // The host creates a session and opens its set.
 host(`t=games.create_table(host,'Live table',9)
s=games.create_session(host,{'table_id':t.pk,'game_date':timezone.localdate(),'location':'x','game_type':'nlh','small_blind':1000,'big_blind':2000,'min_buy_in':50000,'max_buy_in':500000,'default_buy_in':100000})
games.transition(s.pk,host,'open')`);
 const tg=await G.until(`/Live table/.test(${text})`),th=await H.until(`/More open sessions ${more+1}/.test(${text})||/Live table/.test(${text})`);
 check('a session opened by the host appears on the player\'s group page within about 5 seconds',tg>0&&tg<8000,tg);
 check('…and on their Your groups',th>0&&th<8000,[th,(await H.js(text)).slice(0,200)]);
 check('…without a reload, at the same scroll position',await G.js(`${fresh}&&Math.abs(scrollY-__y)<=2`)&&await H.js(`${fresh}&&__y>50&&Math.abs(scrollY-__y)<=2`),[await G.js('[__loaded,scrollY,__y]'),await H.js('[__loaded,scrollY,__y]')]);
 await G.shot('hublive-390-1-group');await H.shot('hublive-390-2-home');
 const row=`[...document.querySelectorAll('main li, main a, main .row')].filter(e=>/Live table/.test(e.textContent)).map(e=>e.textContent.replace(/\\s+/g,' ')).sort((a,b)=>a.length-b.length)[0]||''`;
 host(`games.add_participant(live().pk,host,ben.pk)
games.transition(live().pk,host,'start',opening_buy_ins=False)`);
 check('the set starting reaches the group page',await G.until(`/In play/.test(${row})`)>0,await G.js(row));
 // New group open and half typed: nothing is redrawn under it.
 await H.js(`(()=>{const d=document.querySelector('details.home-create:not(.home-archived)');d.open=true;d.querySelector('input[type=text]').value='Half typed';window.__n=__renders})()`);
 host(`games.transition(live().pk,host,'end')`);
 check('the group page learns that play ended',await G.until(`/Counting up/.test(${row})`)>0,await G.js(row));
 await sleep(6500);
 check('Your groups waits while New group is open with typing',await H.js(`__renders===__n&&document.querySelector('details.home-create:not(.home-archived)').open&&document.querySelector('details.home-create:not(.home-archived) input[type=text]').value==='Half typed'`));
 await H.js(`(()=>{const d=document.querySelector('details.home-create:not(.home-archived)');d.querySelector('input[type=text]').value='';d.open=false;document.activeElement&&document.activeElement.blur()})()`);
 const t2=await H.until(`__renders>__n`,5000);
 check('…and the update lands once the form is closed',t2>0&&t2<3500,t2);
 // A transfer the player owes is marked paid: "you owe" follows.
 const owes=(await H.js(text)).match(/You owe \w+/g)||[];
 host(`t=Transfer.objects.filter(payer=ben,plan__is_current=True).exclude(pk__in=Payment.objects.filter(active=True).values('transfer_id')).first()
settlement.mark_paid(t.plan.night_id,host,t.pk,uuid.uuid4())`);
 check('a transfer marked paid leaves the player\'s "to settle"',owes.length>0&&await H.until(`((${text}).match(/You owe \\w+/g)||[]).length===${owes.length-1}`)>0,owes);
 // Hidden: no questions. Back: one at once.
 await G.js(`Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));window.__n=__asked.length`);await sleep(6500);
 check('a hidden tab asks nothing',await G.js(`__asked.length===__n`));
 await G.js(`Object.defineProperty(document,'hidden',{value:false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))`);await sleep(600);
 check('…and asks at once on return',await G.js(`__asked.length===__n+1`));
 // Tabs that must never redraw by themselves.
 const S=await user('hana',`/g/${GROUP}/?view=settings`),T=await user('hana',`/g/${GROUP}/?view=stats`);
 await sleep(6500);
 check('Group settings and Stats ask nothing',await S.js(`__asked.length===0&&!document.querySelector('[data-state-url]')`)&&await T.js(`__asked.length===0&&!document.querySelector('[data-state-url]')`));
 // The arrival after a login is not replayed by a redraw.
 const W=await user('ben');await sleep(1600);
 check('after a login the arrival has finished and the page asks',await W.js(`location.pathname==='/'&&!document.getElementById('main').hasAttribute('data-welcome')&&__asked.length>=1`),await W.js(`[location.pathname,__asked.length]`));
 await W.js(`window.__n=__renders`);
 host(`games.transition(live().pk,host,'resume')`);
 check('a redraw after it replays no arrival',await W.until(`__renders>__n`)>0&&await W.js(`!document.getElementById('main').hasAttribute('data-welcome')&&document.getAnimations().filter(a=>/welcome/.test(a.animationName||'')).length===0`));
 for(const [n,u] of [['Your groups',H],['group page',G],['settings',S],['after login',W]])check(`${n}: no script error`,await u.js(`__errors.length===0`),await u.js('__errors'));
}finally{
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
