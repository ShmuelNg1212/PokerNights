// Renders static/branding/app-icon.svg to the PNG app icons with headless Chrome.
// Run from the repository root after changing the SVG: node web/tests/browser/make_icons.mjs
// Icons are cached for a week without a version tag: change the file names if the art changes.
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const svg=readFileSync('static/branding/app-icon.svg','utf8');
const SIZES=[['app-180.png',180],['app-192.png',192],['app-512.png',512],['app-maskable-512.png',512]];
const chrome=spawn(process.env.PN_CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9354','--user-data-dir=/private/tmp/pn-icons-chrome','--no-first-run','--disable-gpu','about:blank'],{stdio:'ignore'});
let url;for(let i=0;i<40&&!url;i++){try{url=(await(await fetch('http://127.0.0.1:9354/json/version')).json()).webSocketDebuggerUrl;}catch{await sleep(150)}}
const ws=new WebSocket(url);await new Promise(r=>ws.onopen=r);let id=0;const wait=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(wait.has(m.id)){const [ok,no]=wait.get(m.id);wait.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result)}};
const send=(method,params={},sessionId)=>new Promise((ok,no)=>{wait.set(++id,[ok,no]);ws.send(JSON.stringify({id,method,params,sessionId}))});
try{const{targetId}=await send('Target.createTarget',{url:'about:blank'});const{sessionId:s}=await send('Target.attachToTarget',{targetId,flatten:true});await send('Page.enable',{},s);
 mkdirSync('static/icons',{recursive:true});
 for(const [name,size] of SIZES){await send('Emulation.setDeviceMetricsOverride',{width:size,height:size,deviceScaleFactor:1,mobile:false},s);
  const page=`<!doctype html><html><body style="margin:0">${svg.replace('<svg ',`<svg width="${size}" height="${size}" style="display:block" `)}</body></html>`;
  await send('Page.navigate',{url:'data:text/html;charset=utf-8,'+encodeURIComponent(page)},s);await sleep(400);
  const{data}=await send('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:size,height:size,scale:1}},s);writeFileSync('static/icons/'+name,Buffer.from(data,'base64'));console.log('wrote static/icons/'+name);}
}finally{await send('Browser.close').catch(()=>{});ws.close();chrome.kill()}
