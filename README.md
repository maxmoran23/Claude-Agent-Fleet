# Claude Agent Fleet

**A production-grade framework for building, scheduling, and operating autonomous agent fleets on Claude Code. Self-repairing, self-budgeting, zero traditional code.**

---

## What This Is

A reference architecture for operating multiple autonomous agents as a cohesive intelligence system — covering real-time monitoring, scheduled analysis, workflow automation, and operational self-maintenance. Designed around the idea that a structured natural language prompt executed on a schedule, with persistent memory and self-observability, is a production-viable software component.

Every agent is a structured natural language prompt executed on a schedule. Agents gather live data from external sources, maintain persistent memory across runs via Slack Canvases and a SQLite data layer, rate their own output quality, and — when something breaks — repair themselves without human intervention. A JIT budget manager monitors fleet-wide token consumption and autonomously throttles agent frequencies as resource limits approach, preserving output quality by reducing run count rather than degrading the model or prompt depth.

This repository documents the architecture, design decisions, and operational patterns. Three fully functional example agents are included — copy-paste ready, no API keys required. Production agent configurations running on top of this framework are maintained separately.

---

## What It Does

The framework is built to operate an agent fleet across any domain. Illustrative use cases where this architecture has been applied:

| Domain | Example Agents | Function |
|--------|---------------|----------|
| **Crypto Markets** | Price monitor, macro sentiment, on-chain analytics, virtual portfolio manager, token discovery | Real-time data feeds synthesized into narrative intelligence |
| **Regulatory / AML** | Enforcement tracker, legislation watch, sanctions screening, deadline alerts | Compliance landscape monitoring with structured severity scoring |
| **Research** | Paper translation, cross-domain synthesis, topic discovery | Signal extraction from high-volume research streams |
| **Workflow** | Meeting prep, email triage, channel summarization, interactive Q&A | Active participation in day-to-day work |
| **Delivery** | Consolidated digest aggregator, calendar alerts, critical escalation routing | Many-to-few notification consolidation |
| **Fleet Ops** | Health monitoring, self-repair, budget management, engagement tracking, meta-analysis | The fleet monitoring and maintaining itself |
| **Execution Scaffolding** | Threshold-triggered action packages (pre-filled drafts) | Human-in-the-loop handoff where the agent does the prep work |

Each category can be extended without touching the others — agents communicate through shared state stores rather than direct dependencies, so any agent can fail without cascading.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                            │
│  Real-time prices  Social sentiment  On-chain data           │
│  Financial news  Market tearsheets  Email  Calendar          │
│  Government databases  Regulatory filings                    │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        AGENT FLEET                           │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Analysis │ │ Real-    │ │ Daily    │ │ Workflow │       │
│  │  Engines │ │ Time     │ │ Briefs   │ │ Auto.    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Fleet    │ │ Specialty│ │ Execution│ │ Maint.   │       │
│  │ Infra    │ │ Intel    │ │ Scaf.    │ │ Util.    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Each agent: Load State -> Gather -> Analyze -> Deliver ->   │
│              Update Dashboard -> Write Data Layer ->          │
│              Self-Rate -> Persist State                       │
│                                                              │
│  JIT Budget Manager: Watchdog monitors burn rate,            │
│  autonomously throttles frequencies across 4 priority tiers  │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                          │
│  Slack channels + canvases (primary backbone)                │
│  Consolidated digest emails (morning + evening)              │
│  Calendar (iOS push for deadlines)                           │
│                                                              │
│  Structured archive: SQLite data layer + Notion database     │
└──────────────────────────────────────────────────────────────┘
```

Full architecture documentation: **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## System Capabilities

### Visual Dashboard System
Agents embed dynamic PNG image cards in Slack posts — score gauges, market dashboards, alert cards, fleet status overviews, pipeline funnels, action-package cards. Generated on-the-fly by serverless endpoints using Satori (JSX-to-SVG) + Sharp (SVG-to-PNG). Agents construct URLs with live data parameters; Slack renders inline. Dark theme throughout.

### Execution Scaffolding
Agents can generate pre-filled action packages when findings cross defined thresholds. The pattern: the agent does all the preparation work, then hands a draft to the human for approval. Reduces 90% of the prep overhead while preserving human judgment on anything that creates external effects.

Example threshold-triggered handoffs:
- Regulatory enforcement action above severity threshold → draft response brief with citations, impact analysis, and recommended internal escalation path
- Opportunity detection with fit score above threshold → pre-researched application package (tailored bullets, cover letter draft, checklist)
- Cross-domain synthesis scoring above threshold → full launch-ready concept brief with positioning, segments, and 30-day plan

Everything is a draft. Emoji reactions confirm, skip, or modify. A Feedback Harvester agent tracks execution outcomes to measure real-world impact.

### JIT Budget Management
The Watchdog agent doubles as an autonomous budget manager. It counts fleet-wide runs per week, projects burn rate against a configured target, and escalates through four throttle levels:

| Level | Trigger | Action |
|-------|---------|--------|
| NORMAL | On budget | All agents at baseline frequencies |
| GREEN | Approaching limit | Pause luxury/research agents |
| YELLOW | Over budget | Throttle high-frequency P2 agents (wider intervals) |
| RED | Significant overshoot | Protect only core P0 agents at full schedule |

De-escalation is automatic — when burn rate drops, agents restore to baseline. Manual override available via DM. The key design principle: **reduce frequency, never reduce model or prompt quality.** Output stays the same; it just arrives less often.

### Structured Data Layer
Beyond real-time dashboards (Slack Canvases, overwritten each run), a SQLite database serves as the permanent historical record — tables covering fleet metrics, market snapshots, predictions, portfolio state, regulatory events, and agent performance. Designed to be migration-compatible with hosted databases when ready to scale.

### Conversational Interface
A Fleet Query agent monitors for questions on an interval, reads state stores, channels, and the SQLite data layer, and replies in-thread with data-cited answers. Self-documenting help system with domain menu.

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Runtime | Claude Code scheduled tasks | Always-on remote execution — no server, no laptop dependency |
| State | Slack Canvases as persistent stores | Human-readable, agent-writable, survives restarts, no database required |
| Historical data | SQLite append-only layer | Canvases are dashboards (current state); SQLite is the ledger (what was true on date X) |
| Coupling | Zero file dependencies between agents | Any agent can fail without cascading — total fault isolation |
| Delivery | Consolidated multi-app pipeline | Slack (backbone) + digest emails (2x daily) + calendar (iOS push) |
| Observability | Fleet agents, not external tools | The fleet monitors itself using the same architecture it runs on |
| Self-repair | Autonomous, not alerting-only | Auto-Repair fixes problems, not just flags them |
| Budget | JIT throttle protocol | Reduce run frequency, never model quality — graceful degradation under resource pressure |

---

## Production Patterns

Every agent follows the same execution cycle — see **[FLEET-OPS.md](FLEET-OPS.md)** for full documentation.

```
STEP 0        STEPS 1-5      STEP 6        STEP 6.5       STEP 7
Load State -> Execute ------> Deliver ----> Write Data --> Persist State
(canvas +     (gather,        (channels,    Layer          (write back
 data layer)   analyze,        dashboards,   (SQLite)       run log,
               self-rate)      DB, email)                   quality score)
