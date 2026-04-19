# Case Study: Autonomous Agent Self-Repair

End-to-end walkthrough showing how a degraded agent gets detected, diagnosed, repaired, and validated — all without operator input.

> This case study uses fabricated data for illustration.

---

## Scenario

A market-data agent's primary source (a dedicated price MCP server) has been renamed as part of an upstream integration change. The agent's configuration still references the old name. Over several runs, the agent has been silently falling back to web search for prices, producing lower-quality output, and writing degraded quality scores to state.

No single run triggers an alarm on its own. The pattern is only visible across runs. The fleet needs to:

1. Notice the quality trend
2. Diagnose the root cause
3. Apply a safe fix
4. Validate the fix
5. Log everything for audit

---

## Timeline

### Runs 1–5: The silent degradation

**Run 1 (Monday morning):** Agent runs normally. Primary source hits, quality: 9/10, fallbacks: 0.

**Run 2 (Monday noon):** Primary source throws an error. Agent falls back to web search. Quality: 6/10, fallbacks: 1. Health footer logs the fallback. Channel post still delivers.

**Run 3 (Monday evening):** Same. Quality: 6/10, fallbacks: 1.

**Run 4 (Tuesday morning):** Same. Quality: 7/10, fallbacks: 1.

**Run 5 (Tuesday noon):** Same. Quality: 6/10, fallbacks: 1.

At this point, no individual run is a crisis. Output is still being produced. The operator, scanning morning briefs, might notice quality has been 6–7 instead of 9 lately, but would not necessarily escalate.

The watchdog agent, however, runs every 6 hours and reads quality trends across the fleet.

---

### Run 6 (Tuesday 2:00 PM) — Watchdog detects

The Watchdog agent runs its regular cycle. Reads `agent_runs` data layer for the last 48 hours:

```sql
SELECT agent_name, run_timestamp, quality_score, fallbacks_triggered
FROM agent_runs
WHERE agent_name = 'market-pulse'
  AND run_timestamp > date('now', '-48 hours')
ORDER BY run_timestamp;
```

Results:
```
market-pulse | 2026-04-19T06:00 | 9 | 0
market-pulse | 2026-04-19T12:00 | 6 | 1
market-pulse | 2026-04-19T18:00 | 6 | 1
market-pulse | 2026-04-20T06:00 | 7 | 1
market-pulse | 2026-04-20T12:00 | 6 | 1
```

Watchdog pattern: 4 consecutive runs with fallback > 0 and quality dropped from 9 → 6–7 range. Matches the `chronic_fallback_use` pattern.

Watchdog posts to the fleet operations channel:

```markdown
:warning: Watchdog — Fleet Health Alert

Agent: market-pulse
Pattern: Chronic fallback use (4 consecutive runs)
Quality trend: 9 → 6 → 6 → 7 → 6 (24h window)
Fallback count: 0 → 1 → 1 → 1 → 1

Likely cause: Primary source is failing. Agent is producing output via fallback chain
but primary data source should be investigated. Escalating to auto-repair for diagnosis.

Context: This is a pattern-based detection. No single run failed; the trend is the signal.
```

The escalation is logged to the Watchdog's state. Auto-Repair is flagged to diagnose on its next run.

---

### Run 7 (Tuesday 2:30 PM) — Auto-Repair diagnoses

The Fleet Auto-Repair agent runs on its 3x/day cycle. Reads the Watchdog's escalation log. Picks up the market-pulse flag.

Diagnosis pass:

**Step 1:** Load market-pulse's AGENT.md
**Step 2:** Extract the configured primary source reference from the Configuration section

Found:
```
6. Optional: Add MCP servers for real-time price and sentiment data
   Example: price-data-mcp-v1
```

**Step 3:** Check the current fleet MCP configuration for `price-data-mcp-v1`

Result: Not found in current MCP config.

**Step 4:** Check the fleet MCP change log for recent renames

Found: `price-data-mcp-v1` was renamed to `price-data-mcp-v2` on [DATE] (3 days ago) during an integration update.

**Step 5:** Classify the finding

Pattern: `dead_source_reference` — primary source reference points to a renamed integration.

Classification: **REVIEW_AUTO** — the fix is unambiguous (repoint to the new name), but the operator should see the change.

**Step 6:** Apply the fix

Edit market-pulse/AGENT.md:
```diff
-   Example: price-data-mcp-v1
+   Example: price-data-mcp-v2
```

Commit:
```
repair: update market-pulse primary source reference

Source price-data-mcp-v1 was renamed to price-data-mcp-v2 in the fleet
MCP configuration on [DATE]. Market-pulse AGENT.md still referenced the
old name, causing the agent to fall back to web search on every run for
the past 48 hours.

Auto-repair classification: REVIEW_AUTO
Triggering agent: watchdog (chronic_fallback_use pattern)
Run count since degradation began: 4
Quality impact: -2 to -3 points per run during degradation

Change is safe to apply autonomously but operator should confirm the new
name is correct for this deployment.
```

**Step 7:** Log the repair

Auto-Repair writes to its state:

```json
{
  "repair_id": "repair-2026-04-20-001",
  "agent": "market-pulse",
  "file": "examples/market-pulse/AGENT.md",
  "change_type": "integration_update",
  "pattern_matched": "dead_source_reference",
  "before": "price-data-mcp-v1",
  "after": "price-data-mcp-v2",
  "reason": "Primary source renamed in fleet MCP config 3 days ago; agent configuration not updated",
  "timestamp": "[ISO]",
  "git_commit": "[commit hash]",
  "triggering_alert": "watchdog chronic_fallback_use"
}
```

**Step 8:** Post to fleet operations channel

