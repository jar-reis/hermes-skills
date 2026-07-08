---
name: sudo-password
description: Use sudo in terminal without interactive prompts via .env.
version: 0.1.0
author: Hermes
platforms: [macos, linux]
metadata:
  hermes.tags:
    - Terminal
    - Sudo
    - Security
---

# Sudo Password Auto-Rewrite

Hermes automatically rewrites bare `sudo` commands to read the password from stdin via `sudo -S -p ''`, piping the value of `SUDO_PASSWORD` from `~/.hermes/.env`. No interactive prompt appears, and no `sudo -S` should ever be typed manually. If `SUDO_PASSWORD` is absent, the command falls through gracefully — sudo reports "a password is required" rather than blocking. On messaging platforms, the output includes a tip to set `SUDO_PASSWORD` in `.env`.

## When to Use

- You need to run a command that requires root (installs, service management, system config).
- You see "sudo: a password is required" in `terminal` output.
- You are on a messaging platform (Telegram, Discord) where no TTY is available.
- You are configuring a new Hermes host and want sudo to work headlessly.

## Prerequisites

- `SUDO_PASSWORD` set in `~/.hermes/.env` (or the profile-aware equivalent: `get_hermes_home()/.env`).
- The password must match the current user's sudo credentials on the host machine.

**Set it via setup wizard:**

```bash
hermes setup
```

The wizard prompts for "Sudo password" and writes it to `.env` via `save_env_value("SUDO_PASSWORD", ...)`.

**Set it manually** by adding a line to `~/.hermes/.env`:

```
SUDO_PASSWORD=yourpassword
```

The key is also configurable through `hermes config` (category: `setting`, password-masked).

## How to Run

Invoke the command through the `terminal` tool exactly as you normally would — write `sudo apt update`, not `sudo -S apt update`. The transform fires automatically before execution:

1. `_rewrite_real_sudo_invocations` scans the command string for the bare token `sudo` at command-start positions (after `;`, `|`, `&`, `(`, newlines, `&&`, `||`).
2. Each real `sudo` token is replaced with `sudo -S -p ''`.
3. `_transform_sudo_command` prepends `SUDO_PASSWORD\n` to the subprocess stdin.
4. sudo reads exactly one line from stdin (the password), then passes remaining stdin to the child command.

## Quick Reference

| Item | Value |
|---|---|
| Env var | `SUDO_PASSWORD` |
| Config location | `~/.hermes/.env` (profile-aware) |
| Transform | `sudo` → `sudo -S -p ''` + stdin pipe |
| Interactive fallback | `HERMES_INTERACTIVE=1` → 45s prompt, cached per session |
| NOPASSWD hosts | Probed via `sudo -n true`; if it works, command runs unchanged |
| Guard | Explicit `sudo -S` without `SUDO_PASSWORD` is hardline-blocked |

## Procedure

1. Write the command with bare `sudo` — never add `-S` yourself:

   ```
   sudo systemctl restart nginx
   sudo apt update && sudo apt upgrade -y
   ```

2. Invoke through the `terminal` tool. The transform handles single commands, chained commands (`&&`, `||`), and multi-line scripts.

3. If output contains "sudo: a password is required" or "sudo: no tty present":
   - Check whether `SUDO_PASSWORD` is set: `search_files` in `~/.hermes/.env` for `SUDO_PASSWORD`.
   - If missing, add it to `.env` and restart the agent session (env is read at boot).

4. On a host with sudoers `NOPASSWD`, no `.env` entry is needed. Hermes probes `sudo -n true` on each call (local backend only) and skips the pipe if NOPASSWD works.

## Pitfalls

- **Never type `sudo -S` manually.** When `SUDO_PASSWORD` is NOT set, the hardline blocklist in `tools/approval.py` catches explicit `sudo -S` as a brute-force attack vector and blocks it unconditionally — even with `--yolo` or `approvals.mode=off`. When `SUDO_PASSWORD` IS set, the transform injects `-S` internally, so adding it yourself is redundant and can confuse the stdin pipe.
- **Env read at boot.** `SUDO_PASSWORD` is loaded from `.env` when the agent process starts. Editing `.env` mid-session does not take effect until restart.
- **Messaging platforms have no TTY.** Without `SUDO_PASSWORD`, sudo cannot prompt on Telegram/Discord/etc. — it fails immediately. The failure output includes a tip pointing to `.env`.
- **Interactive mode** (`HERMES_INTERACTIVE=1`, CLI only): if `SUDO_PASSWORD` is unset, Hermes prompts once with a 45s timeout and caches the password for the session via `_set_cached_sudo_password`. This path does not work on messaging platforms.
- **NOPASSWD probe is local-only.** Docker, SSH, Modal, and other remote backends do not inherit the host's sudo state. The probe (`_sudo_nopasswd_works`) returns `False` for any `TERMINAL_ENV` other than `local`.
- **Empty string is valid.** Setting `SUDO_PASSWORD=` (empty) tells Hermes to try an empty password without prompting — useful for hosts with passwordless sudo configured via a different mechanism.
- **Quoted or commented "sudo" is not rewritten.** The tokenizer (`_read_shell_token`) only matches `sudo` at command-start positions, not inside strings, comments, or variable assignments.

## Verification

Run a harmless sudo command through the `terminal` tool:

```bash
sudo true
```

If `SUDO_PASSWORD` is correctly configured, the command exits 0 with no prompt and no "a password is required" message. If it fails, check `.env`.