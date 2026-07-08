---
name: iterm2-python-api
description: "Control iTerm2 windows, tabs, panes, and sessions via Python API."
version: 0.1.0
author: Hermes
platforms: [macos]
metadata:
  hermes.tags:
    - iTerm2
    - Terminal
    - Automation
    - macOS
---

# iTerm2 Python API

Drive iTerm2 programmatically via its built-in Python API. Create windows, tabs,
split panes, send commands, register RPCs bound to keystrokes, and run daemon
scripts that react to terminal events. Requires iTerm2 3.4+ (tested on 3.6.11).
The `iterm2` Python module is installed automatically by iTerm2 in its own
embedded environment — no pip install needed for basic scripts.

## When to Use

- "Open a new iTerm2 tab and run a command"
- "Split the current pane vertically"
- "Create an iTerm2 layout with multiple panes"
- "Bind a keystroke to clear scrollback in all sessions"
- "Set session titles or colors programmatically"
- "Monitor iTerm2 events (new session, tab change, long-running job)"
- "Launch iTerm2 from the command line and connect"

## Prerequisites

1. iTerm2 installed at `/Applications/iTerm.app` (check: `/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" /Applications/iTerm.app/Contents/Info.plist`)
2. Python API enabled: iTerm2 menu bar > Python API > Enable Python API
3. External connections allowed: iTerm2 menu bar > Python API > Allow all apps to connect (lets any Python process connect directly — no permission dialog, no `it2run` wrapper needed)
4. No `PYTHONPATH` env var set when running scripts (breaks module resolution)
5. Scripts directory: `~/Library/ApplicationSupport/iTerm2/Scripts/`
6. Auto-launch directory: `~/Library/ApplicationSupport/iTerm2/Scripts/AutoLaunch/`

## Quick Reference

```
# Embedded Python (basic scripts):
~/Library/ApplicationSupport/iTerm2/iterm2env/versions/*/bin/python3

# Launch script from CLI (bypasses permission dialog via osascript):
/Applications/iTerm.app/Contents/Resources/it2run myscript.py arg1 arg2

# Core pattern:
async def main(connection):
    app = await iterm2.async_get_app(connection)
    ...
iterm2.run_until_complete(main)   # one-shot
iterm2.run_forever(main)           # daemon

# Key methods:
app.current_window                 # Window or None
window.async_create_tab()           # new tab with default profile
session.async_split_pane(vertical=True)  # split pane
session.async_send_text(text)       # send command to session
session.async_inject(code)          # inject escape sequences
app.get_session_by_id(session_id)   # lookup session
iterm2.RPC                           # decorator for registerable functions
```

## How to Run

Invoke scripts through the `terminal` tool. Two modes:

**One-shot script** — write a `.py` file with `write_file`, then run:
```
/Applications/iTerm.app/Contents/Resources/it2run /path/to/script.py
```

**Auto-launch daemon** — place script in `~/Library/ApplicationSupport/iTerm2/Scripts/AutoLaunch/` via `write_file`. iTerm2 starts it on launch.

**From Scripts menu** — place in `~/Library/ApplicationSupport/iTerm2/Scripts/`. Appears under Scripts menu in iTerm2.

**REPL** — interactive: iTerm2 > Scripts > Open Python REPL. Uses aioconsole; `await` works without wrapping in `run_until_complete`.

**Script Console** — iTerm2 > Scripts > Script Console. Shows script output and errors. Use for debugging.

## Procedure

### 1. Enable the API (if not already done)

Verify via `terminal`:
```
defaults read com.googlecode.iterm2 2>/dev/null | grep -i api
```
If the API is not enabled, use `computer_use` to click: iTerm2 menu bar > Python API > Enable Python API, then > Allow all apps to connect. Or instruct the user to do it manually — the menu item is visible in the iTerm2 menu bar.

### 2. Write a simple script (create a tab)

```python
#!/usr/bin/env python3
import iterm2

async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = app.current_window
    if window is not None:
        await window.async_create_tab()
    else:
        print("No current window")

iterm2.run_until_complete(main)
```

Save with `write_file` to `~/Library/ApplicationSupport/iTerm2/Scripts/new_tab.py`, then invoke through `terminal`:
```
/Applications/iTerm.app/Contents/Resources/it2run ~/Library/ApplicationSupport/iTerm2/Scripts/new_tab.py
```

