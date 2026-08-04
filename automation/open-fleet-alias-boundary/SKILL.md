---
name: open-fleet-alias-boundary
description: Scope Open Fleet identity per persistent conversation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [open-fleet, telegram, paperclip, herdr, profiles]
    related_skills: [fleet-orchestration, fleet-config-sync, hermes-agent]
    created_by: agent
---

# Open Fleet Alias Boundary

## Overview

Treat a **persistent Telegram alias/conversation or stable operator profile** as the Open Fleet identity boundary. A shared group thread may contain many people and named agents while still being handled by one Hermes profile and one runtime. Group participation alone must never create another Paperclip agent, Hermes profile, Herdr workspace, permapane, tunnel, or shortcut.

When a genuinely distinct persistent alias is commissioned, bind that alias to one provider-agnostic Paperclip profile plus one durable Herdr operator surface. Keep model/provider selection outside the weight-bearing materials so routing can evolve without rebuilding the identity.

## When to Use

Load this skill when:

- Jack asks agents to register themselves in Paperclip or join Open Fleet.
- A Telegram conversation, bot alias, Hermes profile, or persistent operator identity is being introduced.
- Work mentions Herdr Plus shortcuts, permapanes, watchers, or fleet tunnels.
- A group thread contains several apparent participants and runtime multiplication is possible.
- An existing Open Fleet identity needs its Paperclip materials or Herdr surface audited.

Do **not** use this skill to provision one runtime per human or agent name visible inside a shared group. Do not create anything when the existing conversation already resolves to the correct persistent profile.

## Identity Decision Gate

Before any mutation, establish the live boundary:

1. Inspect the active Hermes profile and gateway routing. Record the profile name and `HERMES_HOME`; completion requires a concrete path rather than an inferred identity.
2. Determine whether the Telegram source is a distinct persistent alias/conversation or merely another participant/thread inside an existing group runtime.
3. Search Paperclip agents for the same `HERMES_HOME`, symbolic identity, or managed instruction source.
4. Inspect Herdr workspaces, panes, process commands, and Herdr Plus shortcuts for an existing operator surface.
5. Classify the request:
   - **Shared group path:** reuse the current profile and stop provisioning.
   - **Distinct persistent alias path:** continue with the profile, Paperclip, and Herdr procedure below.

The gate is complete only when the classification is supported by live routing/profile evidence. Ambiguous chat display names are not evidence.

## Shared Group Path

For a shared group runtime:

1. Do not create a Paperclip agent.
2. Do not create a Hermes profile or gateway.
3. Do not create a Herdr workspace, pane, tunnel, watcher, or duplicate shortcut.
4. Record or reinforce the alias-boundary lesson in durable memory or this skill.
5. Continue using Paperclip, Beads, and the existing profile for durable coordination.

This path is complete when no additional runtime surface was created and the existing profile remains the sole execution boundary for the conversation.

## Distinct Persistent Alias Path

### 1. Bind the profile

- Reuse an existing Hermes profile when it already represents the alias.
- Create a profile only when the alias has a genuinely independent identity, memory, routing, or gateway requirement.
- Record its canonical `HERMES_HOME`.
- Never clone credentials into documentation or managed instructions.

Completion criterion: the alias resolves to exactly one stable profile path.

### 2. Register the Paperclip identity

Create or update one Paperclip agent with:

- `adapterType: hermes_local`
- `provider: auto` and `model: auto`, or equivalent inherited/unspecified routing
- `HERMES_HOME` bound to the canonical profile
- wake-on-demand heartbeat unless the role has a separately approved schedule
- one concurrent run by default
- an appropriate reporting parent based on the live Paperclip hierarchy

Keep managed materials configuration-agnostic. A safe bundle normally includes:

- `AGENTS.md` — identity, role, queue discipline, evidence contract
- `SOUL.md` — non-secret personality/identity source
- host/project operating contracts needed by the role
- a mirror manifest recording canonical sources and exclusions

Exclude raw memory, user-profile data, secrets, auth files, `.env`, API keys, session transcripts, and volatile model pins.

Completion criterion: API readback confirms the intended profile path, managed bundle, and inherited/automatic routing.

