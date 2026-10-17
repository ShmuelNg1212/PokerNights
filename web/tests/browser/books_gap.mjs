// Books off (2026-10-17): the host bar's "See the ₱100 difference" leads to the record that looks wrong
// (gap.js). Seed a fresh temporary database with seed.py then seed_end_set.py (set 9 "Recount needed",
// set 10 covered by an override), serve it on 127.0.0.1:8773, then run.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-agent3-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8773';
const PORT=process.env.PN_CHROME_PORT || '9353';
const OFF=process.env.PN_OFF_SET || '9', COVERED=process.env.PN_COVERED_SET || '10';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-agent3-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${PORT}`,'--user-data-dir=/private/tmp/pn-agent3-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
// Every Motion call and error is logged.
const LOG=`addEventListener('DOMContentLoaded',()=>{window.__runs=[];
 if(window.Motion){const a=Motion.animate;Motion.animate=function(el,k,o){__runs.push({el:(el.className&&el.className.baseVal===undefined?el.className:el.tagName)+'',keys:Object.keys(k)});return a.apply(this,arguments)}}});
 window.__errors=[];addEventListener('error',e=>__errors.push(e.message));`;
async function user(name,width=390,{reduce=false,noJs=false}={}){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:width<900?844:800,deviceScaleFactor:2,mobile:width<900},s);
 if(reduce)await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}await sleep(300)};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 const tap=async sel=>{const p=await js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)}),f=e.getBoundingClientRect();if(f.top<0||f.bottom>innerHeight)e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},s)};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1200);
 if(noJs)await send('Emulation.setScriptExecutionDisabled',{value:true},s);
 return {s,js,go,shot,tap};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,500)}`)};

// Where the target sits against the band between the sticky header and whatever is fixed at the bottom.
const place=`(()=>{const el=document.querySelector('#live [data-suspect]')||document.getElementById('books-gap')||document.getElementById('balance');
 const r=el.getBoundingClientRect(),top=Math.max(0,document.querySelector('.site-header').getBoundingClientRect().bottom);let bottom=innerHeight;
 document.querySelectorAll('.host-controls, .host-controls .next-action').forEach(e=>{if(getComputedStyle(e).position==='fixed'&&e.getClientRects().length)bottom=Math.min(bottom,e.getBoundingClientRect().top)});
 const fits=r.height<=bottom-top;
 return {id:el.id||el.className,top:Math.round(r.top),bottom:Math.round(r.bottom),band:[Math.round(top),Math.round(bottom)],inBand:fits?(r.top>=top-1&&r.bottom<=bottom+1):(r.top>=top-1&&r.top<bottom),
  focused:document.activeElement===el,ring:getComputedStyle(el).outlineStyle,scrollY:Math.round(scrollY),hash:location.hash}})()`;
const bar=`(()=>{const t=document.querySelector('.dock-toggle'),g=t.querySelector('.dock-gap'),b=document.querySelector('a[data-books-gap]');
 const lh=e=>{const cs=getComputedStyle(e);return Math.round(e.getBoundingClientRect().height/(parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.4))};
 const down=getComputedStyle(document.documentElement).getPropertyValue('--down').trim();const probe=document.createElement('i');probe.style.color=down;document.body.appendChild(probe);const want=getComputedStyle(probe).color;probe.remove();
 return {text:g&&g.textContent,color:g&&getComputedStyle(g).color===want,mark:g&&getComputedStyle(g,'::before').content,count:/still to count/.test(t.textContent),
  gapLines:g&&g.getClientRects().length?lh(g):0,button:b&&b.getClientRects().length?Math.round(b.getBoundingClientRect().height):0,label:b&&b.textContent.trim(),overflow:document.documentElement.scrollWidth>innerWidth}})()`;
const okRuns=`__runs.every(r=>r.keys.every(k=>['transform','opacity','boxShadow','x','y','scale'].includes(k)))`;