### 3. Create a split-pane layout

```python
#!/usr/bin/env python3
import iterm2

async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = app.current_window
    if window is None:
        print("No current window")
        return
    tab = window.current_tab
    session = tab.current_session
    # Split vertically (side by side)
    right = await session.async_split_pane(vertical=True)
    # Split the right pane horizontally (stacked)
    bottom = await right.async_split_pane(vertical=False)
    # Send commands
    await session.async_send_text("echo top-left\n")
    await right.async_send_text("echo top-right\n")
    await bottom.async_send_text("echo bottom-right\n")

iterm2.run_until_complete(main)
```

### 4. Register an RPC (keystroke-bound function)

```python
#!/usr/bin/env python3
import iterm2

async def main(connection):
    app = await iterm2.async_get_app(connection)

    @iterm2.RPC
    async def clear_all_sessions():
        code = b'\x1b' + b']1337;ClearScrollback' + b'\x07'
        for window in app.windows:
            for tab in window.tabs:
                for session in tab.sessions:
                    await session.async_inject(code)

    await clear_all_sessions.async_register(connection)

iterm2.run_forever(main)
```

Bind in iTerm2: Preferences > Keys > + > Action: Invoke Script Function > `clear_all_sessions()`

### 5. RPC with session context

```python
@iterm2.RPC
async def clear_session(session_id=iterm2.Reference("id")):
    code = b'\x1b' + b']1337;ClearScrollback' + b'\x07'
    session = app.get_session_by_id(session_id)
    if session:
        await session.async_inject(code)
await clear_session.async_register(connection)
```

Use `iterm2.Reference("id?")` for optional variables (returns None instead of failing if undefined).

### 6. Launch iTerm2 from CLI (standalone script)

```python
#!/usr/bin/env python3
import AppKit
import iterm2

bundle = "com.googlecode.iterm2"
if not AppKit.NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle):
    AppKit.NSWorkspace.sharedWorkspace().launchApplication_("iTerm")

async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = app.current_window
    if window:
        tab = await window.async_create_tab()
        await tab.current_session.async_send_text("echo hello\n")

iterm2.run_until_complete(main)
```

`run_until_complete` blocks until the connection is established, so no wait logic needed after launch.

### 7. Monitor events (daemon)

```python
#!/usr/bin/env python3
import iterm2

async def main(connection):
    app = await iterm2.async_get_app(connection)

    async with iterm2.NewSessionMonitor(connection) as mon:
        while True:
            session_id = await mon.async_get()
            print(f"New session: {session_id}")

iterm2.run_forever(main)
```

## Pitfalls

- **Permission dialog**: Scripts launched from CLI (not via it2run) on iTerm2 3.3.9+ prompt for permission. Use `it2run` to bypass (one-time osascript permission grant instead). When "Allow all apps to connect" is checked (iTerm2 menu bar > Python API > Allow all apps to connect), external Python processes can connect directly without `it2run` and without any permission dialog — `python3 myscript.py` just works.
- **Forget `await`**: Every `async_` function must be called with `await`. Forgetting it silently fails — check Script Console for warnings.
- **`PYTHONPATH` set**: Breaks the embedded Python's module resolution. Unset before running: `unset PYTHONPATH`.
- **No current window**: `app.current_window` returns None if iTerm2 has no terminal window open. Always check.
- **Naming the function**: RPCs share a global namespace. An RPC is identified by name + argument names (order-independent). Avoid generic names like `main`.
- **Basic vs Full environment**: Basic uses iTerm2's embedded Python. Full environment scripts get their own venv at `~/Library/ApplicationSupport/iTerm2/Scripts/YourScript/iterm2env/`. Use Full if you need third-party pip packages.
- **`run_until_complete` vs `run_forever`**: One-shot scripts use `run_until_complete` (exits when main returns). Daemons use `run_forever` (stays running to handle events/RPCs).
- **Spaces in path**: iTerm2 symlinks `ApplicationSupport` (no space) to `Application Support` (with space) because pip doesn't handle spaces in paths well. Always use `ApplicationSupport` in script paths.

## Verification

Run the example script from step 2 via `terminal`:
```
/Applications/iTerm.app/Contents/Resources/it2run ~/Library/ApplicationSupport/iTerm2/Scripts/new_tab.py
```
A new tab appears in the current iTerm2 window. Check Script Console (Scripts > Script Console) for any errors.