// Motion system, stage 3: motion between screens (turbo-setup.js, the last block of app.css). Seed a fresh
// temporary database with seed.py, serve it on 127.0.0.1:8765, then run. Every screen change the browser
// animates is recorded: the direction set on <html> when it began, the animations that ran, and how long it took.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
rmSync('/private/tmp/pn-screens-chrome',{recursive:true,force:true});
const chrome=spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9341','--user-data-dir=/private/tmp/pn-screens-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9341/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const LOG=`(()=>{window.__vt=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));
 const start=document.startViewTransition&&document.startViewTransition.bind(document);if(!start)return;
 document.startViewTransition=function(cb){const t=start(cb),rec={go:document.documentElement.dataset.go||'',t0:performance.now(),anims:[],ok:null};__vt.push(rec);
  t.ready.then(()=>{rec.anims=document.getAnimations().filter(a=>a.effect&&a.effect.pseudoElement&&a.effect.pseudoElement.startsWith('::view-transition')).map(a=>({p:a.effect.pseudoElement.replace('::view-transition-',''),n:a.animationName||'',d:Math.round(a.effect.getComputedTiming().endTime)}))},e=>{rec.ok=false;rec.err=String(e)});
  // Until the browser says the change has finished, its layers are still on screen: a marker removed before then restarts their animation.
  const watch=()=>{if(rec.ok!==null)return;if(rec.go&&document.documentElement.dataset.go!==rec.go)rec.lost=true;requestAnimationFrame(watch)};requestAnimationFrame(watch);
  t.finished.then(()=>{if(rec.go&&document.documentElement.dataset.go!==rec.go)rec.lost=true;rec.ms=Math.round(performance.now()-rec.t0);if(rec.ok===null)rec.ok=true});return t}})()`;
async function user(name,width=390,setup){const {browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:LOG},s);if(setup)await setup(s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,400));return r.result.value};
 const go=async path=>{await send('Page.navigate',{url:BASE+path},s);await sleep(500);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)}};
 const shot=async n=>{const{data}=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`${OUT}/${n}.png`,Buffer.from(data,'base64'))};
 // Taps a link (or runs any step) and waits for the screen change it causes to finish.
 const hop=async(step,name)=>{const n=await js('__vt.length'),at=await js('location.href');await js(step.startsWith('!')?step.slice(1):`document.querySelector(${JSON.stringify(step)}).click()`);
  let rec=null;for(let i=0;i<80;i++){await sleep(25);if(name&&i===3)await shot(name);rec=await js(`__vt.length>${n}&&__vt.at(-1).ok!==null?__vt.at(-1):null`);if(rec)break}
  if(!rec){for(let i=0;i<40&&await js('location.href')===at;i++)await sleep(50);await sleep(300)}
  await sleep(120);return {...(rec||{go:'',anims:[],none:true}),left:await js(`(document.documentElement.dataset.go||'')+document.querySelectorAll('[style*="view-transition-name"]').length`),path:await js('location.pathname+location.search')}};
 await go('/accounts/login/');await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(900);
 return {s,js,go,shot,hop};}
const results=[];const check=(name,ok,detail)=>{results.push({name,ok:!!ok});console.log(`${ok?'PASS':'FAIL'} ${name}${ok||detail===undefined?'':' :: '+JSON.stringify(detail).slice(0,500)}`)};
const ran=(r,p,n)=>r.anims.some(a=>a.p===p&&a.n===n);
const has=(r,p)=>r.anims.some(a=>a.p===p);
const deeper=r=>r.ok&&r.go==='deeper'&&ran(r,'old(root)','screen-out-left')&&ran(r,'new(root)','screen-in-right');
const back=r=>r.ok&&r.go==='back'&&ran(r,'old(root)','screen-out-right')&&ran(r,'new(root)','screen-in-left');
const plain=r=>r.ok&&r.go===''&&r.anims.filter(a=>a.p.endsWith('(root)')).every(a=>!a.n.startsWith('screen-'));
const quick=r=>r.anims.every(a=>a.d<=300);
const clean=r=>r.left==='0';
const still=r=>!has(r,'old(site-header)')&&!has(r,'new(site-header)');

