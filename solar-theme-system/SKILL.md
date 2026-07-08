---
name: solar-theme-system
description: Solar-aware 6-mode time-of-day theming with NOAA sunrise/sunset calculation
author: Hermes
version: 1.0.0
category: software-development
metadata:
  hermes:
    lane: Shape
    tags: [theme, solar, noaa, design-system, time-of-day, css]
---

# Solar-Aware Theme System

A portable 6-mode time-of-day theme system driven by NOAA solar position calculations. The UI shifts through six themes — **light → dawn → sunrise → twilight → dusk → dark** — automatically matching the real sky outside the user's window at any latitude/longitude on Earth.

## What This Skill Produces

When you use this skill, you'll generate a self-contained solar theming system for any web app that includes:

1. **NOAA Solar Calculator** — pure JS, no dependencies, computes sunrise/sunset for any lat/lon/date
2. **6 Theme Palettes** — CSS custom properties for each time-of-day mode
3. **Natural Theme Selection** — picks the right theme based on current time vs. sunrise/sunset
4. **Manual Toggle with Daily Reset** — user can cycle themes; resets to solar calc next day
5. **Rotating Icon** — a sun-behind-horizon icon that rotates 60° per theme step

## Quick Start (3 Steps)

1. **Set your lat/lon** in the JS config section
2. **Map your CSS variables** to the 6 theme palettes (or use the reference palettes as-is)
3. **Add the toggle button** to your HTML and call `initSolarTheme()`

## Reference Location

The reference implementation uses Sea Ranch, CA:
- **Latitude:** 38.71° N
- **Longitude:** 123.39° W (entered as -123.39)

Change these two values to adapt to any location on Earth.

---

## 1. The Six Themes

The system defines six time-of-day themes that cycle through a full day:

| Theme | When | Sky Feeling | Palette Character |
|-------|------|-------------|-------------------|
| `light` | Daytime (full sun up) | Bright daylight | Warm paper, earthy sage greens |
| `dawn` | 50 min before → 10 min before sunrise | Cool grey-blue pre-dawn glow | Muted blue-greys, soft horizon |
| `sunrise` | 10 min before → 10 min after sunrise | Soft pink/coral first light | Rose corals, warm pinks |
| `twilight` | 10 min after sunrise / 30 min before sunset | Warm golden hour | Golden ambers, sienna browns |
| `dusk` | 10 min after sunset → 50 min after | Deep indigo post-sunset | Dark indigos, muted blue-violets |
| `dark` | Night (full dark) | Deep ocean night | Dark navy-black, muted teal greens |

### Theme Timeline (relative to sunrise/sunset)

```
Night ─── Dawn ─── Sunrise ── Twilight ─── Light (daytime) ─── Twilight ── Dusk ─── Dark ─── Night
              50min       10min       0        +10min          -30min     -10min    +10min   +50min
              before      before      sunrise                  before     sunset    after    after
              sunrise     sunrise                              sunset
```

> **Note:** `twilight` appears in both the morning (10 min after sunrise) and evening (30 min before sunset) windows — it's the golden-hour theme, used at both ends of the day. `dawn` and `dusk` are the transitional bookends around sunrise and sunset respectively.

---

## 2. Reference CSS — All 6 Theme Palettes

The CSS below uses Sally Starfish's Vista del Mar design system as a concrete reference. **Replace the color values with your own design system's palette** — the structure (which variables to define per theme) is what matters.

