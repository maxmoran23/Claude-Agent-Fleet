# Fleet Operations

Operational patterns, observability, self-repair, and budget management documentation for the Claude Agent Fleet.

---

## Production Execution Cycle

Every agent follows the same execution cycle, regardless of domain or schedule:

```
STEP 0 --> STEP 1-3 ------> STEP 4 --> STEP 5 --> STEP 6 --> STEP 6.5 --> STEP 7
Load       Gather, Analyze,  Post to    Update     Write to   Write to     Persist
State      Rate Severity     Channel    Dashboard  Notion DB  Data Layer   State
(local     (w/fallback)                 (canvas               (SQLite)     (local file
 file)                                   mirror)                            + mirrors)
```

The mechanical steps of this cycle — state load, state persistence, the health footer, and the idempotency guard — are implemented as shared kernel helpers rather than per-agent prose. See [`docs/patterns/agent-kernel.md`](docs/patterns/agent-kernel.md).

### Step 0: Load State
- Agent loads its local `state/state.json` (the authoritative inter-run memory) plus its last 3 runs from the SQLite data layer, in one kernel helper call
- The loader returns an explicit status: `loaded`, `FIRST_RUN`, or `corrupt — treat as first_run, do not overwrite` (corruption is loud and non-destructive)
- Retrieves: last run timestamp, prior findings, running state (e.g., portfolio positions, known enforcement actions)
- Optionally reads state store canvases for cross-agent context — that read is advisory and a failure never blocks the run

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
- Write inter-run state to the local authority file (`state/state.json`) via the kernel helper: atomic write, timestamp/version stamping, 30-day history snapshot, fleet state-index update
- Then mirror a compact snapshot to the display canvas — explicitly non-fatal; a canvas failure never loses state (see [`docs/patterns/state-management.md`](docs/patterns/state-management.md))
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

### Fleet State Store (display projection)
Centralized canvas where every agent mirrors:
- Run timestamp, sources used, fallbacks triggered
- Quality self-rating, key state changes
- Error conditions and recovery actions
- JIT budget state (current level, burn rate, projections)

The canvas is a human-glanceable projection, not the system of record — authoritative liveness evidence lives in each agent's local state file (tracked fleet-wide in a generated `state-index.json`) and in the SQLite run history.

### Deadman Liveness Check (out-of-band)
The watchdog catches agents that run and degrade; it cannot catch a fleet that silently stops running — including the watchdog itself. A separate deadman check runs *outside* the fleet's own scheduler chain:

- For every enabled task in the schedule manifest, derive a maximum-silence window from its cron (daily → 30h, every-6h → ~9h, weekly → 8 days), plus a grace period for scheduler jitter
- Check the freshest evidence across two independent sources: the SQLite run history and the state index
- Alert the operator on any agent silent past its window; maintain an explicit exempt list for agents whose work product legitimately never writes run records

See [`docs/patterns/generated-registry.md`](docs/patterns/generated-registry.md) for the full design.

### Measured-Quality Evals
Self-ratings measure process health as the agent perceives it. An independent eval harness scores each agent's actual published output against a weighted structural rubric (0–100), trends the scores over time, and supplies before/after evidence for upgrade experiments. See [`docs/patterns/evaluation-harness.md`](docs/patterns/evaluation-harness.md).

### Generated Fleet Registry
Fleet inventory is generated, never hand-written: a registry generator cross-joins agent directories, the schedule manifest, the live scheduler snapshot, the model policy, the run database, and the state index into a machine-readable registry plus a human index with an auto-computed drift section. It runs inside the self-repair cycle, so spec-vs-runtime drift surfaces within hours instead of waiting for an audit. See [`docs/patterns/generated-registry.md`](docs/patterns/generated-registry.md).

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
- Model assignments against each agent's declared model-policy tier (see below)
- Channel routing (correct Slack channel IDs)
- State store read/write references and kernel version declarations
- Required sections and formatting
- The generated fleet registry (regenerated each cycle; its drift section becomes findings)

**What it fixes:**
- Broken channel references -> corrects to canonical IDs
- Missing configuration sections -> regenerates from template
- Formatting drift -> standardizes
- Auto-commits fixes to version control

**What it flags (declared-intent drift, human decides):**
- Model drift -> an agent ran on a model below its declared policy tier (runtime model lives in the scheduler UI, so the fix is a human action)
- Schedule drift -> manifest vs live scheduler mismatches, including the missing-task signature of a scheduler-state wipe

**What it escalates:**
- Issues it cannot fix automatically
- Structural problems requiring human decision
- Repeated failures of the same agent

### Fleet Evolution Engine (weekly)
Assesses each agent against a 5-level maturity framework (L1 SCOUT → L5 MASTER). Identifies the highest-impact upgrades across the fleet and routes them through a propose-and-gate workflow: complete proposal packages (proposed file, rationale, diff) on a dedicated branch, human approval by reaction vote, then isolated one-commit applications that are trivially revertible. Tracks each applied upgrade as a structured experiment with pre- and post-upgrade metrics in the data layer; evaluates outcomes after a two-week window and rolls back upgrades that didn't pay off.

See [`docs/patterns/fleet-evolution.md`](docs/patterns/fleet-evolution.md) for the level definitions and scoring criteria, and [`docs/patterns/propose-and-gate.md`](docs/patterns/propose-and-gate.md) for the change-control workflow.

