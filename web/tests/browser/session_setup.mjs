// Session setup: New session, the draft set, "More host controls", Set settings and Add players.
// Seed a fresh temporary database with seed.py and seed_setup.py, serve it on 127.0.0.1:8765, then run
//   node web/tests/browser/session_setup.mjs 390          (also 1280; add "reduce" for reduced motion)
// It creates two sessions, so use another fresh database for a repeat. See README.md.
import {spawn} from 'node:child_process';
import {writeFileSync, rmSync, mkdirSync} from 'node:fs';
const [W = '390', MOTION = 'motion'] = process.argv.slice(2);
const OUT = process.env.PN_REVIEW_DIR || '/private/tmp/pn-rack-review'; mkdirSync(OUT, {recursive: true});
const BASE = process.env.PN_BROWSER_URL || 'http://127.0.0.1:8765', PORT = 9341, PROFILE = '/private/tmp/pn-setup-chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
rmSync(PROFILE, {recursive: true, force: true});
const chrome = spawn(process.env.PN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`, '--no-first-run', '--disable-gpu', 'about:blank'], {stdio: 'ignore'});
let wsUrl; for (let i = 0; i < 60 && !wsUrl; i++) { try { wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl; } catch { await sleep(150); } }
const ws = new WebSocket(wsUrl); await new Promise(r => ws.onopen = r);
let id = 0; const wait = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait.has(m.id)) { const [ok, no] = wait.get(m.id); wait.delete(m.id); m.error ? no(Error(JSON.stringify(m.error))) : ok(m.result); } };
const send = (method, params = {}, sessionId) => new Promise((ok, no) => { wait.set(++id, [ok, no]); ws.send(JSON.stringify({id, method, params, sessionId})); });
const results = []; const check = (name, ok, detail) => { results.push(ok); console.log(`${ok ? 'PASS' : 'FAIL'} ${W} ${name}${ok || detail === undefined ? '' : ' :: ' + JSON.stringify(detail).slice(0, 400)}`); };
try {
  const {targetId} = await send('Target.createTarget', {url: 'about:blank'});
  const {sessionId: s} = await send('Target.attachToTarget', {targetId, flatten: true});
  await send('Page.enable', {}, s); await send('Runtime.enable', {}, s);
  await send('Emulation.setDeviceMetricsOverride', {width: +W, height: +W < 900 ? 844 : 800, deviceScaleFactor: 2, mobile: +W < 900}, s);
  if (MOTION !== 'motion') await send('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]}, s);
  const js = async expression => { const r = await send('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true}, s); if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; };
  const settle = async () => { await sleep(700); for (let i = 0; i < 40; i++) { if (await js('document.readyState') === 'complete') break; await sleep(100); } await sleep(400); };
  const go = async p => { await send('Page.navigate', {url: BASE + p}, s); await settle(); };
  const shot = async (name, full = true) => { const m = await send('Page.getLayoutMetrics', {}, s); const h = Math.ceil(m.cssContentSize.height); const {data} = await send('Page.captureScreenshot', full ? {format: 'png', captureBeyondViewport: true, clip: {x: 0, y: 0, width: +W, height: h, scale: 1}} : {format: 'png'}, s); writeFileSync(`${OUT}/setup-${name}-${W}.png`, Buffer.from(data, 'base64')); };
  const R = sel => `(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;const r=e.getBoundingClientRect();return {l:Math.round(r.left),t:Math.round(r.top+scrollY),r:Math.round(r.right),b:Math.round(r.bottom+scrollY),w:getComputedStyle(e).fontWeight,d:getComputedStyle(e).display}})()`;
  await go('/accounts/login/');
  await js(`document.querySelector('[name=username]').value='hana';document.querySelector('[name=password]').value='tablestakes-91';document.querySelector('form.form-section [type=submit]').click()`); await settle();
  // New session
  await go('/g/1/sessions/new/'); await shot('new-session');
  const title = await js(R('.preset-group .group-title')), when = await js(R('#group-when')), psel = await js(R('#preset')), rake = await js(R('.rake-settings legend')), game = await js(R('#group-game'));
  check('group titles share a weight', rake.w === game.w && title.w === game.w, {rake, game, title});
  check('preset → next title is the 41px group rhythm', when.t - psel.b === 41, when.t - psel.b);
  check('Use is hidden once the script runs', await js(`getComputedStyle(document.querySelector('.preset-group [type=submit]')).display==='none'`));
  check('preset select spans the column', psel.l === 16 + (+W >= 900 ? when.l - 16 : 0) && psel.r === when.r, {psel, when});
  check('rake Off: no amount field shows', await js(`[...document.querySelectorAll('.rake-settings .field')].every(f=>getComputedStyle(f).display==='none')`));
  const btn = await js(R('.form-groups > .btn-block')); const docH = await js('document.documentElement.scrollHeight');
  check('page ends 48px under the button', docH - btn.b === 48, docH - btn.b);
  // preset in place keeps typed fields
  await js(`document.querySelector('[name=location]').value="Hana's place";document.querySelector('[name=game_date]').value='2026-10-17';const p=document.querySelector('#preset');p.selectedIndex=1;p.dispatchEvent(new Event('change',{bubbles:true}))`); await sleep(300);
  const vals = await js(`(()=>{const f=document.querySelector('.form-groups');return {loc:f.location.value,date:f.game_date.value,unit:f.unit.value,sb:f.small_blind.value,bb:f.big_blind.value,min:f.min_buy_in.value,max:f.max_buy_in.value,def:f.default_buy_in.value,pid:f.preset_id.value,path:location.pathname+location.search}})()`);
  check('choosing a preset fills stakes and keeps typed fields', vals.loc === "Hana's place" && vals.date === '2026-10-17' && vals.unit === 'chips' && vals.sb === '25' && vals.max === '5000000' && vals.pid === await js(`document.querySelector('#preset').value`) && vals.path === '/g/1/sessions/new/', vals);
  await js(`document.querySelector('[name=rake_mode][value=flat]').click()`); await sleep(200);
  check('rake Flat: only the flat field shows', await js(`getComputedStyle(document.querySelector('[name=rake_flat]').closest('.field')).display!=='none'&&getComputedStyle(document.querySelector('[name=rake_percentage]').closest('.field')).display==='none'`));
  await shot('new-session-chips-flat');
  await js(`document.querySelector('[name=rake_mode][value=percent]').click();document.querySelector('[name=rake_percentage]').value='250';document.querySelector('.form-groups').noValidate=true;document.querySelector('.form-groups [type=submit]').click()`); await settle();
  check('a refused percentage shows its field and message', await js(`location.pathname==='/g/1/sessions/new/'&&getComputedStyle(document.querySelector('[name=rake_percentage]').closest('.field')).display!=='none'&&!!document.querySelector('[name=rake_percentage]').closest('.field').querySelector('.errors')`));
  await shot('new-session-error');
  await js(`document.querySelector('[name=rake_mode][value=off]').click();document.querySelector('.form-groups [type=submit]').click()`); await settle();
  const setPath = await js('location.pathname'); check('the session is created with the chips preset', /^\/s\/\d+\/$/.test(setPath) && (await js(`document.body.textContent.includes('1,000,000 chips')`)), setPath);
  await shot('set-draft-chips');
  // Draft set (pesos one made earlier by the seed is not a draft; make another)
  await go('/g/1/sessions/new/'); await js(`document.querySelector('.form-groups [type=submit]').click()`); await settle();
  const draft = await js('location.pathname'); await shot('set-draft');
  const facts = await js(`[...document.querySelectorAll('.prep-line .fact')].map(e=>{const r=e.getClientRects();return r.length})`);
  check('no fact of the stakes line breaks inside', facts.length === 3 && facts.every(n => n === 1), facts);
  const ends = await js(`[...document.querySelectorAll('.prep-step .btn')].map(e=>Math.round(e.getBoundingClientRect().left))`);
  check('step buttons start at one place', new Set(ends).size === 1 && ends.length >= 2, ends);
  check('step 2 says Change', await js(`document.querySelector('[data-step=stakes] .btn').textContent.trim()==='Change'`));
  check('host sees no second "No players yet"', await js(`!document.body.textContent.includes('No players yet')`));
  if (+W < 900) { const t = await js(R('.dock-toggle .dock-title')), i = await js(R('.dock-toggle .icon')); check('dock arrow centred on the title', Math.abs((t.t + t.b) / 2 - (i.t + i.b) / 2) <= 1, {t, i}); }
  // Flyout
  const state = `(()=>{const m=document.querySelector('.host-more'),d=m.closest('.host-controls');return {open:m.open,anims:document.getAnimations().filter(a=>d.contains(a.effect.target)).length,dockT:Math.round(d.getBoundingClientRect().top),tf:getComputedStyle(d).transform}})()`;
  const before = await js(state);
  await js(`document.querySelector('.host-more > summary').click()`); await sleep(60); const mid = await js(state); if (MOTION === 'motion') await shot('flyout-mid', false);
  await sleep(700); const opened = await js(state); await shot('more-open', false);
  await js(`document.querySelector('.host-more > summary').click()`); await sleep(60); const midClose = await js(state); await sleep(500); const closed = await js(state);
  if (MOTION === 'motion') {
    check('flyout: opens with motion and settles clean', mid.open && mid.anims > 0 && opened.open && opened.anims === 0 && opened.tf === 'none', {before, mid, opened});
    check('flyout: stays rendered while closing, then closes clean', midClose.open && midClose.anims > 0 && !closed.open && closed.anims === 0 && closed.dockT === before.dockT, {midClose, closed, before});
    // a tap during the flight turns it round; a keyboard press works the same
    await js(`document.querySelector('.host-more > summary').click()`); await sleep(40); await js(`document.querySelector('.host-more > summary').click()`); await sleep(600);
    check('flyout: a second tap mid-flight closes it', !(await js(state)).open, await js(state));
  } else {
    check('reduced motion: opens and closes at once', mid.open && mid.anims === 0 && !midClose.open && midClose.anims === 0, {mid, midClose});
  }
  await go(draft + 'settings/'); await shot('set-settings');
  await go(draft + 'players/add-several/'); await shot('add-players');
  const rows = await js(`[...document.querySelectorAll('[data-pick-row]')].slice(0,3).map(e=>Math.round(e.getBoundingClientRect().height))`);
  check('roster rows are one 48px line (+ rule)', rows.every(h => h >= 48 && h <= 49), rows);
  check('roster is first; one primary button', await js(`document.body.innerHTML.indexOf('Choose from the roster')<document.body.innerHTML.indexOf('New players')&&document.querySelectorAll('#main .btn-primary').length===1`));
  check('no page overflows sideways', await js(`document.documentElement.scrollWidth<=${W}`));
} finally { await send('Browser.close').catch(() => {}); ws.close(); chrome.kill(); }
console.log(`${results.filter(Boolean).length} of ${results.length}`);
if (results.some(ok => !ok)) process.exitCode = 1;
