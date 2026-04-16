# Claude Agent Fleet

**50 autonomous AI agents. ~800 scheduled runs per week. Self-repairing, self-evolving, self-budgeting. Visual dashboards. Execution scaffolding. Zero traditional code. Solo build on Claude Code (Opus 4.6, 1M context).**

---

## What This Is

A production-grade autonomous intelligence system covering crypto markets, regulatory compliance, research, workflow automation, and operational self-maintenance — built and operated by one person using Claude Code.

Every agent is a structured natural language prompt executed on a schedule. Agents gather live data from 12+ sources, maintain persistent memory across runs via Slack Canvases and a SQLite data layer, rate their own output quality, and — when something breaks — repair themselves without human intervention. A JIT budget manager monitors fleet-wide token consumption and autonomously throttles agent frequencies as resource limits approach, preserving output quality by reducing run count rather than degrading the model or prompt depth.

The system has been through nine weeks of iterative development — each architectural decision reflects a problem that was hit, diagnosed, and solved. State management, delivery consolidation, fault isolation, observability, self-repair economics, and budget optimization were all learned through production operation, not designed up front.

This repository documents the architecture, design decisions, and operational patterns. Three fully functional example agents are included. The production agent configurations are maintained in a separate private repository.

---

## What It Does

The fleet operates as a **personal intelligence layer** across seven domains:

| Domain | Agents | Function |
|--------|--------|----------|
| **Crypto Markets** | 5 | Real-time prices, macro sentiment, on-chain analytics, virtual $100K portfolio, token discovery with compliance flags |
| **Regulatory / AML** | 3 | Enforcement actions, legislation tracking (GENIUS Act, MiCA), OFAC sanctions, compliance deadline alerts |
| **Research & Ideas** | 4 | AI/ML paper translation, frontier science, cross-domain synthesis, autonomous topic discovery |
| **Workflow** | 6 | Meeting prep, email triage, Slack summarization, cross-agent enrichment, opportunity scanning, interactive Q&A |
| **Daily Delivery** | 7 | Morning-to-evening curated briefs consolidated into 2 daily digest emails + Slack channel posts |
| **Fleet Ops** | 9 | Health monitoring, self-repair, autonomous evolution, JIT budget management, engagement tracking, backup, meta-analysis |
| **Execution** | 3 | Pre-filled bet slips, tailored application kits, monetization launch kits — 90% of prep work automated, human confirms |

Plus specialty agents (compliance reports, real estate analytics, career intelligence) and a weekend review agent.

