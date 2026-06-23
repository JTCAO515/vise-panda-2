const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const css = fs.readFileSync(path.join(root, "app.css"), "utf8");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");

test("core layout uses stable responsive grids and bounded cards", () => {
  assert.match(css, /grid-template-columns: repeat\(auto-fill, minmax\(240px, 1fr\)\)/);
  assert.match(css, /min-height: 100dvh/);
  assert.match(css, /border-radius: 8px/);
  assert.doesNotMatch(css, /font-size:\s*[^;]*vw/);
});

test("overview remains available but Ask is the first screen", () => {
  assert.match(html, /id="quickPlanner"/);
  assert.match(html, /data-view-panel="dashboard"/);
  assert.match(html, /id="featuredCities"/);
  assert.match(html, /id="overviewButton"/);
  assert.match(html, /class="workspace section chat-hero"[^>]*id="panel-chat"/);
  assert.match(appJs(), /setView\("chat"\)/);
});

test("mobile portrait interaction shell has thumb-friendly controls", () => {
  assert.match(css, /\.nav\s*{[^}]*position: fixed/s);
  assert.match(css, /bottom: calc\(8px \+ env\(safe-area-inset-bottom\)\)/);
  assert.match(css, /grid-template-columns: repeat\(4, minmax\(0, 1fr\)\)/);
  assert.match(css, /\.city-strip\s*{[^}]*scroll-snap-type: x mandatory/s);
  assert.match(html, /data-prompt="Plan a first-time 7 day China route/);
});

test("v6.1.1 exposes mobile status surfaces", () => {
  assert.match(html, /id="cityStatus"/);
  assert.match(html, /id="toolStatus"/);
  assert.match(html, /id="tripStatus"/);
  assert.match(html, /id="toast"/);
  assert.match(css, /\.empty-state/);
  assert.match(css, /\.skeleton-card/);
  assert.match(css, /\.toast\.is-visible/);
  assert.match(css, /\.sheet-handle/);
});

test("v6.1.1 uses shared visual system tokens", () => {
  assert.match(css, /--surface:/);
  assert.match(css, /--focus-ring:/);
  assert.match(css, /--shadow-raised:/);
  assert.match(css, /\.city-card__facts/);
  assert.match(css, /\.trip-card__facts/);
  assert.match(html, /20260623-v611-responsive-qa2/);
  assert.match(css, /prefers-color-scheme: dark/);
});

test("v6.1.1 exposes professional chat controls progressively", () => {
  assert.match(html, /id="chatMode"/);
  assert.match(html, /id="chatProvider"/);
  assert.match(html, /id="chatDepth"/);
  assert.match(html, /data-mode="entry"/);
  assert.match(html, /data-depth="expert"/);
  assert.match(html, /class="chat-toolbar is-hidden"/);
  assert.match(html, /id="chatWelcome"/);
  assert.match(css, /\.chat-welcome/);
  assert.match(css, /\.preset-group/);
});

test("v6.1.1 exposes email verification and Google auth controls", () => {
  assert.match(html, /id="googleLogin"/);
  assert.match(html, /id="verifyForm"/);
  assert.match(html, /id="resendVerification"/);
  assert.doesNotMatch(html, /name="name" placeholder="Name"/);
  assert.match(appJs(), /\/api\/auth\/verify-email/);
  assert.match(appJs(), /\/api\/auth\/resend-verification/);
});

test("v6.1.1 makes mobile navigation behave like real app tabs", () => {
  assert.match(html, /role="tablist"/);
  assert.match(html, /id="tab-chat"[^>]*aria-selected="true"/);
  assert.doesNotMatch(html, /id="tab-dashboard"/);
  assert.match(html, /role="tabpanel" aria-labelledby="tab-chat"/);
  assert.match(css, /\.nav__item\.is-active::after/);
  assert.match(appJs(), /setAttribute\("aria-selected"/);
  assert.match(appJs(), /toggleAttribute\("hidden"/);
});

test("v6.1.1 strengthens the AI-first mobile planning surface", () => {
  assert.match(html, /class="home-snapshot"/);
  assert.match(html, /class="quick-chips"/);
  assert.match(css, /\.chat-hero/);
  assert.match(css, /\.agent-mark/);
  assert.match(html, /id="mobileAskButton"/);
  assert.match(css, /\.mobile-ask-fab/);
  assert.match(css, /bottom: calc\(92px \+ env\(safe-area-inset-bottom\)\)/);
  assert.match(appJs(), /mobileAskButton/);
});

test("v6.1.1 fixes verified AI-first responsive regressions", () => {
  assert.doesNotMatch(appJs(), /Use planner", \(\) => setView\("dashboard"\)/);
  assert.match(appJs(), /Ask AI", \(\) => setView\("chat"\)/);
  assert.match(appJs(), /is-chat-composing/);
  assert.match(css, /@media \(min-width: 1440px\)/);
  assert.match(css, /width: min\(1120px, calc\(100vw - 180px\)\)/);
  assert.match(css, /body\[data-view="chat"\]\.is-chat-composing \.nav/);
  assert.match(css, /\.chat-toolbar label:first-child/);
  assert.match(css, /\.chat-toolbar\s*{[^}]*overflow-x: auto/s);
  assert.match(appJs(), /window\.scrollTo\(\{ top: 0, behavior: "auto" \}\)/);
});

function appJs() {
  return fs.readFileSync(path.join(root, "app.js"), "utf8");
}
