// Slice A of the UI revamp (doc/plan/1793431937_ui_revamp.md): one main action per screen, one way back,
// whole initials on token stacks, straight row hairlines, and the words on a first buy-in.
// Seed a fresh temporary database with seed.py, seed_end_set.py, seed_night.py, seed_remaining.py and
// seed_opening.py, serve it on 127.0.0.1:8765, run. It records buy-ins on the opening fixture: reset for a repeat.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-corrections-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';
const NIGHTS=JSON.parse(readFileSync('/private/tmp/pn-slice3-manifest.json','utf8'));
const OPENING=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
const PROFILE='/private/tmp/pn-corrections-chrome';rmSync(PROFILE,{recursive:true,force:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9462',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<60&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9462/json/version')).json()).webSocketDebuggerUrl}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const[ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
async function user(name,width=390){
 const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,300));return r.result.value};
 const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await sleep(700);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)};await js(`document.querySelector('dialog[open]')?.close()`)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'jpeg',quality:70},s);writeFileSync(`${OUT}/${n}.jpg`,Buffer.from(data,'base64'))};
 await go('/accounts/login/');await sleep(500);await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1500);
 return{js,go,shot,width,s,send};
}
const PRIMARY=`[...document.querySelectorAll('main .btn-primary')].filter(e=>e.getClientRects().length&&!e.closest('dialog:not([open])')).map(e=>e.textContent.trim().slice(0,28))`;
const SETS=[1,2,3,4,5,6,7,8,11,OPENING.default.set];
const NIGHT_LIST=[NIGHTS.partly,NIGHTS.unpaid,NIGHTS.ready,NIGHTS['two-sets'],OPENING.default.night];
try{
 for(const width of [390,1280]){
  const H=await user('hana',width);
  for(const s of SETS){await H.go(`/s/${s}/`);const p=await H.js(PRIMARY);check(`${width} host set ${s}: at most one main action (${p.join(' / ')||'none'})`,p.length<=1)}
  for(const n of NIGHT_LIST){await H.go(`/n/${n}/`);const p=await H.js(PRIMARY);check(`${width} host session ${n}: at most one main action (${p.join(' / ')||'none'})`,p.length<=1)}
  await H.go(`/n/${OPENING.default.night}/`);
  check(`${width} the session's main action leads to the set`,await H.js(`document.querySelector('main .btn-primary').getAttribute('href').startsWith('/s/')`));
  check(`${width} Announce and Chip values are 48px rows or taller`,await H.js(`[...document.querySelectorAll('.night-option > summary, a.night-option-link')].length>=1&&[...document.querySelectorAll('.night-option > summary, a.night-option-link')].every(e=>e.getBoundingClientRect().height>=48)`));
  const P=await user('ben',width);
  for(const s of [3,6]){await P.go(`/s/${s}/`);check(`${width} player set ${s}: at most one main action`,(await P.js(PRIMARY)).length<=1)}
 }
 // One way back.
 const H=await user('hana');
 const session=OPENING.default.set,night=OPENING.default.night;
 const backs=[`/s/${session}/players/add-several/`,`/s/${session}/settings/`,`/s/${session}/log/`,`/n/${night}/chip-values/`,`/n/${night}/archive/`,`/n/${night}/paid-at-table/`,'/g/1/sessions/new/','/g/1/presets/new/','/g/1/chip-presets/new/','/g/1/archive/'];
 await H.go('/g/1/?view=settings');backs.push(await H.js(`document.querySelector('a[href*="/remove/"]').getAttribute('href')`));
 for(const path of backs){await H.go(path);
  const r=await H.js(`(()=>{const a=document.querySelector('.site-header .table-bar a');const b=a&&a.getBoundingClientRect();return{bar:!!a,height:b?b.height:0,brand:!!document.querySelector('.site-header .brand'),inPage:!!document.querySelector('main p.small > a[href]:first-child')&&/^(Back to|.* settings$)/.test(document.querySelector('main p.small > a[href]:first-child').textContent.trim()),words:a?a.textContent.trim():''}})()`);
  check(`${path} goes back from the header (${r.words}), at 48px`,r.bar&&r.height>=48&&!r.brand&&!r.inPage);
 }
 // Whole initials on a stack: each letter stops short of the next token.
 for(const width of [320,390]){await H.send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true},H.s);
 for(const[name,path]of[['Your groups','/'],['Sessions','/g/1/']]){await H.go(path);
  check(`${width} ${name}: no token's initials run under the next, all 36px, nothing overflows`,await H.js(`(()=>{const chips=[...document.querySelectorAll('.token-stack > .chip')];if(chips.length<2)return false;return chips.every(c=>{const n=c.nextElementSibling;if(!n)return true;const r=document.createRange();r.selectNodeContents(c);return r.getBoundingClientRect().right<=n.getBoundingClientRect().left-3&&c.getBoundingClientRect().width===36})&&document.documentElement.scrollWidth<=innerWidth&&[...document.querySelectorAll('.token-row')].every(row=>{const a=row.querySelector('.token-stack').getBoundingClientRect(),badge=row.querySelector('.badge');const b=badge&&badge.getBoundingClientRect();return a.right<=row.getBoundingClientRect().right+1&&(!b||b.top>=a.bottom-1||b.left>=a.right)})})()`));
  await H.shot(`stack-${width}-${name.replace(/\s/g,'-')}`);
 }}
 await H.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},H.s);
 // k6's initials against its own fill, measured by the browser's colour.
 const ratio=await H.js(`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=a=>{const f=a.map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4});return .2126*f[0]+.7152*f[1]+.0722*f[2]};
  const t=document.createElement('span');t.className='chip k6';document.body.append(t);const s=getComputedStyle(t);const a=lum(rgb(s.color)),b=lum(rgb(s.getPropertyValue('--c')));t.remove();return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`);
 check(`k6 initials measure ${ratio.toFixed(2)}:1, at least 4.5:1`,ratio>=4.5);
 // Straight hairlines.
 await H.go('/s/3/');check('a player row has no rounded corners to curl its hairline',await H.js(`getComputedStyle(document.querySelector('.player-row')).borderBottomLeftRadius==='0px'`));
 await H.go('/g/1/?view=stats');check('a stat row has no rounded corners to curl its hairline',await H.js(`getComputedStyle(document.querySelector('.stat-row')).borderBottomLeftRadius==='0px'`));
 // Rebuys seen in one redraw are separate events: each keeps its word, as when a locked phone wakes.
 await H.go('/s/3/');
 await H.js(`[...document.querySelectorAll('#live .player-row[data-watch]')].slice(0,3).forEach(r=>{const v=r.dataset.value.split(':');v[1]=String(Math.max(0,Number(v[1])-1));sessionStorage.setItem('rack:'+document.getElementById('live').dataset.url+':'+r.dataset.watch,v.join(':'))})`);
 await H.go('/s/3/');
 check('three rebuys seen late each keep their word and box',await H.js(`(()=>{const rows=[...document.querySelectorAll('#live .player-row.just-changed')];return rows.length===3&&!rows.some(r=>r.classList.contains('changed-together'))&&rows.every(r=>[...r.querySelectorAll('.change-label')].some(b=>b.getClientRects().length&&/added$/.test(b.textContent)))})()`));
 // A real success from the server: one line under the header, no button, gone by itself.
 await H.go('/g/1/?view=settings');
 await H.js(`(()=>{const f=document.querySelector('form[action$="/name/"]');f.querySelector('[name=name]').value='Kamuning Club';f.requestSubmit()})()`);await sleep(1100);
 const toast=await H.js(`(()=>{const t=document.querySelector('.toast.message-success');if(!t)return null;const r=t.getBoundingClientRect();const h=document.querySelector('.site-header').getBoundingClientRect();return{quiet:t.classList.contains('toast-quiet'),button:!!t.querySelector('button,a'),h:r.height,below:r.top>=h.bottom,words:t.textContent.trim()}})()`);
 check(`a success is one line under the header with no button (${toast&&toast.words}, ${toast&&toast.h}px)`,!!toast&&toast.quiet&&!toast.button&&toast.h<=40&&toast.below);
 await sleep(1500);check('it is still there after about 2.6 seconds',await H.js(`!!document.querySelector('.toast.message-success')`));
 await sleep(1700);check('it has gone by about 4.3 seconds',await H.js(`!document.querySelector('.toast.message-success')`));
 // A real tap at the toast's centre: it reaches the control underneath and sends the toast away.
 const message=(words)=>`(()=>{const m=document.querySelector('#main > .messages')||(()=>{const u=document.createElement('ul');u.className='messages';u.setAttribute('role','status');document.getElementById('main').prepend(u);return u})();const l=document.createElement('li');l.className='message message-success';l.textContent=${JSON.stringify(words)};m.append(l);document.dispatchEvent(new CustomEvent('inplace:updated',{detail:{}}))})()`;
 await H.go('/s/3/');
 await H.js(`(()=>{window.__hit=0;const b=[...document.querySelectorAll('main .player-row button')].find(x=>x.textContent.trim()==='Rebuy');b.addEventListener('click',e=>{window.__hit++;e.preventDefault();e.stopPropagation()},true);window.__b=b})()`);
 await H.js(message('Payment recorded.'));await sleep(400);
 const spot=await H.js(`(()=>{const t=document.querySelector('.toast.message-success').getBoundingClientRect();const y=t.top+t.height/2;scrollBy(0,window.__b.getBoundingClientRect().top+window.__b.getBoundingClientRect().height/2-y);const r=window.__b.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 await sleep(150);
 check('the toast stands over the button',await H.js(`(()=>{const t=document.querySelector('.toast.message-success').getBoundingClientRect(),r=window.__b.getBoundingClientRect();return r.top<t.bottom&&r.bottom>t.top})()`));
 await H.send('Input.dispatchMouseEvent',{type:'mousePressed',x:spot.x,y:spot.y,button:'left',clickCount:1},H.s);await H.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:spot.x,y:spot.y,button:'left',clickCount:1},H.s);await sleep(500);
 check('a tap goes through the toast to the button',await H.js(`window.__hit===1`));
 check('and that tap sends the toast away',await H.js(`!document.querySelector('.toast.message-success:not(.leaving)')`));
 await H.go('/s/3/');
 await H.js(message('Password changed. Other phones and browsers are logged out.'));await sleep(4800);
 check('a longer success is still there after 4.8 seconds',await H.js(`!!document.querySelector('.toast.message-success')`));
 await sleep(1700);check('and gone by 6.5 seconds',await H.js(`!document.querySelector('.toast.message-success')`));
 await H.go('/s/3/');
 await H.js(`(()=>{const m=document.querySelector('#main > .messages')||document.getElementById('main').appendChild(Object.assign(document.createElement('ul'),{className:'messages'}));const l=document.createElement('li');l.className='message message-error';l.textContent='Refused.';m.append(l);document.dispatchEvent(new CustomEvent('inplace:updated',{detail:{}}))})()`);await sleep(300);
 check('a refusal keeps the foot of the screen and Dismiss',await H.js(`(()=>{const t=document.querySelector('.toast.message-error');return !!t&&!t.classList.contains('toast-quiet')&&!!t.querySelector('button')&&t.getBoundingClientRect().top>innerHeight/2})()`));
 // A first buy-in is not a rebuy.
 await H.go(`/s/${session}/`);
 const before=await H.js(`[...document.querySelectorAll('.player-row button')].find(b=>b.textContent.trim()==='Buy-in')?.closest('.player-row').dataset.watch`);
 check('the fixture has a player with no buy-in',!!before);
 await H.js(`[...document.querySelectorAll('.player-row button')].find(b=>b.textContent.trim()==='Buy-in').click()`);await sleep(800);
 await H.js(`[...document.querySelectorAll('dialog[open] button')].find(b=>/^Confirm/.test(b.textContent.trim())).click()`);await sleep(1300);
 check('one first buy-in says Buy-in added',await H.js(`[...document.querySelectorAll('.change-label')].filter(b=>b.getClientRects().length).map(b=>b.textContent).join()==='Buy-in added'`));
 await H.shot('first-buy-in');
}catch(e){check(`the run finished: ${e.message}`,false)}
ws.close();chrome.kill();
const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed} of ${results.length} checks passed`);process.exit(failed?1:0);
