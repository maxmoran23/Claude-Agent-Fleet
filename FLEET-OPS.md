# Fleet Operations

Operational patterns, observability, self-repair, and budget management documentation for the Claude Agent Fleet.

---

## Production Execution Cycle

Every agent follows the same execution cycle, regardless of domain or schedule:

```
STEP 0 --> STEP 1-3 ------> STEP 4 --> STEP 5 --> STEP 6 --> STEP 6.5 --> STEP 7
Load       Gather, Analyze,  Post to    Update     Write to   Write to     Persist
State      Rate Severity     Channel    Dashboard  Notion DB  Data Layer   State
(canvas)   (w/fallback)                 (canvas)              (SQLite)     (canvas)
```

### Step 0: Load State
- Agent reads its section from the relevant state store canvas
- Retrieves: last run timestamp, prior findings, running state (e.g., portfolio positions, known enforcement actions)
- Also queries the SQLite data layer for historical context if the analysis requires trend data
- If state store is unavailable, agent proceeds with empty state (graceful degradation)

### Steps 1-3: Gather, Analyze, Rate
- Gather data from assigned sources using fallback chains
- If primary source fails, fall back to secondary, then tertiary
- Analyze gathered data in context of prior state — detect deltas, not just snapshots
- Rate findings by severity (CRITICAL / HIGH / MEDIUM / LOW)
- Self-rate output quality on a 1-10 scale based on source availability and analysis depth

### Step 4: Post to Channel
- Full report to assigned Slack channel with threading discipline
- Embed visual cards (dynamic PNG images) where applicable
- Flag CRITICAL findings for escalation routing

