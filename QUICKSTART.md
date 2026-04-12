# Quickstart: Build Your Own Agent

This guide walks you through deploying one of the example agents from this repository. No programming experience required — just Claude Code.

---

## Prerequisites

- [Claude Code](https://claude.ai/code) (Max plan recommended for scheduled tasks)
- A working directory on your machine (e.g., `~/agents/`)

---

## Deploy an Example Agent in 5 Minutes

### 1. Choose an agent

| Agent | What It Does | Best For |
|-------|-------------|----------|
| [Research Digest](examples/research-digest/AGENT.md) | Daily AI/ML research briefing | Staying current on AI developments |
| [Market Monitor](examples/market-monitor/AGENT.md) | Crypto market snapshots with sentiment | Market awareness |
| [Fleet Watchdog](examples/fleet-watchdog/AGENT.md) | Monitors health of other agents | Once you have 3+ agents running |

### 2. Set up the directory

```bash
mkdir -p ~/agents/research-digest/state
mkdir -p ~/agents/research-digest/reports
```

### 3. Copy the agent config

Copy the AGENT.md file from this repo into your new directory:

```bash
cp examples/research-digest/AGENT.md ~/agents/research-digest/
```

Or simply copy-paste the contents of the AGENT.md file into a new file at `~/agents/research-digest/AGENT.md`.

### 4. Create a scheduled task

In Claude Code, create a scheduled task that:
- Points to the AGENT.md file as the prompt
- Runs on your preferred schedule (e.g., daily at 8:00 AM)
- Has access to the agent's directory for state persistence

### 5. That's it

The agent will:
- Run on schedule
- Gather data using web search (no API keys needed)
- Maintain its own state between runs
- Self-assess its output quality
- Write reports to the `reports/` directory

---

## Customizing

Each AGENT.md is plain English. Modify it however you want:

- **Change the domain** — swap "AI/ML research" for "climate tech" or "biotech" or anything else
- **Adjust the schedule** — daily, hourly, weekly, whatever fits
- **Add output channels** — configure Slack delivery by connecting the Slack MCP server
- **Change severity thresholds** — tune what counts as CRITICAL vs. LOW for your use case
- **Add data sources** — connect MCP servers for richer data (e.g., Crypto.com for live prices)

---

## Scaling to a Fleet

Once you have a few agents running:

1. **Add the Watchdog** — deploy the Fleet Watchdog agent alongside your other agents. It auto-discovers new agents and monitors them.

2. **Standardize the pattern** — each agent should follow the Steps 0-7 lifecycle:
   - Step 0: Load state
   - Steps 1-5: Gather, analyze, format, deliver
   - Step 6: Update any dashboards
   - Step 7: Persist state

3. **Add delivery channels** — connect Slack for real-time posts, Gmail for digest emails, Apple Notes for mobile reference.

4. **Build a Synthesis agent** — once you have 5+ agents, create an agent that reads all their outputs and identifies cross-cutting themes. This is where fleet intelligence becomes more than the sum of its parts.

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
