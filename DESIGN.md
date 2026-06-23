# VisePanda Design System

Last updated: 2026-06-22
Current version: v6.0.8

## Design Direction

VisePanda should feel like a focused travel planning workspace for international visitors to China. The interface should be calm, practical, mobile-friendly, and trustworthy.

The current design direction is:

- English-native travel product
- Light sky-blue workspace
- Warm orange primary actions
- Clear app-style tabs
- Real destination imagery
- Compact mobile-first controls
- Professional AI assistant tone

Avoid returning to the older dark ink-wash visual system unless explicitly requested as a new brand exploration. The active product UI is now lighter and more utilitarian.

## Current Tokens

Current source of truth: `web/app.css`.

Important active colors:

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#eef8fc` | Page background |
| `--bg-elevated` | `#f8fcff` | Elevated background |
| `--surface` | `#ffffff` | Cards, controls, panels |
| `--surface-soft` | `#f3f9fc` | Soft sections |
| `--surface-tint` | `#dff4fb` | Selected tab / tint |
| `--text` | `#0f2633` | Primary text |
| `--text-muted` | `#486474` | Secondary text |
| `--border` | `#d4e6ee` | Default border |
| `--brand` | `#0ea5e9` | Sky-blue brand/action accent |
| `--brand-strong` | `#075985` | Strong brand text |
| `--accent` | `#f97316` | Primary CTA |
| `--accent-strong` | `#c2410c` | CTA hover |
| `--success` | `#2d8a63` | Success/check states |
| `--danger` | `#b42318` | Error states |

## Typography

Current font stack:

```css
"Plus Jakarta Sans", Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

Rules:

- Do not scale font sizes with viewport width.
- Keep letter spacing at `0` unless there is a clear local reason.
- Body text must stay readable on mobile.
- Buttons, tabs, inputs, status text, and chat controls need explicit, polished sizing.

## Shape and Spacing

Current radius:

```css
--radius: 8px;
```

Use 8px cards and controls by default. Mobile bottom nav uses a slightly larger shell radius for ergonomic separation.

Spacing rules:

- Mobile sides: about 14px.
- Desktop page sides: responsive clamp from 18px to 48px.
- Avoid nested cards.
- Use cards for repeated items, dialogs, and tool surfaces.
- Keep page sections as open bands or unframed layouts.

## Navigation

The primary nav has five tabs:

1. Plan
2. Ask
3. Cities
4. Tools
5. Trips

Desktop:

- Sticky below the topbar.
- Centered tab row.
- Active tab has sky tint and orange underline.

Mobile:

- Fixed bottom app-style tab bar.
- Five equally sized tab targets.
- Safe-area aware.
- Active state must be visually obvious.
- `aria-selected` must stay in sync with the active tab.

## Mobile UX Rules

Mobile portrait is a primary surface.

Required checks after UI changes:

- No horizontal overflow at 390px width.
- Bottom nav does not cover core controls.
- Chat input does not fight the bottom nav.
- Auth dialog acts like a bottom sheet.
- Floating Ask button hides in Ask view.
- Tap targets should be at least 44px where practical.

## Plan View

The Plan view is the first product screen.

It should show:

- Brand topbar
- Quick planning copy
- Prompt chips
- Destination/length planner
- Primary Ask AI CTA
- Entry / Route / Local snapshot cards
- Destination imagery
- Featured city cards
- Readiness checklist

The first screen should not become a marketing landing page. It must remain usable.

## Ask View

Ask is a professional AI consultation workspace.

It should show:

- Mode selector
- Provider/model route selector
- Depth selector
- Professional preset prompts
- Chat status surface
- Chat log
- Input composer

Chat messages should remain readable and structured. Avoid decorative chrome that reduces space for answers.

## Cities, Tools, Trips

Cities:

- Use real city imagery.
- Keep cards scannable.
- Search should remain prominent.

Tools:

- Cards should clearly describe practical use.
- Opened tool details should be readable and actionable.

Trips:

- Guest and synced states should be clear.
- Empty states should offer a useful next action.

## Auth Dialog

The auth dialog supports:

- Sign in
- Create account
- Verify email
- Resend code
- Optional Google login
- Profile update
- Logout

Mobile behavior:

- Bottom-sheet layout.
- Visible sheet handle.
- Inputs are full width.
- No name field during registration.

## Visual Asset Rules

- Use real travel imagery for cities and hero/supporting surfaces.
- Avoid dark blurred overlays.
- Avoid decorative blobs and one-note palettes.
- Keep product imagery inspectable.
- Do not use emoji as primary UI icons.
- Inline SVG icons are acceptable and currently used.

## Accessibility Rules

- Preserve semantic buttons and labels.
- Keep focus states visible.
- Keep color contrast strong.
- Preserve `role="tablist"`, `role="tab"`, `role="tabpanel"`, and `aria-selected`.
- Keep status text in live regions where already present.
- Respect `prefers-reduced-motion`.

## Cache and Release Rule

When CSS or JS changes, update:

- `web/index.html`
- `web/admin.html`
- `web/sw.js`
- `web/tests/stability-ui.test.js`

Current frontend cache marker:

```text
20260622-v608-mobile-ui3
```

Current service worker cache:

```text
visepanda-shell-v608-mobile-ui3
```
