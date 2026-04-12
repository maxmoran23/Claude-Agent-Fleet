# Fleet Operations

Operational patterns, observability, and self-repair documentation for the Claude Agent Fleet.

---

## Production Execution Cycle

Every agent follows the same 8-step execution cycle, regardless of domain or schedule:

```
STEP 0 ──▶ STEP 1 ──▶ STEP 2 ──▶ STEP 3 ──▶ STEP 4 ──▶ STEP 5 ──▶ STEP 6 ──▶ STEP 7
Load       Gather     Analyze    Format     Post to    Update     Write to    Persist
State      Data       & Rate     Output     Channel    Dashboard  Database    State
           (w/fallback)                                (canvas)   (Notion)    (canvas)
```

### Step 0: Load State
- Agent reads its section from the relevant state store canvas
- Retrieves: last run timestamp, prior findings, running state (e.g., portfolio positions, known enforcement actions)
- If state store is unavailable, agent proceeds with empty state (graceful degradation)

### Steps 1-5: Execute
- Gather data from assigned sources using fallback chains
- If primary source fails, fall back to secondary, then tertiary
- Analyze gathered data in context of prior state
- Self-rate output quality on a 1-10 scale based on source availability and analysis depth

### Step 6: Deliver
- Post full report to assigned Slack channel
- Update display canvas dashboard (section-level only — never overwrite other agents' sections)
- Write findings (severity >= MEDIUM) to shared Notion database
- Send emails/notes for brief agents
- Flag CRITICAL findings for escalation

### Step 7: Persist State
- Write back to state store canvas: run timestamp, key state changes, quality score, sources used
- This becomes Step 0 input for the next run

---

## Fallback Chains

Every data source has a degradation path. Agents never hard-fail on source unavailability:

```
PRIMARY SOURCE
    │
    ├── Available? ──▶ Use it, proceed normally
    │
    └── Unavailable?
            │
            ├── SECONDARY SOURCE
            │       │
            │       ├── Available? ──▶ Use it, note fallback in health footer
            │       │
            │       └── Unavailable?
            │               │
            │               ├── TERTIARY SOURCE (web search, cached data)
            │               │       │
            │               │       └── Use it, flag DEGRADED quality
            │               │
            │               └── ALL SOURCES DOWN
            │                       │
            │                       └── Post state-only update, flag in health footer
            │                           Quality self-rating: 1-3/10
```

**Result:** In 6+ weeks of production operation, no agent has ever fully failed to produce output. Degraded runs happen occasionally; total failures have not occurred.

---

## Observability Layer

### Watchdog Agent (runs every 3 hours)
Dedicated fleet health monitor that:

- Scans all agent run logs from fleet state store
- Tracks missed runs (agent didn't execute on schedule)
- Monitors data source uptime across the fleet
- Calculates fleet-wide quality score (average of all agents' self-ratings)
- Detects quality drift (trending downward over time)
- Posts health report to fleet channel
- Escalates to DM if fleet health is degraded

### Health Footer (every agent, every run)
Every output includes a standardized footer:

```
─── Health ───────────────────────────────────
Sources: Crypto.com (OK), LunarCrush (OK), Blockscout (FALLBACK: web search)
Fallbacks triggered: 1 of 3 sources
Quality self-rating: 7/10
Runtime: 45s
Last run: 2026-04-12T06:00:00Z
──────────────────────────────────────────────
```

### Fleet State Store
Centralized canvas where every agent logs:
- Run timestamp
- Sources used / fallbacks triggered
- Quality self-rating
- Key state changes
- Error conditions

This creates a queryable operational history across the entire fleet.

---

## Self-Repair

### Fleet Auto-Repair Agent (runs every 4 hours)
This agent doesn't just alert on problems — it fixes them autonomously:

**What it scans:**
- All 38 agent configuration files
- Model specifications (must be `claude-opus-4-6[1m]`)
- Channel routing (correct Slack channel IDs)
- Email delivery configuration
- State store read/write references
- Required sections and formatting

**What it fixes:**
- Model downgrades → restores to Opus 4.6
- Broken channel references → corrects to canonical IDs
- Missing configuration sections → regenerates from template
- Formatting drift → standardizes

**What it escalates:**
- Issues it cannot fix automatically
- Structural problems requiring human decision
- Repeated failures of the same agent

**Reporting:**
- Posts repair log to fleet channel
- DMs operator if critical issues found
- Tracks repair history in fleet state store

---

## Escalation Protocol

```
SEVERITY: LOW/MEDIUM
    └──▶ Normal channel post + Notion DB entry

SEVERITY: HIGH  
    └──▶ Channel post + Notion DB + flagged in daily brief

SEVERITY: CRITICAL
    └──▶ Channel post + Notion DB + direct DM + #alerts channel
         + Calendar event (if time-sensitive)
```

Any agent can trigger any severity level. The Smart Thread Responder cross-references CRITICAL findings across channels to ensure nothing is missed in isolation.

---

## Fleet Scaling Pattern

Adding a new agent to the fleet follows a repeatable process:

1. Create agent directory with AGENT.md (fully self-contained instructions)
2. Add HTML report template (if Cortex-type agent)
3. Create scheduled task with appropriate cron schedule
4. Assign to Slack channel and display canvas section
5. Add state store section for persistent memory
6. Watchdog automatically begins monitoring on next health scan
7. Auto-Repair automatically begins config scanning on next repair cycle

**Time to add a new agent:** typically under 1 hour from concept to production, including testing.

The fleet has grown from an initial proof of concept to 38 agents over approximately 6 weeks, with the infrastructure patterns stabilizing around week 3 and the focus shifting to domain coverage and delivery quality.

---

## Operational Metrics

| Metric | Current State |
|--------|--------------|
| Fleet uptime | Near-continuous since initial deployment |
| Agents requiring manual intervention | Rare — Auto-Repair handles most issues |
| Average agent quality self-rating | Tracked per-run in fleet state store |
| Data source availability | Tracked per-source by Watchdog |
| Mean time to new agent deployment | < 1 hour |
| Escalation rate (CRITICAL findings) | ~2-5 per week across fleet |
