// The Your groups page after its redesign. Seed a fresh temporary database with seed_home.py alone,
// serve it on 127.0.0.1:8765, then run. It reads /private/tmp/pn-home-manifest.json.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-home-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-home-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-home-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name,width=390,script=true){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const h=await js('Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)');await send('Emulation.setDeviceMetricsOverride',{width,height:Math.min(h,5200),deviceScaleFactor:1,mobile:width<900},s);await sleep(150);const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'));await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 if(!script)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,400)}`)};
// Helpers that run in the page.
const LIB=`(()=>{const lum=c=>{const v=c.map(x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4});return .2126*v[0]+.7152*v[1]+.0722*v[2]};
 const cv=document.createElement('canvas').getContext('2d',{willReadFrequently:true});const rgb=c=>{cv.clearRect(0,0,1,1);cv.fillStyle='#000';cv.fillStyle=c;cv.fillRect(0,0,1,1);const d=cv.getImageData(0,0,1,1).data;return [d[0],d[1],d[2],d[3]/255]};
 const bg=el=>{for(let e=el;e;e=e.parentElement){const c=rgb(getComputedStyle(e).backgroundColor);if(c[3]>.9)return c}return rgb(getComputedStyle(document.body).backgroundColor)};
 window.__contrast=el=>{const f=rgb(getComputedStyle(el).color),b=bg(el),a=lum(f),z=lum(b);return (Math.max(a,z)+.05)/(Math.min(a,z)+.05)};
 window.__texts=root=>[...root.querySelectorAll('*')].filter(e=>!e.closest('.visually-hidden,.chip,.chip-more,svg')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&e.getClientRects().length);
 window.__small=root=>__texts(root).filter(e=>parseFloat(getComputedStyle(e).fontSize)<16).length})()`;
const card=g=>`document.querySelector('#group-${g}').closest('.group-home')`;

async function page(width){
 const W=`${width}px`,A=await user(M.viewer,width);await A.go('/');await A.js(LIB);await A.shot(`home-${width}`);
 check(`${W} five groups, each a card with a surface and an edge`,await A.js(`(()=>{const c=[...document.querySelectorAll('.group-home')];return c.length===5&&c.every(e=>{const s=getComputedStyle(e);return s.backgroundColor!==getComputedStyle(document.body).backgroundColor&&parseFloat(s.borderTopWidth)>=1&&parseFloat(s.borderTopLeftRadius)>=16})})()`));
 check(`${W} nothing is wider than the screen`,await A.js(`document.documentElement.scrollWidth<=${width}&&[...document.querySelectorAll('.group-home *')].every(e=>{const b=e.getBoundingClientRect();return b.width===0||(b.left>=-1&&b.right<=${width}+1)})`));
 check(`${W} one settings button per card, 48px, named for its group`,await A.js(`[...document.querySelectorAll('.group-home')].every(c=>{const g=c.querySelectorAll('.group-gear');const b=g[0]&&g[0].getBoundingClientRect();return g.length===1&&b.width>=48&&b.height>=48&&g[0].getAttribute('aria-label')==='Group settings for '+c.querySelector('h2').textContent.trim()&&g[0].getAttribute('href').endsWith('?view=settings')})`));
 check(`${W} no Sessions, Stats or Group settings links at the foot`,await A.js(`!document.querySelector('.home-links')&&![...document.querySelectorAll('.group-home a')].some(a=>/view=stats/.test(a.href)||['Sessions','Stats','Group settings'].includes(a.textContent.trim()))`));
 check(`${W} every link and button in a card is at least 48px tall`,await A.js(`[...document.querySelectorAll('.group-home a, .home-create > summary')].every(a=>a.getBoundingClientRect().height>=47.5)`),await A.js(`[...document.querySelectorAll('.group-home a')].filter(a=>a.getBoundingClientRect().height<47.5).map(a=>a.textContent.trim().slice(0,30)+':'+Math.round(a.getBoundingClientRect().height))`));
 check(`${W} all text, the felt band included, has contrast of at least 4.5:1`,await A.js(`__texts(document.querySelector('.home-groups')).every(e=>__contrast(e)>=4.5)`),await A.js(`__texts(document.querySelector('.home-groups')).filter(e=>__contrast(e)<4.5).map(e=>e.textContent.trim().slice(0,24)+':'+__contrast(e).toFixed(2)).slice(0,6)`));
 check(`${W} a set in play: the only felt, with its one action`,await A.js(`document.querySelectorAll('.home-band.felt').length===1&&${card(M.groups.play)}.querySelector('.home-band.felt a.btn-primary').getAttribute('href')==='/s/${M.live}/'`));
 check(`${W} further open sessions: one row with the number`,await A.js(`(()=>{const r=${card(M.groups.play)}.querySelector('.home-row');return !!r&&r.querySelector('.home-count').textContent.trim()==='3'&&r.getAttribute('href')==='/g/${M.groups.play}/'})()`));
 check(`${W} fourteen players: six chips and "+8"; the count is still read out`,await A.js(`(()=>{const c=${card(M.groups.play)};return c.querySelectorAll('.token-stack .chip').length===6&&c.querySelector('.chip-more').textContent==='+8'&&c.querySelector('.token-row .visually-hidden').textContent==='14 players'})()`));
 check(`${W} figures are large, signed and never broken inside a number`,await A.js(`[...document.querySelectorAll('.home-facts .amount:not(.home-absent)')].every(a=>parseFloat(getComputedStyle(a).fontSize)>=26&&/^[+−]?[₱\\d]/.test(a.textContent.trim())&&a.getBoundingClientRect().height<parseFloat(getComputedStyle(a).fontSize)*1.3*(/chips/.test(a.textContent)?2:1)+2)`),await A.js(`[...document.querySelectorAll('.home-facts .amount')].map(a=>a.textContent.trim()+':'+Math.round(a.getBoundingClientRect().height))`));
 check(`${W} pesos and chips records stay apart`,await A.js(`(()=>{const a=[...${card(M.groups.play)}.querySelectorAll('.home-facts .amount')].map(x=>x.textContent.trim());return a.some(t=>t.includes('₱'))&&a.some(t=>t.includes('chips'))})()`));
 check(`${W} a session sat out says "Did not play"`,await A.js(`${card(M.groups.owed)}.querySelector('.home-absent').textContent==='Did not play'`));
 check(`${W} dues: who, and a large coloured amount`,await A.js(`(()=>{const d=[...${card(M.groups.play)}.querySelectorAll('.home-dues li')];return d.length===3&&d.every(li=>parseFloat(getComputedStyle(li.querySelector('.amount')).fontSize)>=22)&&d[2].querySelector('.amount').classList.contains('minus')})()`));
 check(`${W} a 60-character name wraps inside its card and keeps the gear beside it`,await A.js(`(()=>{const c=${card(M.groups.long)},h=c.querySelector('h2').getBoundingClientRect(),g=c.querySelector('.group-gear').getBoundingClientRect(),b=c.getBoundingClientRect();return h.right<=g.left&&g.right<=b.right&&Math.abs(g.top-h.top)<8})()`));
 const small=await A.js(`[__small(${card(M.groups.play)}),__texts(${card(M.groups.play)}).length]`);
 check(`${W} small text on the fullest card: ${small[0]} pieces under 16px (the layout before had 17), none under 11px`,small[0]<=4&&await A.js(`__texts(${card(M.groups.play)}).every(e=>parseFloat(getComputedStyle(e).fontSize)>=11)`),await A.js(`__texts(${card(M.groups.play)}).filter(e=>parseFloat(getComputedStyle(e).fontSize)<16).map(e=>e.textContent.trim().slice(0,22)+':'+getComputedStyle(e).fontSize)`));
 check(`${W} keyboard order follows reading order in a card`,await A.js(`(()=>{const c=${card(M.groups.play)};const order=[...c.querySelectorAll('a')].map(a=>a.className.split(' ')[0]||a.textContent.trim().slice(0,12));return order[0]!=='btn'&&c.querySelector('a')===c.querySelector('h2 a')&&c.querySelectorAll('a')[1].classList.contains('group-gear')})()`));
 return A;
}

