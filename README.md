# Claude Agent Fleet

**38 autonomous AI agents. 35+ scheduled tasks. Fully self-repairing. Built entirely in Claude Code.**

This is a production-grade autonomous agent fleet I designed, built, and operate as a solo builder using Claude Code (Opus 4.6, 1M context). The system runs 24/7 on remote scheduled tasks — no server infrastructure, no custom code, no frameworks. Every agent is a structured prompt with persistent state, fallback logic, quality self-assessment, and multi-channel output delivery.

This repository documents the system architecture, design decisions, and operational patterns. Agent instructions and proprietary configurations are maintained in a separate private repository.

---

## What This System Does

The fleet operates as a **personal intelligence layer** — continuously gathering, analyzing, synthesizing, and delivering structured intelligence across multiple domains:

| Domain | What the Agents Do |
|--------|-------------------|
| **Crypto Markets** | Real-time price monitoring, macro sentiment analysis, on-chain analytics, DeFi protocol risk assessment, virtual portfolio management ($100K sim) |
| **Regulatory / AML** | Enforcement action tracking, legislation monitoring (GENIUS Act, MiCA, etc.), OFAC sanctions screening, compliance deadline alerts |
| **Research & Ideas** | AI/ML paper translation, frontier science scanning, cross-domain innovation synthesis, autonomous idea discovery |
| **Workflow Automation** | Smart email triage, meeting prep with attendee research, Slack channel summarization, cross-agent thread enrichment |
| **Sports Analytics** | Positive expected value edge detection, quarter-Kelly position sizing, systematic betting analytics |
| **Fleet Operations** | Health monitoring every 3 hours, autonomous self-repair every 4 hours, cross-fleet meta-analysis, fleet-wide quality scoring |

---

## System at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (7+)                      │
│  Real-time prices · Social sentiment · On-chain data        │
│  Financial news · Market tearsheets · Email · Calendar      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT FLEET (38 agents)                   │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Cortex   │ │ Real-    │ │ Daily    │ │ Workflow │       │
│  │ Core(10) │ │ Time (4) │ │ Briefs(9)│ │ Auto (5) │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Fleet    │ │ On-      │ │ Weekend  │                    │
│  │ Infra(5) │ │ Demand(2)│ │ Review(1)│                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                             │
│  Each agent: Load State → Gather → Analyze → Post →        │
│              Update Dashboard → Self-Rate → Persist State   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER (5 apps)                     │
│  Slack channels · Gmail emails · Apple Notes ·              │
│  Google Calendar events · Notion database                   │
│                                                             │
│  ~40-50 automated touchpoints/day · 5am-9pm ET             │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Inventory

### Cortex Core (10 agents) — Deep Analysis Engines
The analytical backbone. Each Cortex agent specializes in a domain, runs on a fixed schedule, generates full HTML intelligence reports, and maintains persistent state across runs.

| Agent | Frequency | Domain |
|-------|-----------|--------|
| Market Maven | Every 8h | Crypto macro — narrative shifts, sentiment regimes, correlation analysis |
| Alt-Coin Scout | Daily | Token discovery with built-in compliance risk flags |
| Crypto Sim Trader | Every 4h | Virtual $100K portfolio — autonomous position management with risk limits |
| Alpha Lab | Every 6h | DeFi protocol monitoring — TVL shifts, yield analysis, smart contract risk |
| Edge Hunter | Daily | Sports analytics — statistical edge detection, quarter-Kelly sizing |
| Regulatory Oracle | Daily | Crypto/AML regulatory landscape — enforcement, legislation, deadlines |
| AI Vanguard | Daily | AI/ML research translation — papers to actionable insights |
| Idea Forge | Daily | Cross-domain innovation — connects signals across all fleet channels |
| Frontier Theorist | Weekly | Frontier science — physics, biology, computation breakthroughs |
| Synthesis Engine | Daily | Meta-analyst — reads all other agents' output, identifies cross-cutting themes |

### Real-Time Layer (4 agents) — Live Monitoring
Continuous awareness. These agents run at 2-3 hour intervals during market hours.

| Agent | Frequency | Function |
|-------|-----------|----------|
| Headline Flash | Every 2h | Breaking news aggregation — concise, Twitter-length intelligence drops |
| Market Pulse Alert | Every 3h | Live price snapshots with sentiment overlay |
| Fleet Slack Relay | Every 2h | Top findings surfaced from across the Cortex fleet |
| Calendar Smart Alerts | 2x daily | Time-sensitive regulatory and market deadlines pushed to calendar |

### Daily Intelligence Briefs (9 agents) — Curated Delivery
Multi-format, multi-channel delivery pipeline optimized for mobile consumption.

| Agent | Schedule | Delivery |
|-------|----------|----------|
| Daily Brief | 7:00 AM | Command center — full fleet synthesis |
| Morning Email | 7:15 AM | Gmail — prioritized morning intelligence |
| iPhone Notes Brief | 7:20 AM | Apple Notes — glanceable reference synced to phone |
| Weekly Project Status | Monday AM | Project-level progress and blockers |
| Regulatory Watch | Wednesday AM | Deep-dive regulatory analysis |
| Midday Intelligence | 12:00 PM | Gmail — midday market + workflow update |
| Afternoon Brief | 3:30 PM | Gmail — afternoon synthesis |
| Evening Wrap | 7:30 PM | Gmail — end-of-day summary and overnight watch items |
| Friday Roundup | Friday 6 PM | Gmail — comprehensive weekly synthesis |

### Workflow Automation (5 agents) — Productivity
Agents that actively participate in daily work, not just report.

