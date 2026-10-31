// RSVP. Seed a fresh temporary database with seed_rsvp.py alone, serve it on 127.0.0.1:8765, then run.
// Captures 320, 390 and 1280px, as host and players, and an answer sent without JavaScript.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-rsvp-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-rsvp-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-rsvp-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();const errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,{width=390,height=844,scripts=true}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,600));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async(file,full=false)=>{let clip;if(full){const m=await send('Page.getLayoutMetrics',{},s);clip={x:0,y:0,width,height:Math.ceil(m.cssContentSize.height),scale:1}}const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:full,...(clip?{clip}:{})},s);writeFileSync(`${OUT}/${file}.png`,Buffer.from(data,'base64'))};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(800);
 if(!scripts)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,width};}
const results=[];function check(name,ok,detail){results.push({name,ok:!!ok,detail});console.log(`${ok?'PASS':'FAIL'} ${name} ${detail===undefined?'':JSON.stringify(detail)}`)}
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const targets=sel=>`[...document.querySelectorAll('${sel} button, ${sel} summary.btn, ${sel} .rsvp-pill, ${sel} input:not([type=hidden]), ${sel} .rsvp-more > summary')].filter(e=>e.offsetParent).map(e=>Math.round(e.getBoundingClientRect().height))`;
// Contrast of an element's text on the first opaque background behind it.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d',{willReadFrequently:true});const rgb=v=>{c.clearRect(0,0,1,1);c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};
 const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};
 const el=document.querySelector('${sel}');let n=el,bg;while(n){const v=rgb(getComputedStyle(n).backgroundColor);if(v[3]===255){bg=v;break}n=n.parentElement}bg=bg||rgb(getComputedStyle(document.body).backgroundColor);
 const a=lum(rgb(getComputedStyle(el).color)),b=lum(bg);return Math.round((Math.max(a,b)+.05)/(Math.min(a,b)+.05)*100)/100})()`;
const tab='/g/'+M.group+'/',friday='/n/'+M.friday+'/',back='/n/'+M.back+'/';
try {
// Ben has not answered; the seats are full.
const B=await user('ben');
await B.go('/');
check('Your groups asks Ben "Are you in?" with the time',await B.js(`/Are you in\\?.*Friday table.*8:00 PM/.test(document.querySelector('.home-ask').textContent.replace(/\\s+/g,' '))`));
await B.go(tab);
check('Coming up follows Now playing',await B.js(`[...document.querySelectorAll('.group-sessions h2')].map(h=>h.textContent.trim()).join('|').startsWith('Now playing|Coming up')`));
check('the card gives date, time, seats and waiting',await B.js(`/8:00 PM/.test(document.querySelector('.coming-card .table-card-when').textContent)&&/3 of 3 seats · 1 waiting/.test(document.querySelector('.coming-card .table-card-facts').textContent)`));
await B.go(friday);
check('a player who has not answered has one main action on the session page',await B.js(`[...document.querySelectorAll('main .btn-primary')].filter(e=>e.getClientRects().length).length===1&&!document.querySelector('.hero a.btn-primary')`),await B.js(`[...document.querySelectorAll('main .btn-primary')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim())`));
await B.go(tab);
check('full: the primary reads Join the waitlist, beside Can\'t make it',await B.js(`(()=>{const b=[...document.querySelectorAll('.coming-card .rsvp-actions button')];return b.length===2&&b[0].textContent.trim()==='Join the waitlist'&&b[0].classList.contains('btn-primary')&&b[0].getBoundingClientRect().top===b[1].getBoundingClientRect().top})()`));
check('card controls are 48px',(await B.js(targets('.coming-card'))).every(h=>h>=48),await B.js(targets('.coming-card')));
check('390: no sideways scroll',await B.js(fits(390)));
await B.js(`document.querySelector('.coming-card').scrollIntoView()`);await B.shot('rsvp-card-asked-390');
await B.js(`document.querySelector('.coming-card .rsvp-actions button').click()`);await sleep(1500);
check('Ben is 2nd in line, in Brass, after the server accepts',await B.js(`document.querySelector('.coming-card .rsvp-you').textContent.trim()==='Waitlist · 2nd in line'`),await B.js(`document.querySelector('.coming-card .rsvp-you')?.textContent`));
const brass=await B.js(contrast('.coming-card .rsvp-you.is-waiting'));check('the waitlist line has at least 4.5:1',brass>=4.5,brass);
await B.js(`document.querySelector('.coming-card').scrollIntoView()`);await B.shot('rsvp-card-waiting-390');
// Carlo drops out: Dina moves up.
const C=await user('carlo');await C.go(tab);
check('Carlo reads You\'re in with a quiet Can\'t make it',await C.js(`/You're in/.test(document.querySelector('.coming-card .rsvp-you').textContent)&&document.querySelector('.coming-card .rsvp-actions button').classList.contains('btn-quiet')`));
await C.js(`document.querySelector('.coming-card').scrollIntoView()`);await C.shot('rsvp-card-in-390');
await C.js(`document.querySelector('.coming-card .rsvp-actions button').click()`);await sleep(1500);
check('Carlo now reads that he can\'t make it',await C.js(`/You said you can't make it/.test(document.querySelector('.coming-card .rsvp-you').textContent)`));
const D=await user('dina');await D.go(tab);
check('Dina moved up: You\'re in',await D.js(`/You're in/.test(document.querySelector('.coming-card .rsvp-you').textContent)`));
await B.go(tab);check('Ben is now 1st in line',await B.js(`/1st in line/.test(document.querySelector('.coming-card .rsvp-you').textContent)`));
// Host: Who's coming.
const H=await user('hana');await H.go(friday);
check('the felt says the time once; the count is in Who\'s coming',await H.js(`/Starts 8:00 PM\\./.test(document.querySelector('.hero').textContent)&&!/Starts/.test(document.querySelector('.rsvp').textContent)&&/3 of 3/.test(document.querySelector('.rsvp-count').textContent)`));
check('Who\'s coming: three coming, one waiting numbered, Can\'t make it and Not answered folded',await H.js(`(()=>{const r=document.querySelector('.rsvp');return r.querySelectorAll('.rsvp-list:not(.rsvp-line) > .rsvp-row').length>=3&&r.querySelector('.rsvp-line .rsvp-place').textContent.trim()==='1'&&[...r.querySelectorAll('.rsvp-more > summary')].map(s=>s.textContent.replace(/\\s+/g,' ').trim()).join('|')==="Can't make it · 1|Not answered · 1"})()`),await H.js(`[...document.querySelectorAll('.rsvp-more > summary')].map(s=>s.textContent.replace(/\\s+/g,' ').trim())`));
check('a roster player answered by the host says so',await H.js(`/answered by hana/.test(document.querySelector('.rsvp').textContent)`));
check('host controls are 48px',(await H.js(targets('.rsvp'))).every(h=>h>=48),await H.js(targets('.rsvp')));
await H.js(`document.querySelector('.rsvp').scrollIntoView()`);await H.shot('rsvp-coming-host-390',true);
// A host's row opens its confirmation in place: the pill keeps its place and reads Cancel.
const row=n=>`[...document.querySelectorAll('.rsvp-row')].find(r=>r.querySelector('strong').textContent===${JSON.stringify(n)})`;
const pillAt=n=>H.js(`(()=>{const b=${row(n)}.querySelector('.rsvp-pill').getBoundingClientRect();return Math.round(b.left)+','+Math.round(b.top+scrollY)})()`);
const closedAt=await pillAt('Ana');await H.js(`${row("Ana")}.querySelector('summary').click()`);await sleep(900);
check('open: the pill stays where it was and reads Cancel; one button confirms',await pillAt('Ana')===closedAt&&await H.js(`(()=>{const r=${row("Ana")};return r.querySelector('.rsvp-pill').innerText.trim()==='Cancel'&&[...r.querySelectorAll('button')].filter(b=>b.offsetParent).map(b=>b.textContent.trim()).join('|')==='Mark Ana out'})()`),[closedAt,await pillAt('Ana')]);
const styled=await H.js(`[...document.querySelectorAll('.rsvp [style]')].map(e=>e.className+' '+e.getAttribute('style')).filter(t=>!/ $/.test(t))`);check('open: nothing is left moving or styled inline',!styled.length,styled);
await H.js(`document.querySelector('.rsvp').scrollIntoView()`);await H.shot('rsvp-confirm-host-390',true);
await H.js(`${row("Dina")}.querySelector('summary').click()`);await sleep(400);
check('one confirmation at a time',await H.js(`[...document.querySelectorAll('.rsvp-host[open]')].map(d=>d.closest('li').dataset.person).length===1&&${row("Dina")}.querySelector('.rsvp-host').open`));
await H.js(`${row("Dina")}.querySelector('summary').focus()`);await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27},H.s);await sleep(300);
check('Escape closes it and keeps focus on the row',await H.js(`!document.querySelector('.rsvp-host[open]')&&document.activeElement===${row("Dina")}.querySelector('summary')`));
// Seats refused under the count, keeping what was typed.
await H.js(`(()=>{const f=document.querySelector('.rsvp-seats');f.querySelector('input[name=seat_limit]').value='2';f.querySelector('button').click()})()`);await sleep(1500);
check('lowering under the count is refused with the reason',await H.js(`/3 players are coming\\. Mark someone out first\\./.test(document.documentElement.innerHTML)&&document.querySelector('.rsvp-seats input[name=seat_limit]').value==='2'`),await H.js(`[document.querySelector('.rsvp-seats input[name=seat_limit]').value,location.href,/3 players are coming/.test(document.documentElement.innerHTML)]`));
// Seat now from the waitlist.
await H.js(`window.__stay=1;(()=>{const d=document.querySelector('.rsvp-line .rsvp-host');d.open=true;d.querySelector('button').click()})()`);await sleep(1500);
check('Seat now seats Ben and raises the seats to 4',await H.js(`/4 of 4/.test(document.querySelector('.rsvp-count').textContent)&&!document.querySelector('.rsvp-line')`),await H.js(`document.querySelector('.rsvp-count').textContent`));
check('the answer updates in place: no reload, the row closed and marked',await H.js(`window.__stay===1&&!document.querySelector('.rsvp-host[open]')&&${row("Ben")}.classList.contains('just-changed')`));
// Set 1's add-players.
await H.go('/s/'+M.friday_set+'/players/add-several/');
check('add-players ticks the four coming and lists them first',await H.js(`(()=>{const rows=[...document.querySelectorAll('[data-pick-row]')];const ticked=rows.filter(r=>r.querySelector('input').checked);return ticked.length===4&&rows.slice(0,4).every(r=>r.querySelector('input').checked)&&/Said they're coming/.test(rows[0].textContent)})()`));
await H.shot('rsvp-add-players-390',true);
// Announce the other draft.
await H.go(back);
check('a draft shows the Announce card with the table\'s 9 seats',await H.js(`!!document.querySelector('#announce')&&document.querySelector('#announce-seats').value==='9'&&/4 players with a login get a notice\\./.test(document.querySelector('#announce').textContent)`));
await H.js(`document.querySelector('#announce').scrollIntoView()`);await H.shot('rsvp-announce-390');
check('Announce starts folded, under one main action',await H.js(`!document.querySelector('#announce').open&&document.querySelector('.hero a.btn-primary')!==null`));
await H.js(`(()=>{const d=document.querySelector('#announce');d.open=true;document.querySelector('#announce-seats').value='many';document.querySelector('#announce button[type=submit]').click()})()`);await sleep(1500);
check('a refused Announce opens again with what was typed and the reason',await H.js(`document.querySelector('#announce').open&&document.querySelector('#announce-seats').value==='many'&&document.body.textContent.includes('Enter the number of seats.')`));
await H.js(`(()=>{document.querySelector('#announce-time').value='21:30';document.querySelector('#announce-seats').value='6';document.querySelector('#announce button[type=submit]').click()})()`);await sleep(1500);
check('announcing replaces the card with Who\'s coming, 0 of 6',await H.js(`!document.querySelector('#announce')&&/0 of 6/.test(document.querySelector('.rsvp-count').textContent)`));
// Widths.
const N=await user('hana',{width:320,height:700});await N.go(friday);
check('320: no sideways scroll; the long name wraps in its row',await N.js(fits(320)+`&&[...document.querySelectorAll('.rsvp-row')].every(r=>r.scrollWidth<=r.clientWidth+1)`));
await N.js(`document.querySelector('.rsvp').scrollIntoView()`);await N.shot('rsvp-coming-host-320');
const N2=await user('ben',{width:320,height:700});await N2.go(tab);
check('320 tab: no sideways scroll',await N2.js(fits(320)));await N2.js(`document.querySelector('.coming-card').scrollIntoView()`);await N2.shot('rsvp-card-320');
const W=await user('hana',{width:1280,height:900});await W.go(tab);
check('1280 tab: no sideways scroll',await W.js(fits(1280)));await W.shot('rsvp-tab-1280',true);
await W.go(friday);check('1280 session: no sideways scroll',await W.js(fits(1280)));await W.shot('rsvp-night-1280',true);
// Without JavaScript the answer is a plain form.
const X=await user('carlo',{scripts:false});await X.go(tab);
check('no JavaScript: Carlo is offered I\'m in after all',await X.js(`document.querySelector('.coming-card .rsvp-actions button').textContent.trim()==="I'm in after all"`));
await X.js(`document.querySelector('.coming-card .rsvp-actions button').click()`);await sleep(1500);
check('no JavaScript: the plain form posts and Carlo joins the line',await X.js(`/Waitlist · 1st in line/.test(document.querySelector('.coming-card .rsvp-you').textContent)`),await X.js(`document.querySelector('.coming-card .rsvp-you')?.textContent`));
check('no runtime errors',errors.length===0,errors);
} finally { ws.close();chrome.kill(); }
const failed=results.filter(r=>!r.ok);writeFileSync(`${OUT}/rsvp.json`,JSON.stringify(results,null,1));
console.log(`${results.length-failed.length} of ${results.length} pass`);process.exit(failed.length?1:0);