async function walk(width){
 const W=`${width}px`,A=await user('hana',width);await A.go('/');const all=[];const step=async(...a)=>{const r=await A.hop(...a);all.push(r);return r};
 let r=await step('.group-home h2 a',`screens-deeper-${width}`);
 check(`${W} Your groups → group: deeper, the group's name is carried`,deeper(r)&&has(r,'group(title)')&&r.path==='/g/1/',r);
 check(`${W} the list has several sessions and one name holder`,await A.js(`document.querySelectorAll('a.session-link').length>1`)&&r.ok);
 r=await step('a.session-link');const night=r.path;
 check(`${W} group → session: deeper, the table name is carried from the row`,deeper(r)&&has(r,'group(title)')&&/^\/n\/\d+\/$/.test(night),r);
 r=await step('.night-page a[href^="/s/"]');
 check(`${W} session → set: deeper, the name stays in the heading`,deeper(r)&&has(r,'group(title)')&&/^\/s\/\d+\/$/.test(r.path),r);
 r=await step('a[href$="/log/"]');check(`${W} set → set log: deeper, nothing carried`,deeper(r)&&!has(r,'group(title)'),r);
 r=await step('#main a[href^="/s/"]');check(`${W} set log → set: back`,back(r),r);
 r=await step('.table-bar a');check(`${W} set → session: back, the name is carried`,back(r)&&has(r,'group(title)')&&r.path===night,r);
 r=await step('.table-bar a',`screens-back-${width}`);check(`${W} session → group: back, the name returns to its row`,back(r)&&has(r,'group(title)')&&r.path==='/g/1/',r);
 r=await step('.tabs a[href$="view=stats"]',`screens-tab-${width}`);
 check(`${W} Sessions → Stats: the content shifts, the marker slides, the heading and tab bar stay`,r.ok&&r.go==='next'&&ran(r,'new(root)','screen-in-right')&&has(r,'group(tab-current)')&&has(r,'group(tabs)')&&has(r,'group(page-heading)'),r);
 check(`${W} tabs: the marker is its own layer under the words, and each word is a layer that stays in place`,['tab-1','tab-2','tab-3'].every(n=>has(r,`group(${n})`))&&await A.js(`(()=>{const m=document.querySelector('.tabs a[aria-current] .tab-marker');return !!m&&m.textContent===''&&document.querySelectorAll('.tab-marker').length===1&&getComputedStyle(document.querySelector('.tabs a[aria-current]')).backgroundColor==='rgba(0, 0, 0, 0)'})()`),r);
 r=await step('.tabs a[href$="view=settings"]');check(`${W} Stats → Group settings: onward`,r.ok&&r.go==='next',r);
 r=await step('.tabs a:first-child');check(`${W} Group settings → Sessions: the other way`,r.ok&&r.go==='prev'&&ran(r,'new(root)','screen-in-left'),r);
 r=await step('.table-bar a');check(`${W} group → Your groups: back, the name returns to its card`,back(r)&&has(r,'group(title)')&&r.path==='/',r);
 r=await step('!history.back()');check(`${W} the phone's Back: the plain cross-fade`,plain(r)&&r.path==='/g/1/',r);
 r=await step('!history.forward()');check(`${W} the phone's Forward: the plain cross-fade`,plain(r)&&r.path==='/',r);
 check(`${W} the top bar never animates`,all.every(still),all.filter(x=>!still(x))[0]);
 check(`${W} every movement lasts 300ms or less (longest ${Math.max(...all.flatMap(x=>x.anims.map(a=>a.d)))}ms; slowest change ${Math.max(...all.map(x=>x.ms||0))}ms in all)`,all.every(quick));
 check(`${W} the direction stays until the browser has finished each change`,all.every(x=>!x.lost),all.filter(x=>x.lost)[0]);
 check(`${W} nothing is left on the page after any change`,all.every(clean),all.filter(x=>!clean(x))[0]);
 check(`${W} no change was cancelled and no script error`,all.every(x=>x.ok)&&await A.js(`__errors.length===0`),await A.js(`__errors`));
 return A;
}

