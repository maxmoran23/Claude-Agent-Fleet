# Schema: AGENT.md Frontmatter

Conventions for the YAML frontmatter at the top of every AGENT.md file.

---

## Purpose

Every agent is defined by an AGENT.md file containing:

1. **Frontmatter** (YAML block at the top) — machine-readable metadata
2. **Content** (markdown below frontmatter) — human- and agent-readable instructions

The frontmatter is parsed by Claude Code when the agent is invoked and by fleet ops agents (watchdog, auto-repair) when scanning the fleet. Consistent frontmatter is what makes fleet-wide operations possible.

---

## Minimal Required Frontmatter

```yaml
---
model: claude-opus-4-6[1m]
---
```

Only `model` is strictly required. Without it, the agent cannot be invoked.

---

## Full Frontmatter Schema

```yaml
---
# Required
model: claude-opus-4-6[1m]

# Recommended
name: [agent name, e.g., regulatory-oracle]
priority: P0 | P1 | P2 | P3
category: [regulatory | market | onchain | defi | workflow | fleet | execution | research]
version: [semver, e.g., 1.0.0]

# Scheduling metadata (informational — actual scheduling is in Claude Code task config)
schedule_hint: [e.g., "daily 8am", "every 4h during market hours", "on-demand"]

# State and delivery
state_file: [relative path to state file, e.g., "state/last-run.json"]
state_canvas_id: [Slack canvas ID if using canvas state]
primary_channel: [Slack channel name or ID]
critical_alerts_channel: [Slack channel for CRITICAL escalation]

# Fleet coordination
reads_from: [array of upstream agent names or state paths]
writes_to: [array of downstream channel IDs or table names]

# Data layer writes
data_layer_tables: [array of SQLite tables this agent writes to]

# Operational
max_fallback_tier: [primary | secondary | tertiary]  # deepest fallback allowed
sla_runtime_seconds: [soft target for run duration]
---
```

---

## Field Descriptions

### model (required)

The Claude model to use. Use the current supported model ID. Auto-repair updates stale references.

Valid current values (subject to change as models evolve):
- `claude-opus-4-6[1m]` — current premium with 1M context
- `claude-sonnet-4-6` — mid-tier
- `claude-haiku-4-5-20251001` — entry-level

The `[1m]` suffix explicitly requests the 1M-context variant. Without it, models use their standard context window.

### name

Human-readable agent name, typically matching the folder name. Used for logging, channel posts, data layer writes, and cross-agent references.

Convention: lowercase, hyphen-separated, descriptive role noun-phrase.

Good: `regulatory-oracle`, `on-chain-watchlist`, `daily-brief`
Avoid: `agent-1`, `reg_oracle`, `MyAgent`

### priority

Priority tier for JIT budget management. See [JIT Budget Management](../docs/patterns/jit-budget-management.md).

- **P0** — core agents the fleet cannot function without
- **P1** — high-value primary intelligence agents
- **P2** — high-frequency support and routing agents
- **P3** — luxury / exploration / research agents

Watchdog uses this field when deciding what to throttle under budget pressure.

### category

Domain category. Drives routing, channel mapping, and fleet-ops classification. Standard values:

- `regulatory`
- `market`
- `onchain`
- `defi`
- `workflow`
- `fleet`
- `execution`
- `research`
- `cross-domain`

### version

Semver-style version of the agent configuration. Incremented when the prompt, frontmatter, or integrations change meaningfully. Useful for experiment tracking (upgrade_experiments table).

### schedule_hint

Informational string describing when the agent runs. Not authoritative — actual scheduling is in Claude Code scheduled task config — but useful for the watchdog's comparison of configured vs. actual runs.

### state_file

Relative path to the agent's local state file. Defaults to `state/last-run.json` by convention.

### state_canvas_id

Slack canvas ID if the agent uses a canvas for state. The auto-repair agent uses this to verify canvas references resolve.

### primary_channel

Slack channel for the agent's primary output delivery. Channel ID preferred over channel name (IDs are stable across renames).

### critical_alerts_channel

Slack channel for CRITICAL finding escalation. If the agent's output is in a topic channel (e.g., #regulatory), critical findings also post here.

### reads_from

Array of upstream sources this agent consumes. Helps the auto-repair agent verify references and helps the synthesis engine trace information flow.

Format: agent names or relative state paths.

```yaml
reads_from:
  - regulatory-oracle
  - onchain-watchlist
  - ./state/shared/market-state.json
```

### writes_to

Array of downstream outputs. Helps the fleet map data flow.

```yaml
writes_to:
  - C01ABC123  # #regulatory channel ID
  - notion://intelligence-feed
  - sqlite://regulatory_events
```

### data_layer_tables

Array of SQLite tables the agent writes to. Helps the auto-repair agent validate that referenced tables exist and helps fleet query agent find historical data.

```yaml
data_layer_tables:
  - agent_runs       # universal
  - regulatory_events
```

### max_fallback_tier

Deepest fallback the agent is allowed to operate with. If the agent would need to go deeper than this, it should abort rather than produce low-confidence output. Useful for compliance-critical agents where tertiary fallback output is unacceptable.

```yaml
max_fallback_tier: secondary  # abort if would need tertiary
```

### sla_runtime_seconds

Soft target for typical run duration. The watchdog uses this to detect runs that are taking much longer than expected, which often indicates an upstream source issue.

```yaml
sla_runtime_seconds: 60  # typical run should finish in ~60s
```

---

## Example: Full Frontmatter

```yaml
---
model: claude-opus-4-6[1m]
name: regulatory-oracle
priority: P0
category: regulatory
version: 1.3.2

schedule_hint: "daily 6am ET"

state_file: state/last-run.json
state_canvas_id: F0123456789
primary_channel: C0123456789
critical_alerts_channel: C0123456780

reads_from:
  - ./state/shared/regulatory-state.json

writes_to:
  - C0123456789
  - notion://intelligence-feed
  - sqlite://regulatory_events

data_layer_tables:
  - agent_runs
  - regulatory_events

max_fallback_tier: secondary
sla_runtime_seconds: 120
---
```

---

## Example: Minimal Frontmatter

```yaml
---
model: claude-opus-4-6[1m]
---
```

This works for agents in development or for agents where the operator hasn't yet decided on categorization. The auto-repair agent may flag missing recommended fields for operator review but will not block the agent from running.

---

## Migration Notes

When adding new required or recommended fields to this schema, update all existing agents via the auto-repair agent:

1. Add the new field to the schema document
2. Update the auto-repair agent's ruleset to check for the field
3. Set classification to REVIEW_AUTO with a sensible default if auto-derivable, or ESCALATE if not
4. Auto-repair's next run updates every agent and commits each change

Keep the schema stable once agents are deployed. Changes propagate through auto-repair — any breaking change affects every agent simultaneously.

---

## Related Patterns

- [Self-Repair](../docs/patterns/self-repair.md) — how auto-repair uses frontmatter to validate agents
- [JIT Budget Management](../docs/patterns/jit-budget-management.md) — how the priority field drives throttling
- [State Management](../docs/patterns/state-management.md) — the state_file and state_canvas_id fields
