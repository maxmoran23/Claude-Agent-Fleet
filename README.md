# Claude Agent Fleet

**38 autonomous AI agents. 35 scheduled tasks. Self-repairing. Zero traditional code. Built by one person in 6 weeks using Claude Code.**

---

I'm a financial crime compliance professional (CAMS), not a software engineer. Over the past six weeks, I've built and now operate a 38-agent autonomous intelligence system using nothing but Claude Code (Opus 4.6, 1M context window). No Python. No JavaScript. No servers. No frameworks. Every agent is a structured natural language prompt that Claude executes on a schedule, gathers live data, maintains persistent memory, rates its own output quality, and — when something breaks — repairs itself without my intervention.

This repository documents the architecture, design decisions, and operational patterns behind the system. The actual agent configurations are maintained in a separate private repository.

---

## What It Does

The fleet runs as a **personal intelligence layer** across six domains:

| Domain | Agents | What They Do |
|--------|--------|-------------|
| **Crypto Markets** | 4 | Real-time prices, macro sentiment, on-chain analytics, virtual $100K portfolio with autonomous position management |
| **Regulatory / AML** | 3 | Enforcement actions, legislation tracking (GENIUS Act, MiCA), OFAC sanctions, compliance deadline alerts |
| **Research & Ideas** | 4 | AI/ML paper translation, frontier science, cross-domain synthesis, autonomous topic discovery |
| **Workflow** | 5 | Meeting prep, email triage, Slack summarization, cross-agent thread enrichment, opportunity scanning |
| **Daily Delivery** | 9 | Morning-to-evening curated briefs delivered to Gmail, Apple Notes, and Slack for mobile consumption |
| **Fleet Ops** | 5 | Health monitoring (every 3h), self-repair (every 4h), meta-analysis, storage cleanup, alert routing |

**Plus** 2 on-demand agents (compliance reports, real estate analytics) and 1 weekend review agent.

