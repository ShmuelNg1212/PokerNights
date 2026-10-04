import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-settled-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:(process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765')+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

// Settle status in the Past sessions list and the session top bar. Run after seed.py, seed_end_set.py and seed_night.py.
const size=(A,width)=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
const contrast=sel=>`(()=>{const c=document.createElement('canvas').getContext('2d');const rgb=v=>{c.fillStyle='#000';c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3)};const lum=([r,g,b])=>{const f=x=>{x/=255;return x<=.03928?x/12.92:((x+.055)/1.055)**2.4};return .2126*f(r)+.7152*f(g)+.0722*f(b)};const el=document.querySelector(${JSON.stringify(sel)});const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(getComputedStyle(document.body).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)})()`;
const rows=`[...document.querySelectorAll('[aria-labelledby=past-sessions] .session-link')]`;
try {
 const A=await user('hana'),P=await user('ben');
 for(const width of [320,390,1280]){await size(A,width);await A.go('/g/1/');
  check('list fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));
  check('rows are 48px targets '+width,await A.js(`${rows}.length>0&&${rows}.every(a=>a.getBoundingClientRect().height>=48)`));
  check('every row has one status badge '+width,await A.js(`${rows}.every(a=>a.querySelectorAll('.badge').length===1&&/^(Settled|Partly settled|Unsettled)$/.test(a.querySelector('.badge').textContent.trim()))`));
  check('badge stays inside its row '+width,await A.js(`${rows}.every(a=>a.querySelector('.badge').getBoundingClientRect().right<=a.getBoundingClientRect().right+1)`));
  await A.shot('settled-list-'+width);}
 await size(A,390);
 const seen=await A.js(`${rows}.map(a=>a.querySelector('.badge').textContent.trim())`);console.log('  statuses',JSON.stringify(seen));
 check('all three statuses appear in the fixture',['Settled','Partly settled','Unsettled'].every(s=>seen.includes(s)));
 check('settled rows carry a check and no amount',await A.js(`${rows}.filter(a=>a.querySelector('.badge').textContent.trim()==='Settled').every(a=>!!a.querySelector('.badge .icon')&&!a.textContent.includes('still to pay'))`));
 check('other rows carry the amount and no check',await A.js(`${rows}.filter(a=>a.querySelector('.badge').textContent.trim()!=='Settled').every(a=>!a.querySelector('.badge .icon')&&/still to pay/.test(a.textContent))`));
 check('heading counts the sessions not settled',await A.js(`(()=>{const n=${rows}.filter(a=>a.querySelector('.badge').textContent.trim()!=='Settled').length;return document.querySelector('#past-sessions').textContent.includes(n+' not settled')})()`));
 check('contrast settled badge',await A.js(contrast('.session-link .badge-good'))>=4.5);check('contrast warn badge',await A.js(contrast('.session-link .badge-warn'))>=4.5);check('contrast heading count',await A.js(contrast('.heading-count'))>=4.5);
 // The list and each session page agree.
 const list=await A.js(`${rows}.map(a=>[a.getAttribute('href'),a.querySelector('.badge').textContent.trim()])`);let agree=true;
 for(const [href,status] of list){await A.go(href);const bar=await A.js(`document.querySelector('.table-bar .badge').textContent.trim()`);if(bar!==status){agree=false;console.log('  mismatch',href,status,bar)}}
 check('top bar of every session matches its row',agree);
 // Marking the last transfer paid turns the row to Settled; undo turns it back.
 const partly=list.find(([,s])=>s==='Partly settled')[0];await A.go(partly);
 for(let i=0;i<12&&await A.js(`!!document.querySelector('form[action$="/paid/"] button')`);i++)await A.click(`document.querySelector('form[action$="/paid/"] button')`);
 check('top bar says Settled after the last paid mark',await A.js(`document.querySelector('.table-bar .badge').textContent.trim()==='Settled'&&!!document.querySelector('.table-bar .badge .icon')`));await A.shot('settled-night-390');
 await A.go('/g/1/');check('row turns Settled',await A.js(`document.querySelector('a.session-link[href="${partly}"] .badge').textContent.trim()==='Settled'`));
 await A.go(partly);await A.click(`document.querySelector('form[action$="/unpaid/"] button')`);await A.go('/g/1/');
 check('row returns to Partly settled after undo',await A.js(`document.querySelector('a.session-link[href="${partly}"] .badge').textContent.trim()==='Partly settled'`));
 await P.go('/g/1/');check('player sees the statuses',await P.js(`${rows}.length>0&&${rows}.every(a=>a.querySelectorAll('.badge').length===1)`));
 await size(A,1280);await A.go(partly);await A.shot('settled-night-1280');
 writeFileSync(`${OUT}/settled.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
