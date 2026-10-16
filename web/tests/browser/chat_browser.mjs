// The front door inside a chat app's browser: the card, its moment, Copy link, Open in Chrome and Continue here.
// Seed a fresh temporary database with seed_chat_browser.py, serve it on 127.0.0.1:8765, then run.
import {spawn} from 'node:child_process';
import {writeFileSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const M=JSON.parse(readFileSync('/private/tmp/pn-chat-manifest.json','utf8'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const UA={
 messenger:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/MessengerForiOS;FBAV/460.0.0.37.106;FBDV/iPhone15,2]',
 android:'Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.6422.165 Mobile Safari/537.36 [FB_IAB/MESSENGER;FBAV/460.0.0.48.109;]',
 safari:'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'};
rmSync('/private/tmp/pn-chat-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-chat-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const BOOT=`window.__errors=[];addEventListener('error',e=>__errors.push(e.message));window.__copied=[];
 try{Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>(__copied.push(t),Promise.resolve())},configurable:true})}catch(e){}`;
async function user(kind,width,{reduced=false,height=844}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:2,mobile:true},s);
 await send('Emulation.setUserAgentOverride',{userAgent:UA[kind]},s);await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s);
 if(reduced)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:BOOT},s);
 const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,500));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(400);for(let i=0;i<30;i++){if(await ev('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const until=async(expression,ms=4000)=>{for(let t=0;t<ms;t+=50){if(await ev(expression))return true;await sleep(50)}return false};
 return {s,js:ev,go,shot,until};}
const results=[];const check=(name,ok,note)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||note===undefined?'':' :: '+JSON.stringify(note)}`)};
const C=`document.getElementById('chat-browser')`;
const tidy=w=>`[...${C}.querySelectorAll('.btn')].filter(e=>e.getClientRects().length).every(e=>e.getBoundingClientRect().height>=48)&&document.documentElement.scrollWidth<=${w}&&${C}.scrollWidth<=${C}.clientWidth`;

