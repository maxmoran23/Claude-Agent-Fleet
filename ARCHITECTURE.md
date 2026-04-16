# Architecture

System design documentation for the Claude Agent Fleet — a 50-agent autonomous system built on Claude Code.

---

## Design Philosophy

Four principles guided every architectural decision:

1. **Zero-infrastructure** — no servers, no databases (beyond a local SQLite file), no deployment pipelines. The system runs on Claude Code scheduled tasks and commodity SaaS tools.

2. **Self-contained agents** — every agent is a complete, independent unit. No agent depends on another agent's files, output, or availability. Any agent can fail, be modified, or be removed without cascading effects.

3. **The fleet maintains itself** — observability, repair, evolution, and budget management are not bolted-on afterthoughts. They are agents in the fleet, running the same architecture, following the same patterns.

4. **Degrade gracefully under pressure** — whether a data source goes down or the token budget gets tight, the system reduces scope rather than failing. Fallback chains handle source outages. JIT budget management handles resource limits. Output quality is sacred; frequency is the lever.

---

## Runtime Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE PLATFORM                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SCHEDULED TASK ENGINE                        │   │
│  │                                                          │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │Task 1  │ │Task 2  │ │Task 3  │ │Task N  │  (46)     │   │
│  │  │cron:8h │ │cron:4h │ │cron:1d │ │cron:20m│           │   │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │   │
│  │      │          │          │          │                  │   │
│  │      ▼          ▼          ▼          ▼                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │Prompt  │ │Prompt  │ │Prompt  │ │Prompt  │           │   │
│  │  │Config  │ │Config  │ │Config  │ │Config  │           │   │
│  │  │(.md)   │ │(.md)   │ │(.md)   │ │(.md)   │           │   │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │   │
│  │      │          │          │          │                  │   │
│  └──────┼──────────┼──────────┼──────────┼──────────────────┘   │
│         │          │          │          │                       │
│         ▼          ▼          ▼          ▼                       │
│    REMOTE EXECUTION (always-on, laptop-independent)             │
└─────────────────────────────────────────────────────────────────┘
```

Agents execute remotely on Anthropic's infrastructure via scheduled tasks. The system does not depend on a laptop being open, a server running, or any local process.

---

## State Management

### The Problem
Agents are stateless by default — each scheduled run is a fresh invocation with no memory of previous runs. Useful intelligence agents need to know what they reported last time, what positions they hold, what they've already seen.

### The Solution: Two-Tier State Architecture

**Tier 1: Live State (Slack Canvases)** — 4 persistent canvases serve as real-time dashboards that agents read from and write to on every run. Each agent owns its section; writes are section-level only (never full-canvas overwrites). This is the "working memory" layer.

**Tier 2: Historical State (SQLite Data Layer)** — An append-only database (11 tables) serves as the permanent record. Canvases show current state; the data layer answers "what was true on date X?" Designed to be migration-compatible with hosted databases.

```
┌──────────────────────────────────────────────────────┐
│           TIER 1: LIVE STATE (4 Canvases)            │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │   Market     │  │ Regulatory  │                   │
│  │   State      │  │   State     │                   │
│  │  Prices,     │  │  Rules,     │                   │
│  │  positions,  │  │  enforcement│                   │
│  │  sentiment   │  │  deadlines  │                   │
│  └─────────────┘  └─────────────┘                   │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │   Fleet      │  │  Analytics  │                   │
│  │   State      │  │   State     │                   │
│  │  Health,     │  │  Signals,   │                   │
│  │  JIT budget, │  │  models,    │                   │
│  │  quality     │  │  tracking   │                   │
│  └─────────────┘  └─────────────┘                   │
│                                                      │
│  PROTOCOL:                                           │
│  - Step 0: Read own section from canvas              │
│  - Step 7: Write back run log + state changes        │
│  - Section-level writes only (never full canvas)     │
│  - Human-readable at all times                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│       TIER 2: HISTORICAL STATE (SQLite)              │
│                                                      │
│  11 tables: fleet_metrics, market_snapshots,         │
│  predictions, portfolio_snapshots, agent_runs,       │
│  regulatory_events, betting_edges,                   │
│  opportunity_pipeline, execution_outcomes,           │
│  upgrade_experiments, attention_audit                 │
│                                                      │
│  PROTOCOL:                                           │
│  - Step 6.5: Append-only writes after delivery       │
│  - Fleet Query reads for historical/trend questions  │
│  - Daily backup to cloud storage                     │
└──────────────────────────────────────────────────────┘
```

**Why Slack Canvases for live state instead of a database?**
- No infrastructure to maintain
- Human-readable — open a canvas and see exactly what any agent "remembers"
- Agents read/write via existing MCP tools
- Survives restarts, reconfigurations, and failures
- Multiple agents can share state without file coupling

**Why SQLite for history instead of a hosted database?**
- Zero setup, zero cost, zero network dependency
- Schema is Supabase/Postgres-compatible — migration-ready when scale demands it
- Agents write via simple bash commands (sqlite3) — no ORM, no SDK
- Fleet Query agent reads via `sqlite3 -json` for structured historical queries

---

## Data Flow Architecture

```
LAYER 1: SOURCES (12+)
    Real-time prices ──┐
    Social sentiment ──┤
    On-chain data ─────┤
    Financial news ────┼──> AGENTS (gather with fallback chains)
    Market tearsheets ─┤
    Email inbox ───────┤
    Calendar ──────────┘

