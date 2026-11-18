// Sheet drag and the iPhone haptics path in WebKit, through Playwright (see README: install it outside the
// repository). Seed a fresh temporary SQLite database with seed_sheet_drag.py alone, start Django on
// 127.0.0.1:8765 with it, then run with PN_PLAYWRIGHT and PLAYWRIGHT_BROWSERS_PATH set.
// Playwright has no touch-move input, and WebKit has no Touch constructor, so the drags are synthetic
// touch events (an Event with a touches list) on the sheet: sheets.js reads them as it would a finger,
// but they do not scroll anything. WebKit has the switch input and no
// navigator.vibrate, so haptics.js takes its real iPhone path here.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const {webkit}=await import(`${process.env.PN_PLAYWRIGHT || '/private/tmp/pn-browser-tools/node_modules/playwright'}/index.mjs`);
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-drag-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const IDS=JSON.parse(readFileSync(process.env.PN_MANIFEST || '/private/tmp/pn-drag-manifest.json','utf8'));
const results=[];const check=(name,ok,detail='')=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||!detail?'':' — '+detail}`)};
const browser=await webkit.launch();
try {
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
 await context.addInitScript(()=>{window.__ticks=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));
  addEventListener('click',e=>{if(e.target.matches&&e.target.matches('label[data-haptic]'))__ticks.push(Math.round(performance.now()))},true)});
 const page=await context.newPage();
 await page.goto(BASE+'/accounts/login/');await page.fill('[name=username]','hana');await page.fill('[name=password]','tablestakes-91');
 await page.click('form.form-section [type=submit]');await page.waitForTimeout(900);
 await page.evaluate(()=>{localStorage.setItem('rack-dock','open');localStorage.setItem('rack-install','done')});
 await page.goto(`${BASE}/s/${IDS.play}/`);await page.waitForTimeout(600);
 // In the page: a drag of dy px from an element, in steps; returns the sheet's offset before the lift.
 const DRAG=`window.__drag=async function(el,dy,o){o=o||{};const r=el.getBoundingClientRect(),x=r.left+Math.min(60,r.width/2),y=r.top+r.height/2,d=document.querySelector('dialog.sheet');
  const t=(yy)=>({identifier:1,target:el,clientX:x,clientY:yy,pageX:x,pageY:yy});const fire=(type,list)=>{const e=new Event(type,{bubbles:true,cancelable:true});Object.defineProperty(e,'touches',{value:list});el.dispatchEvent(e)};
  fire('touchstart',[t(y)]);const steps=o.steps||10;for(let i=1;i<=steps;i++){await new Promise(r=>setTimeout(r,(o.ms||300)/steps));fire('touchmove',[t(y+dy*i/steps)])}
  await new Promise(r=>setTimeout(r,o.hold===undefined?150:o.hold));const seen=new DOMMatrix(getComputedStyle(d).transform).m42;window.__during={overflow:getComputedStyle(d).overflowY,top:d.scrollTop};fire('touchend',[]);return seen}`;
 await page.addScriptTag({content:DRAG});
 const D=`document.querySelector('dialog.sheet')`,opener=`[...document.querySelectorAll('[data-sheet-open^=buy]')].find(b=>b.getClientRects().length)`;
 const ev=s=>page.evaluate(s);
 const openBuy=async()=>{await ev(`${opener}.click()`);await page.waitForTimeout(800)};
 check('webkit: haptics take the switch path',await ev(`pokerHaptics.can()&&!('vibrate' in navigator)&&('switch' in HTMLInputElement.prototype)`));
 check('webkit: the Vibration switch is shown',await ev(`!document.querySelector('[data-haptics-switch]').hidden`));
 await openBuy();
 check('webkit: grab handle, and no overscroll bounce of the content',await ev(`getComputedStyle(${D}.querySelector('.sheet-head'),'::before').width==='36px'&&getComputedStyle(${D}).overscrollBehaviorY==='none'`));
 let seen=await ev(`__drag(${D}.querySelector('.sheet-head h2'),60)`);await page.waitForTimeout(700);
 check('webkit: a drag follows the finger',Math.abs(seen-60)<=2,String(seen));
 check('webkit: while it is dragged, the content cannot scroll',await ev(`__during.overflow==='hidden'`)&&await ev(`getComputedStyle(${D}).overflowY==='auto'`),await ev(`JSON.stringify(__during)`));
 check('webkit: a short drag goes back, nothing inline',await ev(`${D}.open&&new DOMMatrix(getComputedStyle(${D}).transform).m42===0&&${D}.style.transform===''`));
 await ev(`__ticks.length=0`);
 seen=await ev(`__drag(${D}.querySelector('.sheet-head h2'),220)`);await page.waitForTimeout(700);
 check('webkit: a long drag closes, focus on the opener',seen>200&&await ev(`!${D}.open&&document.activeElement===${opener}`),String(seen));
 check('webkit: the drag ticked once on the switch',await ev(`__ticks.length`)===1,await ev(`JSON.stringify(__ticks)`));
 await openBuy();
 seen=await ev(`__drag(${D}.querySelector('.numpad-key[data-key="5"]'),120)`);await page.waitForTimeout(500);
 check('webkit: no drag from a number key',seen===0,String(seen));
 // The switch: focus, form values, the account menu.
 const before=await ev(`(()=>{const f=${D}.querySelector('[name=amount]');f.focus();f.value='300';return JSON.stringify([...new FormData(f.form)])})()`);
 await ev(`__ticks.length=0;pokerHaptics.play('tick')`);
 check('webkit: a tick keeps focus and form values',await ev(`document.activeElement===${D}.querySelector('[name=amount]')&&__ticks.length===1`)&&await ev(`JSON.stringify([...new FormData(${D}.querySelector('[name=amount]').form)])`)===before);
 check('webkit: the helper is in the sheet with no box',await ev(`(()=>{const h=document.querySelector('[data-haptic]');return ${D}.contains(h)&&h.getClientRects().length===0})()`));
 // Tab stays inside the sheet's own controls.
 const tabs=[];for(let i=0;i<12;i++){await page.keyboard.press('Tab');tabs.push(await ev(`!!document.activeElement.closest('[data-haptic]')`))}
 check('webkit: Tab never reaches the helper',!tabs.some(Boolean));
 await ev(`${D}.querySelector('.sheet-head button').click()`);await page.waitForTimeout(500);
 await ev(`document.querySelector('#account summary').click()`);await page.waitForTimeout(400);
 await ev(`document.querySelector('[data-haptics-switch]').click()`);await page.waitForTimeout(100);
 await ev(`__ticks.length=0;document.querySelector('[data-haptics-switch]').click()`);await page.waitForTimeout(200);
 check('webkit: switching on ticks and the menu stays open',await ev(`document.getElementById('account').open&&__ticks.length===1`));
 // The recap: a scrolled body does not drag.
 await page.goto(`${BASE}/n/${IDS.twelve}/`);await page.waitForTimeout(7000);
 await page.addScriptTag({content:DRAG});
 if(await ev(`!!${D}&&${D}.open`)){await ev(`${D}.querySelector('.sheet-head button').click()`);await page.waitForTimeout(500)}
 await ev(`document.querySelector('[data-sheet-open="recap"]').click()`);await page.waitForTimeout(900);
 await ev(`${D}.scrollTop=300`);
 seen=await ev(`__drag(${D}.querySelector('.sheet-body .recap')||${D}.querySelector('.sheet-body'),150)`);await page.waitForTimeout(400);
 check('webkit: a scrolled recap does not drag from its body',seen===0&&await ev(`${D}.open`),String(seen));
 await ev(`${D}.scrollTop=300`);const kept=await ev(`${D}.scrollTop`);
 seen=await ev(`__drag(${D}.querySelector('.sheet-head h2'),60)`);await page.waitForTimeout(700);
 check('webkit: a short head drag on a scrolled recap keeps its place in the text',seen>40&&await ev(`${D}.open&&${D}.scrollTop===${kept}&&__during.top===${kept}`),await ev(`JSON.stringify({now:${D}.scrollTop,during:__during,kept:${kept}})`));
 seen=await ev(`__drag(${D}.querySelector('.sheet-head h2'),220)`);await page.waitForTimeout(700);
 check('webkit: the recap head drags at any scroll and closes',seen>200&&await ev(`!${D}.open`),String(seen));
 check('webkit: no errors',await ev(`__errors.length===0`),await ev(`JSON.stringify(__errors)`));
} catch(error){console.error(error);check('probe ran to its end',false,String(error))}
finally {
 const failed=results.filter(r=>!r.ok).length;
 console.log(`${results.length-failed}/${results.length} checks passed`);
 writeFileSync(`${OUT}/webkit-results.json`,JSON.stringify(results,null,1));
 await browser.close();process.exit(failed?1:0);
}
