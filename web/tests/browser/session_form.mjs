import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341',`--user-data-dir=/private/tmp/pn-form-chrome2`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
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

// Stakes forms: one field box, titled groups and pairs. Run after seed.py on a fresh temporary database.
const size=(A,width)=>send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},A.s);
const F=`document.querySelector('form.form-groups')`;
const boxes=`[...${F}.querySelectorAll('input[type=text],input[type=date],select')].filter(e=>!e.closest('.field-pair')).map(e=>{const r=e.getBoundingClientRect();return [Math.round(r.left),Math.round(r.right),Math.round(r.height)]})`;
const same=`(()=>{const b=${boxes};return b.length>0&&b.every(x=>x[0]===b[0][0]&&x[1]===b[0][1]&&x[2]===48)})()`;
const pairs=`[...${F}.querySelectorAll('.field-pair')].map(p=>[...p.querySelectorAll('input,select')].map(e=>{const r=e.getBoundingClientRect();return [Math.round(r.top),Math.round(r.left),Math.round(r.right),Math.round(r.height),p.classList.contains('field-pair-wide')?480:360]}))`;
const pairsAligned=width=>`(()=>{const edge=${boxes}[0];return ${pairs}.every(([a,b])=>a[3]===48&&b[3]===48&&(${width}<a[4]?(a[1]===edge[0]&&a[2]===edge[1]&&b[1]===edge[0]&&b[2]===edge[1]&&b[0]>a[0]):(a[0]===b[0]&&a[1]===edge[0]&&b[2]===edge[1]&&Math.abs((a[2]-a[1])-(b[2]-b[1]))<=1)))})()`;
const edgeItems=`(()=>{const edge=${boxes}[0][0];return [...${F}.querySelectorAll('input[type=radio],legend,.group-title,label:not(.check),.hint')].every(e=>Math.round(e.getBoundingClientRect().left)===edge||e.closest('.field-pair .field:last-child'))})()`;
const fill=`(()=>{const v={small_blind:'10',big_blind:'20',min_buy_in:'500',max_buy_in:'2000',default_buy_in:'1000'};for(const k in v)document.querySelector('[name='+k+']').value=v[k]})()`;
const PAGES=[['new','/g/1/sessions/new/',3],['settings','/s/4/settings/',2],['preset','/g/1/presets/new/',3]];
try {
 const A=await user('hana');
 for(const width of [320,390,1280])for(const [name,path,pairCount] of PAGES){await size(A,width);await A.go(path);const tag=`${name} ${width}`;
  check(tag+' fits',await A.js(`document.documentElement.scrollWidth<=${width}`));
  check(tag+' full-width fields share edges and 48px height',await A.js(same));
  check(tag+' pairs aligned',await A.js(`${pairs}.length===${pairCount}&&${pairsAligned(width)}`));
  check(tag+' radios, legends, labels and help on the field edge',await A.js(edgeItems));
  check(tag+' field text is 16px',await A.js(`[...${F}.querySelectorAll('input[type=text],input[type=date],select')].every(e=>getComputedStyle(e).fontSize==='16px')`));
  check(tag+' controls are 48px targets',await A.js(`[...${F}.querySelectorAll('input[type=text],input[type=date],select,label.check,button')].every(e=>e.getBoundingClientRect().height>=48)`));
  await A.shot(`form-${name}-${width}`);}
 await size(A,390);await A.go('/g/1/sessions/new/');
 check('date field is a native date input, left-aligned',await A.js(`(()=>{const d=document.querySelector('[name=game_date]');return d.type==='date'&&getComputedStyle(d).textAlign==='left'&&getComputedStyle(d).display==='block'&&d.value.length===10})()`));
 check('select has the app arrow and equal text inset',await A.js(`(()=>{const s=getComputedStyle(document.querySelector('[name=table_id]')),t=getComputedStyle(document.querySelector('[name=location]'));return s.backgroundImage.includes('svg')&&s.paddingLeft===t.paddingLeft&&s.appearance==='none'})()`));
 check('dropdown values are not cut off on a phone',await A.js(`[...${F}.querySelectorAll('select')].every(e=>{const c=document.createElement('canvas').getContext('2d');c.font=getComputedStyle(e).font;return c.measureText(e.selectedOptions[0].textContent).width<=e.clientWidth-56})`));
 check('four groups in order',await A.js(`JSON.stringify([...document.querySelectorAll('.group-title')].map(e=>e.textContent.trim()))===JSON.stringify(['When and where','Game','Stakes','Rake per buy-in'])`));
 // Keyboard order follows the visual order.
 await A.js(`document.querySelector('[name=table_id]').focus()`);const order=[];
 for(let i=0;i<16;i++){await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},A.s);const n=await A.js(`document.activeElement.name`);if(n!==order[order.length-1])order.push(n);}order.length=Math.min(order.length,10);console.log('  order',order.join(' '));
 check('keyboard order',JSON.stringify(order)===JSON.stringify(['game_date','location','game_type','unit','small_blind','big_blind','min_buy_in','max_buy_in','default_buy_in','rake_mode']));
 // One field of a pair refused: the partner input does not move.
 await A.go('/g/1/sessions/new/');await A.js(fill);await A.js(`${F}.noValidate=true;document.querySelector('[name=small_blind]').value='';document.querySelector('[name=max_buy_in]').value='x';document.querySelector('[name=game_date]').value=''`);await A.click(`${F}.querySelector('[type=submit]')`);
 for(const width of [320,390]){await size(A,width);
  check('refused pairs stay aligned '+width,await A.js(pairsAligned(width)));
  check('refused full-width fields keep edges '+width,await A.js(same));
  check('refused form fits '+width,await A.js(`document.documentElement.scrollWidth<=${width}`));await A.shot('form-new-error-'+width);}
 await size(A,390);
 check('each error sits in its own field, one id each',await A.js(`['game_date','small_blind','max_buy_in'].every(n=>document.querySelectorAll('#id_'+n+'_error').length===1&&document.querySelector('[name='+n+']').closest('.field').contains(document.querySelector('#id_'+n+'_error')))&&!document.querySelector('#id_big_blind_error')`));
 check('empty date keeps 48px',await A.js(`document.querySelector('[name=game_date]').value===''&&Math.round(document.querySelector('[name=game_date]').getBoundingClientRect().height)===48`));
 // Locked settings on a running set.
 await A.go('/s/3/settings/');check('locked unit and rake are disabled and aligned',await A.js(`document.querySelector('[name=unit]').disabled&&[...document.querySelectorAll('[name=rake_mode]')].every(r=>r.disabled)&&${same}`));await A.shot('form-settings-locked-390');
 // Without JavaScript: create a session through the native form.
 await send('Emulation.setScriptExecutionDisabled',{value:true},A.s);await A.go('/g/1/sessions/new/');
 await A.js(fill);await A.js(`document.querySelector('[name=location]').value='No script'`);await A.click(`${F}.querySelector('[type=submit]')`);
 check('no JavaScript: session created',await A.js(`/^\\/s\\/\\d+\\/$/.test(location.pathname)`));
 await send('Emulation.setScriptExecutionDisabled',{value:false},A.s);
 writeFileSync(`${OUT}/session_form.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
if(results.some(x=>!x.ok))process.exitCode=1;