**Weekly throughput:** ~800 runs across 3 delivery apps, 5 AM to 9 PM ET.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (12+)                      │
│  Real-time prices  Social sentiment  On-chain data           │
│  Financial news  Market tearsheets  Email  Calendar          │
│  Government databases  Regulatory filings                    │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    AGENT FLEET (50 agents)                    │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Cortex   │ │ Real-    │ │ Daily    │ │ Workflow │       │
│  │ Core(10) │ │ Time (4) │ │ Briefs(7)│ │ Auto (6) │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Fleet    │ │ Specialty│ │ Execution│ │ Maint.   │       │
│  │ Infra(9) │ │ Intel(5) │ │ Scaf.(3) │ │ Util.(4) │       │
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
│                     OUTPUT LAYER (3 apps)                     │
│  Slack channels + canvases (primary backbone)                │
│  Gmail (2 consolidated digest emails/day)                    │
│  Google Calendar (iOS push for deadlines)                    │
│                                                              │
│  Structured archive: SQLite data layer + Notion database     │
│                                                              │
│  ~800 runs/week  3 delivery apps  5 AM - 9 PM ET            │
└──────────────────────────────────────────────────────────────┘
```

Full architecture documentation: **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## The Agent Roster

<details>
<summary><strong>Cortex Core (10 agents)</strong> — Deep analysis engines with full HTML intelligence reports</summary>

| Agent | Frequency | Domain |
|-------|-----------|--------|
| Market Maven | Every 8h | Crypto macro — narrative shifts, sentiment regimes, correlation analysis |
| Alt-Coin Scout | Daily | Token discovery with built-in compliance risk flags |
| Crypto Sim Trader | Every 4h | Virtual $100K portfolio — autonomous position management with risk limits |
| Alpha Lab | Every 6h | DeFi protocol monitoring — TVL shifts, yield analysis, smart contract risk |
| Edge Hunter | Daily | Quantitative analytics — statistical signal detection, probabilistic modeling |
| Regulatory Oracle | Daily | Crypto/AML regulatory landscape — enforcement, legislation, deadlines |
| AI Vanguard | 3x/week | AI/ML research translation — papers to actionable insights |
| Idea Forge | 3x/week | Cross-domain innovation — connects signals across all fleet channels |
| Frontier Theorist | Weekly | Frontier science — physics, biology, computation breakthroughs |
| Synthesis Engine | Daily | Meta-analyst — reads all other agents' output, identifies cross-cutting themes |

</details>

<details>
<summary><strong>Real-Time Layer (4 agents)</strong> — Live monitoring at defined intervals</summary>

| Agent | Frequency | Function |
|-------|-----------|----------|
| Headline Flash | 5x/day | Breaking news — concise intelligence drops |
| Market Pulse Alert | 4x/day | Live prices with sentiment overlay |
| Fleet Slack Relay | 3x/day | Top findings surfaced across the Cortex fleet |
| Calendar Smart Alerts | 2x daily | Time-sensitive deadlines pushed to calendar |

</details>

<details>
<summary><strong>Daily Briefs (7 agents)</strong> — Consolidated delivery pipeline</summary>

| Agent | Schedule | Delivery |
|-------|----------|----------|
| Daily Brief | Weekday mornings | Full fleet synthesis to Slack |
| Weekly Project Status | Monday | Progress and blockers |
| Regulatory Watch | Wednesday | Deep-dive regulatory analysis |
| Midday Intelligence | Weekday noon | Market + fleet update |
| Afternoon Brief | Weekday afternoon | Regulatory + market synthesis |
| Evening Wrap | Daily evening | Full day consolidation |
| Friday Roundup | Friday evening | Comprehensive weekly synthesis |

All briefs are automatically aggregated by the **Email Digest Aggregator** into 2 consolidated HTML emails per day (morning + evening), replacing what was previously 7+ individual email agents.

</details>

<details>
<summary><strong>Workflow Automation (6 agents)</strong> — Active participants in daily work</summary>

| Agent | Function |
|-------|----------|
| Meeting Prep | Pre-meeting context briefs with attendee research |
| Email Intelligence | Smart email triage — categorization, priority, draft responses (5x/day) |
| Slack Catch-Up | "What did I miss" channel summaries |
| Smart Thread Responder | Cross-references findings between agents, enriches threads |
| Opportunity Radar | Surfaces career, financial, and project opportunities with 0-100 fit scoring |
| Fleet Query | Interactive Q&A — ask any question, get a data-cited answer from across the fleet |

</details>

<details>
<summary><strong>Fleet Infrastructure (9 agents)</strong> — Self-maintaining operational layer</summary>

| Agent | Frequency | Function |
|-------|-----------|----------|
| Watchdog + JIT Budget Manager | 4x/day | Fleet health monitoring + autonomous token budget management across 4 priority tiers |
| Fleet Auto-Repair | 3x/day | Self-healing — scans all agent configs, fixes issues autonomously, auto-commits to Git |
| Fleet Evolution Engine | Weekly | Assesses each agent against a 5-level maturity framework, implements upgrades |
| Feedback Harvester | Daily | Tracks engagement (emoji reactions) to measure real-world value per agent |
| Alert Scan | 3x/day | Critical-only finding router — the "red phone" channel |
| Synthesis Engine | Daily | Cross-fleet meta-analysis — patterns, contradictions, blind spots |
| Alpha Discovery Loop | 3x/week | Autonomous research trawl — finds uncovered topics |
| Fleet Backup | Daily | Configuration + data layer backup to Google Drive |
| Email Digest Aggregator | 2x/day | Consolidates all fleet intelligence into 2 HTML emails (morning + evening) |

</details>

---

## System Capabilities

### Visual Dashboard System
Agents embed dynamic PNG image cards in Slack posts — score gauges, market dashboards, alert cards, fleet status overviews, pipeline funnels, and bet slips. Generated on-the-fly by serverless endpoints using Satori (JSX-to-SVG) + Sharp (SVG-to-PNG). Agents construct URLs with live data parameters; Slack renders inline. Dark theme throughout.

### Execution Scaffolding
Three agents generate pre-filled action packages when findings cross defined thresholds:

| Agent | Trigger | Output |
|-------|---------|--------|
| Edge Hunter | Edge >= 1% EV | **Bet Slip** — sport, pick, line, quarter-Kelly stake, step-by-step instructions |
| Opportunity Radar | Fit Score >= 85 | **Application Kit** — tailored resume bullets, cover letter draft, LinkedIn message, checklist |
| Idea Forge | OPS >= 85 | **Launch Kit** — landing page concept, pricing model, customer segments, 30-day plan |

Human-in-the-loop: everything is a draft. Emoji reactions confirm, skip, or modify. The Feedback Harvester tracks execution outcomes to measure real-world impact.

### JIT Budget Management
The Watchdog agent doubles as an autonomous budget manager. It counts fleet-wide runs per week, projects burn rate against an 800 run/week target, and escalates through four throttle levels:

| Level | Trigger | Action |
|-------|---------|--------|
| NORMAL | On budget | All agents at baseline frequencies |
| GREEN | Approaching limit | Pause luxury/research agents |
| YELLOW | Over budget | Throttle high-frequency P2 agents (wider intervals) |
| RED | Significant overshoot | Protect only 7 core P0 agents at full schedule |

De-escalation is automatic — when burn rate drops, agents restore to baseline. Manual override available via DM. The key design principle: **reduce frequency, never reduce model or prompt quality.** Output stays the same; it just arrives less often.

### Structured Data Layer
Beyond real-time dashboards (Slack Canvases, overwritten each run), a SQLite database serves as the permanent historical record — 11 tables covering fleet metrics, market snapshots, predictions, portfolio state, regulatory events, and agent performance. Designed to be migration-compatible with hosted databases when ready to scale.

### Conversational Interface
Fleet Query monitors for questions every 20 minutes, reads all 4 state stores + 9 channels + the SQLite data layer, and replies in-thread with data-cited answers. Self-documenting help system with domain menu.

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Runtime | Claude Code scheduled tasks | Always-on remote execution — no server, no laptop dependency |
| State | Slack Canvases as persistent stores | Human-readable, agent-writable, survives restarts, no database required |
| Historical data | SQLite append-only layer | Canvases are dashboards (current state); SQLite is the ledger (what was true on date X) |
| Coupling | Zero file dependencies between agents | Any agent can fail without cascading — total fault isolation |
| Delivery | 3-app consolidated pipeline | Slack (backbone) + Gmail (2 digests/day) + Calendar (iOS push). Evolved from 5 apps through iteration |
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

## Build Timeline

| Week | What Happened |
|------|--------------|
| **1** | First agent (Market Maven). Validated that a structured prompt with scheduled execution could produce useful, repeatable output. |
| **2** | Expanded to 8 agents. Hit the state management problem — agents had no memory between runs. Solved with Slack Canvases as persistent state stores. |
| **3** | 15+ agents. Built the multi-app delivery pipeline. Built Watchdog — agents monitoring agents. |
| **4** | 25+ agents. Standardized the 7-step production pattern (fallback chains, health footers, quality self-rating). Consistency became measurable. |
| **5** | Added workflow agents (meeting prep, email triage, thread enrichment). The system started actively participating in daily work. Fleet Auto-Repair went live — autonomous self-healing. |
| **6** | 38 agents. Added Synthesis Engine, skills library (21 capability categories), and on-demand compliance tooling. |
| **7** | Visual dashboard system (7 serverless image endpoints), execution scaffolding, Fleet Query (conversational interface), Evolution Engine (weekly autonomous upgrades). |
| **8** | Consolidated delivery pipeline — 7+ individual email agents replaced by a single Email Digest Aggregator (2 emails/day). Removed redundant delivery channels. Added SQLite data layer for historical queries. |
| **9** | 50 agents, 46 scheduled tasks. Full token budget diagnostic. JIT Budget Manager built into Watchdog — autonomous 4-tier throttle protocol. Fleet optimized from ~1,900 to ~800 runs/week with zero quality degradation. |

---

## Architecture Evolution

The system's current form reflects decisions that were iterated, not planned:

**Delivery consolidation** — The fleet initially had 7+ agents each sending individual emails, plus Apple Notes syncs, plus Slack posts. Through production use, it became clear that volume was working against utility — too many touchpoints caused notification fatigue. The current architecture consolidates all email delivery into a single aggregator (2 emails/day), removed Apple Notes entirely, and made Slack the primary backbone. Three delivery apps instead of five. Fewer notifications, same information density.

**JIT budget management** — Running 50 agents on Opus 4.6 at their original frequencies produced ~1,900 runs/week. A token consumption analysis identified that a single agent (Fleet Query at every 5 minutes) consumed 63% of all runs, most of which were fast-exit no-ops. The fleet was reorganized into 4 priority tiers (P0 sacred through P3 luxury), frequencies were optimized, and the Watchdog was upgraded to autonomously manage throttling as limits approach. The budget dropped to ~800 runs/week with identical output quality — the only change is how often agents run, never what model they use or how thoroughly they analyze.

**State layer separation** — Early agents used only Slack Canvases for state, which worked for dashboards but made historical queries impossible (each run overwrites the canvas). Adding a SQLite data layer created a two-tier system: canvases for live state, SQLite for permanent history. "What's BTC at?" queries the canvas; "what was BTC doing last Tuesday?" queries the database.

---

## Numbers

| Metric | Value |
|--------|-------|
| Agents | 50 |
| Scheduled tasks | 46 active |
| Weekly run budget | ~800 (JIT-managed) |
| Operating hours | 5 AM - 9 PM ET |
| Delivery apps | 3 (Slack, Gmail, Google Calendar) |
| Live data sources | 12+ |
| MCP integrations | 25+ |
| State stores | 4 persistent canvases + SQLite data layer |
| Display dashboards | 11 live canvases |
| Image card endpoints | 8 dynamic PNG generators |
| Domain indices | 13 composite 0-100 scores |
| Self-repair cycle | 3x/day |
| Health monitoring | 4x/day (includes JIT budget analysis) |
| Evolution cycle | Weekly autonomous maturity assessment |
| Interactive Q&A | Every 20 minutes |
| Backup | Daily to Google Drive |
| Build approach | Solo build, Claude Code only |
| Traditional code | 0 lines (agents are structured prompts) |
| Infrastructure cost | $0 (Vercel hobby tier for image cards) |
| Build time | 9 weeks, continuous iteration |

---

## Try It Yourself

Three fully functional example agents are included — copy-paste ready, no API keys required, immediately deployable as Claude Code scheduled tasks.

| Example | What It Does | Complexity |
|---------|-------------|-----------|
| **[Research Digest](examples/research-digest/AGENT.md)** | Daily AI/ML research briefing with severity-rated findings | Entry-level |
| **[Market Monitor](examples/market-monitor/AGENT.md)** | Crypto market snapshots with sentiment analysis and state deltas | Intermediate |
| **[Fleet Watchdog](examples/fleet-watchdog/AGENT.md)** | Auto-discovers and monitors other agents' health, flags failures | Advanced |

Each agent demonstrates the full production pattern: state loading, data gathering with fallback chains, quality self-assessment, structured output, and state persistence. See **[QUICKSTART.md](QUICKSTART.md)** for setup instructions.

These examples are functional starting points. The production agents that run the actual fleet include additional infrastructure (multi-canvas state management, cross-agent enrichment, visual card integration, data layer writes, JIT budget awareness) that is maintained separately.

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

The 50 production agent configurations, skills library, Vercel API endpoints, data layer, and operational data are maintained in a separate private repository.

---

## About

Built and operated by **Max Moran, CAMS** — financial crime and digital asset compliance professional specializing in AML, sanctions screening, and regulatory intelligence.

This system sits at the intersection of deep domain expertise in crypto/AML regulatory work and hands-on experience designing autonomous AI agent systems at production scale. The compliance background shapes how the fleet is built — audit-defensible documentation, structured severity frameworks, escalation protocols, and systematic evidence-based analysis are not afterthoughts bolted onto an AI project. They are the native operating language of the domain applied to a new medium.

The fleet is actively running in production and continues to evolve.