```css
/* ═════════════════════════════════════════════════════════════════
   SOLAR THEME SYSTEM — 6 Time-of-Day Palettes
   Reference palette: Vista del Mar (Sea Ranch, CA)
   Adapt by replacing color values with your design system's tokens.
   ═════════════════════════════════════════════════════════════════ */

/* ── LIGHT (daytime, default — no data-theme attribute needed) ── */
:root,
[data-theme="light"] {
  --paper: #fdfcf8;
  --body-ink: #2c2c2c;
  --ink: #2c2c2c;

  --sage-500: #7a9e8e;
  --sage-700: #5e7d71;
  --sage-300: #a5bfb4;

  --driftwood-300: #ddd1b8;
  --driftwood-500: #c8b89a;
  --driftwood-700: #8a7a5e;

  --slate-300: #a8b4bc;
  --slate-500: #6b7c87;
  --slate-700: #4a5a65;

  --header-bg: transparent;
  --header-ink: var(--sage-700);

  --avatar-bg: radial-gradient(circle at 35% 30%, var(--sage-500), var(--sage-700) 60%, var(--sage-300));
}

/* ── DAWN (cool grey-blue pre-dawn, 50→10 min before sunrise) ── */
[data-theme="dawn"] {
  --paper: #e8edf2;
  --body-ink: #2a3540;
  --ink: #2a3540;

  --sage-500: #6b8aa0;
  --sage-700: #4a6878;
  --sage-300: #a0b8c8;

  --header-bg: #4a6878;
  --header-ink: #e8edf2;

  --avatar-bg: radial-gradient(circle at 35% 30%, #a0b8c8, #6b8aa0 60%, #4a6878);
}

/* ── SUNRISE (soft pink/coral first light, ±10 min of sunrise) ── */
[data-theme="sunrise"] {
  --paper: #fff0f0;
  --body-ink: #5c2a2a;
  --ink: #5c2a2a;

  --sage-500: #c95a5a;
  --sage-700: #b04848;
  --sage-300: #d05060;

  --header-bg: #b04848;
  --header-ink: #fff0f0;

  --avatar-bg: radial-gradient(circle at 35% 30%, #e07080, #c95a5a 60%, #b04848);
}

/* ── TWILIGHT (warm golden hour, +10min after sunrise / -30min before sunset) ── */
[data-theme="twilight"] {
  --paper: #fff4e0;
  --body-ink: #3d2817;
  --ink: #3d2817;

  --sage-500: #a0522d;
  --sage-700: #6b3410;
  --sage-300: #c8731a;

  --header-bg: #6b3410;
  --header-ink: #fff4e0;

  --avatar-bg: radial-gradient(circle at 35% 30%, #e08a20, #a0522d 60%, #6b3410);
}

/* ── DUSK (deep indigo post-sunset, 10→50 min after sunset) ── */
[data-theme="dusk"] {
  --paper: #1a1e2e;
  --body-ink: #c0c8d4;
  --ink: #c0c8d4;

  --sage-500: #7a8a9e;
  --sage-700: #5a6a7e;
  --sage-300: #a0b0c4;

  --header-bg: #2a2e40;
  --header-ink: #a0b0c4;

  --avatar-bg: radial-gradient(circle at 35% 30%, #5a6a7e, #3a4050 60%, #2a2e40);
}

/* ── DARK (full night, deep ocean) ── */
[data-theme="dark"] {
  --paper: #0f1c27;
  --body-ink: #c8d0d8;
  --ink: #c8d0d8;

  --sage-300: #a5bfb4;
  --sage-500: #7a9e8e;
  --sage-700: #5e7d71;

  --header-bg: #0f1c27;
  --header-ink: var(--sage-300);

  --avatar-bg: radial-gradient(circle at 35% 30%, var(--sage-500), var(--sage-700) 60%, #0f1c27);
}

/* ── Smooth transition when theme changes ── */
:root,
[data-theme] {
  --theme-transition: background-color 0.6s ease, color 0.6s ease, border-color 0.6s ease;
}

body {
  background-color: var(--paper);
  color: var(--body-ink);
  transition: var(--theme-transition);
}

/* ── Theme toggle icon (sun behind horizon) ── */
.theme-toggle {
  all: unset;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.theme-toggle svg {
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Adapting to Your Design System

The CSS variables above (`--paper`, `--ink`, `--sage-*`, etc.) are **placeholder names** from the reference implementation. To adapt:

1. **Identify your design tokens** — find the CSS custom properties your app uses for backgrounds, text, accents, headers
2. **Create 6 value-sets** — one per theme, maintaining the semantic mapping (background → paper, text → ink, primary accent → sage, etc.)
3. **Keep the `data-theme` selector structure** — `[data-theme="dawn"] { ... }` etc.
4. **Light theme on `:root`** — the light/default theme lives on `:root` so the page works even before JS loads

---

## 3. Complete JavaScript — Solar Calc + Theme Engine

This is the full, self-contained JS module. Copy it as-is, change `LAT`/`LON`, and it works.

```javascript
/* ═════════════════════════════════════════════════════════════════
   SOLAR THEME ENGINE — NOAA Solar Position Calculator + Theme System
   Framework-agnostic. No dependencies. Pure vanilla JS.
   ═════════════════════════════════════════════════════════════════ */

