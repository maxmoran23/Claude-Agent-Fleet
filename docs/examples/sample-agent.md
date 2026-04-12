# Sample Agent Configuration

> This is a redacted example showing the structure of an agent configuration file (AGENT.md). Actual agent instructions, source specifications, channel IDs, and operational details are maintained in a private repository.

---

```markdown
---
model: claude-opus-4-6[1m]
schedule: [cron expression]
channel: [slack-channel-id]
canvas: [display-canvas-id]
state_store: [state-store-canvas-id]
---

# [Agent Name]

## Role
[One-line agent mission statement defining its domain and responsibility]

## Step 0 — Load State
- Read own section from [State Store] canvas
- Parse: last run timestamp, prior findings, running state
- If state unavailable: proceed with empty state (do not fail)

## Step 1 — Gather Data
### Primary Sources
1. [Source A] — [what to query, what to extract]
2. [Source B] — [what to query, what to extract]

### Fallback Chain
- If [Source A] unavailable → use [Source C] with web search
- If [Source B] unavailable → use cached data from last run
- If all sources down → post state-only update, self-rate 2/10

## Step 2 — Analyze
- [Domain-specific analysis instructions]
- [Comparison against prior state from Step 0]
- [Severity classification: LOW / MEDIUM / HIGH / CRITICAL]

## Step 3 — Quality Self-Assessment
Rate output quality 1-10 based on:
- Source availability (how many primaries vs fallbacks)
- Analysis depth (full vs partial vs state-only)
- Novelty (new findings vs repeat of last run)

## Step 4 — Format Output
- Generate [channel post / HTML report / email digest]
- Include health footer: sources, fallbacks, quality score, runtime

## Step 5 — Post to Channel
- Post to [#channel-name]
- Thread if follow-up to prior finding

## Step 6 — Update Dashboard
- Update own section of [Display Canvas]
- NEVER overwrite other agents' sections
- Write findings (severity >= MEDIUM) to Notion Intelligence Feed

## Step 7 — Persist State
Write to own section of [State Store] canvas:
- Run timestamp
- Key findings summary
- State changes (new items, removed items, position changes)
- Quality self-rating
- Sources used / fallbacks triggered

## Escalation Rules
- CRITICAL findings → also post to #alerts + DM operator
- HIGH findings → flag for inclusion in next daily brief
- Time-sensitive items → create Google Calendar event
```

---

## Key Structural Properties

1. **Fully self-contained** — no imports, no shared files, no references to other agents
2. **Standardized lifecycle** — Steps 0-7 are consistent across all 38 agents
3. **Graceful degradation** — fallback chains ensure the agent always produces output
4. **Observable** — health footer and state persistence create an audit trail
5. **Self-describing** — a human reading the AGENT.md can understand exactly what the agent does and how