**Daily throughput:** ~40-50 automated touchpoints across 5 apps, 5 AM to 9 PM ET.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (7+)                       │
│  Real-time prices · Social sentiment · On-chain data         │
│  Financial news · Market tearsheets · Email · Calendar       │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    AGENT FLEET (38 agents)                    │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Cortex   │ │ Real-    │ │ Daily    │ │ Workflow │        │
│  │ Core(10) │ │ Time (4) │ │ Briefs(9)│ │ Auto (5) │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ Fleet    │ │ On-      │ │ Weekend  │                     │
│  │ Infra(5) │ │ Demand(2)│ │ Review(1)│                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
│                                                              │
│  Each agent: Load State → Gather → Analyze → Post →         │
│              Update Dashboard → Self-Rate → Persist State    │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER (5 apps)                     │
│  Slack channels · Gmail emails · Apple Notes                 │
│  Google Calendar events · Notion database                    │
│                                                              │
│  ~40-50 automated touchpoints/day · 5 AM – 9 PM ET          │
└──────────────────────────────────────────────────────────────┘
```

Full architecture documentation: **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## The Agent Roster

<details>
<summary><strong>Cortex Core (10 agents)</strong> — Deep analysis engines, each generating full HTML intelligence reports</summary>

| Agent | Frequency | Domain |
|-------|-----------|--------|
| Market Maven | Every 8h | Crypto macro — narrative shifts, sentiment regimes, correlation analysis |
| Alt-Coin Scout | Daily | Token discovery with built-in compliance risk flags |
| Crypto Sim Trader | Every 4h | Virtual $100K portfolio — autonomous position management with risk limits |
| Alpha Lab | Every 6h | DeFi protocol monitoring — TVL shifts, yield analysis, smart contract risk |
| Edge Hunter | Daily | Quantitative analytics — statistical signal detection, probabilistic modeling |
| Regulatory Oracle | Daily | Crypto/AML regulatory landscape — enforcement, legislation, deadlines |
| AI Vanguard | Daily | AI/ML research translation — papers to actionable insights |
| Idea Forge | Daily | Cross-domain innovation — connects signals across all fleet channels |
| Frontier Theorist | Weekly | Frontier science — physics, biology, computation breakthroughs |
| Synthesis Engine | Daily | Meta-analyst — reads all other agents' output, identifies cross-cutting themes |

</details>

<details>
<summary><strong>Real-Time Layer (4 agents)</strong> — Live monitoring at 2-3 hour intervals</summary>

| Agent | Frequency | Function |
|-------|-----------|----------|
| Headline Flash | Every 2h | Breaking news — concise intelligence drops |
| Market Pulse Alert | Every 3h | Live prices with sentiment overlay |
| Fleet Slack Relay | Every 2h | Top findings surfaced across the Cortex fleet |
| Calendar Smart Alerts | 2x daily | Time-sensitive deadlines pushed to calendar |

</details>

<details>
<summary><strong>Daily Briefs (9 agents)</strong> — Morning-to-evening delivery pipeline</summary>

| Agent | Schedule | Delivery |
|-------|----------|----------|
| Daily Brief | 7:00 AM | Full fleet synthesis |
| Morning Email | 7:15 AM | Gmail — prioritized morning intelligence |
| iPhone Notes Brief | 7:20 AM | Apple Notes — glanceable reference |
| Weekly Project Status | Monday AM | Progress and blockers |
| Regulatory Watch | Wednesday AM | Deep-dive regulatory analysis |
| Midday Intelligence | 12:00 PM | Gmail — midday update |
| Afternoon Brief | 3:30 PM | Gmail — afternoon synthesis |
| Evening Wrap | 7:30 PM | Gmail — end-of-day summary |
| Friday Roundup | Friday 6 PM | Gmail — comprehensive weekly synthesis |

</details>

<details>
<summary><strong>Workflow Automation (5 agents)</strong> — Active participants in daily work</summary>

| Agent | Function |
|-------|----------|
| Meeting Prep | Pre-meeting context briefs with attendee research |
| Email Intelligence | Smart email triage — categorization, priority, draft responses |
| Slack Catch-Up | "What did I miss" channel summaries |
| Smart Thread Responder | Cross-references findings between agents, enriches threads |
| Opportunity Radar | Surfaces career, financial, and project opportunities |

</details>

<details>
<summary><strong>Fleet Infrastructure (5 agents)</strong> — The fleet maintains itself</summary>

| Agent | Frequency | Function |
|-------|-----------|----------|
| Alpha Discovery Loop | Daily 5 AM | Autonomous research — finds uncovered topics |
| Watchdog | Every 3h | Fleet health — missed runs, source uptime, quality drift |
| Fleet Auto-Repair | Every 4h | Self-healing — scans all configs, fixes issues autonomously |
| Alert Distribution | Scheduled | Routes critical findings to escalation channels |
| Gmail Cleanup | Weekly | Storage management and inbox hygiene |

</details>

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Runtime | Claude Code scheduled tasks | Always-on remote execution — no server, no laptop dependency |
| State | Slack Canvases as persistent stores | Human-readable, agent-writable, survives restarts, no database |
| Coupling | Zero file dependencies between agents | Any agent can fail without cascading — total fault isolation |
| Delivery | 5-app multi-channel pipeline | Right information, right app, right time — optimized for mobile |
| Observability | Fleet agents, not external tools | The fleet monitors itself using the same architecture it runs on |
| Self-repair | Autonomous, not alerting-only | Auto-Repair fixes problems, not just flags them |

---

## Production Patterns

Every agent follows the same execution cycle — see **[FLEET-OPS.md](FLEET-OPS.md)** for full documentation.

```
STEP 0        STEP 1-5       STEP 6         STEP 7
Load State ─▶ Execute ─────▶ Deliver ─────▶ Persist State
(canvas)      (gather,        (channels,     (write back
               analyze,        dashboards,    run log,
               self-rate)      DB, email)     quality score)