### 3. Establish the Herdr Plus surface

First verify Herdr Plus is installed, enabled, and reachable. Reuse global shortcuts instead of creating profile-specific duplicates. The standard bindings are:

- `prefix+up` → `herdr-plus projects`
- `prefix+down` → `herdr-plus quick-actions`

For a new alias, create one durable workspace/permapane only if none exists. The launch command should identify the profile but not the model:

```bash
hermes -p <profile> --tui --pass-session-id
```

Use a stable label such as `<Alias> · Open Fleet Watcher`. Avoid model names in workspace labels, pane labels, metadata, or launch commands.

Completion criterion: Herdr process readback shows the expected profile command alive in the intended pane, and Herdr Plus ping succeeds through the active socket.

### 4. Add tunnels only when transport requires them

A tunnel is justified only when the alias must reach a service across hosts and no managed route already exists.

- Discover listener and port ownership on both ends before assigning ports.
- Prefer existing launchd-managed fleet tunnels.
- Do not add a loopback SSH tunnel on the host that already originates the service.
- Pair weight-bearing tunnels with a watcher or health surface; do not rely on an undocumented terminal command.

Completion criterion: the remote service is reachable through the intended managed route and there is no redundant listener or port collision.

### 5. Keep documentation synchronized

Use a deterministic profile-local sync script or equivalent managed process to refresh the non-secret Paperclip instruction bundle from canonical docs. Preserve Paperclip-owned runtime state while updating materials. Make the script idempotent and ensure it does not ingest memories or secrets.

Completion criterion: a second sync produces the same bundle and mirrored source/target hashes match.

### 6. Record evidence

For a real provisioning change, record:

- Paperclip agent ID and evidence issue/comment
- Hermes profile path
- Herdr workspace and pane IDs
- exact profile-only launch command
- Herdr Plus shortcut and ping verification
- mirror file list and hash checks
- Beads issue state
- tunnel/listener proof when a cross-host route was actually added

Do not treat a Telegram message as the only evidence.

## Configuration-Agnostic Materials

Weight-bearing materials describe contracts, not transient runtime choices. Keep these out of shared profile documents:

- model names and provider accounts
- API keys or secret reference values
- current process IDs
- temporary ports not governed by the fleet registry
- chat-specific message IDs
- assumptions that every group participant has a separate runtime

Put model selection, credentials, retries, and routing in the runtime adapter/configuration layer. A model change should require no rewrite of the Paperclip identity bundle or Herdr pane command.

## Common Pitfalls

1. **Multiplying runtimes from chat labels.** Display names and inline participants do not prove separate Hermes profiles. Inspect routing first.
2. **Registering every Paperclip role as a Telegram identity.** Paperclip worker roles may share one Hermes profile; do not infer one gateway or permapane per role.
3. **Pinning a model in durable materials.** This turns a routing change into an identity migration. Use automatic/inherited routing.
4. **Copying raw memory into Paperclip.** Managed instructions are operational context, not a memory dump. Mirror only non-secret documents.
5. **Duplicating Herdr Plus shortcuts.** Shortcuts are global in the Herdr config unless a verified alias-specific requirement exists.
6. **Calling an idle shell a watcher.** Verify the intended Hermes process or actual health watcher is alive and labeled.
7. **Adding redundant tunnels on the service-origin host.** Check listener ownership and existing managed tunnels before creating transport.
8. **Broadcasting by spawning.** Teaching the fleet is a skill-distribution action, not a reason to start every gateway or create new conversations.

## Verification Checklist

- [ ] Live routing proves shared-group or distinct-alias classification.
- [ ] Shared-group work created no additional runtime surface.
- [ ] Distinct aliases map to exactly one canonical Hermes profile.
- [ ] Paperclip provider/model routing is automatic or inherited.
- [ ] Managed instructions contain no secrets, raw memory, or volatile model pins.
- [ ] Herdr Plus shortcuts are present once and plugin ping passes.
- [ ] The permapane command contains the profile but no model flag.
- [ ] Any tunnel is necessary, managed, collision-free, and watched.
- [ ] Documentation synchronization is idempotent and hash-verified.
- [ ] Paperclip and Beads evidence records are current.