try {
 const A=await walk(390);
 // A closed session's results and its set show the same players: their chips are carried.
 await A.go('/n/1/');let r=await A.hop(`!document.querySelector('.night-results').scrollIntoView();document.querySelector('.night-page a.set-link').click()`,'screens-chips-390');
 const chipGroups=r.anims.filter(a=>a.p.startsWith('group(chip-')).length;
 check(`session → set: players' chips are carried (${chipGroups})`,deeper(r)&&chipGroups>0&&clean(r),r);
 r=await A.hop('.table-bar a');check('set → session: the chips return',back(r)&&r.anims.some(a=>a.p.startsWith('group(chip-'))&&clean(r),r);
 // A tap during the movement is followed: the pointer reaches the new screen.
 await A.go('/');await A.js(`document.querySelector('.group-home h2 a').click()`);
 for(let i=0;i<60&&!await A.js(`location.pathname==='/g/1/'&&!!document.querySelector('.tabs')&&__vt.at(-1).ok===null`);i++)await sleep(10);
 const mid=await A.js(`__vt.at(-1).ok===null`);
 const p=await A.js(`(()=>{const b=document.querySelector('.tabs a[href$="view=settings"]').getBoundingClientRect();return {x:b.left+b.width/2,y:b.top+b.height/2}})()`);
 for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},A.s);
 for(let i=0;i<40&&!(await A.js(`location.search`)).includes('settings');i++)await sleep(50);
 check('a tap during the movement is followed',mid&&(await A.js(`location.search`)).includes('settings'),{mid,at:await A.js(`location.href`),hit:await A.js(`(()=>{const e=document.elementFromPoint(${p.x},${p.y});return e&&e.outerHTML.slice(0,80)})()`).catch(()=>null)});
 await sleep(600);
 // An action on the set page is not a screen change.
 await A.go('/s/3/');const n=await A.js(`__vt.length`);
 await A.js(`(()=>{[...document.querySelectorAll('[data-sheet-open^=buy]')].at(-1).click();const f=document.querySelector('dialog.sheet [name=amount]');f.value='500';f.form.requestSubmit(f.form.querySelector('[type=submit]'))})()`);await sleep(1500);
 check('an action on the set page sets no direction',await A.js(`__vt.slice(${n}).every(x=>x.go==='')&&!document.documentElement.dataset.go`));
 // Twenty changes leave nothing behind.
 await A.go('/');for(let i=0;i<10;i++){await A.hop('.group-home h2 a');await A.hop('.table-bar a')}
 check('twenty changes: no marker, no temporary name, no error',await A.js(`!document.documentElement.dataset.go&&document.querySelectorAll('[style*="view-transition-name"]').length===0&&__errors.length===0&&__vt.every(x=>x.ok)`));

 await walk(1280);

 // Reduced motion: screens change, nothing is directed or carried.
 const R=await user('hana',390,s=>send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},s));await R.go('/');
 r=await R.hop('.group-home h2 a');const r2=await R.hop('a.session-link');
 check('reduced motion: screens change with no direction, no carried name and no movement',r.path==='/g/1/'&&/^\/n\//.test(r2.path)&&[r,r2].every(x=>x.go===''&&!x.anims.some(a=>a.n.startsWith('screen-'))&&!has(x,'group(title)')&&clean(x)),[r,r2]);
 writeFileSync(`${OUT}/screens.json`,JSON.stringify(results,null,2));
} finally {await send('Browser.close');ws.close();chrome.kill()}
console.log(`${results.filter(x=>x.ok).length} of ${results.length}`);
if(results.some(x=>!x.ok))process.exitCode=1;
