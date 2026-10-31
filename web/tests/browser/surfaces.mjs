// Slice E of the UI revamp (doc/plan/1793431937_ui_revamp.md): captures each page and state, and measures frames,
// heads, type and contrast. Seed a fresh temporary database with seed.py, seed_end_set.py, seed_night.py,
// seed_remaining.py, seed_opening.py and seed_surfaces.py, serve it on 127.0.0.1:8765, run. It writes nothing.
// PN_SURFACES_REPORT=1 prints the figures and sets no exit code: the baseline run before the slice.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync,rmSync,readFileSync} from 'node:fs';
const OUT=process.env.PN_REVIEW_DIR||'/private/tmp/pn-surfaces-review';mkdirSync(OUT,{recursive:true});
const BASE=process.env.PN_BROWSER_URL||'http://127.0.0.1:8765';const REPORT=!!process.env.PN_SURFACES_REPORT;
const NIGHTS=JSON.parse(readFileSync('/private/tmp/pn-slice3-manifest.json','utf8'));
const OPENING=JSON.parse(readFileSync('/private/tmp/pn-opening-manifest.json','utf8'));
const EMPTY=JSON.parse(readFileSync('/private/tmp/pn-surfaces-manifest.json','utf8')).group;
const PROFILE='/private/tmp/pn-surfaces-chrome';rmSync(PROFILE,{recursive:true,force:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9463',`--user-data-dir=${PROFILE}`,'--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<60&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9463/json/version')).json()).webSocketDebuggerUrl}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&wait.has(m.id)){const[ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
const results=[];const check=(name,ok)=>{results.push({name,ok});console.log(`${ok?'PASS':'FAIL'} ${name}`)};
async function user(name,width=390){
 const{browserContextId}=await send('Target.createBrowserContext');const{targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});
 await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<900},s);
 const js=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails).slice(0,300));return r.result.value};
 const go=async p=>{await send('Page.navigate',{url:BASE+p},s);await sleep(600);for(let i=0;i<30;i++){if(await js('document.readyState')==='complete')break;await sleep(100)};await js(`document.querySelector('dialog[open]')?.close()`);await sleep(150)};
 const shot=async(n,full=false)=>{const params={format:'jpeg',quality:72};if(full)params.captureBeyondViewport=true;if(full){const{cssContentSize:c}=await send('Page.getLayoutMetrics',{},s);params.clip={x:0,y:0,width,height:Math.min(c.height,3200),scale:1}}const{data}=await send('Page.captureScreenshot',params,s);writeFileSync(`${OUT}/${n}.jpg`,Buffer.from(data,'base64'))};
 await go('/accounts/login/');await sleep(400);await js(`document.querySelector('[name=username]').value=${JSON.stringify(name)};document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`);await sleep(1300);
 await js(`document.querySelector('dialog[open]')?.close()`);
 return{js,go,shot,width,s,name};
}
// Text is read as drawn: a visible text node, its size, and its contrast against the first solid fill behind it.
const MEASURE=`(()=>{
 const ctx=document.createElement('canvas').getContext('2d',{willReadFrequently:true});
 const rgba=v=>{ctx.clearRect(0,0,1,1);ctx.fillStyle='#000';ctx.fillStyle=v;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data]};
 const lum=a=>{const f=a.slice(0,3).map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4});return .2126*f[0]+.7152*f[1]+.0722*f[2]};
 const shown=e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&e.getClientRects().length;
 const fill=e=>{for(let n=e;n;n=n.parentElement){const mark=n.querySelector&&n.querySelector(':scope > .pill-marker');if(mark)return rgba(getComputedStyle(mark).backgroundColor);const s=getComputedStyle(n);const c=rgba(s.backgroundColor);if(c[3]>200)return c;if(s.backgroundImage!=='none'&&n.matches('.felt:not(.hero),.felt:not(.hero) *'))return rgba(getComputedStyle(n).getPropertyValue('--felt-deep')||'#222')}return rgba(getComputedStyle(document.body).backgroundColor)};
 const main=document.querySelector('main')||document.body;const small=[],low=[],heads={};
 const w=document.createTreeWalker(main,NodeFilter.SHOW_TEXT);
 while(w.nextNode()){const t=w.currentNode;const words=t.textContent.trim();if(!words)continue;const e=t.parentElement;if(!shown(e)||e.closest('.chip,.sr-only,.visually-hidden,script,style,noscript,option,dialog:not([open]),summary.sr'))continue;const r=document.createRange();r.selectNodeContents(t);if(!r.getClientRects().length)continue;
  const s=getComputedStyle(e);const size=parseFloat(s.fontSize);if(size<13)small.push(size+'px '+(e.className||e.tagName).toString().slice(0,24)+': '+words.slice(0,28));
  const a=lum(rgba(s.color)),b=lum(fill(e));const ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);if(ratio<4.5&&!e.closest('[disabled],:disabled,.btn[aria-disabled=true]'))low.push(ratio.toFixed(2)+' '+(e.className||e.tagName).toString().slice(0,24)+': '+words.slice(0,28))}
 for(const h of main.querySelectorAll('h1,h2,h3,h4')){if(!shown(h))continue;const k=h.tagName+' '+getComputedStyle(h).fontSize;heads[k]=(heads[k]||0)+1}
 // A frame draws a box: a border on all four sides or a fill that differs from what lies behind it, with rounded corners. Controls and marks are no frames.
 const frames=[...main.querySelectorAll('*')].filter(e=>{if(!shown(e)||e.closest('button,.btn,input,select,textarea,.chip,.badge,svg,.toast,dialog:not([open])'))return false;if(e.matches('button,a.btn,input,select,textarea,label,summary,.pill,.tabs *'))return false;const s=getComputedStyle(e);const box=e.getBoundingClientRect();if(box.width<120||box.height<40)return false;const border=['Top','Right','Bottom','Left'].every(k=>parseFloat(s['border'+k+'Width'])>0&&rgba(s['border'+k+'Color'])[3]>0);const own=rgba(s.backgroundColor);const behind=e.parentElement?fill(e.parentElement):own;const filled=own[3]>200&&own.slice(0,3).join()!==behind.slice(0,3).join();return (border||filled)&&Math.max(...['TopLeft','TopRight','BottomLeft','BottomRight'].map(k=>parseFloat(s['border'+k+'Radius'])))>=6});
 const depth=e=>{let d=1,n=e.parentElement;while(n){if(frames.includes(n))d++;n=n.parentElement}return d};
 const deepest=frames.length?Math.max(...frames.map(depth)):0;const deep=frames.filter(f=>depth(f)>1).map(f=>(f.className||f.tagName).toString().slice(0,28));
 const header=document.querySelector('.site-header');const hb=header?header.getBoundingClientRect().bottom:0;const h1=[...document.querySelectorAll('main h1, h1')].find(shown);const tabs=document.querySelector('main .tabs');
 const range=h1&&document.createRange();if(range)range.selectNodeContents(h1);const backWords=(header&&header.querySelector('.table-bar a'))?header.querySelector('.table-bar a').textContent.trim().replace(/\\s+/g,' '):'';
 const allBtns=[...main.querySelectorAll('.btn,button.btn,a.btn')].filter(shown);const undersides=allBtns.filter(b=>!b.matches('.btn-primary')&&getComputedStyle(b).boxShadow!=='none').length;
 return{small:[...new Set(small)],low:[...new Set(low)],heads,frames:frames.length,deepest,deep:[...new Set(deep)],title:h1?h1.textContent.trim().replace(/\\s+/g,' ').slice(0,60):'',titleSize:h1?getComputedStyle(h1).fontSize:'',titleGap:range?Math.round(range.getBoundingClientRect().top-hb):null,back:backWords,tabsEnd:tabs?Math.round(tabs.getBoundingClientRect().bottom+scrollY):null,undersides,overflow:document.documentElement.scrollWidth>innerWidth,height:document.documentElement.scrollHeight};
})()`;
const host=[['home','/'],['group-sessions','/g/1/'],['group-players','/g/1/?view=players'],['group-stats','/g/1/?view=stats'],['group-settings','/g/1/?view=settings'],
 ['set-draft-empty','/s/4/'],['set-joining',`/s/${OPENING.default.set}/`],['set-in-play','/s/3/'],['set-counting','/s/2/'],['set-counting-chips','/s/6/'],['set-balanced','/s/8/'],['set-recount','/s/9/'],['set-final','/s/1/'],['set-large','/s/11/'],
 ['session-before-play',`/n/${OPENING.default.night}/`],['session-in-play','/n/3/'],['session-closed-partly',`/n/${NIGHTS.partly}/`],['session-closed-unpaid',`/n/${NIGHTS.unpaid}/`],['session-closed-settled',`/n/${NIGHTS.settled}/`],['session-ready',`/n/${NIGHTS.ready}/`],['session-two-sets',`/n/${NIGHTS['two-sets']}/`],
 ['set-log','/s/3/log/'],['form-new-session','/g/1/sessions/new/'],['form-set-settings',`/s/${OPENING.default.set}/settings/`],['form-add-players',`/s/${OPENING.default.set}/players/add-several/`],['form-chip-values',`/n/${OPENING.default.night}/chip-values/`]];