try{
 // iPhone, Messenger: the invite lands on Sign up with the card above it.
 const A=await user('messenger',390);await A.go(M.join);
 const first=await A.js(`({path:location.pathname+location.search,title:${C}.querySelector('.chat-out-title').textContent,why:${C}.querySelector('.chat-out-why').textContent,above:${C}.compareDocumentPosition(document.querySelector('form'))&Node.DOCUMENT_POSITION_FOLLOWING,buttons:[...${C}.querySelectorAll('.btn')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim()),html:document.documentElement.dataset.chatBrowser})`);
 check('Messenger iPhone: the invite reaches Sign up with the card above the form',first.path.startsWith('/accounts/signup/')&&first.above&&first.title==='Open this in Safari'&&first.html==='ios',first);
 check('Messenger iPhone: it names the app and keeps the invite',/^Messenger’s browser/.test(first.why)&&/Your invite comes with you\./.test(first.why),first.why);
 check('Messenger iPhone: Copy link and Continue here, no button that cannot work',first.buttons.join('|')==='Copy link|Continue here',first.buttons);
 const dots=await A.js(`[...${C}.querySelectorAll('.chat-out-menu path')].map(p=>p.getAnimations().map(a=>a.animationName+'@'+a.effect.getTiming().delay))`);
 check('Messenger iPhone: the three dots light in turn, once, after the door settles',dots.length===3&&dots.every((d,i)=>d.length===1&&d[0]===`chat-dot@${900+120*i}`),dots);
 await sleep(1900);
 check('At rest: nothing runs, targets are 48px and nothing overflows',await A.js(`document.getAnimations().filter(a=>a.playState==='running').length===0&&${tidy(390)}`));
 await A.shot('chat-390-1-messenger-iphone');
 const fit=await A.js(`({card:${C}.getBoundingClientRect().bottom,field:document.querySelector('form input:not([type=hidden])').getBoundingClientRect().top})`);
 check('390 × 844: the card and the first field are both on the first screen',fit.field<844,fit);
 await A.js(`${C}.querySelector('[data-chat-copy]').click()`);await sleep(150);
 const copied=await A.js(`({copied:__copied,status:${C}.querySelector('[data-chat-status]').textContent,button:${C}.querySelector('[data-chat-copy]').textContent})`);
 check('Copy link copies this page, invite included, and says where to paste it',copied.copied[0]===location_href(M.join)&&copied.button==='Copied'&&/Paste it into Safari/.test(copied.status),copied);
 await A.js(`${C}.querySelector('[data-chat-here]').click()`);
 await sleep(60);
 const mid=await A.js(`({moving:document.getAnimations().length>0,cardOpacity:getComputedStyle(${C}).opacity})`);
 await sleep(700);
 const after=await A.js(`({hidden:${C}.hidden,focus:document.activeElement.tagName,url:location.pathname+location.search,cookie:document.cookie,left:[...document.querySelectorAll('.door-sheet > *')].filter(e=>e.style.transform).length,running:document.getAnimations().filter(a=>a.playState==='running').length})`);
 check('Continue here: the card leaves and the form rises into its place',mid.moving&&after.hidden&&after.left===0&&after.running===0,{mid,after});
 check('Continue here: focus on the heading, no navigation, remembered',after.focus==='H1'&&after.url.startsWith('/accounts/signup/')&&/chat_here=1/.test(after.cookie),after);
 await A.shot('chat-390-2-continued');
 await A.go('/accounts/login/');
 check('Continue here holds for the browser session',await A.js(`!${C}`));
 check('No script errors on iPhone',(await A.js('__errors')).length===0,await A.js('__errors'));

 // Android, Messenger: Open in Chrome, and the menu when it does not leave.
 const B=await user('android',390);await B.go(M.join);
 const b=await B.js(`({title:${C}.querySelector('.chat-out-title').textContent,href:${C}.querySelector('[data-chat-open]').getAttribute('href'),turbo:${C}.querySelector('[data-chat-open]').dataset.turbo,primary:[...${C}.querySelectorAll('.btn-primary')].map(e=>e.textContent.trim())})`);
 check('Messenger Android: Open in Chrome to this exact address',b.title==='Open this in Chrome'&&b.primary.join()==='Open in Chrome'&&b.href.startsWith('intent://127.0.0.1:8765/accounts/signup/?next=')&&b.href.includes('package=com.android.chrome')&&b.turbo==='false',b);
 await sleep(1700);await B.shot('chat-390-3-messenger-android');
 check('Android: targets 48px, no overflow',await B.js(tidy(390)));
 // The emulated browser cannot open an intent: the page stays, as a refusing chat app leaves it.
 await B.js(`${C}.querySelector('[data-chat-open]').addEventListener('click',e=>e.preventDefault(),{once:true});${C}.querySelector('[data-chat-open]').click()`);
 check('Android: still here after a second and a half, it says to use the menu and points again',await B.until(`/Use the three dots/.test(${C}.querySelector('[data-chat-status]').textContent)&&${C}.classList.contains('is-pointing')`,2500));
 await sleep(200);
 check('Android: the dots play again',await B.js(`[...${C}.querySelectorAll('.chat-out-menu path')].some(p=>p.getAnimations().some(a=>a.animationName==='chat-dot-again'))`));

 // 320 × 568, the smallest phone.
 const N=await user('messenger',320,{height:568});await N.go(M.join);await sleep(1800);
 check('320px: the card fits',await N.js(tidy(320)));
 check('320 × 568: the page opens at the top with the card in view, nothing focused',await N.js(`scrollY===0&&${C}.getBoundingClientRect().top<innerHeight/2&&document.activeElement===document.body`),await N.js(`({y:scrollY,active:document.activeElement.tagName})`));await N.shot('chat-320-1-messenger');

 // Reduced motion.
 const R=await user('messenger',390,{reduced:true});await R.go(M.join);await sleep(100);
 check('Reduced motion: the dots are still',await R.js(`[...${C}.querySelectorAll('.chat-out-menu path')].every(p=>p.getAnimations().length===0)`));
 await R.js(`${C}.querySelector('[data-chat-here]').click()`);await sleep(50);
 check('Reduced motion: Continue here removes the card at once',await R.js(`${C}.hidden&&document.getAnimations().length===0`));

 // Without JavaScript.
 // Without JavaScript: the page as fetched.
 const raw=await (await fetch(BASE+M.join,{headers:{'User-Agent':UA.messenger},redirect:'follow'})).text();
 check('No JavaScript: Continue here is a link to this page marked here=1',/data-chat-copy="[^"]+" hidden>/.test(raw)&&/href="\/accounts\/signup\/\?next=[^"]+&amp;here=1" data-chat-here/.test(raw));

 // Safari: nothing.
 const S=await user('safari',390);await S.go(M.join);
 check('Safari: no card, no mark on the page',await S.js(`!${C}&&!document.documentElement.dataset.chatBrowser`));
}finally{
 const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed} of ${results.length} passed`);
 ws.close();chrome.kill();process.exitCode=failed?1:0;
}
function location_href(path){return `${BASE}/accounts/signup/?next=${encodeURIComponent(path)}`}
