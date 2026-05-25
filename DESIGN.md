---
version: alpha
name: VisePanda
description: AI China travel planner — deep Chinese ink-wash aesthetic meets modern dark UI.
colors:
  primary: "#0E0B14"
  secondary: "#1A1428"
  tertiary: "#0A0F17"
  accent: "#7DD3FC"
  accent2: "#BC3A2C"
  gold: "#C9A96E"
  bg0: "#05070B"
  text: "#EBEBED"
  muted: "#8A8A9A"
  surface: "rgba(255,255,255,.025)"
  line: "rgba(255,255,255,.07)"
typography:
  h1:
    fontFamily: "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', ui-sans-serif, system-ui, -apple-system"
    fontSize: 2.25rem
    fontWeight: 700
    letterSpacing: "-0.02em"
  h2:
    fontFamily: "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', ui-sans-serif, system-ui"
    fontSize: 1.25rem
    fontWeight: 650
  body:
    fontFamily: "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', ui-sans-serif"
    fontSize: 0.875rem
    lineHeight: 1.5
  sub:
    fontFamily: "ui-sans-serif, system-ui"
    fontSize: 0.75rem
    letterSpacing: "0.08em"
rounded:
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  full: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
components:
  header:
    backgroundColor: "rgba(10,8,16,.6)"
    height: "56px"
    padding: "0 16px"
    backdropFilter: "blur(12px)"
    borderBottom: "1px solid {colors.line}"
  logo-seal:
    backgroundColor: "linear-gradient(135deg, rgba(188,58,44,.08), rgba(188,58,44,.02))"
    border: "1.5px solid {colors.accent2}"
    rounded: "{rounded.sm}"
    width: "28px"
    height: "28px"
    transform: "rotate(-2deg)"
  btn-default:
    backgroundColor: "rgba(255,255,255,.03)"
    border: "1px solid {colors.line}"
    rounded: "{rounded.md}"
    padding: "7px 14px"
    textColor: "{colors.text}"
  btn-accent:
    backgroundColor: "rgba(125,211,252,.12)"
    border: "1px solid rgba(125,211,252,.35)"
    rounded: "{rounded.md}"
    padding: "7px 14px"
    textColor: "{colors.text}"
  btn-red:
    backgroundColor: "rgba(188,58,44,.14)"
    border: "1px solid rgba(188,58,44,.35)"
    rounded: "{rounded.md}"
    padding: "8px 24px"
    textColor: "{colors.text}"
  card:
    backgroundColor: "linear-gradient(160deg, rgba(255,255,255,.025), rgba(255,255,255,.005))"
    border: "1px solid {colors.line}"
    rounded: "{rounded.lg}"
    padding: "18px"
  card-hover:
    backgroundColor: "linear-gradient(160deg, rgba(255,255,255,.04), rgba(255,255,255,.01))"
    boxShadow: "0 8px 30px rgba(0,0,0,.3)"
    translateY: "-3px"
  chat-bubble-user:
    backgroundColor: "rgba(125,211,252,.10)"
    border: "1px solid rgba(125,211,252,.18)"
    rounded: "{rounded.xl}"
    maxWidth: "88%"
    padding: "10px 14px"
  chat-bubble-bot:
    backgroundColor: "rgba(255,255,255,.03)"
    border: "1px solid {colors.line}"
    rounded: "{rounded.xl}"
    maxWidth: "88%"
    padding: "10px 14px"
  send-btn:
    backgroundColor: "rgba(188,58,44,.14)"
    border: "1px solid rgba(188,58,44,.35)"
    rounded: "{rounded.md}"
    height: "44px"
    padding: "0 24px"
    textColor: "{colors.text}"
  profile-avatar:
    backgroundColor: "linear-gradient(135deg, rgba(188,58,44,.15), rgba(188,58,44,.04))"
    border: "2px solid rgba(188,58,44,.15)"
    rounded: "{rounded.full}"
    size: "64px"
  input:
    backgroundColor: "rgba(255,255,255,.03)"
    border: "1px solid {colors.line}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
    textColor: "{colors.text}"
  input-focus:
    borderColor: "rgba(125,211,252,.35)"
    boxShadow: "0 0 0 4px rgba(125,211,252,.08)"