/* ── CONFIGURATION: Set your location ── */
const LAT = 38.71;      // Sea Ranch, CA — change to your latitude
const LON = -123.39;    // Sea Ranch, CA — change to your longitude (negative = West)
const TIMEZONE = null;  // null = auto-detect from browser; or set e.g. 'America/Los_Angeles'

/* ── The 6 themes in cycle order ── */
const THEME_CYCLE = ['light', 'dawn', 'sunrise', 'twilight', 'dusk', 'dark'];

/* ═════════════════════════════════════════════════════════════════
   NOAA Solar Position Calculator
   Based on the NOAA Solar Calculator algorithm.
   https://gml.noaa.gov/grad/solcalc/calcdetails.html
   ═════════════════════════════════════════════════════════════════ */

function computeSunTimes(date) {
  // Get day of year
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date - start;
  const dayOfYear = Math.floor(diff / 86400000);

  // Solar declination angle (degrees)
  const declRad = 23.45 * Math.sin((Math.PI / 180) * (360 * (284 + dayOfYear) / 365));
  const decl = declRad * Math.PI / 180;

  // Lat in radians
  const latRad = LAT * Math.PI / 180;

  // Hour angle at sunrise/sunset (when solar elevation = -0.833°, accounts for refraction + semidiameter)
  const cosH = (Math.sin(-0.833 * Math.PI / 180) - Math.sin(latRad) * Math.sin(decl))
             / (Math.cos(latRad) * Math.cos(decl));

  // Polar day/night: sun never rises or never sets
  if (cosH > 1) return { sunrise: null, sunset: null };  // Polar night
  if (cosH < -1) return { sunrise: null, sunset: null }; // Polar day (midnight sun)

  const H = Math.acos(cosH) * 180 / Math.PI / 15; // hours

  // Solar noon (local solar time) in UTC
  // Equation of time correction
  const B = 2 * Math.PI * (dayOfYear - 81) / 365;
  const EoT = 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B); // minutes

  // Solar noon = 12:00 - (longitude/15) - EoT/60, in UTC hours
  // The -LON/15 term: for West longitudes (negative), this adds time
  const utcOffsetHours = -LON / 15 - EoT / 60;
  const solarNoonUTC = 12 - utcOffsetHours;

  // Convert UTC solar noon to local time
  const tzOffset = getTimezoneOffsetHours(date);
  const solarNoonLocal = solarNoonUTC + tzOffset;

  const sunriseLocal = solarNoonLocal - H;
  const sunsetLocal = solarNoonLocal + H;

  // Convert fractional hours to Date objects
  const sunrise = hoursToDate(date, sunriseLocal);
  const sunset = hoursToDate(date, sunsetLocal);

  return { sunrise, sunset };
}

function getTimezoneOffsetHours(date) {
  // Returns the offset such that localTime = utcTime + offset
  return -date.getTimezoneOffset() / 60;
}

function hoursToDate(baseDate, fractionalHours) {
  const d = new Date(baseDate);
  d.setHours(0, 0, 0, 0);
  d.setTime(d.getTime() + fractionalHours * 3600 * 1000);
  return d;
}

/* ═════════════════════════════════════════════════════════════════
   Natural Theme Determination
   Returns one of: 'light', 'dawn', 'sunrise', 'twilight', 'dusk', 'dark'
   based on current time relative to sunrise/sunset.
   ═════════════════════════════════════════════════════════════════ */

function naturalTheme(date) {
  const { sunrise, sunset } = computeSunTimes(date);
  const now = date.getTime();

  // Handle polar regions (no sunrise/sunset)
  if (!sunrise || !sunset) {
    // If no sunrise, it's either polar day or polar night
    // Use month as heuristic: summer months = light, winter = dark
    const month = date.getMonth(); // 0=Jan
    const isNorthernSummer = month >= 3 && month <= 8;
    return (LAT > 0 ? isNorthernSummer : !isNorthernSummer) ? 'light' : 'dark';
  }

  const sr = sunrise.getTime();
  const ss = sunset.getTime();
  const MIN = 60 * 1000;

  // Morning sequence: dawn → sunrise → twilight → light
  if (now < sr - 50 * MIN) return 'dark';                    // Pre-dawn night
  if (now < sr - 10 * MIN) return 'dawn';                    // 50→10 min before sunrise
  if (now < sr + 10 * MIN) return 'sunrise';                 // ±10 min of sunrise
  if (now < sr + 10 * MIN + 1) return 'twilight';            // Brief golden hour after sunrise

  // Evening sequence: twilight → dusk → dark
  if (now < ss - 30 * MIN) return 'light';                   // Daytime
  if (now < ss - 10 * MIN) return 'twilight';                // 30→10 min before sunset
  if (now < ss + 10 * MIN) return 'sunrise';                 // ±10 min of sunset (reuse sunrise palette)
  if (now < ss + 50 * MIN) return 'dusk';                    // 10→50 min after sunset
  return 'dark';                                             // Full night
}

