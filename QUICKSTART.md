# Quickstart: Deploy Your First Agent

This guide walks you through deploying one of the example agents from this repository. No programming experience required — just Claude Code.

---

## Prerequisites

- [Claude Code](https://claude.ai/code) (Max plan recommended for scheduled tasks)
- A working directory on your machine (e.g., `~/agents/`)

---

## Pick Your Starting Point

Fifteen fully functional example agents are available. Start with one that matches your complexity comfort:

### Entry-level (start here for your first agent)

| Agent | What It Does | No Dependencies Required |
|-------|-------------|--------------------------|
| [Research Digest](examples/research-digest/AGENT.md) | Daily research briefing on a configurable topic | ✓ |
| [Breaking News Monitor](examples/breaking-news-monitor/AGENT.md) | Real-time intelligence drops on a configurable domain | ✓ |
| [Market Pulse](examples/market-pulse/AGENT.md) | Lightweight crypto market snapshot | ✓ |

### Intermediate (for your second or third agent)

| Agent | What It Does | Optional Enhancements |
|-------|-------------|----------------------|
| [Market Monitor](examples/market-monitor/AGENT.md) | Deeper crypto market analysis with state deltas | Dedicated price MCP improves quality |
| [Regulatory Oracle](examples/regulatory-oracle/AGENT.md) | Regulatory landscape tracking | Legal-publication MCPs improve coverage |
| [Calendar Alerts](examples/calendar-alerts/AGENT.md) | Time-sensitive deadline routing | Calendar integration required for event creation |
| [Daily Intelligence Brief](examples/daily-intelligence-brief/AGENT.md) | Multi-agent consolidation | Requires upstream agents |
| [Meeting Prep](examples/meeting-prep/AGENT.md) | Pre-meeting context briefs | Calendar integration strongly recommended |

### Advanced (once you have 3+ agents running)

| Agent | What It Does | Requires |
|-------|-------------|----------|
| [Fleet Watchdog](examples/fleet-watchdog/AGENT.md) | Monitors the health of other agents | Other agents to monitor |
| [On-Chain Watchlist](examples/onchain-watchlist/AGENT.md) | Address monitoring with sanctions screening | Chain explorer MCP, sanctions source |
| [Synthesis Engine](examples/synthesis-engine/AGENT.md) | Cross-fleet meta-analysis | Multiple upstream agents |
| [DeFi Protocol Monitor](examples/defi-protocol-monitor/AGENT.md) | DeFi protocol risk monitoring | DeFi data source (DefiLlama, etc.) |
| [Execution Scaffold](examples/execution-scaffold/AGENT.md) | Threshold-triggered action packages | Upstream intelligence agents |
| [Fleet Auto-Repair](examples/fleet-auto-repair/AGENT.md) | Autonomous fleet configuration healing | Multiple agents in a fleet root |
| [Fleet Query](examples/fleet-query/AGENT.md) | Conversational interface over the fleet | Mature fleet with populated state stores |

---

## Deploy an Agent in 5 Minutes

### 1. Set up the directory

```bash
mkdir -p ~/agents/[agent-name]/state
mkdir -p ~/agents/[agent-name]/reports
```

### 2. Copy the agent config

```bash
cp examples/[agent-name]/AGENT.md ~/agents/[agent-name]/
```

Or copy the contents of the AGENT.md file into a new file at that path.

### 3. Create a scheduled task in Claude Code

Create a scheduled task that:
- Points to the AGENT.md file as the prompt
- Runs on your preferred schedule (see "Recommended schedule" in each AGENT.md)
- Has access to the agent's directory for state persistence

### 4. Observe the first run

The agent will:
- Run on its schedule
- Gather data using available sources (web search at minimum)
- Maintain its own state between runs
- Self-assess output quality on a 1–10 scale
- Write reports to the `reports/` directory (or post to Slack if configured)

After the first run, check the output to see the health footer — it will tell you which sources were used and what quality score the agent gave itself.

---

## Customizing

Each AGENT.md is plain English. Modify it however you want:

- **Change the topic domain** — swap "crypto markets" for "climate tech", "biotech", or any other configurable area
- **Adjust the schedule** — daily, hourly, weekly — whatever fits
- **Add output channels** — configure Slack delivery by connecting the Slack MCP server
- **Change severity thresholds** — tune what counts as CRITICAL vs. LOW for your use case
- **Add data sources** — connect MCP servers for richer data (crypto prices, on-chain data, sentiment, news)
- **Adjust fallback chains** — if you have specific sources that should be tried in a specific order, write that in

---

## Scaling to a Fleet

Once you have a few agents running, the real leverage appears. Follow this order for smooth scaling:

### Step 1: Add the Watchdog
Deploy the [Fleet Watchdog](examples/fleet-watchdog/AGENT.md). It auto-discovers and monitors your other agents. This is the first operational agent you add — it gives you visibility into fleet health before you have enough agents to need it urgently.

### Step 2: Standardize the pattern
Every agent should follow Steps 0–7:
- **Step 0**: Load state from the local authority file (canvas reads are optional cross-agent context)
- **Steps 1–5**: Gather, analyze, self-assess, format, deliver
- **Step 6**: Update any live dashboards
- **Step 6.5**: Write to the SQLite data layer (historical record)
- **Step 7**: Persist state to the local file for the next run, then mirror to any display canvas (non-fatal)

### Step 3: Add delivery channels
Connect Slack for real-time posts, Gmail for digest emails (via a digest-aggregator agent), Calendar for push notifications. Start with Slack only — it's the primary backbone.

### Step 4: Add a Synthesis Engine
Once you have 4+ intelligence agents, deploy the [Synthesis Engine](examples/synthesis-engine/AGENT.md). It reads all the other agents' outputs and identifies cross-cutting themes. This is where fleet intelligence becomes more than the sum of its parts.

### Step 5: Add budget awareness
As your fleet grows, track run frequency and assign priority tiers (P0–P3). Deploy JIT budget management via the Watchdog so frequencies throttle automatically under pressure rather than degrading quality. See [JIT Budget Management](docs/patterns/jit-budget-management.md).

### Step 6: Add self-repair
Deploy [Fleet Auto-Repair](examples/fleet-auto-repair/AGENT.md). It continuously scans agent configurations, catches drift, and applies safe fixes autonomously. Commits the fixes to git so everything is audited.

### Step 7: Add the conversational interface
Once the fleet is mature, deploy [Fleet Query](examples/fleet-query/AGENT.md). It gives you a Slack-based Q&A interface over all accumulated fleet knowledge — ask any question, get a data-cited answer.

---

## Architecture Pattern

```
YOUR AGENT (AGENT.md)
    │
    ├── Reads:  state/last-run.json (own memory from prior runs)
    ├── Gathers: web search + MCP data sources
    ├── Writes:  reports/[agent]-[date].md (output)
    ├── Writes:  state/last-run.json (updated memory)
    └── Posts:   Slack channel (if configured)
```

**Key principle:** Each agent is fully self-contained. It has its own directory, its own state, and its own output. No agent depends on another agent's files. Communication between agents happens through shared channels (Slack) or state stores (shared canvas), not file dependencies.

This is what makes the system resilient at scale — any agent can fail, be modified, or be removed without affecting any other agent.

---

## Deeper Reading

Once you have the basics running, dive into the architectural patterns that make this framework distinct:

- **[State Management](docs/patterns/state-management.md)** — the two-tier state system
- **[Fallback Chains](docs/patterns/fallback-chains.md)** — graceful source degradation
- **[Quality Self-Rating](docs/patterns/quality-self-rating.md)** — the self-assessment protocol
- **[Execution Scaffolding](docs/patterns/execution-scaffolding.md)** — threshold-triggered action packages
- **[JIT Budget Management](docs/patterns/jit-budget-management.md)** — autonomous throttle protocol
- **[Self-Repair](docs/patterns/self-repair.md)** — autonomous fleet maintenance
- **[Visual Cards](docs/patterns/visual-cards.md)** — dynamic PNG cards in output

And the end-to-end case studies showing what the framework delivers in practice:

- **[Regulatory Enforcement Response](docs/case-studies/regulatory-enforcement-response.md)**
- **[On-Chain Sanctions Hit](docs/case-studies/onchain-sanctions-hit.md)**
- **[Daily Intelligence Digest](docs/case-studies/daily-intelligence-digest.md)**
- **[Agent Self-Repair](docs/case-studies/agent-self-repair.md)**
