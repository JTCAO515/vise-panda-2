const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");

test("auth state uses session storage instead of persistent token storage", () => {
  assert.match(app, /sessionStorage\.getItem\("vp_token"\)/);
  assert.doesNotMatch(app, /localStorage\.getItem\("vp_token"\)/);
});

test("profile form requires current password field for password changes", () => {
  assert.match(html, /name="currentPassword"/);
  assert.match(app, /currentPassword/);
});