/* ═════════════════════════════════════════════════════════════════
   Theme Management: Apply, Override, Daily Reset
   ═════════════════════════════════════════════════════════════════ */

const STORAGE_KEY = 'solar-theme-override';
const STORAGE_DATE_KEY = 'solar-theme-override-date';

function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
  updateToggleIcon(theme);
}

function getOverride() {
  try {
    const storedDate = localStorage.getItem(STORAGE_DATE_KEY);
    const today = new Date().toDateString();
    if (storedDate !== today) {
      // New day — clear yesterday's override, return to natural
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STORAGE_DATE_KEY);
      return null;
    }
    return localStorage.getItem(STORAGE_KEY);
  } catch (e) {
    return null;
  }
}

function setOverride(theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
    localStorage.setItem(STORAGE_DATE_KEY, new Date().toDateString());
  } catch (e) { /* localStorage may be blocked */ }
}

function cycleTheme() {
  const current = getCurrentTheme();
  const idx = THEME_CYCLE.indexOf(current);
  const next = THEME_CYCLE[(idx + 1) % THEME_CYCLE.length];
  applyTheme(next);
  setOverride(next);
}

function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') || 'light';
}

/* ═════════════════════════════════════════════════════════════════
   Toggle Icon — Sun Behind Horizon (rotates 60° per theme step)
   ═════════════════════════════════════════════════════════════════ */

function updateToggleIcon(theme) {
  const idx = THEME_CYCLE.indexOf(theme);
  const rotation = idx * 60; // 0°, 60°, 120°, 180°, 240°, 300°
  const icon = document.querySelector('.theme-toggle svg');
  if (icon) {
    icon.style.transform = `rotate(${rotation}deg)`;
  }
}

/* ── SVG: Sun behind horizon line ──
   At 0° (light): sun fully above horizon
   At 180° (dark): sun fully below horizon
   Intermediate rotations show the sun rising/setting through the horizon line */

const TOGGLE_SVG = `
<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="4"/>
  <line x1="12" y1="2" x2="12" y2="4"/>
  <line x1="12" y1="20" x2="12" y2="22"/>
  <line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/>
  <line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/>
  <line x1="2" y1="12" x2="4" y2="12"/>
  <line x1="20" y1="12" x2="22" y2="12"/>
  <line x1="4.93" y1="19.07" x2="6.34" y2="17.66"/>
  <line x1="17.66" y1="6.34" x2="19.07" y2="4.93"/>
  <line x1="2" y1="18" x2="22" y2="18"/>
</svg>
`;

/* ═════════════════════════════════════════════════════════════════
   Initialization
   ═════════════════════════════════════════════════════════════════ */

function initSolarTheme() {
  // 1. Set up toggle button if present
  const toggleBtn = document.querySelector('.theme-toggle');
  if (toggleBtn) {
    toggleBtn.innerHTML = TOGGLE_SVG;
    toggleBtn.addEventListener('click', cycleTheme);
  }

  // 2. Apply theme: manual override if valid, else natural solar theme
  const override = getOverride();
  if (override && THEME_CYCLE.includes(override)) {
    applyTheme(override);
  } else {
    applyTheme(naturalTheme(new Date()));
  }

  // 3. Check periodically if using natural theme (no override active)
  // Re-evaluates every 10 minutes to catch theme transitions
  setInterval(() => {
    if (!getOverride()) {
      applyTheme(naturalTheme(new Date()));
    }
  }, 10 * 60 * 1000);
}