```

- **Fallback chains** — every source has graceful degradation; no agent hard-fails
- **Quality self-assessment** — agents rate their own output 1-10, flag degraded runs
- **Health footers** — every output includes sources used, fallbacks triggered, quality score, runtime
- **Structured data bus** — all findings (severity >= MEDIUM) written to shared database
- **Escalation routing** — CRITICAL findings bypass normal channels, go direct to alerts + DM
- **JIT-aware** — agents operate within a budget-managed framework; frequency adjusts, quality doesn't

---

## Architecture Evolution

The framework's current form reflects decisions that were iterated, not planned. Three structural lessons worth calling out for anyone building in this direction:

**Delivery consolidation.** Early iterations had many agents each sending individual emails, syncing notes, posting to channels. Volume was working against utility — too many touchpoints caused notification fatigue. The current architecture consolidates all email delivery into a single aggregator (2 emails per day), with Slack as the primary backbone and calendar for time-sensitive pushes. Fewer notifications, same information density.

**JIT budget management.** Running many agents on a premium model at naive frequencies burns token budget fast. A token consumption diagnostic typically reveals that a small number of high-frequency agents consume a disproportionate share, much of it on fast-exit no-ops. Reorganizing the fleet into priority tiers and autonomously throttling frequencies as limits approach reduces run count dramatically without touching model selection or prompt depth. Only how often agents run changes, never what they do when they run.

**State layer separation.** Using only real-time dashboards for state works for live monitoring but makes historical queries impossible (each run overwrites the dashboard). Adding an append-only SQLite layer creates a two-tier system: dashboards for live state, database for permanent history. "What's the current value?" queries the dashboard; "what was it doing last Tuesday?" queries the database.

---

## Try It Yourself

Three fully functional example agents are included — copy-paste ready, no API keys required, immediately deployable as Claude Code scheduled tasks.

| Example | What It Does | Complexity |
|---------|-------------|-----------|
| **[Research Digest](examples/research-digest/AGENT.md)** | Daily AI/ML research briefing with severity-rated findings | Entry-level |
| **[Market Monitor](examples/market-monitor/AGENT.md)** | Crypto market snapshots with sentiment analysis and state deltas | Intermediate |
| **[Fleet Watchdog](examples/fleet-watchdog/AGENT.md)** | Auto-discovers and monitors other agents' health, flags failures | Advanced |

Each agent demonstrates the full production pattern: state loading, data gathering with fallback chains, quality self-assessment, structured output, and state persistence. See **[QUICKSTART.md](QUICKSTART.md)** for setup instructions.

These examples are functional starting points. Any production fleet built on top of this framework will include additional infrastructure (multi-canvas state management, cross-agent enrichment, visual card integration, data layer writes, JIT budget awareness) layered on top of these primitives.

---

## Repository Structure

```
├── README.md                                    # This file
├── ARCHITECTURE.md                              # System design, state management, data flow
├── FLEET-OPS.md                                 # Operational patterns, observability, self-repair
├── QUICKSTART.md                                # Deploy an example agent in 5 minutes
│
├── examples/                                    # Fully functional, copy-paste ready agents
│   ├── research-digest/AGENT.md                 # AI/ML research briefing agent
│   ├── market-monitor/AGENT.md                  # Crypto market intelligence agent
│   └── fleet-watchdog/AGENT.md                  # Fleet health monitoring agent
│
└── docs/examples/                               # Structural references
    ├── structural-reference-agent.md            # Annotated template showing agent anatomy
    └── report-template-reference.html           # HTML report template with styling patterns
```

Production agent configurations, skills libraries, serverless endpoints, data layers, and operational data built on top of this framework are maintained separately.

---

## About

This framework emerged from building and operating a production autonomous agent fleet at the intersection of crypto/AML regulatory work and hands-on AI agent system design. The compliance background shapes how the framework is structured — audit-defensible documentation, structured severity frameworks, escalation protocols, and systematic evidence-based analysis are native operating principles, not afterthoughts bolted onto an AI project.

Actively used in production and continues to evolve.
