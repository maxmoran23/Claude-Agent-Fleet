# Architecture

System design documentation for the Claude Agent Fleet — a framework for running autonomous agent fleets on Claude Code.

---

## Design Principles

Four principles guide every architectural decision. They compound — the framework's value comes from all four holding simultaneously.

### 1. Zero-infrastructure

No servers, no databases (beyond a local SQLite file), no deployment pipelines. The system runs on Claude Code scheduled tasks and commodity SaaS tools (Slack, optionally Gmail, optionally Notion). A fleet can be deployed, operated, and extended without standing up any new infrastructure.

### 2. Self-contained agents

Every agent is a complete, independent unit. No agent depends on another agent's files, output, or availability. Any agent can fail, be modified, or be removed without cascading effects. Cross-agent communication happens through shared state stores (Slack Canvases, SQLite tables) rather than direct calls.

This is what lets a fleet scale from 3 agents to 30+ without the operator rebuilding orchestration. Each agent is a drop-in unit.

### 3. The fleet maintains itself

Observability, repair, evolution, and budget management are not bolted-on afterthoughts. They are agents in the fleet, running the same architecture, following the same patterns. The Watchdog watches the fleet. The Auto-Repair agent fixes the fleet. The Synthesis Engine makes sense of the fleet. All of them are just agents.

This principle means: the fleet scales without the operator adding orchestration layers. New operational capability is added by adding more agents.

### 4. Degrade gracefully under pressure

Whether a data source goes down or the token budget gets tight, the system reduces scope rather than failing. Fallback chains handle source outages. JIT budget management handles resource limits. Output quality is sacred; frequency is the lever.

This is non-negotiable: under pressure, the fleet produces less output at the same quality, never more output at lower quality.

---

## Pattern Deep-Dives

The architectural patterns that implement these principles are documented individually:

- **[State Management](docs/patterns/state-management.md)** — state authority and projections (local files as truth, canvases as mirrors)
- **[Agent Kernel](docs/patterns/agent-kernel.md)** — versioned contract + shared helpers replacing per-agent boilerplate
- **[Fallback Chains](docs/patterns/fallback-chains.md)** — graceful source degradation
- **[Quality Self-Rating](docs/patterns/quality-self-rating.md)** — per-run self-assessment
- **[Evaluation Harness](docs/patterns/evaluation-harness.md)** — independent rubric scoring of published output
- **[Idempotency Outbox](docs/patterns/idempotency-outbox.md)** — claim/confirm dedup for non-idempotent sends
- **[Execution Scaffolding](docs/patterns/execution-scaffolding.md)** — threshold-triggered action packages
- **[JIT Budget Management](docs/patterns/jit-budget-management.md)** — autonomous throttle protocol
- **[Self-Repair](docs/patterns/self-repair.md)** — autonomous configuration healing
- **[Propose-and-Gate](docs/patterns/propose-and-gate.md)** — human-gated, revertible self-modification
- **[Generated Registry](docs/patterns/generated-registry.md)** — generated inventory, drift detection, deadman liveness
- **[Fleet Evolution](docs/patterns/fleet-evolution.md)** — maturity framework and bounded upgrade cycles
- **[Visual Cards](docs/patterns/visual-cards.md)** — inline PNG dashboard cards

And the schemas that define the framework's data contracts:

- **[Data Layer Schema](schemas/data-layer.sql)**
- **[Slack Canvas Structure](schemas/slack-canvas-structure.md)**
- **[Notion Intelligence Feed](schemas/notion-intelligence-feed.md)**
- **[Agent Skill Frontmatter](schemas/agent-skill-frontmatter.md)**

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
│  │  │Task 1  │ │Task 2  │ │Task 3  │ │Task N  │           │   │
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

### The Solution: One Authority, Multiple Projections

Earlier revisions of this framework treated Slack canvases as the source of truth for live state. That design failed in production: canvases hit platform write-saturation limits and began rejecting appends, and because they were authoritative, agents silently lost persistence. The current architecture designates exactly one authority and demotes everything else to projections.

**Authority: Local State Files** — Each agent owns `state/state.json` in its own directory: durable, atomically written (temp file + rename), version-stamped, with a 30-day rolling history for recovery. Kernel helpers implement the load (Step 0) and persist (Step 7) protocol, including explicit corruption handling — a state file that fails to decode is treated as first-run and preserved, never overwritten. A generated `state-index.json` tracks which agents have state and how fresh it is.

**Projection: Slack Canvases** — Real-time display dashboards mirrored at Step 7. Each agent owns its section; writes are section-level and *non-fatal* — a canvas failure degrades the display, never the state.