```

- **Fallback chains** — every source has graceful degradation; no agent hard-fails
- **Quality self-assessment** — agents rate their own output 1-10, flag degraded runs
- **Health footers** — every output includes sources used, fallbacks triggered, quality score, runtime
- **Structured data bus** — all findings (severity >= MEDIUM) written to shared Notion DB
- **Escalation routing** — CRITICAL findings bypass normal channels, go direct to alerts + DM

---

## Build Journey

| Week | What Happened |
|------|--------------|
| **1** | First agent (Market Maven). Proof of concept — can a structured prompt with scheduled execution actually produce useful, repeatable output? It could. |
| **2** | Expanded to 8 agents. Discovered the state management problem — agents had no memory between runs. Solved it with Slack Canvases as persistent state stores. |
| **3** | Hit 15+ agents. Built the delivery pipeline (Gmail, Apple Notes, Calendar). Realized I needed agents to monitor other agents — built Watchdog. |
| **4** | Scaled to 25+ agents. Standardized the production patterns (Steps 0-7, fallback chains, health footers). Quality became consistent and measurable. |
| **5** | Added workflow agents (meeting prep, email triage, thread enrichment). The system started actively participating in daily work, not just reporting. Fleet Auto-Repair went live — the system could now fix itself. |
| **6** | 38 agents in production. Added the Synthesis Engine (reads all agents, finds cross-cutting themes), skills library (21 capability categories), and on-demand compliance report generation. The system is now self-maintaining and expanding. |

---

## What I Learned Building This

Things that might be useful context for anyone thinking about agent systems at scale:

**State management is the real problem.** Getting one agent to run once is easy. Getting 38 agents to remember what they did last time, coordinate without coupling, and not overwrite each other's data — that's the actual engineering challenge. Slack Canvases turned out to be an unexpectedly good solution: persistent, human-readable, section-addressable, and accessible through existing MCP tools.

**Self-repair changes the economics.** Before Auto-Repair, a config drift in one agent meant I'd find broken output hours later. After Auto-Repair, the fleet scans itself every 4 hours and fixes issues before I ever see them. The psychological shift from "I maintain 38 agents" to "38 agents maintain themselves and I steer" was the single biggest upgrade.

**Delivery matters more than analysis.** The Cortex agents that do deep analysis are impressive, but the brief agents that package and deliver insights to the right app at the right time are what make the system actually useful. Intelligence you don't see is intelligence that doesn't exist.

**Fallback chains make the difference between demo and production.** Any individual agent run might hit a rate limit, get a timeout, or find a data source down. The system runs ~150+ agent executions per day. Without fallback chains, something would break every day. With them, I've had zero total failures in 6 weeks of production operation.

**The non-engineer angle is a feature, not a limitation.** Every design decision was driven by "what's the simplest thing that actually works" rather than "what's the proper engineering approach." The result is a system that's arguably more resilient than a traditional codebase — no dependency trees to break, no deployment pipelines to fail, no version conflicts to resolve.

---

## Numbers

| Metric | Value |
|--------|-------|
| Agents | 38 |
| Scheduled tasks | 35+ |
| Daily outputs | 40-50 touchpoints |
| Operating hours | 5 AM – 9 PM ET |
| Delivery apps | 5 |
| Live data sources | 7+ |
| State stores | 4 persistent canvases |
| Self-repair cycle | Every 4 hours |
| Health monitoring | Every 3 hours |
| Build time | ~6 weeks, solo |
| Servers | 0 |
| Databases | 0 |
| Lines of code | 0 |
| Infrastructure cost | $0 |

---

## Try It Yourself

Three fully functional example agents are included in this repo — copy-paste ready, no API keys required, immediately deployable as Claude Code scheduled tasks.

| Example | What It Does | Complexity |
|---------|-------------|-----------|
| **[Research Digest](examples/research-digest/AGENT.md)** | Daily AI/ML research briefing with severity-rated findings | Entry-level |
| **[Market Monitor](examples/market-monitor/AGENT.md)** | Crypto market snapshots with sentiment analysis and state deltas | Intermediate |
| **[Fleet Watchdog](examples/fleet-watchdog/AGENT.md)** | Auto-discovers and monitors other agents' health, flags failures | Advanced |

Each agent demonstrates the full production pattern: state loading, data gathering with fallback chains, quality self-assessment, structured output, and state persistence. See **[QUICKSTART.md](QUICKSTART.md)** for setup instructions.

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

The 38 production agent configurations, skills library, and operational data are maintained in a separate private repository.

---

## About

Built and operated by **Max Moran** — financial crime and digital asset compliance professional (CAMS). This system sits at the intersection of deep domain expertise in crypto/AML regulatory work and intensive hands-on experience building autonomous AI agent systems at scale.

The fleet is actively running in production and continues to expand.