```markdown
# Fleet Auto-Repair — [DATE] [TIME]
Agents scanned: 15 | Repairs applied: 1 | Escalations: 0

## Repairs Applied
| Agent | Change | Reason |
|-------|--------|--------|
| market-pulse | Updated primary source from price-data-mcp-v1 to price-data-mcp-v2 | Source renamed in fleet MCP config 3 days ago |

## Detail
market-pulse was the agent flagged by Watchdog earlier today for chronic fallback use.
Root cause: primary source reference pointed to a renamed integration.
Fix classification: REVIEW_AUTO (unambiguous repoint, operator visibility appropriate).
Commit: [hash]

Expected effect: market-pulse quality should return to 8–9 range on next run.
Will validate via quality trend monitoring over next 3 runs.

---
Health: Agents scanned: 15/15 | Fallbacks: 0 | Quality: 10/10
```

---

### Run 8 (Tuesday 6:00 PM) — Market Pulse next scheduled run

Market-pulse runs on its normal 6 PM schedule. Primary source reference now correct. Load state, gather data:

- Primary source: hit (fresh real-time data)
- Fallbacks: 0
- Quality: 9/10

Output posts normally. Quality score written to data layer.

---

### Run 9 (Wednesday 6:00 AM) — Validation

Watchdog's next run. Reads the updated quality trend:

```
market-pulse | 2026-04-20T12:00 | 6 | 1
market-pulse | 2026-04-20T18:00 | 9 | 0
market-pulse | 2026-04-21T06:00 | 9 | 0
```

Pattern: recovery confirmed. Fallback count returned to 0. Quality restored to 9.

Watchdog posts to fleet operations:

```markdown
:white_check_mark: Watchdog — Recovery Confirmed

Agent: market-pulse
Repair validated: Quality returned to baseline (9/10) on last 2 runs, fallbacks at 0.
Escalation closed.

Escalation timeline:
- [ISO] — First flagged (chronic fallback use)
- [ISO] — Auto-Repair diagnosed and applied REVIEW_AUTO fix
- [ISO] — Validation run confirmed recovery
- [ISO] — Escalation closed

No operator intervention required. Logging for audit trail.
```

---

## What Happened End-to-End

From silent degradation through detection, diagnosis, repair, and validation — all autonomous:

1. **Agent degraded silently** for 4 runs over 24 hours. No individual run was a failure.
2. **Watchdog detected the pattern** via data-layer query on fallback and quality trends.
3. **Auto-Repair diagnosed the root cause** by cross-referencing the agent's config against the current fleet MCP config.
4. **Fix was classified REVIEW_AUTO** (safe to apply autonomously, but operator should see it).
5. **Fix was committed** with a descriptive message citing the triggering pattern.
6. **Validation confirmed** the quality return over the next 2 runs.
7. **Full audit trail** exists in the repair log, the Watchdog's escalation log, and git history.

Operator time spent: zero. Operator awareness: the repair commit + the two channel posts. If the operator chooses to review, the full context is available in under a minute.

---

## What Could Have Gone Wrong Without This Pattern

Several failure modes this pattern prevents:

**Silent drift.** Without Watchdog tracking quality trends, the agent would have continued operating at degraded quality indefinitely. The operator might eventually notice outputs were less sharp, but might not trace to the root cause.

**Manual diagnostic labor.** Even with a Watchdog alert, without Auto-Repair the operator would need to manually check the agent's config, cross-reference the fleet MCP list, identify the rename, and edit the config. Easily 30–60 minutes of labor for a 1-line fix.

**Escalation fatigue.** If every minor drift required operator attention, the operator would stop reading Watchdog alerts. Auto-Repair handling SAFE_AUTO and REVIEW_AUTO fixes autonomously means only true ESCALATE cases reach the operator — preserving attention for things that genuinely need judgment.

**Loss of audit trail.** Without a structured repair log + git commits, the fleet's evolution would be undocumented. Six months from now, "when did we rename that integration?" would be unanswerable.

---

## When the Pattern Escalates Instead of Repairs

Not every finding is auto-repairable. If the same degradation pattern had a different root cause — say, the primary source still exists but is returning unusable data, or the agent's entire gather step has a logic error — Auto-Repair would escalate rather than fix:

```markdown
## Escalations (operator review needed)
### market-pulse — chronic fallback use, cause unclear
Finding: Quality trend degraded 9→6 over last 5 runs, fallback count consistently 1.
Auto-Repair diagnostic: Primary source reference is valid, integration is configured,
integration returns 200 OK but data format may have changed.
Recommended fix: Manually verify source data format against agent parsing logic.
Why not auto-applied: Data-format parsing changes require testing; not safe for
autonomous fix.
```

The operator would then decide whether to fix, accept temporarily, or rewrite. Auto-Repair's role is handling the unambiguous cases and surfacing the ambiguous ones.

---

## What This Demonstrates

**Pattern detection > single-run alerting.** The real value of the Watchdog + Auto-Repair pair is catching issues no individual agent or run could surface. Trends are the signal.

**Classification discipline.** Auto-Repair's safety model is entirely built on the SAFE_AUTO / REVIEW_AUTO / ESCALATE classification. Bypassing it — being too aggressive about auto-fix — would be the primary way this pattern goes wrong.

**Observability as first-class output.** Every step of the pattern (degradation, detection, diagnosis, fix, validation) produced output to channels and logs. Nothing happened invisibly.

**Autonomous but audited.** Zero operator time spent, but full audit trail in git + repair log + escalation log. The operator can review retroactively if curious, or ignore entirely if trust in the pattern has been established.

---

## Related Patterns

- [Self-Repair](../patterns/self-repair.md)
- [Fallback Chains](../patterns/fallback-chains.md)
- [Quality Self-Rating](../patterns/quality-self-rating.md)
- [JIT Budget Management](../patterns/jit-budget-management.md)