---

## Overview

VisePanda is an AI-powered China travel planner with a distinctive visual identity combining:

- **Chinese ink-wash painting (水墨画)** — layered mountain silhouettes, drifting mist, and a subtle harvest moon as atmospheric background elements
- **Dark modern UI** — deep purple-black base (#0E0B14) with clean, minimal interface
- **Red seal accent** — cinnabar red (#BC3A2C) derived from traditional Chinese seal stamps (印章), used for primary CTAs
- **Gold accents** (#C9A96E) for cultural/navigation elements
- **Sky blue** (#7DD3FC) as tertiary travel accent for maps and secondary UI

## Colors

- **Primary (#0E0B14):** Deep purple-black — main canvas background
- **Accent (#BC3A2C):** 朱砂红 (cinnabar red) — CTAs, send button, seal logo, profile avatar
- **Gold (#C9A96E):** Navigation accents, Chinese subtitle text
- **Sky Blue (#7DD3FC):** Travel accent — chat bubbles, map UI, secondary borders, links
- **Moon glow:** Radial gradient from warm yellow-white (rgba(255,233,196,.04)) — inspired by the ink-wash moon

## Typography

Chinese-first stack: `Noto Sans SC → PingFang SC → Microsoft YaHei` for all UI text, with fallback to system sans-serif. Body text at 14px for readability. Small caps (11px, 0.08em letter-spacing) for Chinese subtitles.

## Layout & Spacing

- Max landing content width: 640px (96vw on mobile) centered
- Chat max-width: 800px centered
- Card grid: auto-fit columns, min 160px
- Mobile padding: 12px sides, safe-area-inset-bottom respected

## Elevation & Depth

Background uses 3 stacked ink-wash mountain silhouettes at opacities 0.008-0.016, blurred at 5px. A moon glow radial gradient adds warmth to the upper-right. Surface cards use subtle gradient backgrounds with hover elevation (translateY -3px + box-shadow).

## Shapes

Cards: 12px rounded. Buttons: 8px rounded (modern square-ish). Chat bubbles: 16px rounded. Input fields: 8px rounded. The logo seal is rotated -2deg for an organic stamp feel.

## Components

### Header
Fixed 56px with glassmorphism (rgba(10,8,16,.6) with 12px blur). Left side: red seal stamp square with 熊猫行 (Xiong Mao Xing / Panda Travel) in Songti serif. Right side: language toggle + sign-in/actions.

### Landing Cards
6 destination cards in responsive grid. Each card has gradient surface, subtle gold top-border on hover (gold 0.12 opacity), and a 3px lift animation.

### Chat
Clean chat interface with user bubbles (blue-tinted) and bot bubbles (neutral). Send button in cinnabar red. Welcome section with gold subtitle "AI 中国旅行规划". Quick-reply chips with neutral styling.

### Map
Leaflet dark theme overlay for itinerary visualization. 320px height container with border-radius 12px, visible when itinerary is detected.

## Do's and Don'ts

- DO use the seal-style logo on all pages for brand consistency
- DO keep ink-wash background as a subtle layer (max 0.2 opacity + 5px blur) — never make it compete with content
- DO use gold (#C9A96E) sparingly — titles and accents only
- DO use red (#BC3A2C) for the primary action button on every page
- DON'T make the UI feel "temple-like" or overly traditional — the Chinese elements should be atmospheric, not decorative
- DON'T use full-width Chinese text backgrounds
- DON'T use Chinese characters as primary navigation labels (keep them English with Chinese subtitles)
- DON'T use the red accent for every button — reserve for the primary CTA
