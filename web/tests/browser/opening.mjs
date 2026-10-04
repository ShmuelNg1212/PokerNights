import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-rack-chrome`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);
const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const go=async path=>{await send('Page.navigate',{url:(process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765')+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
const click=async expr=>{await js(expr+'.click()');await sleep(650)};
const shot=async name=>{await js('window.scrollTo(0,0)');await js('document.fonts.ready');const{cssContentSize:size}=await send('Page.getLayoutMetrics',{},s);const{data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
await go('/accounts/login/');if(name)await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section button').click()`);await sleep(650);
return {s,js,go,click,shot};}
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};

const M=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
try {
 const A=await user('hana');
 for(const width of [390,1280]) {
  await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
  await A.go('/s/'+M.default.set+'/');
  check('default checked '+width,await A.js(`document.querySelector('[name=opening_buy_ins]').checked && document.querySelector('[name=opening_buy_ins]').closest('form').textContent.includes('₱1,000')`));
  check('layout fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));
  check('checkbox label target '+width,await A.js(`document.querySelector('label[for=opening-buy-ins]').getBoundingClientRect().height>=48`));
  await A.js('window.scrollTo(0,document.body.scrollHeight)');
  check('last row clears dock '+width,await A.js(`(()=>{const row=document.querySelector('.player-list');const dock=document.querySelector('.host-controls');return ${width}>=900||row.getBoundingClientRect().bottom<=dock.getBoundingClientRect().top})()`));
  await A.shot('opening-'+width);
 }
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},A.s);
 await A.go('/s/'+M.chips.set+'/');await A.shot('opening-chips-390');
 check('chips exact guidance',await A.js(`document.querySelector('[name=opening_buy_ins]').closest('form').textContent.includes('1,000 chips')`));
 await A.go('/s/'+M.default.set+'/');
 const data=await A.js(`Object.fromEntries(new FormData(document.querySelector('[name=opening_buy_ins]').form))`);
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
 await A.click(`document.querySelector('button[value=start]')`);
 check('native start total',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('1,500')`));
 // Re-submit the exact native request; inspect observable totals after the redirect.
 await A.js(`const f=document.createElement('form');f.method='post';f.action='/s/${M.default.set}/transition/';for(const [k,v] of Object.entries(${JSON.stringify({...data,action:'start'})})){const i=document.createElement('input');i.name=k;i.value=v;f.append(i)}document.body.append(f);f.submit()`);await sleep(700);
 check('retry keeps total',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('1,500')`));
 await A.go('/s/'+M.default.set+'/log/');check('ordinary host records in log',await A.js(`document.querySelector('#buy-ins').nextElementSibling.textContent.includes('₱500')&&document.querySelector('#buy-ins').nextElementSibling.textContent.includes('₱1,000')&&document.querySelector('#buy-ins').nextElementSibling.textContent.includes('hana')`));
 await A.go('/s/'+M.default.set+'/');await A.click(`document.querySelector('button[value=end]')`);
 await A.go('/n/'+M.default.night+'/');await A.click(`document.querySelector('form[action$="/next-set/"] button')`);
 check('next set still money-free',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('₱0')`));
 await A.click(`document.querySelector('button[value=start]')`);
 check('next set fresh opening total',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('2,000')`));
 await A.go('/s/'+M.opt_out.set+'/');await A.js(`document.querySelector('[name=opening_buy_ins]').checked=false`);await A.click(`document.querySelector('button[value=start]')`);
 check('unchecked native start no money',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('₱0')`));
 await A.go('/s/'+M.chips.set+'/');await A.click(`document.querySelector('button[value=start]')`);
 check('chips opening total exact',await A.js(`document.querySelector('.split-labels > span:first-child b').textContent.includes('2,000 chips')`));
 writeFileSync(`${OUT}/opening.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
