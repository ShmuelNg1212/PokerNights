// The in-app numpad. Run after seed.py on a fresh temporary database (set 3 is a running pesos set, set 5 a running chips set).
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-numpad-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9345','--user-data-dir=/private/tmp/pn-numpad-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9345/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
async function user(name){
 const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Network.enable',{},s);
 const js=async expression=>{let r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(450);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
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
const PESOS=3,CHIPS=5;
const D=`document.querySelector('dialog.sheet')`,F=`${D}.querySelector('[name=amount]')`,PAD=`document.querySelector('.numpad')`;
const key=k=>`${PAD}.querySelector('[data-key="${k}"]')`;
try {
 const A=await user('hana');
 const type=async keys=>{for(const k of keys)await A.tap(key(k))};
 const value=()=>A.js(`${F}.value`);
 const openBuy=async()=>{await A.tap(`document.querySelector('.buy-opener')`,700)};
 const closeSheet=async()=>{await A.js(`${D}.querySelector('.sheet-head button').click()`);await sleep(500)};

 // The page as a phone gets it.
 await A.go(`/s/${PESOS}/`);
 check('a finger is the main pointer in this run',await A.js(`matchMedia('(pointer: coarse)').matches`));
 check('the page turns the numpad on',await A.js(`document.documentElement.dataset.numpad==='on'&&!!window.pokerNumpad`));
 check('amount fields no longer call the phone keyboard',await A.js(`[...document.querySelectorAll('#live input[data-numpad]')].length>0&&[...document.querySelectorAll('#live input[data-numpad]')].every(f=>f.getAttribute('inputmode')==='none')`));
 check('text fields keep the phone keyboard',await A.js(`[...document.querySelectorAll('#live input[name=reason]')].every(f=>f.getAttribute('inputmode')!=='none')`));
 check('no keys are shown before a field is used',await A.js(`!${PAD}`));

 // Buy-in sheet.
 await openBuy();
 check('buy-in sheet: the keys are inside the sheet',await A.js(`!!${PAD}&&${D}.open&&${D}.contains(${PAD})`));
 check('buy-in sheet: twelve keys in a fixed order',await A.js(`[...${PAD}.querySelectorAll('.numpad-key')].map(k=>k.dataset.key).join()`)==='1,2,3,4,5,6,7,8,9,alt,0,del');
 check('buy-in sheet: every key is at least 48px high and 44px wide',await A.js(`[...${PAD}.querySelectorAll('.numpad-key')].every(k=>{const r=k.getBoundingClientRect();return r.height>=48&&r.width>=44})`));
 check('buy-in sheet: keys are 8px apart',await A.js(`(()=>{const k=[...${PAD}.querySelectorAll('.numpad-key')].map(e=>e.getBoundingClientRect());return Math.round(k[1].left-k[0].right)===8&&Math.round(k[3].top-k[0].bottom)===8})()`));
 check('buy-in sheet: pesos get a decimal point',await A.js(`${key('alt')}.textContent`)==='.');
 check('buy-in sheet: delete has a name',await A.js(`${key('del')}.getAttribute('aria-label')`)==='Delete');
 check('buy-in sheet: the amount has focus with its default selected',await A.js(`document.activeElement===${F}&&${F}.selectionStart===0&&${F}.selectionEnd===${F}.value.length&&${F}.value==='1000'`));
 check('buy-in sheet: fits the screen without scrolling at 390 by 844',await A.js(`${D}.scrollHeight<=${D}.clientHeight&&${D}.getBoundingClientRect().top>=0`));
 check('buy-in sheet: the confirm button is on screen',await A.js(`${D}.querySelector('[type=submit]').getBoundingClientRect().bottom<=innerHeight`));
 check('buy-in sheet: one help line',await A.js(`${D}.querySelectorAll('.hint').length`)===1);
 await sleep(400);await A.shot('numpad-buy-390');
 await A.js(`window.__inputs=0;${F}.addEventListener('input',()=>__inputs++)`);
 await type(['5']);
 check('the first key replaces the selected default',await value()==='5');
 await type(['0','0']);
 check('digits append',await value()==='500');
 check('each key sends one input event',await A.js(`__inputs`)===3);
 check('the field keeps focus while keys are tapped',await A.js(`document.activeElement===${F}`));
 await type(['alt','5','0']);
 check('a decimal point and two places',await value()==='500.50');
 await type(['9']);
 check('a third decimal place is refused',await value()==='500.50');
 await type(['alt']);
 check('a second decimal point is refused',await value()==='500.50');
 await A.down(key('alt'));await A.up();
 check('a refused key marks the field for a moment',await A.js(`${F}.classList.contains('numpad-refused')`));
 await sleep(400);
 check('the mark goes',await A.js(`!${F}.classList.contains('numpad-refused')`));
 await type(['del']);
 check('delete removes one character',await value()==='500.5');
 await A.down(key('del'));await sleep(700);await A.up();
 check('holding delete clears the amount',await value()==='');
 await type(['alt']);
 check('a decimal point on an empty amount becomes 0.',await value()==='0.');
 await type(['del','del','0','7']);
 check('a leading zero is dropped',await value()==='7');
 await type(['del','1','0','0','0','0','0','0','0','0','0']);
 check('one billion pesos is the largest amount',await value()==='1000000000');
 await type(['0']);
 check('a digit past the largest amount is refused',await value()==='1000000000');
 // The caret: a key writes where the caret is.
 await A.js(`${F}.value='1250';${F}.setSelectionRange(1,1)`);await type(['9']);
 check('a key writes at the caret',await value()==='19250'&&await A.js(`${F}.selectionStart`)===2);
 await type(['del']);
 check('delete removes before the caret',await value()==='1250');
 // Quick amounts still fill the field; a key then continues.
 await A.tap(`${D}.querySelector('[data-amount]')`);
 check('a quick amount fills the field and keeps the keys',await value()==='500'&&await A.js(`${D}.contains(${PAD})`));
 // A physical keyboard still types into the field.
 await A.js(`${F}.select()`);await send('Input.insertText',{text:'750'},A.s);
 check('a physical keyboard still types',await value()==='750');
 // A key reached without a pointer (keyboard, screen reader) acts once; a tap acts once.
 await A.js(`${F}.value=''`);await A.js(`${key('4')}.click()`);
 check('a key activated without a pointer writes once',await value()==='4');
 await A.tap(key('2'),200);
 check('a tap writes once',await value()==='42');
 // A refused amount keeps the sheet, the amount and the keys.
 await A.js(`${F}.value=''`);await type(['1']);await A.tap(`${D}.querySelector('[type=submit]')`,1500);
 check('a refused amount keeps the sheet, the amount and the keys',await A.js(`${D}.open&&!!${D}.querySelector('.sheet-error')&&${F}.value==='1'&&${D}.contains(${PAD})`));
 await A.shot('numpad-buy-refused-390');
 // An accepted amount closes the sheet and takes the keys away.
 const before=await A.js(`document.querySelector('.player-row .player-figure').firstChild.textContent.trim()`);
 await A.js(`${F}.select()`);await type(['1','5','0','0']);await A.tap(`${D}.querySelector('[type=submit]')`,1800);
 check('an accepted amount closes the sheet and removes the keys',await A.js(`!${D}.open&&!${PAD}`));
 const after=await A.js(`document.querySelector('.player-row .player-figure').firstChild.textContent.trim()`);
 check(`the typed amount was recorded (${before} to ${after})`,Number(after.replace(/[₱,]/g,''))-Number(before.replace(/[₱,]/g,''))===1500);
 check('the fresh amount field is served again',await A.js(`[...document.querySelectorAll('#live input[data-numpad]')].every(f=>f.getAttribute('inputmode')==='none')`));

 // Reopen: the keys come back, and closing mid-way leaves none behind.
 await openBuy();
 check('reopened sheet has the keys once',await A.js(`document.querySelectorAll('.numpad').length===1&&${D}.contains(${PAD})`));
 await closeSheet();
 check('closing the sheet removes the keys',await A.js(`!${PAD}`));

 // Small phones.
 await A.phone(375,667);await A.go(`/s/${PESOS}/`);await openBuy();
 check('buy-in sheet fits 375 by 667 without scrolling',await A.js(`${D}.scrollHeight<=${D}.clientHeight&&${D}.getBoundingClientRect().top>=0`));
 await sleep(400);await A.shot('numpad-buy-375');
 await A.phone(320,568);await A.go(`/s/${PESOS}/`);await openBuy();
 console.log('  320x568 sheet: client',await A.js(`${D}.clientHeight`),'scroll',await A.js(`${D}.scrollHeight`));
 check('buy-in sheet at 320 by 568: keys at least 48px, nothing wider than the screen',await A.js(`[...${PAD}.querySelectorAll('.numpad-key')].every(k=>k.getBoundingClientRect().height>=48)&&document.documentElement.scrollWidth<=320&&${D}.scrollWidth<=${D}.clientWidth`));
 check('buy-in sheet at 320 by 568: the confirm button can be reached',await A.js(`(()=>{const b=${D}.querySelector('[type=submit]');b.scrollIntoView({block:'nearest'});return b.getBoundingClientRect().bottom<=innerHeight})()`));
 await sleep(400);await A.shot('numpad-buy-320');
 await A.phone();

 // Cash-out sheet.
 await A.go(`/s/${PESOS}/`);await A.tap(`document.querySelector('.cash-opener')`,700);
 check('cash-out sheet: the keys are in the sheet',await A.js(`${D}.open&&${D}.contains(${PAD})&&document.activeElement===${F}`));
 await type(['2','5','0']);
 check('cash-out sheet: keys write the amount',await value()==='250');
 check('cash-out sheet: fits the screen',await A.js(`${D}.scrollHeight<=${D}.clientHeight`));
 check('cash-out sheet: amount, keys, option, then the action',await A.js(`(()=>{const y=el=>el.getBoundingClientRect().top;const f=${F},k=${PAD},c=${D}.querySelector('.check'),b=${D}.querySelector('[type=submit]');return y(f)<y(k)&&y(k)<y(c)&&y(c)<y(b)&&b.getBoundingClientRect().width>=k.getBoundingClientRect().width-1})()`));
 check('a tapped key returns to its resting colour',await A.js(`getComputedStyle(${key('0')}).backgroundColor===getComputedStyle(${key('7')}).backgroundColor`));
 await sleep(300);await A.shot('numpad-cash-390');
 await closeSheet();
 // Player details: text fields only, so the phone keyboard and no keys.
 await A.tap(`document.querySelector('.player-opener')`,700);
 check('details sheet: no keys for text fields',await A.js(`${D}.open&&!${PAD}`));
 check('details sheet: a reason field keeps the phone keyboard',await A.js(`[...${D}.querySelectorAll('input[name=reason]')].every(f=>f.getAttribute('inputmode')!=='none')`));
 await closeSheet();

 // Chips: no decimal point can be typed.
 await A.go(`/s/${CHIPS}/`);await openBuy();
 check('chips: the keys are in the sheet',await A.js(`${D}.contains(${PAD})`));
 check('chips: double zero takes the place of the decimal point',await A.js(`${key('alt')}.textContent`)==='00'&&await A.js(`${key('alt')}.getAttribute('aria-label')`)==='Double zero');
 await type(['1','alt']);
 check('chips: double zero writes two zeros',await value()==='100');
 await A.js(`${F}.value=''`);await type(['alt']);
 check('chips: double zero on an empty amount is 0',await value()==='0');
 await type(['5']);
 check('chips: no leading zero',await value()==='5');
 await sleep(300);await A.shot('numpad-buy-chips-390');
 await closeSheet();

 // A live update from another host leaves the open sheet, its amount and the keys alone.
 await A.go(`/s/${PESOS}/`);await openBuy();await type(['8','0','0']);
 const version=await A.js(`document.getElementById('live').dataset.version`);
 const B=await user('hana');await B.go(`/s/${PESOS}/`);
 await B.js(`(()=>{const f=[...document.querySelectorAll('form[action$="/buyins/add/"]')].pop();f.querySelector('[name=amount]').value='500';f.submit()})()`);await sleep(6500);
 check('a live update arrived under the open sheet',await A.js(`document.getElementById('live').dataset.version`)!==version);
 check('the open sheet keeps its amount and keys',await A.js(`${D}.open&&${F}.value==='800'&&${D}.contains(${PAD})`));
 await type(['5']);
 check('the keys still write after the update',await value()==='8005');
 await closeSheet();

 // Leaving the page takes the keys with it; coming back builds them once.
 await A.go(`/s/${PESOS}/`);await openBuy();await A.js(`Turbo.visit('/')`);await sleep(1000);
 check('leaving the page removes the keys',await A.js(`!${PAD}`));
 await A.js(`Turbo.visit('/s/${PESOS}/')`);await sleep(1200);await openBuy();
 check('back on the page: the keys once, and one write per tap',await A.js(`document.querySelectorAll('.numpad').length`)===1);
 await type(['3']);check('back on the page: one write per tap',await value()==='3');
 await closeSheet();

 // Reduced motion: a refused key marks the field without moving it.
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},A.s);
 await A.go(`/s/${CHIPS}/`);await openBuy();await A.js(`${F}.value='100000000000'`);await A.down(key('1'));await A.up();
 check('reduced motion: a refused key marks the field and nothing moves',await A.js(`${F}.classList.contains('numpad-refused')&&${F}.getAnimations().length===0&&${F}.value==='100000000000'`));
 await send('Emulation.setEmulatedMedia',{features:[]},A.s);
 await A.go(`/s/${PESOS}/`);await openBuy();await A.js(`${F}.value='5.55'`);await A.down(key('1'));await sleep(80); // Motion starts on the next frame
 check('with motion: a refused key nudges the field by transform only',await A.js(`${F}.getAnimations().length===1&&${F}.getAnimations()[0].effect.getKeyframes().every(k=>Object.keys(k).filter(p=>!['offset','easing','composite','computedOffset'].includes(p)).join()==='transform')`));
 await A.up();await closeSheet();

 // Fail safe: an error in the keys gives the phone keyboard back.
 await A.go(`/s/${PESOS}/`);await openBuy();
 await A.js(`window.__err=0;addEventListener('error',()=>__err++);${F}.dispatchEvent=()=>{throw new Error('numpad check: forced failure')}`);
 await A.tap(key('1'),200);
 check('an error removes the keys and gives the phone keyboard back',await A.js(`!${PAD}&&[...document.querySelectorAll('input[data-numpad]')].every(f=>f.getAttribute('inputmode')==='decimal')`));
 check('the error is reported, not swallowed',await A.js(`__err`)===1);
 await closeSheet();await openBuy();
 check('after an error the sheet still opens, with the phone keyboard',await A.js(`${D}.open&&!${PAD}&&${F}.getAttribute('inputmode')==='decimal'`));

 // Without the script nothing changes.
 await send('Network.setBlockedURLs',{urls:['*numpad.js*']},A.s);
 await A.go(`/s/${PESOS}/`);await openBuy();
 check('script blocked: the sheet opens with the phone keyboard and no keys',await A.js(`${D}.open&&!${PAD}&&${F}.getAttribute('inputmode')==='decimal'&&!window.pokerNumpad`));
 await send('Network.setBlockedURLs',{urls:[]},A.s);

 // A computer: no keys, the fields as before.
 await A.computer();await A.go(`/s/${PESOS}/`);
 check('computer: a mouse is the main pointer',await A.js(`!matchMedia('(pointer: coarse)').matches`));
 await A.js(`document.querySelector('.buy-opener').click()`);await sleep(700);
 check('computer: the sheet has no keys and the field is as before',await A.js(`${D}.open&&!${PAD}&&${F}.getAttribute('inputmode')==='decimal'`));
 await A.shot('numpad-buy-1280');
} catch(e) { check('run completed: '+e.message,false) } finally {
 const failed=results.filter(r=>!r.ok);console.log(`\n${results.length-failed.length}/${results.length} checks passed`);
 ws.close();chrome.kill();process.exitCode=failed.length?1:0;
}
