# Pattern: Two-Tier State Management

Persistent agent state across runs using live dashboards + an append-only data layer.

---

## The Problem

A scheduled agent runs, produces output, and exits. The next run has no memory of the previous one. Without persistent state:

- The agent can't report deltas ("BTC moved 3% since last pulse")
- The agent can't deduplicate findings ("we already flagged this enforcement action")
- The agent can't maintain tracked items across runs (watchlists, deadlines, open matters)
- The fleet as a whole has no institutional memory
- Historical queries are impossible ("what was X at Y point in time?")

Naive solutions (local JSON files per agent) work for single-agent use but create coupling problems in a multi-agent fleet — agents can't easily read each other's state, and the files are not human-inspectable.

---

## The Pattern

Two distinct tiers serving different purposes:

### Tier 1: Live State Stores (Slack Canvases)

Each agent owns a Slack Canvas that functions as its persistent state store. The canvas is structured markdown, human-readable, and human-editable.

**Purpose:** "What does the agent currently know?"

**Characteristics:**
- Current state only — overwritten each run
- Agent-writable, human-readable, human-editable
- Survives across all agent restarts (canvas lives in Slack)
- No database required
- Cross-agent: any agent can read any other agent's canvas

**Read/write lifecycle:**
- **Step 0 (Load State):** Agent reads its canvas at the start of every run
- **Step 7 (Persist State):** Agent writes updated state to the canvas at the end of every run

### Tier 2: Append-Only Historical Record (SQLite)

A shared SQLite database serves as the permanent, append-only historical archive.

**Purpose:** "What was true at point X in time?"

**Characteristics:**
- Append-only — nothing is ever updated or deleted
- Structured tables with consistent schemas
- Queryable for aggregation and trend analysis
- The authoritative source for "what happened when"
- Written at Step 6.5 (after delivery, before persist)

See the [data layer schema](../../schemas/data-layer.sql) for full DDL.

---

## Why Split It

The two tiers answer two fundamentally different questions that should not be conflated:

| Question | Tier |
|----------|------|
| "What's the current BTC price?" | Live store (latest canvas state) |
| "What was BTC doing at 3pm last Tuesday?" | Historical record (SQLite query) |
| "What matters is the regulatory oracle currently tracking?" | Live store |
| "How many CRITICAL regulatory events were surfaced in April?" | Historical record |
| "Is this finding a duplicate of something surfaced this week?" | Live store |
| "What's the quality-score trend across all agents over 90 days?" | Historical record |

A single store trying to serve both purposes either accumulates unbounded cruft (canvases that grow forever) or loses history (databases overwritten each run).

---

## Concrete Implementation

### Canvas Structure

Each agent's canvas has a consistent structure:

```markdown
# [Agent Name] State — Last Updated: [ISO timestamp]

## Run Log (last 10 runs)
- [ISO] — Quality: [score] | Findings: [n] | Notes: [short]
- [ISO] — Quality: [score] | Findings: [n] | Notes: [short]
...

## Current State
[Agent-specific structured state — watchlists, tracked items, prior snapshot, etc.]

## Covered Items (deduplication)
[List of items already reported in recent runs to avoid duplicates]

## Quality History
[Last N quality self-ratings for the agent itself to self-assess drift]
```

See [schemas/slack-canvas-structure.md](../../schemas/slack-canvas-structure.md) for full conventions.

### SQLite Write Pattern

Every agent includes a Step 6.5: Write to Data Layer. Universal pattern:

```bash
# Universal agent_runs row on every run
sqlite3 ~/fleet/fleet.db <<SQL
INSERT INTO agent_runs (
  agent_name, run_timestamp, quality_score,
  sources_used, fallbacks_triggered, findings_count
) VALUES (
  'regulatory-oracle', '$ISO_TIMESTAMP', $QUALITY,
  '$SOURCES', $FALLBACKS, $FINDINGS_COUNT
);
SQL

# Domain-specific writes
sqlite3 ~/fleet/fleet.db <<SQL
INSERT INTO regulatory_events (
  agent_name, event_date, severity, jurisdiction,
  authority, matter, summary
) VALUES (
  'regulatory-oracle', '$DATE', '$SEVERITY', '$JURISDICTION',
  '$AUTHORITY', '$MATTER', '$SUMMARY'
);
SQL
```

See [schemas/data-layer.sql](../../schemas/data-layer.sql) for the full table set.

---

## Consequences

**Positive:**
- Agents have memory without requiring an external database for live state
- Historical queries are possible and fast (SQLite indexed)
- Canvases are human-inspectable — operator can read current state directly
- No cascading failures: if SQLite is unreachable, agents still have live state from canvases; if canvases are unreachable, agents fall back to empty state and log the gap
- The data layer is migration-compatible with hosted databases (Postgres, Supabase) when scale demands

**Negative:**
- Two write destinations per run (adds ~100ms per agent run, negligible)
- Canvas formatting conventions must be enforced (handled by the auto-repair agent)
- SQLite schema evolution requires migration care

---

## When to Use This Pattern

- **Use when:** You have multiple agents that need cross-references, you want historical queryability, you want the operator to inspect live state without tooling
- **Skip when:** A single agent running in isolation — a local JSON file may be enough
- **Variant:** For fleets running on infrastructure that doesn't integrate with Slack, substitute a structured markdown file under version control for the canvas tier

---

## Related Patterns

- [Fallback Chains](fallback-chains.md) — what the agent does when either state store is unreachable
- [Self-Repair](self-repair.md) — how state-store drift gets caught and fixed
- [Quality Self-Rating](quality-self-rating.md) — the quality_score field written to both state tiers
