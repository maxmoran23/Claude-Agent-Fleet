# Schema: Slack Canvas Display Structure

Conventions for display canvases — the human-glanceable projection layer.

> **Authority note:** earlier framework revisions used canvases as the *source of truth* for agent state. After canvases hit platform write-saturation limits in production, authority moved to local per-agent state files; canvases are now display mirrors updated non-fatally at Step 7. See [docs/patterns/state-management.md](../docs/patterns/state-management.md). The structural conventions below still apply to the display layer.

---

## Why Slack Canvases

The fleet uses Slack Canvases as agent-writable, human-readable, human-editable display surfaces. This choice solves several problems:

- **No database required for live state.** Canvases are hosted by Slack; agents write via the Slack API
- **Human-inspectable.** The operator can open a canvas at any time and see exactly what the agent currently knows
- **Cross-agent readable.** Any agent can read another agent's canvas via the canvas API
- **Survive restarts.** Canvas content persists regardless of fleet infrastructure state
- **Human-editable.** The operator can manually edit a canvas (e.g., add a watched address) and the agent will pick it up on next run

Canvases are *not* suitable for high-frequency writes or historical data. For those, use the SQLite data layer.

---

## Canvas Naming Convention

One canvas per agent (or per state-store role). Canvas titles follow:

```
[Agent Name] State
```

Examples:
- `Market Monitor State`
- `Regulatory Oracle State`
- `On-Chain Watchlist State`
- `Fleet Watchdog State`

Shared state canvases (consumed by multiple agents) use a domain-based title:
- `Market State Store` (shared across market-related agents)
- `Regulatory State Store`
- `Fleet State Store`

---

## Required Sections

Every state canvas has the same top-level section structure for consistency. The auto-repair agent flags missing sections as ESCALATE findings.

### 1. Header

```markdown
# [Agent Name] State — Last Updated: [ISO 8601 UTC timestamp]
```

The timestamp is rewritten on every agent run. A stale timestamp is the first and most visible signal that an agent has stopped running.

### 2. Run Log (last 10 runs)

```markdown
## Run Log (last 10 runs)
- [ISO timestamp] — Quality: [score]/10 | Findings: [n] | Fallbacks: [n] | Notes: [short]
- [ISO timestamp] — Quality: [score]/10 | Findings: [n] | Fallbacks: [n] | Notes: [short]
...
```

Canvas keeps only the last 10 runs. Older runs are only in the SQLite data layer.

### 3. Current State

Agent-specific structured state. Content varies by agent domain but is always structured markdown (tables, bulleted lists, YAML-in-code-blocks, or JSON-in-code-blocks). Never free-form prose.

Examples:

**Market Monitor State canvas:**
```markdown
## Current State
### Prior Snapshot (T-8h)
| Asset | Price | 24h Change |
|-------|-------|------------|
| BTC   | $62,400 | +2.1% |
| ETH   | $3,200  | +1.4% |

### Active Narratives
- Sector rotation into layer-1 alternatives
- Anticipation ahead of Tuesday regulatory markup

### Watchlist Items
- BTC resistance at $65k
- ETH-BTC ratio at 3-month low
```

**On-Chain Watchlist State canvas:**
```markdown
## Current State
### Monitored Addresses
| Address | Chain | Label | Risk | Threshold |
|---------|-------|-------|------|-----------|
| 0xAB...01 | Ethereum | monitored-entity-01 | HIGH | 1M USDT |
| 0xAB...02 | Ethereum | monitored-entity-02 | MEDIUM | 500k USDT |

### Flagged Counterparties (known-bad, institutional memory)
| Address | Reason | First Seen |
|---------|--------|------------|
| 0xCD...FF | Sanctions list EXAMPLE-SDN-2026-042 | 2026-04-19 |
| 0xDE...AA | Mixing service | 2026-02-14 |
```

### 4. Covered Items (deduplication)

Items already reported in recent runs so the agent can avoid duplicates. Kept to the last 30–100 items depending on the agent's cadence.

```markdown
## Covered Items (last 30)
- [timestamp] [item identifier] [short description]
- [timestamp] [item identifier] [short description]
```

### 5. Quality History

```markdown
## Quality History
Last 10 runs: 9, 8, 9, 8, 9, 7, 8, 9, 8, 9
Trend: stable
Moving average (10-run): 8.4
```

Lets the agent itself notice quality drift across runs.

### 6. Configuration

Agent-specific operator-configurable parameters. This is the section the operator is most likely to manually edit.

```markdown
## Configuration
- Schedule: every 4 hours during active hours
- Topic area: crypto markets
- Output channels: [channel]
- Critical-alerts channel: [channel]
- Priority tier: P1
```

---

## Write Lifecycle

On every agent run:

**Step 0 — Load State:**
- Read the canvas via Slack API
- Parse sections into structured state in-memory
- If parsing fails, log and proceed with empty state (never hard-fail)

**Step 7 — Persist State:**
- Update the header timestamp
- Prepend new run to Run Log, truncate to last 10
- Replace Current State section with fresh content
- Prepend new covered items, truncate per agent's policy
- Prepend new quality score to Quality History
- Write the entire canvas via Slack API

The write is a single canvas update operation. If the write fails, the agent logs the failure loudly and retries on the next run (but does not hard-fail — next run's state load simply sees the previous state).

---

## Cross-Agent Reads

Any agent can read any canvas. Convention for referencing:

```markdown
## Data Sources (this agent reads)
- Market State Canvas: `[canvas ID]`
- Regulatory State Canvas: `[canvas ID]`
- Fleet State Canvas: `[canvas ID]`
```

Agents identify canvases by Slack canvas ID (not by title, which can drift).

---

## What to Persist vs. Not Persist

Put in canvas state:
- Current known values (latest prices, current TVL, current tracked matters)
- Last-N run logs for self-awareness
- Deduplication keys (covered items, covered headlines)
- Watchlists and configurations
- Accumulated institutional memory (flagged counterparties, known entities)

Do NOT put in canvas state:
- Historical time-series data (use data layer)
- Full content of prior outputs (too much bulk)
- Credentials, tokens, secrets (keep in environment/config)
- Personally identifiable information
- Full text of upstream regulatory documents (link instead)

---

## Canvas Size Management

Canvases have size limits. If an agent's canvas is growing unbounded:

- `covered_items` is typically the culprit — tighten the retention policy
- Run logs should never exceed the last 10 entries
- Watchlists should have documented upper bounds

The auto-repair agent monitors canvas sizes and flags any canvas exceeding a configured threshold as ESCALATE for the operator to review.

---

## Canvas vs. SQLite — When to Use Which

| Question | Use |
|----------|-----|
| "What does the agent currently know?" | Canvas |
| "What was true at point X in history?" | SQLite |
| "Is this item a duplicate of something we saw recently?" | Canvas (covered items) |
| "How many of these have we surfaced in the last 90 days?" | SQLite |
| "What's the current watchlist?" | Canvas |
| "What was on the watchlist 6 months ago?" | Not available — canvases overwrite, not append. This is a deliberate design decision. |

---

## Manual Operator Edits

The operator can (and should) directly edit canvas content when appropriate:

- Adding a new monitored address to the on-chain watchlist
- Adjusting a threshold value
- Closing out a tracked regulatory matter that's been resolved
- Adding context notes to a flagged counterparty

The agent's next run will read the edits and incorporate them. This is the primary mechanism for manual operator control over agent behavior.

Do NOT directly edit:
- Run logs (these are the audit trail, shouldn't be altered)
- Quality history (ditto)
- Covered items (ditto)

The auto-repair agent will flag operator edits to these sections as anomalies.
