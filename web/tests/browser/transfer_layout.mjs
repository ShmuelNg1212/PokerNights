// Real transfer layout and payment flow on fresh synthetic service fixtures.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-transfer-layout-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9356','--user-data-dir=/private/tmp/pn-transfer-layout-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9356/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)};await js("document.querySelector('dialog[open] .sheet-head button')?.click()");await sleep(250)};
 // A phone: a finger is the main pointer. A computer: a mouse.
 const phone=async(width=390,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:true},s);await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5},s)};
 const computer=async()=>{await send('Emulation.setTouchEmulationEnabled',{enabled:false},s);await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},s)};
 const point=async expr=>js(`(()=>{const el=${expr};el.scrollIntoView({block:'center'});const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
 const down=async expr=>{const p=await point(expr);await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]},s);return p};
 const up=async()=>{await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]},s)};
 const tap=async(expr,pause=40)=>{await down(expr);await up();await sleep(pause)};
 const shot=async name=>{await js('document.fonts.ready.then(()=>1)');const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${name}.png`,Buffer.from(data,'base64'))};
 await phone();
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,phone,computer,tap,down,up,shot};
}
const results=[];const check=(name,ok)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
const manifest=JSON.parse(readFileSync('/private/tmp/pn-transfer-layout-manifest.json'));
const metrics=`(()=>{
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
 return [...document.querySelectorAll('.transfer-row')].map(row=>{
  const parties=[...row.querySelectorAll('.transfer-party')];
  const amount=row.querySelector('.transfer-amount');
  const range=document.createRange();range.selectNodeContents(amount);
  const state=row.querySelector('.transfer-state');
  const button=row.querySelector('button');
  return {card:rect(row),parties:parties.map(p=>({name:rect(p.querySelector('strong')),chip:rect(p.querySelector('.chip'))})),
   amount:rect(amount),amountText:rect(range),amountLines:range.getClientRects().length,text:amount.textContent,state:rect(state),button:button&&rect(button),
   narrow:getComputedStyle(row.querySelector('.transfer-parties')).gridTemplateColumns.split(' ').length===1,
   paid:row.classList.contains('is-paid'),order:[...row.querySelectorAll('.transfer-party,.transfer-amount,.transfer-state,form')].map(e=>e.className||e.tagName)};
 })
})()`;
try {
 const A=await user('hana');
 const allMetrics=[];
 for(const fixture of ['mixed','large','chips-long']) {
  const night=manifest[fixture] || JSON.parse(readFileSync('/private/tmp/pn-slice3-manifest.json'))[fixture];
  for(const width of [320,390,768,900,1280]) {
   await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<900},A.s);
   await A.go(`/n/${night}/`);await A.js('document.fonts.ready.then(()=>1)');
   const rows=await A.js(metrics);allMetrics.push({fixture,width,rows});
   check(`${fixture} ${width}: cards exist`,rows.length===2);
   check(`${fixture} ${width}: reading order matches the DOM`,rows.every(r=>r.order.slice(0,2).every(c=>c==='transfer-party')&&r.order[2].startsWith('transfer-amount')&&r.order[3]==='small transfer-state'&&r.order[4]==='FORM'));
   await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);
   await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);
   check(`${fixture} ${width}: action has visible keyboard focus`,await A.js("(()=>{const b=document.querySelector('.transfer-row button');b.focus();return document.activeElement===b&&getComputedStyle(b).outlineStyle!=='none'})()"));
   check(`${fixture} ${width}: no horizontal overflow`,await A.js('document.documentElement.scrollWidth<=innerWidth'));
   check(`${fixture} ${width}: chips align to first name line`,rows.every(r=>r.parties.every(p=>Math.abs(p.name.y-p.chip.y)<=4.1)));
   check(`${fixture} ${width}: whole amount stays inside card`,rows.every(r=>r.amountText.right<=r.card.right-15&&r.amountText.x>=r.card.x+15&&r.amountLines===1));
   check(`${fixture} ${width}: actions at least 48px and right aligned`,rows.every(r=>r.button.height>=48&&r.button.width>=48&&Math.abs(r.button.right-(r.card.right-17))<1));
   check(`${fixture} ${width}: status below amount, action on assigned row`,rows.every(r=>r.state.y>=r.amount.bottom&&Math.abs(r.button.y-(r.narrow?r.state.y:r.amount.y))<1));
   check(`${fixture} ${width}: identity layout follows available width`,rows.every(r=>r.narrow?r.parties[1].chip.y>r.parties[0].name.bottom:r.parties[0].chip.y===r.parties[1].chip.y));
   if(fixture==='chips-long')check(`${fixture} ${width}: every digit and unit retained`,rows.every(r=>r.text==='9,999,999,999 chips'));
   if([390,900,1280].includes(width)) {
    await A.js(`document.querySelector('#transfers-title').scrollIntoView();scrollBy(0,-90)`);
    await A.shot(`transfers-${fixture}-${width}`);
   }
  }
 }
 writeFileSync(`${OUT}/transfer-metrics.json`,JSON.stringify(allMetrics,null,2));
 await A.computer();await A.go(`/n/${manifest['chips-long']}/`);
 // 1280 physical pixels at 200% desktop zoom: 640 CSS pixels, DPR 2.
 await send('Emulation.setDeviceMetricsOverride',{width:640,height:450,deviceScaleFactor:2,mobile:false},A.s);
 check('200% desktop reflow: no horizontal overflow',await A.js('document.documentElement.scrollWidth<=innerWidth'));
 check('200% desktop reflow: whole amount inside card',(await A.js(metrics)).every(r=>r.amountText.right<=r.card.right-15&&r.amountLines===1));
 await A.js(`document.querySelector('#transfers-title').scrollIntoView();scrollBy(0,-90)`);await A.shot('transfers-chips-zoom200');
 await A.go(`/n/${manifest.mixed}/`);
 const frozen=await A.js("document.querySelector('.night-results').textContent");
 const before=await A.js("document.querySelector('[data-still-to-pay]').dataset.stillToPay");
 await A.js("window.__transferDocument=document");
 await A.js("document.querySelector('.transfer-row:not(.is-paid) button').click()");await sleep(1100);
 check('Mark paid updates in place',await A.js('window.__transferDocument===document'));
 check('Mark paid clears the remaining total',await A.js("document.querySelector('[data-still-to-pay]').dataset.stillToPay==='0'"));
 check('Mark paid preserves frozen results',await A.js("document.querySelector('.night-results').textContent")===frozen);
 await A.js("document.querySelectorAll('.transfer-row button')[1].click()");await sleep(1100);
 check('Undo restores remaining total',await A.js("document.querySelector('[data-still-to-pay]').dataset.stillToPay")===before);
 check('Undo retains a reversed payment record',await A.js("!!document.querySelector('.payment-records .struck')"));
 check('Undo preserves frozen results',await A.js("document.querySelector('.night-results').textContent")===frozen);
 const B=await user('ben');await B.go(`/n/${manifest.mixed}/`);
 check('player sees transfer facts without host actions',await B.js("document.querySelectorAll('.transfer-row').length===2&&!document.querySelector('.transfer-row form')"));
 check('player has no empty action column',await B.js("[...document.querySelectorAll('.transfer-bottom')].every(e=>getComputedStyle(e).gridTemplateColumns.split(' ').length===1)"));
 await A.go(`/n/${manifest.archived}/`);
 check('archived transfers have no actions',await A.js("document.querySelectorAll('.transfer-row').length===2&&!document.querySelector('.transfer-row form')"));
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
 await A.go(`/n/${manifest.mixed}/`);
 check('reduced motion: transfer cards static',await A.js("[...document.querySelectorAll('.transfer-row')].every(e=>getComputedStyle(e).animationName==='none')"));
 await A.js("document.querySelector('.transfer-list').style.containerType='normal'");
 check('without container queries: safe stacked identities',(await A.js(metrics)).every(r=>r.narrow));
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);
 await A.go(`/n/${manifest.mixed}/`);
 await A.js("document.querySelector('.transfer-row:not(.is-paid) button').click()");await sleep(1000);
 check('native Mark paid works without JavaScript',await A.js("document.querySelector('[data-still-to-pay]').dataset.stillToPay==='0'"));
 await A.js("document.querySelectorAll('.transfer-row button')[1].click()");await sleep(1000);
 check('native Undo works without JavaScript',await A.js("document.querySelector('[data-still-to-pay]').dataset.stillToPay")===before);
} catch(e) {check('run completed: '+e.message,false)} finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