| Agent | Function |
|-------|----------|
| Meeting Prep | Pre-meeting context briefs with attendee research and topic synthesis |
| Email Intelligence | Smart email triage — categorization, priority scoring, draft responses |
| Slack Catch-Up | "What did I miss" summaries for channel gaps |
| Smart Thread Responder | Cross-references findings between agents, enriches Slack threads with context |
| Opportunity Radar | Surfaces career, financial, and side-project opportunities from signal analysis |

### Fleet Infrastructure (5 agents) — Self-Maintenance
The fleet monitors and repairs itself.

| Agent | Frequency | Function |
|-------|-----------|----------|
| Alpha Discovery Loop | Daily 5 AM | Autonomous research — finds topics no other agent is covering |
| Watchdog | Every 3h | Fleet health — tracks missed runs, data source uptime, quality drift |
| Fleet Auto-Repair | Every 4h | Self-healing — scans all configs, detects and fixes issues autonomously |
| Alert Distribution | Scheduled | Routes critical findings to appropriate escalation channels |
| Gmail Cleanup | Weekly | Storage management and inbox hygiene |

### On-Demand + Weekend (3 agents)

| Agent | Trigger | Function |
|-------|---------|----------|
| EDD Review | Manual | Enhanced Due Diligence — generates full compliance assessment reports |
| Real Estate Analytics | Daily + Weekly | Market-specific property analytics with trend analysis |
| Weekend Review | Saturday | Personal + professional weekly review with forward planning |

---

## Key Design Decisions

Documented in detail in [ARCHITECTURE.md](ARCHITECTURE.md).

| Decision | Choice | Why |
|----------|--------|-----|
| Runtime | Claude Code scheduled tasks | Always-on remote execution, no server to maintain |
| State management | Slack Canvases as persistent stores | Readable by humans and agents, survives restarts, no database needed |
| Agent coupling | Zero file dependencies between agents | Any agent can fail without cascading — each is fully self-contained |
| Delivery | 5-app multi-channel pipeline | Optimized for mobile — right information in the right app at the right time |
| Observability | Dedicated fleet agents (not external tools) | The fleet monitors itself using the same architecture it runs on |
| Model | Opus 4.6 (1M context) everywhere | Never downgrade — consistency and capability across the entire fleet |
| Self-repair | Autonomous, not alerting-only | Auto-Repair doesn't just detect problems — it fixes them without intervention |

---

## Production Patterns

Every agent in the fleet follows the same battle-tested execution cycle. See [FLEET-OPS.md](FLEET-OPS.md) for full operational documentation.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   STEP 0    │────▶│  STEP 1-5   │────▶│   STEP 6    │────▶│   STEP 7    │
│ Load State  │     │   Execute   │     │   Deliver   │     │Persist State│
│             │     │             │     │             │     │             │
│ Read prior  │     │ Gather data │     │ Post to     │     │ Write run   │
│ run state   │     │ w/ fallback │     │ channels    │     │ log, state  │
│ from canvas │     │ chains      │     │ Update      │     │ changes,    │
│             │     │ Analyze     │     │ dashboards  │     │ quality     │
│             │     │ Self-rate   │     │ Write to DB │     │ score back  │
│             │     │ quality     │     │ Send emails │     │ to canvas   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Key patterns:**
- **Fallback chains** — every data source has graceful degradation; agents run at reduced capacity rather than failing
- **Health footers** — every output includes: sources used, fallbacks triggered, quality self-rating, runtime
- **Quality self-assessment** — agents rate their own output quality (1-10) and flag degraded runs
- **Structured data bus** — all agents write findings (severity >= MEDIUM) to a shared Notion database, enabling cross-agent discovery
- **Escalation routing** — CRITICAL findings bypass normal channels and go directly to alerts + DM

---

## Repository Structure

```
docs/
├── ARCHITECTURE.md          # System design, data flow, state management
├── FLEET-OPS.md             # Operational patterns, observability, self-repair
└── examples/
    ├── sample-agent.md      # Redacted agent template showing structure
    └── sample-report.html   # Redacted report template showing output format
```

The actual agent configurations (38 AGENT.md files, HTML templates, skills library) are maintained in a separate private repository. This public repo documents the system design and architecture.

---

## Scale & Numbers

| Metric | Value |
|--------|-------|
| Total agents | 38 |
| Scheduled tasks | 35+ |
| Daily automated outputs | 40-50 touchpoints |
| Operating hours | 5 AM – 9 PM ET |
| Delivery channels | 5 (Slack, Gmail, Apple Notes, Google Calendar, Notion) |
| Data sources | 7+ live feeds |
| State stores | 4 persistent canvases |
| Self-repair cycle | Every 4 hours |
| Health monitoring cycle | Every 3 hours |
| Build time | ~6 weeks of intensive solo development |
| Infrastructure cost | $0 (runs on Claude Code scheduled tasks) |
| External dependencies | 0 servers, 0 databases, 0 custom code |

---

## Technical Context

This entire system was built using **Claude Code** — Anthropic's agentic coding tool. There is no traditional codebase, no Python scripts, no JavaScript, no deployment pipeline. Every agent is a structured natural language prompt with:

- Explicit execution steps
- Data source specifications with fallback chains  
- Output format and channel routing rules
- State read/write protocols
- Quality self-assessment criteria
- Health reporting standards

The system demonstrates that production-grade autonomous agent fleets can be built and operated by a single non-engineer using AI-native tools — with reliability, observability, and self-healing properties that match traditional software infrastructure.

---

## About

Built and operated by **Max Moran** — financial crime and digital asset compliance professional (CAMS certified). This system reflects the intersection of deep domain expertise in regulatory/AML work with intensive hands-on experience building AI agent systems at scale.

The fleet is actively running in production and continues to be expanded.

*Architecture and operational documentation: [ARCHITECTURE.md](ARCHITECTURE.md) · [FLEET-OPS.md](FLEET-OPS.md)*