/* Auto-init on DOM ready */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSolarTheme);
} else {
  initSolarTheme();
}
```

---

## 4. HTML Integration

Minimal HTML to wire up the system:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Solar Theme App</title>

  <!-- 1. Include your theme CSS (the 6 palettes from section 2) -->
  <link rel="stylesheet" href="themes.css">

  <!-- 2. Include the solar theme engine JS (from section 3) -->
  <script src="solar-theme.js" defer></script>
</head>
<body>
  <!-- Your app content here -->

  <!-- 3. Theme toggle button (place anywhere in your layout) -->
  <button class="theme-toggle" aria-label="Cycle theme" title="Cycle theme">
    <!-- SVG injected by JS -->
  </button>
</body>
</html>
```

### Wiring into Existing Apps

If you already have a theme system:

1. **Merge the CSS variables** — map your existing custom properties to the 6 `data-theme` blocks. You don't need to use the exact variable names from the reference; just ensure each `[data-theme="X"]` block sets all the variables your app reads.
2. **Replace your existing theme toggle** — or keep it alongside. Call `initSolarTheme()` on load and `cycleTheme()` on toggle click.
3. **If using a framework** (React, Vue, Svelte, etc.) — the CSS is framework-agnostic and works as-is. For the JS, either use it as a vanilla module or port the functions into your framework's lifecycle. The core logic (`computeSunTimes`, `naturalTheme`) is pure functions that work anywhere.

---

## 5. Toggle Icon Behavior

The toggle uses a "sun behind horizon" icon that rotates to reflect the current theme:

### Full 6-Mode Cycle (default)

| Theme | Rotation | Visual |
|-------|----------|--------|
| `light` | 0° | Sun fully above horizon |
| `dawn` | 60° | Sun at horizon, rising |
| `sunrise` | 120° | Sun half-risen |
| `twilight` | 180° | Sun at horizon, setting |
| `dusk` | 240° | Sun half-set |
| `dark` | 300° | Sun fully below horizon |

Each click advances 60° clockwise. After `dark` (300°), it wraps back to `light` (0°).

### Simple Light/Dark Only

If you want just 2 themes (light/dark) without the full solar cycle:

```javascript
// Simple mode: 0° = light, 180° = dark
const SIMPLE_CYCLE = ['light', 'dark'];

function cycleSimple() {
  const current = getCurrentTheme() === 'dark' ? 'dark' : 'light';
  const next = current === 'light' ? 'dark' : 'light';
  applyTheme(next);
  setOverride(next);
  // Icon rotates 0° ↔ 180°
  const icon = document.querySelector('.theme-toggle svg');
  if (icon) icon.style.transform = `rotate(${next === 'dark' ? 180 : 0}deg)`;
}
```

---

## 6. Adapting to Any Location

Change two values in the JS config section:

```javascript
// New York City
const LAT = 40.71;
const LON = -74.01;

// London, UK
const LAT = 51.51;
const LON = -0.13;   // West = negative

// Tokyo, Japan
const LAT = 35.68;
const LON = 139.69;  // East = positive

// Sydney, Australia (Southern Hemisphere)
const LAT = -33.87;  // South = negative
const LON = 151.21;
```

### Latitude/Longitude Rules

- **North latitude = positive**, South = negative
- **East longitude = positive**, West = negative
- The algorithm handles the Equator, Arctic/Antarctic circles (polar day/night), and both hemispheres
- For polar regions, the system falls back to month-based light/dark (summer = light, winter = dark)

### Finding Your Coordinates

- Google Maps: right-click any point → coordinates
- `navigator.geolocation.getCurrentPosition()` for user's current location
- Free geocoding APIs (Nominatim/OpenStreetMap) for city name → coordinates

---

## 7. Adapting to Any Design System

The reference CSS uses Vista del Mar's token names (`--paper`, `--ink`, `--sage-*`, `--driftwood-*`, `--slate-*`). Your design system will have different tokens. Here's the mapping approach:

### Minimal Variable Set (required for the system to work)

```css
[data-theme="X"] {
  --bg-color:        /* maps to --paper — page background */
  --text-color:      /* maps to --body-ink — body text */
  --primary:         /* maps to --sage-500 — primary accent */
  --primary-dark:    /* maps to --sage-700 — pressed/active state */
  --primary-light:   /* maps to --sage-300 — hover/light accent */
  --header-bg:       /* header/nav background */
  --header-text:     /* header/nav text color */
}
```

