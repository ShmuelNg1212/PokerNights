// The Players tab and a player's Manage at 320, 390 and 1280px, on a fresh database seeded with seed_roster.py. See README.md.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-roster-check`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
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
const sized=`[...document.querySelectorAll('#players a.btn, #players button, #players summary, #players input:not([type=hidden]), #players textarea, #players .roster-link, .player-manage a.btn, .player-manage button, .player-manage summary, .player-manage input:not([type=hidden]), main.form-page a.btn, main.form-page button')].filter(el=>el.getClientRects().length).every(el=>el.getBoundingClientRect().height>=48)`;
const fits=w=>`document.documentElement.scrollWidth<=${w}`;
const login=async(P,name)=>{await P.go('/accounts/login/');await P.js(`document.querySelector('[name=username]').value='${name}';document.querySelector('[name=password]').value='tablestakes-91'`);await P.click(`document.querySelector('form.form-section [type=submit]')`);};
const row=name=>`[...document.querySelectorAll('#players [data-roster] > li')].find(li=>li.querySelector('.roster-name > span').textContent.trim().startsWith(${JSON.stringify(name)}))`;
// A row leads to the player's page; Manage is there.
let settings;
const openManage=async(P,name)=>{await P.go(settings);await P.click(`${row(name)}.querySelector('a.roster-link')`);await P.js(`document.querySelector('.player-manage').open=true`);await sleep(350)};
const manage=`document.querySelector('.player-manage')`;
try {
 const A=await page();await login(A,'rosa');
 settings=(await A.js(`[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')).find(h=>new RegExp('^/g/[0-9]+/$').test(h))`))+'?view=players';
 await A.go(settings);
 check('rows say sessions and last played',await A.js(text('1 session · last played Oct 1'))&&await A.js(text('No sessions yet')));
 check('the removed list is closed and counted',await A.js(`(()=>{const d=document.querySelector('.roster-removed');return d&&!d.open&&d.querySelector('summary').textContent.includes('Removed players (1)')})()`));
 for(const w of [320,390,1280]){await A.size(w);await A.go(settings);check(`players fits ${w}`,await A.js(fits(w)));check(`48px targets ${w}`,await A.js(sized));await A.shot(`roster-list-${w}`);}
 await A.size(390);await A.go(settings);
 check('activity line contrast',await A.js(contrast('.roster-activity'))>=4.5);
 check('summary contrast',await A.js(contrast('#players summary'))>=4.5);
 check('every chevron lines up at the right edge, and every row is at least 64px',await A.js(`(()=>{const r=[...document.querySelectorAll('.roster-link')];const e=r.map(a=>Math.round(a.querySelector(':scope > svg').getBoundingClientRect().right));return new Set(e).size===1&&r.every(a=>a.getBoundingClientRect().height>=64)})()`));
 check('a row holds no management',await A.js(`!document.querySelector('[data-roster] form, [data-roster] details')`));

 // The way there and back.
 await A.click(`${row('Ben')}.querySelector('a.roster-link')`);
 check('a row opens the player, and the way back names Players',await A.js(`location.pathname.includes('/players/')&&document.querySelector('.back-words').textContent.trim()==='Players'`));
 check('Manage is above the record and closed',await A.js(`(()=>{const m=${manage};return !m.open&&m.getBoundingClientRect().bottom<=innerHeight&&m.querySelector('summary').textContent.trim()==='Manage Ben'})()`));await A.shot('roster-player-page-390');
 await A.click(`document.querySelector('.table-bar a')`);
 check('the way back lands on the row',await A.js(`location.search==='?view=players'&&location.hash.startsWith('#member-')&&!!${row('Ben')}`));

 // Your own name.
 await openManage(A,'rosa');check('own page offers Change your name',await A.js(`${manage}.querySelector('summary').textContent.trim()==='Change your name'`));
 await A.js(`${manage}.querySelector('[name=name]').value='ana'`);await A.click(`${manage}.querySelector('[type=submit]')`);
 check('a taken own name is refused in an open disclosure with the typing kept',await A.js(`(()=>{const m=${manage};return m.open&&m.querySelector('[name=name]').value==='ana'&&m.textContent.includes('already in this group')})()`));await A.shot('roster-own-refused-390');
 await A.js(`${manage}.querySelector('[name=name]').value='Rosa'`);await A.click(`${manage}.querySelector('[type=submit]')`);
 check('own name saved',await A.js(text('Your name is now Rosa.')));

 // Details of another player.
 await openManage(A,'Ben');check('48px targets in Manage',await A.js(sized));await A.shot('roster-manage-390');
 await A.js(`${manage}.querySelector('[name=contact]').value='0917 555 0101'`);await A.click(`${manage}.querySelector('form[action$="/rename/"] [type=submit]')`);
 check('a save comes back to the player with Manage open',await A.js(`${manage}.open&&document.body.textContent.includes('Saved.')`));
 check('contact saved and shown to the host',await A.js(`${manage}.querySelector('[name=contact]').value==='0917 555 0101'`));
 await openManage(A,'dani');check('48px targets in Manage with a login',await A.js(sized));await A.shot('roster-manage-login-390');
 for(const w of [320,1280]){await A.size(w);check(`player page with Manage open fits ${w}`,await A.js(fits(w)));await A.shot(`roster-manage-login-${w}`);}await A.size(390);

 // Several names.
 const add=`document.querySelector('form[action$="/members/add/"]')`;
 await A.go(settings);await A.js(`${add}.closest('details').open=true`);await sleep(300);
 await A.js(`(()=>{const t=${add}.querySelector('textarea');t.value='Eli\\nFe\\nana';t.dispatchEvent(new Event('input',{bubbles:true}))})()`);
 check('the tally counts typed names',await A.js(`${add}.querySelector('[data-names-tally]').textContent==='3 names'`));await A.shot('roster-add-390');
 await A.click(`${add}.querySelector('[type=submit]')`);
 check('a refused batch keeps its text and adds nobody',await A.js(`(()=>{const f=${add};return f.closest('details').open&&f.querySelector('textarea').value.replace(/\\r/g,'')==='Eli\\nFe\\nana'&&document.body.textContent.includes('Already in this group: ana.')&&!${row('Eli')}})()`));await A.shot('roster-add-refused-390');
 for(const w of [320,1280]){await A.size(w);check(`refused batch fits ${w}`,await A.js(fits(w)));}await A.size(390);
 await A.js(`${add}.querySelector('textarea').value='Eli\\nFe\\nGio'`);await A.js(`${add}.querySelector('[type=submit]').click()`);await sleep(250);
 check('new rows are marked',await A.js(`document.querySelectorAll('#players .roster-row.just-changed').length===3`));await A.shot('roster-added-390');
 check('three players added',await A.js(text('Added 3 players.'))&&await A.js(`!!${row('Gio')}`));
 await sleep(3300);check('the mark is taken off and no inline style is left',await A.js(`!document.querySelector('#players .just-changed')&&[...document.querySelectorAll('#players .roster-row')].every(li=>!li.getAttribute('style'))`));

 // Removing: the page asks first.
 await openManage(A,'Carlo');await A.click(`document.querySelector('.roster-leave a')`);
 check('a seated player is refused with a way to the set',await A.js(text('is at the table in Main table set 1'))&&await A.js(`!document.querySelector('main .btn-danger')&&!!document.querySelector('main a[href^="/s/"]')`));
 for(const w of [320,390]){await A.size(w);check(`refusal fits ${w} with a long name`,await A.js(fits(w)));}await A.shot('roster-remove-refused-390');
 await openManage(A,'Ben');await A.click(`document.querySelector('.roster-leave a')`);
 check('the page asks and lists the unpaid transfer',await A.js(text('Remove Ben from the group?'))&&await A.js(text('Still to pay'))&&await A.js(text('₱500')));
 for(const w of [320,390,1280]){await A.size(w);check(`remove page fits ${w}`,await A.js(fits(w)));check(`remove page 48px ${w}`,await A.js(sized));await A.shot(`roster-remove-${w}`);}
 await A.size(390);check('danger button contrast',await A.js(contrast('main .btn-danger'))>=4.5);
 await A.go(settings);check('opening the page removed nobody',await A.js(`!!${row('Ben')}`));
 await openManage(A,'Ben');await A.click(`document.querySelector('.roster-leave a')`);await A.js(`document.querySelector('main form [type=submit]').click()`);await sleep(300);
 check('the removed list is marked after a removal',await A.js(`document.querySelector('.roster-removed > summary').classList.contains('just-changed')`));await sleep(500);
 check('removed, and said where to bring back',await A.js(text('Ben was removed. Bring them back from Removed players.'))&&await A.js(`!${row('Ben')}`)&&await A.js(text('Removed players (2)')));

 // Bringing back.
 await A.js(`document.querySelector('.roster-removed').open=true`);await sleep(350);check('48px targets in Removed players',await A.js(sized));await A.shot('roster-removed-390');
 await A.size(320);check('removed list fits 320',await A.js(fits(320)));await A.shot('roster-removed-320');await A.size(390);
 await A.click(`[...document.querySelectorAll('.roster-removed button')].find(b=>b.getAttribute('aria-label')==='Bring back Ben')`);
 check('Ben is back with the same record',await A.js(text('Ben is back in the group.'))&&await A.js(`${row('Ben')}.textContent.includes('1 session · last played Oct 1')`));
 check('keyboard: a row takes focus and shows it',await A.js(`(()=>{const s=${row('Ben')}.querySelector('a');s.focus();return document.activeElement===s&&getComputedStyle(s).outlineStyle!=='none'})()`));

 // A long list can be searched.
 await A.js(`${add}.closest('details').open=true`);await A.js(`${add}.querySelector('textarea').value='Ivo\\nJun\\nKiko\\nLeo\\nMia'`);await A.click(`${add}.querySelector('[type=submit]')`);await sleep(300);
 check('a long list shows the search',await A.js(`document.querySelectorAll('[data-roster] > li').length>=11&&!document.querySelector('[data-roster-search]').hidden`));
 const find=async t=>{await A.js(`(()=>{const f=document.querySelector('[data-roster-find]');f.value=${JSON.stringify(t)};f.dispatchEvent(new Event('input',{bubbles:true}))})()`);await sleep(60)};
 const visible=`[...document.querySelectorAll('[data-roster] > li')].filter(l=>l.getClientRects().length).length`;
 await find('KIK');check('search finds a name whatever its capitals',await A.js(visible)===1&&await A.js(`!!${row('Kiko')}.getClientRects().length`));await A.shot('roster-search-390');
 await find('zzz');check('search says when nobody matches',await A.js(visible)===0&&await A.js(`!document.querySelector('[data-roster-none]').hidden`));
 await find('');check('clearing the search shows everyone again',await A.js(visible)>=11&&await A.js(`document.querySelector('[data-roster-none]').hidden`));

 // A player sees no host tool.
 const B=await page();await login(B,'dani');await B.go(settings);
 check('a player sees the list and nothing of a host',await B.js(`!document.querySelector('#players details')&&!document.querySelector('#invites')&&!document.body.textContent.includes('0917')&&!document.querySelector('.roster-removed')`));await B.shot('roster-player-390');
 await B.click(`${row('Ben')}.querySelector('a.roster-link')`);
 check('another player\'s page shows a player no management',await B.js(`location.pathname.includes('/players/')&&!document.querySelector('.player-manage')&&!document.body.textContent.includes('0917')`));
 await B.go(settings);await B.click(`${row('dani')}.querySelector('a.roster-link')`);
 check('a player\'s own page offers only their name',await B.js(`${manage}.querySelector('summary').textContent.trim()==='Change your name'&&!document.querySelector('.roster-leave')`));

 // Reduced motion: the mark shows, nothing moves.
 const R=await page();await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},R.s);await login(R,'rosa');await R.go(settings);
 await R.js(`${add}.closest('details').open=true`);await R.js(`${add}.querySelector('textarea').value='Hero'`);await R.js(`${add}.querySelector('[type=submit]').click()`);await sleep(120);
 check('reduced motion: the row is marked and never transparent or moved',await R.js(`(()=>{const li=${row('Hero')};const c=getComputedStyle(li);return li.classList.contains('just-changed')&&c.opacity==='1'&&c.transform==='none'&&!document.documentElement.classList.contains('motion-on')})()`));

 // Without JavaScript every action still works.
 const C=await page();await login(C,'rosa');await C.go(settings);const benUrl=await C.js(`${row('Ben')}.querySelector('a').getAttribute('href')`);await send('Emulation.setScriptExecutionDisabled',{value:true},C.s);await C.go(settings);
 check('no JavaScript: rows are links, and the add form is in the page, with no search',await C.js(`!!document.querySelector('[data-roster] a.roster-link')&&!!document.querySelector('#players details > summary')&&document.querySelector('[data-names-tally]').hidden&&document.querySelector('[data-roster-search]').hidden`));
 await C.go(benUrl);check('no JavaScript: Manage and the remove link are on the player\'s page',await C.js(`!!document.querySelector('.player-manage > summary')&&!!document.querySelector('.player-manage .roster-leave a[href$="/remove/"]')`));
 writeFileSync(`${OUT}/roster.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
