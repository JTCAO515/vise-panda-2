const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

test('tools view exists when navigate tools is supported', () => {
  const navMatches = html.match(/data-view="tools"/g) || [];
  assert.ok(navMatches.length >= 1);
  assert.match(html, /VP\.navigate\('tools'\)/);
  assert.match(html, /id="view-tools"/);
  assert.match(html, /id="tools-grid"/);
});
