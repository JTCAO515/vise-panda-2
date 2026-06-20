const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const appJs = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '..', 'app.css'), 'utf8');

test('auth trigger exposes stable modal hooks', () => {
  assert.match(html, /id="auth-btn"/);
  assert.match(html, /id="auth-modal-overlay"/);
  assert.match(appJs, /bindAuthTriggers/);
  assert.match(appJs, /safeInitStep/);
});

test('view shell exposes loading and error containers', () => {
  assert.match(html, /id="global-loading-state"/);
  assert.match(html, /id="global-error-state"/);
  assert.match(appJs, /showGlobalLoading/);
  assert.match(appJs, /showGlobalError/);
});

test('slow views expose dedicated loading and error shells', () => {
  assert.match(html, /id="cities-loading"/);
  assert.match(html, /id="cities-error"/);
  assert.match(html, /id="tools-loading"/);
  assert.match(html, /id="tools-error"/);
  assert.match(html, /id="trips-loading"/);
  assert.match(html, /id="trips-error"/);
  assert.match(html, /VP\.retryCurrentView\(\)/);
});

test('view state helpers and retry flow are wired in app runtime', () => {
  assert.match(appJs, /function setViewState\(view,\s*state,\s*message\s*=\s*''\)/);
  assert.match(appJs, /function retryCurrentView\(\)/);
  assert.match(appJs, /retryCurrentView,/);
  assert.match(appJs, /if \(view === 'trips'\) loadTrips\(\);/);
});

test('slow view loaders enter loading and error transitions', () => {
  assert.match(appJs, /setViewState\('cities',\s*'loading'\)/);
  assert.match(appJs, /setViewState\('cities',\s*'error',\s*'Could not load city data\.'\)/);
  assert.match(appJs, /setViewState\('tools',\s*'loading'\)/);
  assert.match(appJs, /setViewState\('tools',\s*'error',\s*'Could not load toolkit data\.'\)/);
  assert.match(appJs, /setViewState\('trips',\s*'loading'\)/);
  assert.match(appJs, /setViewState\('trips',\s*'error',\s*'Could not load saved trips\.'\)/);
});

test('view-level feedback styles exist', () => {
  assert.match(css, /\.view-state-shell\b/);
  assert.match(css, /\.view-loading\b/);
  assert.match(css, /\.view-error\b/);
});

test('image elements expose fallback hooks', () => {
  assert.match(html, /data-img-fallback/);
  assert.match(appJs, /attachImageFallbacks/);
  assert.match(css, /\.img-fallback\b/);
});

test('mobile nav uses explicit primary marker and safe-area visibility rules', () => {
  assert.match(html, /id="bottom-nav"/);
  assert.match(html, /data-mobile-nav="primary"/);
  assert.match(css, /--bottom-nav-safe/);
  assert.match(css, /@media\s*\(max-width:\s*640px\)/);
  assert.match(css, /#main\s*\{\s*padding-bottom:\s*calc\(var\(--bottom-nav-safe\)\s*\+\s*8px\)/);
  assert.match(css, /\.view\s*\{\s*padding-bottom:\s*calc\(var\(--bottom-nav-safe\)\s*\+\s*8px\)/);
  assert.match(css, /\.bottom-nav\s*\{\s*display:\s*flex;\s*visibility:\s*visible;\s*opacity:\s*1;\s*z-index:\s*220;/);
});
