# Field Notes 6-Mode Adaptation

Concrete reference for adapting the solar theme system to the Field Notes
warm-parchment design system. Inspired by [Helston Fairground](https://helstonfairground.co.uk)
(cream #f7f3e6, forest-green ink #2c372e, Cormorant Garamond + Karla,
earthy accents: borough green, cornwall gold, terracotta, olive).

## Existing Field Notes Tokens (light/dark anchors)

These are the anchor themes — do NOT change their values when adding
intermediate modes. The 4 new themes bridge between them.

```css
:root {
  --canvas: #F1EBDF; --surface: #F5F0E6; --surface-raised: #E8E2D6;
  --text-primary: #1D291F; --text-body: #2A3B2C; --text-muted: #6B7561; --text-subtle: #8A9580;
  --border-whisper: #DBD6C3; --border-strong: #CBC6B3;
  --terracotta: #A56D4A; --terracotta-ink: #7A4A30;
  --sage-deep: #506050; --sage-mid: #607060; --sage-light: #A0B098;
  --leaf-green: #507634; --grain-gold: #F1C85E; --grain-gold-ink: #8A6A10;
  --font-serif: Georgia, serif; --font-sans: 'Inter', sans-serif;
  --lane-sense: #506050; --lane-shape: #B58932; --lane-spec: #A56D4A;
  --lane-execute: #7D6B8A; --lane-transfer: #5A7A8A;
}
[data-theme="dark"] {
  --canvas: #1A1815; --surface: #252321; --surface-raised: #30302e;
  --text-primary: #E8E2D6; --text-body: #DBD6C3; --text-muted: #B0AEA5;
  --border-whisper: #30302e; --border-strong: #3D3A36;
}
```

## 4 Intermediate Theme Palettes

### dawn — cool pre-dawn mist (grey-parchment, cool undertone)

```css
[data-theme="dawn"] {
  --canvas: #E4E8E2; --surface: #ECEFE8; --surface-raised: #E0E5DC;
  --text-primary: #1F2A26; --text-body: #2A3B30; --text-muted: #6B7B70; --text-subtle: #8A9A8E;
  --border-whisper: #D4D9D0; --border-strong: #C4C9C0;
  --terracotta: #8B6A4A; --terracotta-ink: #6A4A30;
  --sage-deep: #4A5A4A; --sage-mid: #5A6A5A; --sage-light: #90A090;
  --sage-ramp-0: #D8DCD2; --sage-ramp-1: #B8C4B0; --sage-ramp-2: #90A090;
  --sage-ramp-3: #688068; --sage-ramp-4: #4A5A4A;
  --leaf-green: #4A6B34; --grain-gold: #D8B84E; --grain-gold-ink: #7A6A10;
  --shadow-whisper: rgba(0,0,0,0.05) 0px 2px 12px;
  --shadow-elevated: rgba(0,0,0,0.10) 0px 4px 24px;
  --lane-sense: #4A5A4A; --lane-shape: #A88032; --lane-spec: #8B6A4A;
  --lane-execute: #7D6B8A; --lane-transfer: #5A7A8A;
}
```

### sunrise — soft warm coral-pink glow

```css
[data-theme="sunrise"] {
  --canvas: #F1E8E2; --surface: #F8F0E8; --surface-raised: #ECE0D6;
  --text-primary: #2A251F; --text-body: #3A322C; --text-muted: #7A6B61; --text-subtle: #9A8A80;
  --border-whisper: #E0D4C8; --border-strong: #D0C4B8;
  --terracotta: #B56A4A; --terracotta-ink: #8A4A30;
  --sage-deep: #506050; --sage-mid: #607060; --sage-light: #A0B098;
  --sage-ramp-0: #ECE0D6; --sage-ramp-1: #CCD0BC; --sage-ramp-2: #A0B098;
  --sage-ramp-3: #708068; --sage-ramp-4: #506050;
  --leaf-green: #507634; --grain-gold: #F5D06E; --grain-gold-ink: #8A6A10;
  --shadow-whisper: rgba(0,0,0,0.05) 0px 2px 12px;
  --shadow-elevated: rgba(0,0,0,0.10) 0px 4px 24px;
  --lane-sense: #506050; --lane-shape: #C59932; --lane-spec: #B56A4A;
  --lane-execute: #7D6B8A; --lane-transfer: #5A7A8A;
}
```

### twilight — warm golden hour amber

```css
[data-theme="twilight"] {
  --canvas: #F0E8D4; --surface: #F5EDE0; --surface-raised: #E8E0CC;
  --text-primary: #2A2015; --text-body: #3A3025; --text-muted: #7A6E5A; --text-subtle: #9A8A75;
  --border-whisper: #DCCFB8; --border-strong: #CCBFA8;
  --terracotta: #A55A3A; --terracotta-ink: #7A3A20;
  --sage-deep: #506050; --sage-mid: #607060; --sage-light: #A0B098;
  --sage-ramp-0: #E8E0CC; --sage-ramp-1: #C8D0B8; --sage-ramp-2: #A0B098;
  --sage-ramp-3: #708068; --sage-ramp-4: #506050;
  --leaf-green: #507634; --grain-gold: #F8D870; --grain-gold-ink: #8A6A10;
  --shadow-whisper: rgba(0,0,0,0.06) 0px 2px 12px;
  --shadow-elevated: rgba(0,0,0,0.12) 0px 4px 24px;
  --lane-sense: #506050; --lane-shape: #B58932; --lane-spec: #A55A3A;
  --lane-execute: #7D6B8A; --lane-transfer: #5A7A8A;
}
```

### dusk — deep indigo twilight (bridge between twilight and dark)

```css
[data-theme="dusk"] {
  --canvas: #2A2530; --surface: #302B38; --surface-raised: #383340;
  --text-primary: #D8D2C8; --text-body: #C8C2B8; --text-muted: #9A92A0; --text-subtle: #7A7280;
  --border-whisper: #3A3540; --border-strong: #4A4550;
  --terracotta: #8B6A5A; --terracotta-ink: #6A4A40;
  --sage-deep: #607060; --sage-mid: #708070; --sage-light: #90A090;
  --sage-ramp-0: #3A3540; --sage-ramp-1: #4A5050; --sage-ramp-2: #607060;
  --sage-ramp-3: #809078; --sage-ramp-4: #607060;
  --leaf-green: #5A7644; --grain-gold: #B89848; --grain-gold-ink: #8A6A30;
  --shadow-whisper: rgba(0,0,0,0.20) 0px 2px 12px;
  --shadow-elevated: rgba(0,0,0,0.30) 0px 4px 24px;
  --lane-sense: #607060; --lane-shape: #988032; --lane-spec: #8B6A5A;
  --lane-execute: #6D5B7A; --lane-transfer: #4A6A7A;
}
```

## Upgrade Workflow: Binary Light/Dark → 6-Mode Solar

When upgrading an existing page that already has binary light/dark theming:

1. **Do NOT touch `:root` or `[data-theme="dark"]`** — these are the anchor themes
2. **Add 4 new `[data-theme]` CSS blocks** (dawn, sunrise, twilight, dusk) after the dark block. Each must set ALL CSS custom properties the page uses — not just a few. **Common pitfall: forgetting `--sage-ramp-0` through `--sage-ramp-4` and `--shadow-whisper`/`--shadow-elevated`.** The dark theme only overrides canvas/surface/text/border/shadow, but intermediate themes must override everything `:root` defines, including the full sage ramp and both shadow values. Use `scripts/verify-6mode.py` to catch missing variables.
3. **Add NOAA solar calc JS** in the existing `<script>` block:
   - `computeSunTimes()` + `naturalTheme()` (copy from SKILL.md section 3)
   - `THEME_CYCLE = ['light','dawn','sunrise','twilight','dusk','dark']`
   - Use visitor's local time — do NOT hardcode lat/lon for global docs sites. Default: approximate sunrise=6am/sunset=7pm if full solar calc isn't needed.
4. **Update toggle JS** from binary 0°/180° to cumulative 60° per click:
   ```javascript
   var themeClickCount = THEME_CYCLE.indexOf(getCurrentTheme());
   // On click: themeClickCount++; rotation = themeClickCount * 60;
   ```
5. **Set initial icon rotation** based on active theme index × 60°
6. **Change body transition** from `0.3s` to `2s ease` for atmospheric fade. Also add a transition group for all themed surface elements (cards, inputs, pills, headers, detail rail, scrollbar) — without this, only the body background fades smoothly while cards snap instantly, creating a jarring mismatch:
   ```css
   .station-card, .lane-header, .detail-rail, .search-input,
   .lane-filter, .cat-pill, .runtime-chip, .tag-chip,
   .live-indicator, .theme-toggle, .theme-toggle svg {
     transition: background-color 2s ease, color 2s ease, border-color 2s ease;
   }
   ```
7. **localStorage with daily reset** — store manual override with date, clears next day
8. **Verify**: search, filtering, and all functionality work in all 6 themes

## Palette Design Principles

- **Saturation and warmth track the sun**: light and twilight are warm/saturated; dawn and dusk are cool/desaturated; sunrise is warm-pink; dark is deep/muted
- **Helston Fairground inspiration**: earthy, botanical, document-like — cream parchment, forest-green ink, gold/terracotta/olive accents. No cool blues (except dawn which gets a cool grey-blue tint)
- **Lane colors shift per theme** but maintain their relative hue relationships
- **Dark themes (dusk, dark)**: muted accents, lower contrast borders, but maintain WCAG AA
- **2-second transition** on background-color and color for the atmospheric fade effect

## Simplified naturalTheme() for Global Docs Sites

When a page is served globally (GitHub Pages) and full NOAA solar calc
is overkill, use visitor's local hour with approximate sunrise=6am /
sunset=7pm. This avoids hardcoding lat/lon for a global audience.

```javascript
function naturalTheme() {
  var now = new Date();
  var timeDec = now.getHours() + now.getMinutes() / 60.0;
  var sunrise = 6.0;   // ~6:00 AM
  var sunset = 19.0;   // ~7:00 PM

  if (timeDec >= sunrise - 50/60 && timeDec < sunrise - 10/60) return 'dawn';
  if (timeDec >= sunrise - 10/60 && timeDec < sunrise + 10/60) return 'sunrise';
  if (timeDec >= sunrise + 10/60 && timeDec < sunrise + 30/60) return 'twilight';
  if (timeDec >= sunset - 30/60 && timeDec < sunset + 10/60) return 'twilight';
  if (timeDec >= sunset + 10/60 && timeDec < sunset + 50/60) return 'dusk';
  if (timeDec >= sunset + 50/60 || timeDec < sunrise - 50/60) return 'dark';
  return 'light';
}
```

## Per-Site localStorage Keys

**Pitfall:** When multiple themed pages share the same GitHub Pages
domain (e.g. `jackreis.github.io`), localStorage keys must be unique
per site. Using a generic `solar-theme-override` key means visiting
one site sets the override for all sites on that domain.

Use site-specific keys:
- hermes-skills: `hermes-skills-theme-override`
- shared-agent-skills: `shared-skills-theme-override`

## Additional Tokens: shared-agent-skills Variant

The shared-agent-skills page has two extra tokens not present on the
hermes-skills page. All 4 intermediate theme blocks must include these:

```css
--soft-teal: #4A8A8A; --soft-teal-ink: #2E6262;
```

Dark-mode adjustments for these tokens (used in dusk):
```css
--soft-teal: #6ABABA; --soft-teal-ink: #4A8A8A;
```

Badge classes reference these tokens (`.badge-agents`), so omitting
them causes badges to render with `unset` values in intermediate themes.

## Deployed On

- `https://jackreis.github.io/hermes-skills/` — 25 skills, 5 lanes
- `https://jackreis.github.io/shared-agent-skills/` — 12 skills
- Both use Field Notes tokens + these 6-mode palettes
- Auto-update via GitHub Actions workflow on SKILL.md changes
- Source files: `/tmp/hermes-skills-sync/docs/index.html` and `/tmp/shared-agent-skills-sync/docs/index.html`
- shared-agent-skills adds `--soft-teal` / `--soft-teal-ink` tokens for runtime badges