for(const width of (process.env.PN_WIDTHS||'320,390,1280').split(',').map(Number)){
 const A=await user('hana',width);
 await A.go(`/s/${OFF}/`);
 let b=await A.js(bar);
 if(width<900){
  check(`${width} the bar reads "₱100 missing" in Down, no mark, no "still to count"`,b.text==='₱100 missing'&&b.color&&(b.mark==='none'||b.mark==='normal')&&!b.count,b);
  // Folded: the short line and the main action, each on one line.
  await A.js(`localStorage.setItem('rack-dock','collapsed')`);await A.go(`/s/${OFF}/`);b=await A.js(bar);
  check(`${width} folded: "₱100 missing" on one line and the main action under it`,b.gapLines===1&&b.button>=48&&b.button<=56&&!b.overflow,b);
  await A.shot(`folded-${width}`);
  await A.js(`localStorage.setItem('rack-dock','open')`);await A.go(`/s/${OFF}/`);
 }
 check(`${width} the button names the difference`,b.label==='See the ₱100 difference',b);
 // The tap from the top of the page.
 await A.js(`scrollTo(0,0);__runs.length=0`);await A.tap('a[data-books-gap]');await sleep(1200);
 let p=await A.js(place);
 check(`${width} the tap brings the books into the band between the header and the bar`,p.inBand&&p.hash==='',p);
 check(`${width} the tap focuses the target with no outline`,p.focused&&p.ring==='none',p);
 const runs=await A.js('__runs');
 check(`${width} one Motion pulse on the ring, opacity only, and nothing else moved oddly`,runs.filter(r=>r.el==='gap-ring'&&r.keys.join()==='opacity').length===1&&await A.js(okRuns),runs);
 check(`${width} the ring is gone once it has faded`,await A.js(`!document.querySelector('.gap-ring')`));
 await A.shot(`tapped-${width}`);
 // Already in view: a second tap still answers.
 // "Where to look" open as the tap leaves it, then the panel is measured.
 await A.js(`(()=>{const w=document.querySelector('#live .discrepancy-where');if(w)w.open=true})()`);await sleep(100);
 const whole=await A.js(`(()=>{const b=document.getElementById('books-gap').getBoundingClientRect(),h=document.querySelector('.site-header').getBoundingClientRect().bottom,d=document.querySelector('.host-controls'),f=d&&getComputedStyle(d).position==='fixed'?d.getBoundingClientRect().top:innerHeight;return b.top>=h&&b.bottom<=f})()`);
 // The button may sit below the fold on a wide screen: bring it into view first, as a person would, then measure.
 await A.js(`(()=>{const e=document.querySelector('a[data-books-gap]'),f=e.getBoundingClientRect();if(f.top<0||f.bottom>innerHeight)e.scrollIntoView({block:'nearest'})})()`);await sleep(100);
 const whole2=await A.js(`(()=>{const b=document.getElementById('books-gap').getBoundingClientRect(),h=document.querySelector('.site-header').getBoundingClientRect().bottom,d=document.querySelector('.host-controls'),f=d&&getComputedStyle(d).position==='fixed'?d.getBoundingClientRect().top:innerHeight;return b.top>=h&&b.bottom<=f})()`);
 await A.js(`__runs.length=0`);const y0=await A.js('Math.round(scrollY)');await A.tap('a[data-books-gap]');await sleep(150);
 check(`${width} a second tap pulses again, and scrolls only if the panel is not wholly in view`,await A.js(`__runs.some(r=>r.el==='gap-ring')`)&&(!whole2||await A.js('Math.round(scrollY)')===y0),{whole,whole2,y0,y:await A.js('scrollY')});
 await A.shot(`pulse-${width}`);await sleep(600);
 // A suspect row, as the row agent will mark it, is preferred over the books.
 await A.js(`(()=>{const rows=document.querySelectorAll('#live .count-row');rows[rows.length-1].setAttribute('data-suspect','');scrollTo(0,document.documentElement.scrollHeight);__runs.length=0})()`);
 await sleep(200);await A.tap('a[data-books-gap]');await sleep(1200);p=await A.js(place);
 check(`${width} a row marked data-suspect is the target, in the band and focused`,/count-row/.test(p.id)&&p.inBand&&p.focused,p);
 check(`${width} no script error`,await A.js('__errors.length===0'),await A.js('__errors'));
 // The override's bar keeps its own verdict and has no such button.
 await A.go(`/s/${COVERED}/`);
 check(`${width} override: the bar keeps "covered by an override" and no difference button`,await A.js(`/covered by an override/.test(document.querySelector('.dock-toggle').textContent)&&!document.querySelector('.dock-gap')&&!document.querySelector('a[data-books-gap]')`));
}
// Reduced motion: the page jumps, the ring shows still, Motion runs nothing.
{const R=await user('hana',390,{reduce:true});await R.go(`/s/${OFF}/`);await R.js(`scrollTo(0,0);__runs.length=0`);
 await R.tap('a[data-books-gap]');await sleep(60);const p=await R.js(place);
 const ring=await R.js(`(()=>{const r=document.querySelector('.gap-ring');return r&&getComputedStyle(r).opacity})()`);
 check('reduced motion: the books are in the band at once, focused, the ring still, no Motion',p.inBand&&p.focused&&ring==='1'&&await R.js('__runs.length===0'),{p,ring});
 await R.shot('reduced-390');await sleep(1000);
 check('reduced motion: the ring is cleared after a moment',await R.js(`!document.querySelector('.gap-ring')`));}
// No JavaScript: the plain anchor leads to the books.
{const N=await user('hana',390,{noJs:true});await N.go(`/s/${OFF}/`);
 await N.tap('a[data-books-gap]');await sleep(500);
 const r=await send('Runtime.evaluate',{expression:`(()=>{const r=document.getElementById('balance').getBoundingClientRect();return {hash:location.hash,top:Math.round(r.top),y:scrollY}})()`,returnByValue:true},N.s);
 check('no JavaScript: the anchor goes to #balance',r.result.value.hash==='#balance'&&r.result.value.top>=0&&r.result.value.top<300,r.result.value);
 await N.shot('nojs-390');}
// No record explains the gap (set 9): the tap opens "Where to look", so it always shows something new.
{const W=await user('hana',390);await W.go(`/s/${OFF}/`);await W.js(`scrollTo(0,0)`);
 const before=await W.js(`document.querySelector('#live .discrepancy-where').open`);
 await W.tap('a[data-books-gap]');await sleep(700);
 check('no suspect: the tap opens Where to look',!before&&await W.js(`!document.querySelector('[data-suspect]')&&document.querySelector('#live .discrepancy-where').open`));}
console.log(`${results.filter(r=>r.ok).length}/${results.length} passed`);
chrome.kill();process.exit(results.every(r=>r.ok)?0:1);