const player=[['player-home','/'],['player-group','/g/1/'],['player-set-in-play','/s/3/'],['player-set-final','/s/1/'],['player-session',`/n/${NIGHTS.partly}/`]];
const empty=[['nora',[['empty-home','/']]],['owen',[['empty-group',`/g/${EMPTY}/`],['empty-players',`/g/${EMPTY}/?view=players`],['empty-stats',`/g/${EMPTY}/?view=stats`],['empty-settings',`/g/${EMPTY}/?view=settings`],['empty-new-session',`/g/${EMPTY}/sessions/new/`]]],['pia',[['empty-player-group',`/g/${EMPTY}/`],['empty-player-stats',`/g/${EMPTY}/?view=stats`]]]];
const table=[];const rows={};
async function walk(U,list,prefix=''){for(const[name,path]of list){await U.go(path);const m=await U.js(MEASURE);m.name=prefix+name;rows[prefix+name]=m;table.push(m);await U.shot(prefix+name,true);await U.js(`document.querySelector('html').style.filter='brightness(.45)'`);if(U.width===390&&/^(group-sessions|set-joining|set-in-play|set-counting|session-closed-partly|group-settings)$/.test(name))await U.shot('dim-'+name);await U.js(`document.querySelector('html').style.filter=''`)}}
try{
 const H=await user('hana');await walk(H,host);
 await H.go('/g/1/?view=players');const path=await H.js(`[...document.querySelectorAll('a.roster-link')].find(a=>!a.textContent.includes('(you)')).getAttribute('href')`);await walk(H,[['player-page',path]]);
 const P=await user('ben');await walk(P,player);
 for(const[n,list]of empty){const U=await user(n);await walk(U,list)}
 const N=await user('hana',320);await walk(N,[['group-sessions','/g/1/'],['set-in-play','/s/3/'],['set-final','/s/1/'],['session-closed-partly',`/n/${NIGHTS.partly}/`]],'320-');
 const D=await user('hana',1280);await walk(D,[['group-sessions','/g/1/'],['set-in-play','/s/3/'],['session-closed-partly',`/n/${NIGHTS.partly}/`],['group-settings','/g/1/?view=settings']],'1280-');
 console.log('page | frames/deepest | title gap | tabs end | title | back');
 for(const m of table)console.log(`${m.name} | ${m.frames}/${m.deepest} | ${m.titleGap} | ${m.tabsEnd??'-'} | ${m.titleSize} ${m.title} | ${m.back}`);
 const small=[...new Set(table.flatMap(m=>m.small))].sort();const low=[...new Set(table.flatMap(m=>m.low))].sort();const heads={};for(const m of table)for(const k in m.heads)heads[k]=(heads[k]||0)+m.heads[k];
 console.log('\nunder 13px:',small.length);console.log(small.join('\n'));console.log('\nunder 4.5:1:',low.length);console.log(low.join('\n'));console.log('\nheadings:',JSON.stringify(heads));
 console.log('\nnested frames:');for(const m of table)if(m.deepest>1)console.log(m.name,m.deepest,m.deep.join(', '));
 console.log('\nsecondary buttons with an underside:',table.reduce((a,m)=>a+m.undersides,0));
 writeFileSync(`${OUT}/report.json`,JSON.stringify(table,null,1));
}catch(e){check(`the run finished: ${e.message}`,false)}
ws.close();chrome.kill();
const failed=results.filter(r=>!r.ok).length;console.log(`\n${results.length-failed} of ${results.length} checks passed`);process.exit(!REPORT&&failed?1:0);