### Step 5: Update Dashboard
- Update display canvas dashboard (section-level only — never overwrite other agents' sections)

### Step 6: Write to Database
- Write findings (severity >= MEDIUM) to shared Notion database with structured metadata

### Step 6.5: Write to Data Layer
- Append-only write to SQLite: universal `agent_runs` row (every agent, every run) plus domain-specific table writes
- This is the permanent historical record

### Step 7: Persist State
- Write back to state store canvas: run timestamp, key state changes, quality score, sources used
- Update JIT budget state (run count, burn rate metrics)
- This becomes Step 0 input for the next run

---

## Fallback Chains

Every data source has a degradation path. Agents never hard-fail on source unavailability:

```
PRIMARY SOURCE
    |
    +-- Available? --> Use it, proceed normally
    |
    +-- Unavailable?
            |
            +-- SECONDARY SOURCE
            |       |
            |       +-- Available? --> Use it, note fallback in health footer
            |       |
            |       +-- Unavailable?
            |               |
            |               +-- TERTIARY SOURCE (web search, cached data)
            |               |       |
            |               |       +-- Use it, flag DEGRADED quality
            |               |
            |               +-- ALL SOURCES DOWN
            |                       |
            |                       +-- Post state-only update, flag in health footer
            |                           Quality self-rating: 1-3/10
```

In 9+ weeks of production operation, no agent has fully failed to produce output. Degraded runs happen occasionally; total failures have not occurred.

---

## Observability Layer

### Watchdog Agent (runs 4x/day)
Dedicated fleet health monitor and JIT budget manager:

- Scans all agent run logs from fleet state store
- Tracks missed runs (agent didn't execute on schedule)
- Monitors data source uptime across the fleet
- Calculates fleet-wide quality score (average of all agents' self-ratings)
- Detects quality drift (trending downward over time)
- Runs JIT budget analysis (see Budget Management section below)
- Posts health report to fleet channel
- Escalates to DM if fleet health is degraded or JIT level changes

### Health Footer (every agent, every run)
Every output includes a standardized footer:

```
--- Health ------------------------------------------------
Sources: Crypto.com (OK), LunarCrush (OK), Blockscout (FALLBACK: web search)
Fallbacks triggered: 1 of 3 sources
Quality self-rating: 7/10
Runtime: 45s
Last run: 2026-04-15T06:00:00Z
-----------------------------------------------------------
```

### Fleet State Store
Centralized canvas where every agent logs:
- Run timestamp, sources used, fallbacks triggered
- Quality self-rating, key state changes
- Error conditions and recovery actions
- JIT budget state (current level, burn rate, projections)

### Data Layer (SQLite)
Permanent structured history:
- `agent_runs` table: every run from every agent, with quality scores and metadata
- Domain tables: market snapshots, regulatory events, portfolio state, predictions
- Queryable by Fleet Query agent for historical/trend questions
- Backed up daily to cloud storage

---

## Self-Repair

### Fleet Auto-Repair Agent (runs 3x/day)
This agent doesn't just alert on problems — it fixes them autonomously:

**What it scans:**
- All agent configuration files
- Model specifications (must be Opus 4.6 1M)
- Channel routing (correct Slack channel IDs)
- State store read/write references
- Required sections and formatting

**What it fixes:**
- Model downgrades -> restores to Opus 4.6
- Broken channel references -> corrects to canonical IDs
- Missing configuration sections -> regenerates from template
- Formatting drift -> standardizes
- Auto-commits fixes to version control

**What it escalates:**
- Issues it cannot fix automatically
- Structural problems requiring human decision
- Repeated failures of the same agent

### Fleet Evolution Engine (weekly)
Assesses each agent against a 5-level maturity framework (SCOUT through MASTER). Identifies the highest-impact upgrade across the fleet and implements it autonomously. Tracks upgrade experiments and outcomes in the data layer.

### Feedback Harvester (daily)
Tracks emoji reactions on agent posts across all channels. Calculates engagement scores per agent to measure which intelligence outputs are actually valued by the operator. Feeds into the Evolution Engine's prioritization.

---

## JIT Budget Management

The fleet runs all agents on Opus 4.6 (1M context). The budget lever is **frequency, never quality.**

### How It Works

The Watchdog agent counts total fleet runs per billing week and projects burn rate against an 800 run/week target:

```
burn_rate = observed_runs / hours_elapsed_this_week
projected = burn_rate * 168 (hours/week)
budget_ratio = projected / 800
```

### Priority Tiers

| Tier | Agents | Throttle Behavior |
|------|--------|-------------------|
| **P0 (sacred)** | 7 core agents — daily brief, market maven, regulatory oracle, edge hunter, email intelligence, sim trader, email digest | Never throttled. These produce unique, actionable, time-sensitive output. |
| **P1 (protect)** | Alpha Lab, onchain watchlist, synthesis engine, alt-coin scout, meeting prep, calendar alerts, opportunity radar | Frequency can flex under pressure. Reduced to 1x/day max at RED level. |
| **P2 (throttle early)** | Fleet Query, headline flash, auto-repair, fleet relay, alert scan, thread responder, market pulse, catch-up digest | High-frequency agents where wider intervals don't materially impact utility. |
| **P3 (luxury)** | Research trawls, innovation sparks, engagement tracking, portfolio tracker | First to pause — valuable but not urgent. |

### Escalation Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **NORMAL** | budget_ratio <= 1.0 | All agents at baseline frequencies |
| **GREEN** | 1.0 - 1.2x | Pause P3 agents |
| **YELLOW** | 1.2 - 1.5x | Also throttle P2 to wider intervals |
| **RED** | > 1.5x | Protect only P0; pause or minimize everything else |

De-escalation is automatic when burn rate drops. Manual override available via DM.

### Design Rationale

The JIT system exists because running 50 agents on Opus 4.6 at naive frequencies would consume ~1,900 runs/week. A token consumption diagnostic identified that:

- A single agent (interactive Q&A, originally at 5-minute intervals) accounted for 63% of all runs
- Several research/enrichment agents ran daily but produced near-identical output on consecutive days
- Some agents duplicated each other's work (4 agents surfacing the same prices in the same morning window)

Optimizing frequencies — without changing any model, prompt, or output format — reduced the fleet to ~800 runs/week. The JIT protocol ensures this stays sustainable even as new agents are added or usage patterns shift.

---

## Escalation Protocol

```
SEVERITY: LOW/MEDIUM
    +---> Normal channel post + database entry

SEVERITY: HIGH
    +---> Channel post + database + flagged in daily brief

SEVERITY: CRITICAL
    +---> Channel post + database + direct DM + #alerts channel
          + Calendar event (if time-sensitive)
```

Any agent can trigger any severity level. The Smart Thread Responder cross-references CRITICAL findings across channels to ensure nothing is missed in isolation.

---

## Fleet Scaling Pattern

Adding a new agent to the fleet follows a repeatable process:

1. Create agent directory with configuration file (fully self-contained instructions)
2. Add HTML report template (if Cortex-type agent)
3. Create scheduled task with appropriate cron schedule and priority tier assignment
4. Assign to Slack channel and display canvas section
5. Add state store section for persistent memory
6. Watchdog automatically begins monitoring on next health scan
7. Auto-Repair automatically begins config scanning on next repair cycle
8. Evolution Engine includes in next weekly maturity assessment

Time to deploy a new agent: typically under 1 hour from concept to production, including testing.

---

## Operational Metrics

| Metric | Current State |
|--------|--------------|
| Fleet uptime | Near-continuous since initial deployment (9+ weeks) |
| Agents requiring manual intervention | Rare — Auto-Repair handles most issues |
| Weekly run budget | ~800, JIT-managed |
| Self-repair coverage | All agent configs scanned 3x/day |
| Health monitoring frequency | 4x/day (includes budget analysis) |
| Evolution cycle | Weekly autonomous maturity assessment + upgrade |
| Data retention | SQLite (indefinite) + Canvas (current state) + Notion (archive) |
| Mean time to new agent deployment | < 1 hour |
