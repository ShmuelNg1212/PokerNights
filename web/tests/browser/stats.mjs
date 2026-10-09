// The Stats tab and a player's page at 320, 390 and 1280px, on a fresh database seeded with seed_stats.py. It only reads. See README.md.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-stats-check`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8771';
async function page(){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const size=width=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:c.width,height:Math.max(c.height,844),scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
const key=async(k,code,vk,extra={})=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key:k,code,windowsVirtualKeyCode:vk,...extra},s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:k,code,windowsVirtualKeyCode:vk},s)};
await size(390);return {s,js,go,click,shot,size,key,browserContextId};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const text=t=>`document.body.textContent.includes(${JSON.stringify(t)})`;
const targets=`[...document.querySelectorAll('main a.btn, main button, main input:not([type=hidden]), main .entry-alt a, main .entry-invite a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
// WCAG contrast of an element's text against the page ground, via canvas so oklch resolves.
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
const sized=`[...document.querySelectorAll('main a.btn, main button, main select, main summary, main .pills a, main .stat-link, main .player-sessions a, main .player-highlights a, main .table-bar a')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const login=async(P,name)=>{await P.go('/accounts/login/');await P.js(`document.querySelector('[name=username]').value='${name}';document.querySelector('[name=password]').value='tablestakes-91'`);await P.click(`document.querySelector('form.form-section [type=submit]')`);};
const watch=P=>send('Page.addScriptToEvaluateOnNewDocument',{source:"window.__errs=[];addEventListener('error',e=>window.__errs.push(e.message))"},P.s);
const names=`[...document.querySelectorAll('[data-stat-board] .stat-link strong')].map(e=>e.textContent)`;
try {
 const A=await page();await send('Page.enable',{},A.s);await watch(A);await login(A,'rosa');
 const group=await A.js(`[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).find(h=>new RegExp('^/g/[0-9]+/$').test(h))`);
 const board=group+'?view=stats';
 await A.go(board);
 check('your summary leads with a figure, a rank and the last result',await A.js(`(()=>{const y=document.querySelector('.stat-you');return !!y.querySelector('.stat-you-figure')&&new RegExp('of [0-9]+|Not ranked').test(y.textContent)&&y.textContent.includes('Last result')&&!!y.querySelector('a.btn')})()`));
 check('ranked rows have places, others are apart',await A.js(`document.querySelectorAll('[data-stat-board] .stat-row').length>=5&&document.body.textContent.includes('Not ranked yet')&&!document.querySelector('.stat-list-rest .stat-rank').getClientRects().length`));
 check('a removed player stays, and movement is marked in words too',await A.js(`document.body.textContent.includes('Left the group')`)&&await A.js(`[...document.querySelectorAll('.stat-move')].length>0`));
 check('a result is never colour alone: sign and icon',await A.js(`[...document.querySelectorAll('[data-stat-board] .stat-net')].every(e=>new RegExp('^[+−₱]').test(e.textContent.trim())&&(!!e.querySelector('svg')))`));
 for(const w of [320,390,1280]){await A.size(w);await A.go(board);check(`board fits ${w}`,await A.js(fits(w)));check(`board 48px ${w}`,await A.js(sized));await A.shot(`stats-board-${w}`);}
 await A.size(390);await A.go(board);
 for(const sel of ['.stat-facts','.stat-label','.stat-move','.stat-you-facts dt','.stat-notes summary'])check(`contrast ${sel}`,await A.js(contrast(sel))>=4.5);
 const before=await A.js(names);
 await A.click(`[...document.querySelectorAll('[data-stat-pills=sort] a')].find(a=>a.textContent==='Average')`);
 check('Average orders the board and shows profit small beneath',await A.js(`location.search.includes('sort=average')&&!!document.querySelector('.stat-profit')&&document.querySelector('[data-stat-pills=sort] [aria-current]').textContent==='Average'`));
 check('contrast .stat-profit',await A.js(contrast('.stat-profit'))>=4.5);
 await sleep(900);check('rows are at rest with no inline style left',await A.js(`[...document.querySelectorAll('.stat-row')].every(r=>!r.getAttribute('style'))`));await A.shot('stats-board-average-390');
 check('Per hour is offered when time was recorded',await A.js(`[...document.querySelectorAll('[data-stat-pills=sort] a')].some(a=>a.textContent==='Per hour')`));
 await A.js(`(()=>{const s=document.querySelector('#stat-month');s.value=s.options[1].value;s.dispatchEvent(new Event('change',{bubbles:true}))})()`);await sleep(900);
 check('picking a month shows it at once and keeps the order',await A.js(`new RegExp('period=2026-[0-9]{2}').test(location.search)&&location.search.includes('sort=average')&&document.querySelector('#stat-month').hasAttribute('data-chosen')`));await A.shot('stats-board-month-390');
 await A.go(board+'&unit=chips');check('a chips board never shows pesos',await A.js(`!document.querySelector('.group-stats').textContent.includes('₱')&&document.body.textContent.includes('chips')`));
 await A.go(board+'&period=2020-01');check('an empty period says so',await A.js(text('No closed session in January 2020')));

 // A change of period, unit or order keeps the page where it was scrolled.
 const stays=async(P,label,act)=>{await P.js(`window.scrollTo(0,420)`);await sleep(150);const y=await P.js(`window.scrollY`);const steps=await P.js(`history.length`);await act();await sleep(900);check(`${label}: the page stays where it was scrolled`,y>300&&Math.abs(await P.js(`window.scrollY`)-y)<=2);check(`${label}: Back still leaves Stats in one step`,await P.js(`history.length`)===steps);check(`${label}: nothing is left marked`,await P.js(`!document.documentElement.hasAttribute('data-go')&&[...document.querySelectorAll('.stat-row,.pills a,.pill-marker,[data-stat-body],#stat-month')].every(e=>!e.getAttribute('style'))`));};
 await A.size(390);await A.go(board);
 await stays(A,'period',()=>A.js(`[...document.querySelectorAll('[data-stat-pills=period] a')].find(a=>a.textContent.trim()==='This year').click()`));
 check('the period changed',await A.js(`location.search.includes('period=year')&&document.querySelector('[data-stat-pills=period] [aria-current]').textContent==='This year'`));
 await stays(A,'order',()=>A.js(`[...document.querySelectorAll('[data-stat-pills=sort] a')].find(a=>a.textContent.trim()==='Return').click()`));
 await stays(A,'unit',()=>A.js(`[...document.querySelectorAll('[data-stat-pills=unit] a')].find(a=>a.textContent.trim()==='Chips games').click()`));
 await stays(A,'month',()=>A.js(`(()=>{const s=document.querySelector('#stat-month');s.value=s.options[1].value;s.dispatchEvent(new Event('change',{bubbles:true}))})()`));
 await A.go(board);await A.js(`[...document.querySelectorAll('[data-stat-pills=period] a')].find(a=>a.textContent.trim()==='Last 3 months').click()`);await sleep(140);
 {const{data}=await send('Page.captureScreenshot',{format:'png'},A.s);writeFileSync(`${OUT}/stats-mid-switch-390.png`,Buffer.from(data,'base64'));}
 // What moves: sampled over the first half second after a tap.
 const moving=(P,tap)=>P.js(`(async()=>{setTimeout(()=>{${tap}},20);const seen=new Set();for(let i=0;i<40;i++){document.getAnimations().forEach(a=>{const t=a.effect&&a.effect.target;if(!t||a.effect.pseudoElement)return;if(t.matches('.pill-marker'))seen.add('marker');if(t.matches('[data-stat-body]'))seen.add('body');if(t.matches('.stat-row'))seen.add('row')});await new Promise(r=>setTimeout(r,15))}return [...seen].sort().join(',')})()`);
 const pill=(group,label)=>`[...document.querySelectorAll('[data-stat-pills=${group}] a')].find(a=>a.textContent.trim()==='${label}').click()`;
 await A.go(board);
 check('a new period slides the marker over and brings the figures in from the side',await moving(A,pill('period','This year'))==='body,marker');
 await sleep(500);check('a new order slides the marker and moves the rows, and the summary stays still',await moving(A,pill('sort','Sessions'))==='marker,row');
 await sleep(500);check('a new unit slides the marker and brings the figures in',await moving(A,pill('unit','Chips games'))==='body,marker');
 await sleep(700);check('everything is at rest afterwards with no inline style left',await A.js(`[...document.querySelectorAll('.pill-marker,[data-stat-body],.stat-row')].every(e=>!e.getAttribute('style'))`));
 await A.go(board);await A.js(`window.scrollTo(0,420)`);await sleep(150);
 await A.click(`[...document.querySelectorAll('[data-stat-board] .stat-link')].find(a=>a.querySelector('strong').textContent==='Ana')`);
 check('opening a player still starts at the top',await A.js(`window.scrollY`)<5);
 await stays(A,'player period',()=>A.js(`[...document.querySelectorAll('[data-stat-pills=period] a')].find(a=>a.textContent.trim()==='Last 3 months').click()`));

 // A player's page.
 await A.go(board);await A.click(`[...document.querySelectorAll('[data-stat-board] .stat-link')].find(a=>a.querySelector('strong').textContent==='Ana')`);
 const player=await A.js(`location.pathname+location.search`);
 check('a row opens the player with the unit and period kept',player.includes('/players/')&&player.includes('period=all')&&player.includes('unit=php'));
 check('the page has the lead figure, the chart, eight tiles, four highlights and the list',await A.js(`!!document.querySelector('.player-net-figure')&&!!document.querySelector('[data-chart]')&&document.querySelectorAll('.stat-tile').length===8&&document.querySelectorAll('.player-highlights > div').length===4&&document.querySelectorAll('.player-sessions li').length>0`));
 for(const w of [320,390,1280]){await A.size(w);await A.go(player);await sleep(1300);check(`player fits ${w}`,await A.js(fits(w)));check(`player 48px ${w}`,await A.js(sized));await A.shot(`stats-player-${w}`);}
 await A.size(390);await A.go(player);await sleep(1300);
 for(const sel of ['.chart-y','.chart-say','.chart-x','.chart-sub','.stat-tile dt','.stat-tile-note','.player-rank','.player-sessions .roster-activity'])check(`contrast ${sel}`,await A.js(contrast(sel))>=4.5);
 check('every bar is drawn and stands on or hangs from the baseline',await A.js(`(()=>{const base=document.querySelector('.chart-base').getBoundingClientRect().top;return [...document.querySelectorAll('.chart-bar')].every(b=>{const r=b.getBoundingClientRect();return r.height>=1&&r.width>=2&&(b.classList.contains('up')?Math.abs(r.bottom-base)<1.5:b.classList.contains('down')?Math.abs(r.top-base)<1.5:true)})})()`));
 check('the end mark sits on the line inside the chart',await A.js(`(()=>{const e=document.querySelector('.chart-end').getBoundingClientRect(),b=document.querySelector('.chart-line').getBoundingClientRect();return e.left>=b.left&&e.right<=b.right+1&&e.top>=b.top-6&&e.bottom<=b.bottom+6})()`));
 await A.js(`document.querySelector('[data-chart-plot]').scrollIntoView({block:'center'})`);await sleep(200);
 const box=await A.js(`(()=>{const r=document.querySelector('[data-chart-plot]').getBoundingClientRect();return {x:r.left+r.width*0.3,y:r.top+40}})()`);
 await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:box.x,y:box.y},A.s);await sleep(150);
 const said=await A.js(`document.querySelector('[data-chart-say]').textContent`);
 check('pointing at the chart reads that session',said.includes('running total')&&said.includes('that night')&&await A.js(`!document.querySelector('[data-chart-cross]').hidden&&document.querySelectorAll('.chart-bar.is-on').length===1`));await A.shot('stats-chart-read-390');
 await A.js(`document.querySelector('[data-chart]').focus()`);await A.key('ArrowRight','ArrowRight',39);await sleep(100);
 const next=await A.js(`document.querySelector('[data-chart-say]').textContent`);
 await A.key('End','End',35);await sleep(100);
 check('arrow keys step through sessions and End goes to the latest',next!==said&&await A.js(`document.querySelector('.chart-bar:last-of-type').classList.contains('is-on')||[...document.querySelectorAll('.chart-bar')].pop().classList.contains('is-on')`));
 check('focus on the chart is visible',await A.js(`getComputedStyle(document.querySelector('[data-chart]')).outlineStyle!=='none'`));
 check('the list holds every plotted session',await A.js(`(async()=>{const n=document.querySelectorAll('.chart-bar').length;const r=await fetch(location.pathname+'?all=1&period=all&unit=php');const d=new DOMParser().parseFromString(await r.text(),'text/html');return d.querySelectorAll('.player-sessions li').length===n})()`));
 const newcomer=await A.js(`(async()=>{const r=await fetch(${JSON.stringify(board)});const d=new DOMParser().parseFromString(await r.text(),'text/html');return [...d.querySelectorAll('.stat-link')].find(a=>a.querySelector('strong').textContent==='Newcomer').getAttribute('href')})()`);
 await A.go(newcomer);check('one session: no chart, and the page says when it comes',await A.js(`!document.querySelector('[data-chart]')`)&&await A.js(text('The chart appears after three sessions.')));
 check('no script error on any page',await A.js(`window.__errs.length===0`));

 // Reduced motion: everything in place, nothing animates.
 const R=await page();await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await login(R,'rosa');await R.go(player);await sleep(150);
 check('reduced motion: the line, the end mark and the bars are whole at once',await R.js(`(()=>{const s=getComputedStyle(document.querySelector('.chart-line svg'));const bars=[...document.querySelectorAll('.chart-bar.up,.chart-bar.down')];return s.animationName==='none'&&getComputedStyle(document.querySelector('.chart-end')).opacity==='1'&&bars.every(b=>b.getBoundingClientRect().height>=1&&getComputedStyle(b).animationName==='none')})()`));

 // Without JavaScript.
 const C=await page();await login(C,'rosa');await send('Emulation.setScriptExecutionDisabled',{value:true},C.s);await C.go(player);
 check('no JavaScript: the chart and the list are complete',await C.js(`document.querySelectorAll('.chart-bar').length>0&&document.querySelectorAll('.player-sessions li').length>0`));
 await C.go(board);check('no JavaScript: the Month list has its Show button',await C.js(`document.querySelector('.stat-month .btn').getClientRects().length>0`));
 writeFileSync(`${OUT}/stats.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
