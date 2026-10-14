// Renders doc/showcase/splash.html to the iPhone launch screens in static/splash/ with headless Chrome,
// one per size in config/pwa.py (SPLASH_SIZES; this list is a copy, and test_branding checks they agree).
// Run from the repository root after changing the page, the mark or the stylesheet's colours:
// node web/tests/browser/make_splash.mjs
// The images are cached for a week without a version tag: change the file names if the art changes,
// and say that people must add the app to the home screen again, because an iPhone reads them then.
import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const SIZES=[[375,667,2],[414,736,3],[375,812,3],[414,896,2],[414,896,3],[390,844,3],[428,926,3],[393,852,3],[430,932,3],[402,874,3],[440,956,3],[420,912,3]];
const page='file://'+resolve('doc/showcase/splash.html');
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9355','--user-data-dir=/private/tmp/pn-splash-chrome','--no-first-run','--disable-gpu','--allow-file-access-from-files','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9355/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
try{const{targetId}=await send('Target.createTarget',{url:'about:blank'});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);
 mkdirSync('static/splash',{recursive:true});
 for(const [w,h,r] of SIZES){await send('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:r,mobile:true},s);
  await send('Page.navigate',{url:page},s);await sleep(300);
  // The name is set in Archivo; a capture before the font arrives would show the fallback.
  const{result}=await send('Runtime.evaluate',{expression:'document.fonts.ready.then(()=>document.fonts.check("800 32px Archivo"))',awaitPromise:true,returnByValue:true},s);
  if(!result.value)throw Error('Archivo did not load for '+w+'x'+h);
  const{data}=await send('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:w,height:h,scale:1}},s);
  const name=`static/splash/splash-${w*r}x${h*r}.png`;writeFileSync(name,Buffer.from(data,'base64'));console.log('wrote '+name);}
}finally{await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
