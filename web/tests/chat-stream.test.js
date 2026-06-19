const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const appJs = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');

test('split 流程中的 typingId 可安全重赋值', () => {
  assert.match(appJs, /let typingId = addTyping\(\);/);
  assert.match(appJs, /typingId = newId;/);
  assert.doesNotMatch(appJs, /const typingId = addTyping\(\);/);
});