### Feedback Harvester (daily)
Tracks emoji reactions on agent posts across all channels. Calculates engagement scores per agent to measure which intelligence outputs are actually valued by the operator. Feeds into the Evolution Engine's prioritization.

---

## JIT Budget Management

The budget lever is **frequency first, never silent quality loss.** Prompts are never trimmed, and a model change is never made silently — every agent declares a model-policy tier, and the budget manager works within those declarations.

### Model Policy Tiers

Each agent declares one of four intent tiers in a fleet-wide policy file:

| Tier | Meaning | JIT run weight | Drift detection |
|------|---------|----------------|-----------------|
| **premium-locked** | Deep-reasoning agents that must run on the top model | 2.0 | Flagged if a run used anything else |
| **standard-locked** | Money-on-line or compliance-critical work; standard premium model required | 1.0 | Flagged if a run used a lower tier |
| **standard-preferred** | Premium baseline, efficient model tolerated | 1.0 | Never flagged; eligible for downgrade recommendation under YELLOW/RED |
| **efficient-ok** | The efficient model is the intended choice | 0.2 | Never flagged |

The policy file declares *intent*; the runtime model is set in the scheduler UI. Drift detection (auto-repair + generated registry) closes the loop between the two, and run-weighting feeds the burn-rate math below so a premium-locked run counts more heavily against the weekly target.

### How It Works

The Watchdog agent counts total fleet runs per billing week and projects burn rate against a configurable weekly target (set per deployment based on token envelope):

```
burn_rate = observed_runs / hours_elapsed_this_week
projected = burn_rate * 168 (hours/week)
budget_ratio = projected / weekly_target
```

### Priority Tiers

Typical priority tier classification for a mature fleet (adjust for your deployment):

| Tier | Example Agents | Throttle Behavior |
|------|----------------|-------------------|
| **P0 (sacred)** | Daily brief, primary regulatory monitor, critical alert router, digest aggregator, and the watchdog itself | Never throttled. These produce unique, actionable, time-sensitive output the fleet cannot function without. |
| **P1 (protect)** | Market monitor, on-chain watchlist, synthesis engine, regulatory oracle, meeting prep, calendar alerts, auto-repair | Frequency can flex under pressure. Reduced to 1x/day max at RED level. |
| **P2 (throttle early)** | Fleet query, headline flash, market pulse, cross-agent relays, thread enrichers, catch-up digests | High-frequency agents where wider intervals don't materially impact utility. |
| **P3 (luxury)** | Research trawls, innovation/discovery agents, engagement tracking, performance tracking | First to pause — valuable but not urgent. |

### Escalation Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **NORMAL** | budget_ratio <= 1.0 | All agents at baseline frequencies |
| **GREEN** | 1.0 - 1.2x | Pause P3 agents |
| **YELLOW** | 1.2 - 1.5x | Also throttle P2 to wider intervals |
| **RED** | > 1.5x | Protect only P0; pause or minimize everything else |

De-escalation is automatic when burn rate drops. Manual override available via DM.

### Design Rationale

The JIT system exists because running a large agent fleet on a premium model at naive frequencies burns through token budget fast. A typical token consumption diagnostic reveals:

- A small number of high-frequency agents (interactive Q&A, short-interval monitors) account for a disproportionate share of runs — often the majority
- Several research/enrichment agents run daily but produce near-identical output on consecutive days
- Some agents duplicate each other's work (multiple agents surfacing the same data in overlapping time windows)

Optimizing frequencies — without changing any model, prompt, or output format — dramatically reduces weekly run count. The JIT protocol ensures this stays sustainable as new agents are added or usage patterns shift.

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

1. Create agent directory with configuration file (domain logic only — declare the kernel version for the mechanical patterns)
2. Add HTML report template (if the agent produces standalone HTML reports)
3. Create scheduled task with appropriate cron schedule; declare it in the schedule manifest and assign priority tier + model-policy tier
4. Assign to Slack channel and display canvas section
5. Local state (`state/state.json`) initializes itself on first run via the kernel; add a display-canvas section only if human glanceability is wanted
6. Add an eval rubric so measured-quality scoring covers the agent from day one
7. Watchdog and deadman check automatically begin monitoring (the generated registry picks the agent up on its next build)
8. Auto-Repair automatically begins config scanning on next repair cycle
9. Evolution Engine includes in next weekly maturity assessment

Time to deploy a new agent: typically under 1 hour from concept to production, including testing.

---

## Operational Metrics

| Metric | Current State |
|--------|--------------|
| Fleet uptime | Near-continuous since initial deployment (9+ weeks) |
| Agents requiring manual intervention | Rare — Auto-Repair handles most issues |
| Weekly run budget | ~800, JIT-managed |
| Self-repair coverage | All agent configs scanned 3x/day; registry regenerated each cycle |
| Health monitoring frequency | 4x/day (includes budget analysis) + out-of-band deadman liveness check |
| Evolution cycle | Weekly maturity assessment; upgrades gated on human approval, applied as revertible one-commit changes |
| Quality measurement | Per-run self-rating + independent rubric evals (0-100) trended over time |
| Data retention | Local state files (authority, 30-day history) + SQLite (indefinite) + Canvas (display) + Notion (archive) |
| Mean time to new agent deployment | < 1 hour |