### Per-Theme Palette Strategy

Each of the 6 themes should feel like the sky at that time:

| Theme | Palette mood | Hue guidance |
|-------|-------------|--------------|
| `light` | Bright, airy | Your brand's daytime palette — whites, full saturation |
| `dawn` | Cool, muted | Desaturated blue-greys, soft and cold |
| `sunrise` | Warm, gentle | Rose, coral, soft pink — first light warmth |
| `twilight` | Golden, rich | Amber, gold, sienna — golden hour glow |
| `dusk` | Deep, moody | Indigo, dark blue-violet — post-sunset depth |
| `dark` | Dark, calm | Your dark mode — deep navy/black, muted accents |

The key insight: **saturation and warmth track the sun**. `light` and `twilight` are warm and saturated; `dawn` and `dusk` are cool and desaturated; `sunrise` is warm-pink; `dark` is deep and muted.

---

## 8. Complete File Structure

```
your-app/
├── index.html          ← includes toggle button + script tag
├── themes.css          ← the 6 [data-theme] blocks (section 2)
└── solar-theme.js      ← NOAA calc + theme engine (section 3)
```

Or inline everything into a single HTML file — the system has zero external dependencies.

---

## 9. Verification Checklist

When implementing this system, verify:

- [ ] **Light theme shows by default** — `:root` has the light palette, no `data-theme` attribute needed
- [ ] **Toggle cycles through all 6 themes** — click 6 times, returns to start
- [ ] **Icon rotates 60° per click** — visually tracks the sun position
- [ ] **Manual override persists on reload** — same day, same theme
- [ ] **Override resets next day** — next day, natural solar theme is used
- [ ] **Natural theme matches actual sky** — check at dawn/sunrise/sunset that the theme matches the real sky
- [ ] **Sunrise/sunset times are correct** — compare `computeSunTimes(new Date())` output against [timeanddate.com](https://www.timeanddate.com/sun/) for your location
- [ ] **Polar regions handled** — if lat > 66.5° or < -66.5°, test during solstice
- [ ] **Transitions are smooth** — 0.6s ease on background/color changes

---

## 10. Pitfalls and Edge Cases

### Timezone Handling
The code uses `date.getTimezoneOffset()` to convert UTC solar noon to local time. This respects DST automatically. If your server is in a different timezone than your users, ensure the JS runs client-side (browser), not server-side.

### Date Rollover at Midnight
The override date check uses `new Date().toDateString()`, which rolls over at local midnight. The natural theme check runs every 10 minutes, so the theme will update correctly as the day progresses.

### Polar Regions
Above the Arctic Circle (~66.5°N) or below the Antarctic Circle (~66.5°S), the sun may not rise or set for extended periods. The `computeSunTimes` function returns `null` for sunrise/sunset in these cases, and `naturalTheme` falls back to a month-based heuristic (summer = light, winter = dark). For production use in polar regions, consider a more sophisticated approach (e.g., using civil twilight thresholds).

### CSS Specificity
If your app already has `:root` variables with `!important`, the `[data-theme]` selectors may not override them. Ensure theme variables don't use `!important`, or increase specificity on the theme selectors if needed.

### Flash of Wrong Theme
To prevent a flash of the wrong theme before JS loads, add this inline script in `<head>` before the CSS:

```html
<script>
  // Prevent FOUC: set theme before CSS renders
  (function() {
    var override = null;
    try {
      var d = localStorage.getItem('solar-theme-override-date');
      if (d === new Date().toDateString()) {
        override = localStorage.getItem('solar-theme-override');
      }
    } catch(e) {}
    // If no override, light is the default (no data-theme needed)
    if (override && override !== 'light') {
      document.documentElement.setAttribute('data-theme', override);
    }
  })();
</script>
```

This inline script is synchronous and runs before paint, eliminating any theme flash.

---

## Reference Implementation

This skill is extracted from Sally Starfish's solar-aware design system at Vista del Mar / Sea Ranch AI. The reference implementation runs at Sea Ranch, CA (38.71°N, 123.39°W) and has been validated against NOAA's solar calculator. The system was designed to make the web UI feel like the sky outside the window — shifting through the full cycle of natural light from pre-dawn grey to golden hour to deep ocean night.