LAYER 2: PROCESSING
    50 agents analyze, synthesize, cross-reference

LAYER 3: OUTPUT ROUTING
    ┌──> Slack topic channels (full reports, threaded)
    │
    ├──> Slack display canvases (living dashboards, section-updated)
    │
    ├──> SQLite data layer (append-only structured history)
    │
    ├──> Notion database (structured findings, severity-tagged archive)
    │
    └──> Email Digest Aggregator -> Gmail (2 consolidated emails/day)

LAYER 4: CROSS-POLLINATION
    Smart Thread Responder reads ALL state stores
    └──> enriches posts with cross-references between channels

    Synthesis Engine reads ALL channel output
    └──> generates fleet-wide meta-analysis daily

    Fleet Query reads ALL stores + channels + data layer
    └──> answers ad-hoc questions with data-cited responses

LAYER 5: ESCALATION
    Any agent can flag CRITICAL findings
    └──> bypasses normal routing -> direct alerts + DM + Calendar

LAYER 6: BUDGET MANAGEMENT
    Watchdog monitors fleet-wide burn rate
    └──> autonomously throttles frequencies across 4 priority tiers
```

---

## Agent Coupling Model

```
                    ┌─────────────────────┐
                    │  SHARED STATE LAYER  │
                    │  (Canvases + SQLite) │
                    └──┬───┬───┬───┬───┬──┘
                       │   │   │   │   │
            ┌──────────┘   │   │   │   └──────────┐
            ▼              ▼   ▼   ▼              ▼
       ┌─────────┐   ┌─────────────────┐   ┌─────────┐
       │ Agent A  │   │   Agent B ...N  │   │ Agent Z  │
       │          │   │                 │   │          │
       │ Own dir  │   │   Own dirs      │   │ Own dir  │
       │ Own conf │   │   Own confs     │   │ Own conf │
       │ Own tmpl │   │   Own tmpls     │   │ Own tmpl │
       └─────────┘   └─────────────────┘   └─────────┘

       NO file dependencies between agents.
       Communication is via state stores + channel posts.
       Agent A can be deleted without affecting Agent Z.
```

This is a critical design choice. Traditional multi-agent systems often create tight coupling through shared utilities, common configs, or direct agent-to-agent calls. This fleet deliberately avoids all of that. The cost is some duplication across agent configs. The benefit is absolute fault isolation.

---

## Delivery Architecture

The delivery pipeline has been consolidated through iteration. The current architecture uses 3 primary delivery apps, down from an initial 5:

| Channel | Purpose | Consumption Pattern |
|---------|---------|-------------------|
| **Slack** | Full reports, threaded discussion, dashboards, visual cards | Primary backbone — desktop and mobile |
| **Gmail** | 2 consolidated digest emails per day (morning + evening) | Mobile scanning — curated highlights |
| **Google Calendar** | Regulatory deadlines, market events | iOS push notifications |

**Supporting systems (not user-facing delivery):**
| System | Purpose |
|--------|---------|
| **SQLite** | Structured historical archive — queryable by Fleet Query |
| **Notion** | Severity-tagged findings database — cross-agent data bus |

**Delivery consolidation history:** Individual email agents (7+) were replaced by a single Email Digest Aggregator that reads all Slack channel activity and produces 2 HTML emails per day. Apple Notes was removed as a delivery channel (notification fatigue). This reduced daily touchpoints while maintaining information density.

---

## JIT Budget Management Architecture

The fleet runs on Opus 4.6 (1M context) for all agents — no model downgrades, no prompt trimming. The budget lever is frequency, not quality.

```
WATCHDOG (4x/day)
    │
    ├── Count all agent posts across channels this billing week
    ├── Calculate burn rate (runs/hour)
    ├── Project weekly total
    ├── Compare against 800 run/week target
    │
    └── Determine JIT level:
        │
        ├── NORMAL (≤ target)    -> All agents at baseline
        ├── GREEN  (1.0-1.2x)   -> Pause P3 luxury agents
        ├── YELLOW (1.2-1.5x)   -> Throttle P2 high-frequency agents
        └── RED    (> 1.5x)     -> Protect only P0 core (7 agents)
```

**Priority tiers:**
- **P0 (sacred):** 7 agents that produce unique, time-sensitive, actionable output — never throttled
- **P1 (protect):** High-value agents where frequency can flex under pressure
- **P2 (throttle early):** Valuable but running more often than strictly necessary
- **P3 (luxury):** Research, enrichment, and engagement tracking — first to pause

De-escalation is automatic. Manual override is available via DM to the fleet.

---

## Why Structured Prompts Instead of Traditional Code?

Every agent in this system is a structured Markdown file that Claude Code executes directly. This was a deliberate choice:

1. **Faster iteration** — modifying agent behavior means editing English, not debugging code
2. **No dependency management** — no packages, no versions, no breaking updates
3. **No deployment pipeline** — changes take effect on next scheduled run
4. **Native tool integration** — MCP servers provide direct access to external services without API wrappers
5. **Audit-readable** — anyone can open an agent config and understand exactly what it does

The tradeoff is platform dependency on Claude Code. This is an acceptable constraint for a system designed to demonstrate what autonomous agent orchestration looks like when architectural thinking is applied to prompt engineering.
