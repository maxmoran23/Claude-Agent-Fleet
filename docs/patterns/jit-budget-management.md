# Pattern: JIT Budget Management

Autonomous, tiered throttle protocol that reduces agent run frequency — never model or prompt quality — as resource limits approach.

---

## The Problem

A fleet of autonomous agents running on a premium model burns token budget fast. At naive frequencies (every agent running on its originally-configured schedule), weekly run counts compound quickly — and a large fraction of those runs are often fast-exit no-ops (query agents polling an empty inbox, watchdogs scanning a healthy fleet, price monitors running during flat sessions).

When the fleet exceeds its token budget, three options exist:

1. **Reduce model quality** (downgrade to a cheaper model) — degrades every output permanently
2. **Shorten prompts** — same problem, degrades every output
3. **Reduce run frequency** — same output quality, just arrives less often

Only option 3 preserves what the fleet actually produces. But doing it manually is fragile — the operator has to notice budget pressure, audit frequency configurations across dozens of agents, and tune carefully without starving critical agents.

JIT (just-in-time) budget management automates option 3. The fleet monitors its own burn rate and autonomously throttles its own frequencies as limits approach.

---

## The Pattern

A Watchdog agent doubles as an autonomous budget manager. It tracks fleet-wide run count against a configured weekly target, projects burn rate, and escalates through four throttle levels as needed. Throttle decisions are applied without operator input. De-escalation is automatic when burn rate returns to baseline.

---

## The Four Throttle Levels

### NORMAL — on budget

All agents run at baseline frequencies. This is the default state.

### GREEN — approaching limit (projected overshoot ~20%)

**Action:** Pause P3 (luxury) agents. These are agents whose output is nice-to-have but not operationally critical:
- Exploratory research agents
- Frontier science / novel discovery agents
- Weekly deep-dive agents that duplicate daily-brief content
- Engagement-tracking companion agents

**Rationale:** P3 agents contribute depth but can pause for a week without harming the fleet's core function. Pausing them recovers ~20% of weekly budget.

### YELLOW — over budget (projected overshoot ~50%)

**Action:** Throttle P2 (high-frequency) agents to wider intervals:
- Interactive Q&A agents → every 30 minutes instead of every 15
- Breaking-news agents → 3x/day instead of 5x/day
- Cross-agent relays → 1x/day instead of 3x/day
- Thread-enrichment agents → 1x/day instead of 3x/day

**Rationale:** P2 agents are valuable but not time-critical at their highest frequency. The operator can tolerate slightly slower response on these.

### RED — significant overshoot (projected >50% over)

**Action:** Protect only P0 (core) agents at full schedule. Pause or minimize everything else:
- P0 agents: the handful the fleet cannot function without (typically: daily brief, primary regulatory monitor, critical-alert router, email digest aggregator, the watchdog itself)
- Everything else: paused or reduced to minimum viable frequency

**Rationale:** At RED, the choice is between full output from core agents and degraded output from everyone. Core agents preserved, rest deferred.

---

## Escalation and De-Escalation

**Escalation:** The Watchdog projects burn rate on every run (typically 4x/day). If the projection crosses a threshold, the Watchdog raises the throttle level and posts a notification to the fleet operations channel.

**De-escalation:** When burn rate drops (fewer critical events, slower news week, etc.), the Watchdog automatically returns to a lower throttle level. Agents resume their baseline frequencies.

**Manual override:** The operator can override via DM:
- `JIT level 0` — force NORMAL
- `JIT level 1` — force GREEN
- `JIT level 2` — force YELLOW
- `JIT level 3` — force RED
- `JIT auto` — restore autonomous control

Manual overrides persist until explicitly reverted.

---

## Priority Tiers

Every agent is assigned a priority tier in its frontmatter or configuration. Typical classification:

| Tier | Agents |
|------|--------|
| **P0** | Daily brief, critical-alert router, email digest aggregator, primary regulatory monitor, watchdog itself |
| **P1** | Market monitor, on-chain watchlist, daily synthesis, auto-repair, backup |
| **P2** | Interactive Q&A, breaking-news flash, market pulse, cross-agent relay, thread enrichment |
| **P3** | Idea discovery, frontier research, engagement tracker, portfolio-performance tracker |

The classification is opinionated and should be tuned for each deployment. Default starting point: everything ships at P1 unless you have a strong reason to promote to P0 or demote to P3.

---

## The Non-Negotiable Principle

The most important design decision is what the pattern does NOT do:

- **Never reduces model quality.** Agents stay on their configured model (typically the highest-capability option).
- **Never truncates prompts.** Prompts stay at full length.
- **Never skips steps in the agent's execution pattern.** Step 0 through Step 7 run completely every time.
- **Never degrades output format.** Output structure is preserved.

The ONLY thing that changes is *how often* agents run. An agent that runs at YELLOW produces the exact same output it would produce at NORMAL — the output just comes less frequently.

This is the core trade-off: the fleet degrades gracefully on availability, not fidelity.

---

## Why This Approach Wins

**Most fleets have uneven value density.** A small number of high-frequency agents consume a disproportionate share of total runs, and much of that consumption is on low-value fast-exit runs (empty inbox polls, healthy-fleet scans, flat-market checks). Reducing their frequency recovers significant budget at small cost to operator value.

**Output quality is non-fungible.** A market monitor running 2x/day with full-quality output is more valuable than one running 6x/day with a cheaper model. Readers tolerate less-frequent updates; they don't tolerate outputs that seem subtly wrong.

**Frequency is recoverable.** When budget pressure eases, frequencies restore instantly. Model choice and prompt design are sticky — once you downgrade, you tend to stay downgraded. Throttling is the only safe lever.

---

## Configuration and Thresholds

Typical configuration in the Watchdog's state:

```json
{
  "weekly_budget_target": 800,
  "current_run_count_this_week": 612,
  "days_elapsed_in_week": 5,
  "projected_runs_this_week": 857,
  "projection_ratio": 1.07,
  "current_throttle_level": "GREEN",
  "throttle_entered_at": "[ISO timestamp]",
  "agents_throttled": ["[agent1]", "[agent2]"],
  "escalation_thresholds": {
    "GREEN": 1.0,
    "YELLOW": 1.2,
    "RED": 1.5
  }
}
```

The `weekly_budget_target` is operator-configured based on the deployment's token envelope. Everything else is derived and updated autonomously.

---

## Related Patterns

- [Self-Repair](self-repair.md) — the watchdog role in detecting configuration drift
- [Quality Self-Rating](quality-self-rating.md) — score tracking that the watchdog uses for health monitoring
- [State Management](state-management.md) — where throttle state is persisted
