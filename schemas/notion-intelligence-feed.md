# Schema: Notion Intelligence Feed Database

Archive / data bus for finding-level events surfaced by any agent at MEDIUM severity or higher.

---

## Purpose

The Notion Intelligence Feed database serves a specific role in the fleet architecture: **structured archive and inter-agent data bus for finding-level events**. It is not a notification channel. It is not a dashboard. It is a queryable historical log with a schema any agent can write to and any agent (or human) can read from.

The database is append-mostly (entries are not typically updated after insertion, though status changes may update specific fields).

---

## When Agents Write to It

Every agent writes an entry whenever it surfaces a finding at severity >= MEDIUM. Severity LOW findings do not write to the feed — they stay in channel posts only.

Typical triggers:
- Regulatory Oracle surfaces a HIGH or CRITICAL regulatory event
- On-Chain Watchlist detects a CRITICAL sanctions hit
- Market Monitor flags a CRITICAL market event
- Alpha Lab detects a HIGH exploit or DRAINING protocol
- Synthesis Engine produces a HIGH contradiction or coverage gap
- Any agent produces a finding that requires cross-agent awareness

---

## Schema

The database has the following properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `Title` | Title | Yes | Short summary of the finding (under 100 chars) |
| `Agent` | Select | Yes | Name of the agent that surfaced the finding |
| `Severity` | Select | Yes | CRITICAL / HIGH / MEDIUM |
| `Category` | Select | Yes | Domain category (regulatory, market, onchain, defi, fleet, etc.) |
| `Channel` | Text | No | Slack channel where the full finding was posted |
| `Timestamp` | Date | Yes | ISO 8601 UTC timestamp of finding surface |
| `ID` | Text | Yes | Stable unique ID for cross-referencing (agent-generated) |
| `Summary` | Rich Text | Yes | 2-4 sentence summary of the finding |
| `Action Required` | Select | No | None / Review / Draft Response / Escalate / Monitor |
| `Action Deadline` | Date | No | If action is required, the deadline |
| `Source URL` | URL | No | Primary source citation if applicable |
| `Related IDs` | Relation | No | Links to related entries in the same database |
| `Status` | Select | No | Open / Under Review / Actioned / Resolved / Ignored |
| `Status Updated At` | Date | No | When status last changed |

---

## Select Field Options

### Agent
Drawn from the fleet's agent roster. Add new options as new agents are deployed.

### Severity
- CRITICAL
- HIGH
- MEDIUM

(LOW findings do not write to the feed.)

### Category
- regulatory
- market
- onchain
- defi
- research
- workflow
- fleet
- execution
- cross-domain

### Action Required
- None
- Review
- Draft Response
- Escalate
- Monitor
- File

### Status
- Open
- Under Review
- Actioned
- Resolved
- Ignored

---

## Write Pattern

Agents write to the feed as part of their Step 6 Delivery:

```
# Step 6 — Deliver (excerpt)
For each finding at severity >= MEDIUM:
1. Post the finding to the appropriate Slack channel
2. Write an entry to the Notion Intelligence Feed database with:
   - Title: short summary (under 100 chars)
   - Agent: [this agent's name]
   - Severity: [from classification step]
   - Category: [this agent's primary category]
   - Channel: [channel ID where full finding was posted]
   - Timestamp: [ISO timestamp]
   - ID: [stable unique ID, format: {agent}-{severity}-{YYYY-MM-DD}-{seq}]
   - Summary: [2-4 sentence summary]
   - Action Required: [classification]
   - Action Deadline: [if applicable]
   - Source URL: [primary citation if available]
```

The ID format makes cross-referencing straightforward and deterministic:
```
regulatory-oracle-CRITICAL-2026-04-19-001
onchain-watchlist-CRITICAL-2026-04-19-001
```

---

## Why Notion and Not SQLite?

The SQLite data layer captures structured, aggregation-friendly data for historical queries. The Notion Intelligence Feed captures higher-level narrative records — the *finding itself* — with rich formatting, links, and relations.

They serve different purposes:

| Question | Use |
|----------|-----|
| "What was BTC doing last Tuesday at 3pm?" | SQLite (`market_snapshots`) |
| "What regulatory findings did we surface in March?" | Notion (searchable, readable) |
| "What's the average quality score for market monitor?" | SQLite (`agent_runs`) |
| "Show me the full context of that sanctions hit from April" | Notion (full narrative) |
| "What's the approval rate for execution packages?" | SQLite (`execution_outcomes`) |
| "Did we already surface a related finding on this matter?" | Notion (search + relations) |

Agents write to both. The SQLite layer captures structured metrics; the Notion feed captures the narrative finding.

---

## Cross-Agent Consumption

**Synthesis Engine** reads the feed across the previous 24 hours to identify cross-cutting themes. Relations between entries surface connections that individual channel posts can't express.

**Fleet Query** uses the feed as a searchable knowledge base. Questions like "any mentions of [entity] across the fleet?" hit the feed directly.

**Daily Brief** references feed entries by ID when summarizing findings so the operator can click through to the full narrative.

**Execution Scaffold** reads feed entries matching its configured trigger patterns — that's where the package-generating logic finds its inputs.

---

## Operator Use

The operator interacts with the feed primarily through:

- **Search and filtering.** Find all CRITICAL entries from a date range, all entries on a specific matter, all unactioned entries older than N days.
- **Status updates.** After acting on a finding, update its Status field. This lets the fleet know the finding has been handled.
- **Relations.** Manually link related findings that the agents didn't automatically relate.

The operator does NOT need to read every new entry as it arrives — that's what the Slack channels are for. The feed is for *later* — for reference, for search, for audit.

---

## Retention

The feed is retained indefinitely. Notion's database scale allows for years of entries without issues. Old entries are never deleted — institutional memory is the point.

If specific categories of entries need to be pruned for privacy or compliance reasons, that's handled case-by-case at the operator's discretion.

---

## Agent-Side Configuration

Agents need three configuration values to write to the feed:

```json
{
  "notion_integration_token": "[from environment]",
  "notion_database_id": "[database ID]",
  "notion_data_source_id": "[data source ID if multi-source database]"
}
```

The integration token should be in the agent's environment. The database ID and data source ID are stable and can live in the agent's configuration.

---

## Failure Handling

If the Notion write fails (API down, rate limit, schema mismatch):

- Log the failure in the agent's health footer
- Continue with Slack posts and SQLite writes (which don't depend on Notion)
- Retry on the next run (the finding will be idempotent via the ID field)
- If failures persist, the auto-repair agent will flag the pattern

Notion is an archive layer. It should never block an agent's primary output path.