**Projection: SQLite Data Layer** — An append-only database (11 tables) serves as the permanent record and answers "what was true on date X?" Designed to be migration-compatible with hosted databases.

```
┌──────────────────────────────────────────────────────┐
│       AUTHORITY: LOCAL STATE FILES                   │
│                                                      │
│  {agent}/state/state.json                            │
│  - Atomic writes (tmp + rename), stamped with        │
│    agent, last_run, kernel_version                   │
│  - state/history/ snapshots, 30-day retention        │
│  - Fleet-wide state-index.json registry              │
│                                                      │
│  PROTOCOL:                                           │
│  - Step 0: kernel loader -> loaded | FIRST_RUN |     │
│    corrupt (treat as first-run, never overwrite)     │
│  - Step 7: kernel persist, THEN mirror to canvas     │
└──────────────┬───────────────────────────────────────┘
               │ projects to
               ▼
┌──────────────────────────────────────────────────────┐
│  PROJECTION 1: DISPLAY CANVASES (human glanceable)   │
│  Market / Regulatory / Fleet / Analytics sections    │
│  Section-level mirror writes — failure is non-fatal  │
├──────────────────────────────────────────────────────┤
│  PROJECTION 2: HISTORICAL STATE (SQLite)             │
│  11 tables: fleet_metrics, market_snapshots,         │
│  predictions, portfolio_snapshots, agent_runs,       │
│  regulatory_events, betting_edges,                   │
│  opportunity_pipeline, execution_outcomes,           │
│  upgrade_experiments, attention_audit                │
│  - Step 6.5: Append-only writes after delivery       │
│  - Fleet Query reads for historical/trend questions  │
│  - Daily backup to cloud storage                     │
└──────────────────────────────────────────────────────┘
```

**Why local files for authority instead of canvases?**
- Saturation-proof — platform write limits degrade the display, not the memory
- Atomic and recoverable — temp-file writes plus a rolling history directory
- Inspectable and versionable — state changes show up in version control like any other diff

**Why keep canvases at all?**
- Human-readable — open a canvas and see exactly what any agent "remembers"
- Cross-agent context — agents read sibling sections at Step 0 (advisory, never blocking)
- No infrastructure to maintain; read/write via existing MCP tools

**Why SQLite for history instead of a hosted database?**
- Zero setup, zero cost, zero network dependency
- Schema is Supabase/Postgres-compatible — migration-ready when scale demands it
- Agents write via simple bash commands (sqlite3) — no ORM, no SDK
- Fleet Query agent reads via `sqlite3 -json` for structured historical queries

Full pattern: [docs/patterns/state-management.md](docs/patterns/state-management.md).

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
    Agents analyze, synthesize, cross-reference

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

This is a critical design choice. Traditional multi-agent systems often create tight coupling through shared utilities, common configs, or direct agent-to-agent calls. This fleet deliberately avoids all of that. The benefit is absolute fault isolation. The historical cost — duplicated boilerplate across agent configs — is addressed by the [agent kernel](docs/patterns/agent-kernel.md): shared *mechanical* helpers (state load/persist, footers, dedup guards) without shared *domain* logic, so a kernel outage degrades gracefully while agents remain independently deletable.

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

**Delivery consolidation pattern:** Multiple individual email agents can be replaced by a single digest aggregator agent that reads all Slack channel activity and produces consolidated HTML emails on a fixed cadence (e.g., morning + evening). This reduces daily touchpoints while maintaining information density — fewer notifications delivering the same intelligence.

---

## JIT Budget Management Architecture

Every agent declares one of four model-policy tiers (premium-locked, standard-locked, standard-preferred, efficient-ok); runs are weighted by tier in the burn-rate math, and no model is ever changed silently — drift detection flags any run below an agent's declared tier. Prompts are never trimmed. The budget lever is frequency first, with declared-tier model recommendations only under sustained pressure.

```
WATCHDOG (4x/day)
    │
    ├── Count all agent posts across channels this billing week
    ├── Calculate burn rate (runs/hour)
    ├── Project weekly total
    ├── Compare against the configured weekly-target
    │
    └── Determine JIT level:
        │
        ├── NORMAL (≤ target)    -> All agents at baseline
        ├── GREEN  (1.0-1.2x)   -> Pause P3 luxury agents
        ├── YELLOW (1.2-1.5x)   -> Throttle P2 high-frequency agents
        └── RED    (> 1.5x)     -> Protect only P0 core agents
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
