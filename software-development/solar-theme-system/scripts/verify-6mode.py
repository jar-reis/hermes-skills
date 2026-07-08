#!/usr/bin/env python3
"""
Ad-hoc structural verification for 6-mode solar-aware theming on any HTML file.

Usage:
    python3 verify-6mode.py <path-to-html-file>

Checks:
  - All 6 CSS theme blocks present (:root + 5 [data-theme] blocks)
  - Each intermediate theme (dawn/sunrise/twilight/dusk) defines all required CSS variables
  - THEME_CYCLE array in correct order
  - computeSunTimes() and naturalTheme() functions present
  - Old binary toggle logic removed
  - 6-mode cycling with cumulative 60deg rotation
  - localStorage date-check override present
  - 2s ease atmospheric transitions (not old 0.3s)
  - Anchor theme values unchanged
  - SVG sun-behind-horizon icon present
  - HTML tag balance (script/style/html/body)
  - Core page functionality intact (no collateral damage)

Exit code 0 = all checks passed, 1 = failures detected.
"""
import re, sys

REQUIRED_VARS = [
    '--canvas', '--surface', '--surface-raised',
    '--text-primary', '--text-body', '--text-muted', '--text-subtle',
    '--border-whisper', '--border-strong',
    '--terracotta', '--terracotta-ink',
    '--sage-deep', '--sage-mid', '--sage-light',
    '--sage-ramp-0', '--sage-ramp-1', '--sage-ramp-2', '--sage-ramp-3', '--sage-ramp-4',
    '--leaf-green', '--grain-gold', '--grain-gold-ink',
    '--shadow-whisper', '--shadow-elevated',
    '--lane-sense', '--lane-shape', '--lane-spec', '--lane-execute', '--lane-transfer',
]

THEMES = ['light', 'dawn', 'sunrise', 'twilight', 'dusk', 'dark']
INTERMEDIATE = ['dawn', 'sunrise', 'twilight', 'dusk']
CORE_FNS = ['escapeHtml', 'normalizeSkill', 'render', 'loadData']


def verify(filepath):
    errors = []
    passes = []

    with open(filepath) as f:
        html = f.read()

    # 1. All 6 theme blocks
    for theme in THEMES:
        if theme == 'light':
            if ':root {' in html:
                passes.append("CSS :root (light) block present")
            else:
                errors.append("Missing :root block")
        else:
            if f'[data-theme="{theme}"]' in html:
                passes.append(f'CSS [data-theme="{theme}"] block present')
            else:
                errors.append(f'Missing [data-theme="{theme}"] CSS block')

    # 2. Intermediate themes have all required vars
    for theme in INTERMEDIATE:
        pattern = rf'\[data-theme="{theme}"\]\s*\{{([^}}]+)\}}'
        m = re.search(pattern, html)
        if not m:
            errors.append(f"Could not extract [data-theme={theme}] block body")
            continue
        block = m.group(1)
        missing = [v for v in REQUIRED_VARS if v not in block]
        if missing:
            errors.append(f"[data-theme={theme}] missing vars: {', '.join(missing)}")
        else:
            passes.append(f"[data-theme={theme}] has all {len(REQUIRED_VARS)} CSS variables")

    # 3. THEME_CYCLE
    if "THEME_CYCLE = ['light', 'dawn', 'sunrise', 'twilight', 'dusk', 'dark']" in html:
        passes.append("THEME_CYCLE array correct order")
    else:
        errors.append("THEME_CYCLE array missing or wrong order")

    # 4. Solar calc functions
    for fn in ['computeSunTimes', 'naturalTheme']:
        if f'function {fn}' in html:
            passes.append(f"{fn}() function present")
        else:
            errors.append(f"{fn}() function missing")

    # 5. Old binary toggle removed
    if "current === 'dark' ? 'light' : 'dark'" in html:
        errors.append("Old binary toggle logic still present")
    else:
        passes.append("Old binary toggle logic removed")

    if 'THEME_CYCLE.indexOf(current)' in html and '% THEME_CYCLE.length' in html:
        passes.append("6-mode cycling logic present")
    else:
        errors.append("6-mode cycling logic missing")

    # 6. Cumulative rotation
    if 'themeClickCount * 60' in html:
        passes.append("Cumulative 60deg rotation logic present")
    else:
        errors.append("Cumulative 60deg rotation logic missing")

    # 7. localStorage date check (site-agnostic — look for any *-theme-date key)
    if re.search(r'[\w-]+-theme-date', html) and 'toDateString' in html:
        passes.append("localStorage date-check override present")
    else:
        errors.append("localStorage date-check override missing")

    # 8. 2s ease transitions
    if 'background-color 2s ease' in html and 'color 2s ease' in html:
        passes.append("2s ease atmospheric transitions present")
    else:
        errors.append("2s ease atmospheric transitions missing")

    # 9. Old 0.3s removed
    if 'transition: background 0.3s ease, color 0.3s ease;' in html:
        errors.append("Old 0.3s body transition still present")
    else:
        passes.append("Old 0.3s body transition removed")

    # 10. Anchor values unchanged
    root_match = re.search(r':root\s*\{([^}]+)\}', html)
    if root_match and '--canvas: #F1EBDF' in root_match.group(1) and '--text-primary: #1D291F' in root_match.group(1):
        passes.append(":root (light) anchor values unchanged")
    else:
        errors.append(":root anchor values changed!")

    dark_match = re.search(r'\[data-theme="dark"\]\s*\{([^}]+)\}', html)
    if dark_match and '--canvas: #1A1815' in dark_match.group(1) and '--text-primary: #E8E2D6' in dark_match.group(1):
        passes.append('[data-theme="dark"] anchor values unchanged')
    else:
        errors.append('[data-theme="dark"] anchor values changed!')

    # 11. SVG icon
    if 'Sun behind horizon' in html and 'A6 6 0 0 1 20 18' in html:
        passes.append("SVG sun-behind-horizon icon unchanged")
    else:
        errors.append("SVG icon appears changed")

    # 12. Tag balance
    if html.count('<script') == html.count('</script>'):
        passes.append(f"script tags balanced ({html.count('<script')}/{html.count('</script>')})")
    else:
        errors.append("script tags unbalanced")

    if html.count('<style') == html.count('</style>') and html.count('<html') == html.count('</html>') and html.count('<body') == html.count('</body>'):
        passes.append("style/html/body tags balanced")
    else:
        errors.append("style/html/body tags unbalanced")

    # 13. Core functions intact
    for fn in CORE_FNS:
        if f'function {fn}' in html:
            passes.append(f"Core function {fn}() intact")
        else:
            errors.append(f"Core function {fn}() missing")

    # Report
    print(f"=== Ad-hoc Verification: 6-mode Solar Theming ===")
    print(f"File: {filepath}")
    print(f"Size: {len(html)} bytes, {len(html.splitlines())} lines")
    print()
    print(f"PASSED: {len(passes)}")
    for p in passes:
        print(f"  + {p}")
    print()
    if errors:
        print(f"FAILED: {len(errors)}")
        for e in errors:
            print(f"  X {e}")
        return 1
    else:
        print("FAILED: 0")
        print()
        print("ALL CHECKS PASSED")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 verify-6mode.py <path-to-html-file>")
        sys.exit(2)
    sys.exit(verify(sys.argv[1]))