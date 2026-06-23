const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");

test("all primary navigation views have matching panels", () => {
  const navViews = [...html.matchAll(/data-view="([^"]+)"/g)].map((match) => match[1]);
  const panels = [...html.matchAll(/data-view-panel="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual([...new Set(navViews)].sort(), [...new Set(panels)].sort());
});

test("view switching loads the data-heavy panels on demand", () => {
  assert.match(app, /if \(view === "cities"\) loadCities\(\)/);
  assert.match(app, /if \(view === "tools"\) loadTools\(\)/);
  assert.match(app, /if \(view === "trips"\) loadTrips\(\)/);
});

test("data-heavy panels render loading, empty, and error feedback", () => {
  assert.match(app, /function showToast/);
  assert.match(app, /function setStatus/);
  assert.match(app, /function emptyState/);
  assert.match(app, /function loadingCards/);
  assert.match(app, /catch \(error\)/);
});
