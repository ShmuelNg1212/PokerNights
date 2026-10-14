// Add players in one send: ticks and new names, the preview, "Tick … instead", the joint count,
// and the arrival on the set page. Seed a fresh temporary database with seed.py and
// seed_new_names.py, serve it on 127.0.0.1:8765, then run
//   node web/tests/browser/new_names.mjs 390        (also 1280; add "reduce" for reduced motion)
// It adds players, so use another fresh database for a repeat. See README.md.
import {spawn} from 'node:child_process';
import {writeFileSync, rmSync, mkdirSync, readFileSync} from 'node:fs';
const [W = '390', MOTION = 'motion'] = process.argv.slice(2);
const OUT = process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review'; mkdirSync(OUT, {recursive: true});
const BASE = process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765', PORT = 9341, PROFILE = '/private/tmp/pn-names-chrome';
const SET = JSON.parse(readFileSync('/private/tmp/pn-new-names-manifest.json', 'utf8')).set;
const sleep = ms => new Promise(r => setTimeout(r, ms));
rmSync(PROFILE, {recursive: true, force: true});
const chrome = spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`, '--no-first-run', '--disable-gpu', 'about:blank'], {stdio: 'ignore'});
let wsUrl; for (let i = 0; i < 60 && !wsUrl; i++) { try { wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl; } catch { await sleep(150); } }
const ws = new WebSocket(wsUrl); await new Promise(r => ws.onopen = r);
let id = 0; const wait = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait.has(m.id)) { const [ok, no] = wait.get(m.id); wait.delete(m.id); m.error ? no(Error(JSON.stringify(m.error))) : ok(m.result); } };
const send = (method, params = {}, sessionId) => new Promise((ok, no) => { wait.set(++id, [ok, no]); ws.send(JSON.stringify({id, method, params, sessionId})); });
const results = []; const check = (name, ok, detail) => { results.push(!!ok); console.log(`${ok ? 'PASS' : 'FAIL'} ${W}${MOTION === 'reduce' ? ' reduced' : ''} ${name}${ok || detail === undefined ? '' : ' :: ' + JSON.stringify(detail).slice(0, 400)}`); };
// Every animation started on the page is logged, so the arrival can be checked after it ran.
const LOG = `window.__moves=[];window.__errors=[];addEventListener('error',e=>__errors.push(e.message));const a=Element.prototype.animate;Element.prototype.animate=function(k,o){__moves.push({watch:this.dataset&&this.dataset.watch||'',tag:this.tagName,first:JSON.stringify(Array.isArray(k)?k[0]:k).slice(0,80)});return a.call(this,k,o)};`;
try {
  const {targetId} = await send('Target.createTarget', {url: 'about:blank'});
  const {sessionId: s} = await send('Target.attachToTarget', {targetId, flatten: true});
  await send('Page.enable', {}, s); await send('Runtime.enable', {}, s);
  await send('Emulation.setDeviceMetricsOverride', {width: +W, height: +W < 900 ? 844 : 800, deviceScaleFactor: 2, mobile: +W < 900}, s);
  if (MOTION === 'reduce') await send('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]}, s);
  await send('Page.addScriptToEvaluateOnNewDocument', {source: LOG}, s);
  const js = async expression => { const r = await send('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true}, s); if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; };
  const settle = async () => { await sleep(500); for (let i = 0; i < 40; i++) { if (await js('document.readyState') === 'complete') break; await sleep(100); } await sleep(300); };
  const go = async p => { await send('Page.navigate', {url: BASE + p}, s); await settle(); };
  const shot = async (name, full = true) => { const m = await send('Page.getLayoutMetrics', {}, s); const h = Math.ceil(m.cssContentSize.height); const {data} = await send('Page.captureScreenshot', full ? {format: 'png', captureBeyondViewport: true, clip: {x: 0, y: 0, width: +W, height: h, scale: 1}} : {format: 'png'}, s); writeFileSync(`${OUT}/names-${name}-${W}${MOTION === 'reduce' ? '-reduced' : ''}.png`, Buffer.from(data, 'base64')); };
  const type = text => js(`(()=>{const b=document.querySelector('[name=names]');b.value=${JSON.stringify(text)};b.dispatchEvent(new Event('input',{bubbles:true}));return [...document.querySelectorAll('[data-names-preview] li')].map(li=>li.textContent)})()`);
  const bar = `({summary:document.querySelector('[data-pick-summary]').textContent,button:document.querySelector('[data-pick-submit]').textContent,disabled:document.querySelector('[data-pick-submit]').disabled,warning:document.querySelector('[data-pick-warning]').hidden?'':document.querySelector('[data-pick-warning]').textContent})`;
  await go('/accounts/login/');
  await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`); await settle();
  const page = `/s/${SET}/players/add-several/`;
  await go(page);
  check('one form, one send button, the roster first', await js(`document.querySelectorAll('#main form[method=post]').length===1&&document.querySelectorAll('#main [type=submit]').length===1&&document.body.innerHTML.indexOf('Choose from the roster')<document.body.innerHTML.indexOf('New players')`));
  check('nothing chosen: the button waits', (await js(bar)).disabled);
  // The first frame of a new preview line is its first keyframe.
  const first = await js(`(()=>{const b=document.querySelector('[name=names]');b.value='Lia';b.dispatchEvent(new Event('input',{bubbles:true}));const li=document.querySelector('[data-names-preview] li');return {text:li.textContent,opacity:getComputedStyle(li).opacity}})()`);
  check('a new name is previewed as New', first.text === 'LiaNew', first);
  check(MOTION === 'reduce' ? 'reduced motion: the line is simply there' : 'motion: the line starts transparent and fades in', MOTION === 'reduce' ? first.opacity === '1' : first.opacity === '0', first);
  await sleep(400);
  check('the line settles with no inline style left', await js(`(()=>{const li=document.querySelector('[data-names-preview] li');return getComputedStyle(li).opacity==='1'&&!li.getAttribute('style')})()`));
  await type('Lia\n  Mo   Reyes  \n\n');
  let b = await js(bar);
  check('two names: counted and named on the button', b.summary === '2 new.' && b.button === 'Add 2 players' && !b.disabled && !b.warning, b);
  const lines = await type('Lia\ncarlo\nmiguel\nGone\nlia\n' + 'x'.repeat(61));
  check('each problem is named in the preview', JSON.stringify(lines) === JSON.stringify(['LiaNew', 'carloOn the rosterTick carlo instead', 'miguelAlready at the table', 'GoneRemoved from this group. Bring them back in Group settings', 'liaTyped twice', 'x'.repeat(61) + 'Too long: 60 characters at most']), lines);
  b = await js(bar);
  check('problems hold the button and say so', b.disabled && b.warning === '5 names need a change before adding.' && await js(`document.querySelector('[name=names]').getAttribute('aria-invalid')!==null`), b);
  await shot('problems');
  await type('Lia\ncarlo\nMo');
  await js(`[...document.querySelectorAll('[data-names-preview] button')].find(x=>x.textContent==='Tick carlo instead').click()`); await sleep(200);
  const ticked = await js(`(()=>{const box=document.querySelector('input[data-label=Carlo]');return {checked:box.checked,box:document.querySelector('[name=names]').value,mark:box.closest('label').classList.contains('just-changed'),lines:[...document.querySelectorAll('[data-names-preview] li')].length}})()`);
  b = await js(bar);
  check('"Tick … instead" ticks the player, takes the line out and marks the row', ticked.checked && ticked.box === 'Lia\nMo' && ticked.mark && ticked.lines === 2 && b.summary === '1 ticked · 2 new.' && b.button === 'Add 3 players' && !b.disabled, {ticked, b});
  await shot('ticked');
  const many = Array.from({length: 11}, (_, i) => 'New ' + (i + 1)).join('\n');
  await type(many);
  b = await js(bar);
  check('seats count the ticks and the names together', b.disabled && b.warning === 'Only 11 seats are free. Remove 1 player.', b);
  await type('Lia\nMo');
  check('no sideways scroll', await js(`document.documentElement.scrollWidth<=${W}`));
  await js(`window.__moves=[];document.querySelector('[data-pick-submit]').click()`); await settle();
  const landed = await js(`(()=>{const rows=[...document.querySelectorAll('.player-row')].filter(r=>/Carlo|Lia|Mo/.test(r.querySelector('.player-name')?.textContent||''));return {path:location.pathname,toast:document.body.textContent.includes('Added 3 players: Carlo, Lia, Mo.'),marked:rows.filter(r=>r.classList.contains('just-changed')).length,rows:rows.length,miguel:[...document.querySelectorAll('.player-row.just-changed')].some(r=>r.textContent.includes('Miguel')),moves:__moves.filter(m=>/^player-/.test(m.watch)).map(m=>m.first)}})()`);
  check('one send adds a ticked player and two new names', landed.path === `/s/${SET}/` && landed.toast && landed.rows === 3, landed);
  check('the three arrivals carry the brass mark, and no one else', landed.marked === 3 && !landed.miguel, landed);
  if (MOTION === 'reduce') check('reduced motion: the arrivals do not move', landed.moves.length === 0, landed.moves);
  else check('motion: the arrivals rise from 12px below, transparent', landed.moves.length >= 3 && landed.moves.every(f => f.includes('translateY(12px)') || f.includes('"opacity":[0')), landed.moves);
  await shot('arrived', false);
  await sleep(3300);
  check('the mark fades after three seconds and no inline style is left', await js(`!document.querySelector('.player-row.just-changed')&&[...document.querySelectorAll('.player-row')].every(r=>!r.style.opacity&&!r.style.transform)`));
  await go(`/s/${SET}/`);
  check('the next view marks no one', await js(`!document.querySelector('[data-arrived],.player-row.just-changed')`));
  await go(`/g/1/?view=settings`);
  check('the new names are on the roster', await js(`document.body.textContent.includes('Mo Reyes')||document.body.textContent.includes('Lia')`));
  check('no script error', (await js('__errors.length')) === 0, await js('__errors'));
} finally { await send('Browser.close').catch(() => {}); ws.close(); chrome.kill(); }
console.log(`${results.filter(Boolean).length} of ${results.length}`);
if (results.some(ok => !ok)) process.exitCode = 1;