try {
 const A=await page(390);
 const cols=async X=>X.js(`new Set([...document.querySelectorAll('.group-home')].map(c=>Math.round(c.getBoundingClientRect().left))).size`);
 check('390px one column',await cols(A)===1);
 // The gear and the name lead where they say.
 await A.js(`${card(M.groups.open)}.querySelector('.group-gear').click()`);await sleep(900);
 check('the gear opens that group\'s Group settings',await A.js(`location.pathname+location.search`)===`/g/${M.groups.open}/?view=settings`&&await A.js(`document.querySelector('.tabs a[aria-current]').textContent.trim()==='Group settings'`));
 await A.go('/');await A.js(`${card(M.groups.open)}.querySelector('h2 a').click()`);await sleep(900);
 check('the name opens the group on Sessions',await A.js(`location.pathname+location.search`)===`/g/${M.groups.open}/`);
 // New group: a button that opens the form in place; a refused name keeps it open.
 await A.go('/');
 check('New group is a full-width button, closed at first',await A.js(`(()=>{const d=document.querySelector('.home-create:not(.home-archived)'),s=d.querySelector('summary').getBoundingClientRect();return !d.open&&s.width>=300&&s.height>=48&&d.querySelector('summary').textContent.trim()==='New group'})()`));
 await A.js(`document.querySelector('.home-create > summary').click()`);await sleep(150);
 check('New group opens the form in place',await A.js(`document.querySelector('.home-create').open&&!!document.querySelector('.home-create [name=name]').getClientRects().length`));await A.shot('home-create-390');
 await A.js(`(()=>{const f=document.querySelector('.home-create form');f.querySelector('[name=name]').value='G'.repeat(61);f.requestSubmit()})()`);await sleep(1200);
 check('a refused name keeps the form open with what was typed',await A.js(`document.querySelector('.home-create').open&&document.querySelector('.home-create [name=name]').value.length===61&&!!document.querySelector('.home-create [aria-invalid=true], .home-create .error')`));
 for(const w of [320,1280]){const X=await page(w);if(w===1280){check('1280px two columns of cards with more than one group',await cols(X)===2);
   check('1280px no card is split between columns',await X.js(`[...document.querySelectorAll('.group-home')].every(c=>c.getClientRects().length===1)`));}}
 const P=await user(M.single,1280);await P.go('/');await P.shot('home-single-1280');
 check('one group at 1280px: one card, one column, no wider than 560px',await P.js(`document.querySelectorAll('.group-home').length===1&&document.querySelector('.group-home').getBoundingClientRect().width<=560`));
 check('a host with an open session sees its one action',await P.js(`!!document.querySelector('.home-band:not(.felt) a.btn')`));
 const N=await user(M.viewer,390,false);await N.go('/');
 check('without JavaScript: the cards, each gear link and the group links are plain links',await N.js(`document.querySelectorAll('.group-home').length===5&&[...document.querySelectorAll('.group-gear')].every(a=>a.tagName==='A'&&a.getAttribute('href').endsWith('?view=settings'))`));
 await N.js(`document.querySelector('.home-create > summary').click()`);await sleep(150);
 check('without JavaScript: New group opens its form',await N.js(`document.querySelector('.home-create').open&&!!document.querySelector('.home-create form[action] [name=name]').getClientRects().length`));
 writeFileSync(`${OUT}/home.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
