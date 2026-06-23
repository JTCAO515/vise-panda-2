const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.resolve(__dirname, "..", "app.js"), "utf8");

test("chat reads server-sent event tokens from a streaming response", () => {
  assert.match(app, /response\.body\.getReader\(\)/);
  assert.match(app, /line\.startsWith\("data:"\)/);
  assert.match(app, /payload\.token/);
});

test("chat inserts traveler text with textContent", () => {
  assert.match(app, /target\.textContent \+= payload\.token/);
  assert.match(app, /\.message__body", node\)\.textContent = text/);
});

test("chat protects streaming JSON parsing and sends auth header when available", () => {
  assert.match(app, /try\s*{\s*payload = JSON\.parse/s);
  assert.match(app, /headers\.Authorization = `Bearer \$\{state\.token\}`/);
  assert.match(app, /fetchWithTimeout\("\/api\/chat"/);
});
