const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

test('chat 主消息容器 id 唯一', () => {
  const matches = html.match(/id="chat-messages"/g) || [];
  assert.equal(matches.length, 1);
});

test('chat 历史查看器使用独立容器 id', () => {
  const matches = html.match(/id="chat-viewer-messages"/g) || [];
  assert.equal(matches.length, 1);
});
