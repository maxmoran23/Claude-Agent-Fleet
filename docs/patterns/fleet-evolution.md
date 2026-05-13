# Pattern: Fleet Evolution

An autonomous, periodic upgrade loop that assesses each agent against a fixed maturity framework and implements the highest-impact upgrade in the fleet without human intervention.

---

## The Problem

In a fleet of dozens of agents, manual upgrades don't scale. Each agent has its own prompt, configuration, state schema, and output format — and improvements rarely land uniformly. The result is a long tail of agents stuck at minimal viable functionality while a small number get repeatedly polished. The fleet drifts toward uneven quality.

The naive alternative — "rewrite every agent quarterly" — is worse. It conflates maintenance with reinvention, breaks working agents, and burns the operator's attention on agents that don't need changes.

The pattern that works: a fixed maturity framework that every agent can be scored against, plus an autonomous weekly loop that picks the single highest-impact upgrade in the fleet and ships it. Quality compounds across the fleet without a human running per-agent retrospectives.

---

## The Pattern

A dedicated Evolution Engine agent runs once per week. Each cycle, it:

1. Scores every agent against the maturity framework, producing a current level (L1–L5) and the gap to the next level.
2. Estimates the upgrade impact for each candidate (how much fleet-wide quality moves if this agent is promoted).
3. Picks the single highest-impact upgrade for the cycle.
4. Implements the upgrade — editing the agent's configuration, prompt, or supporting files.
5. Logs the upgrade as an experiment in the data layer, with pre- and post-upgrade metrics for later evaluation.
6. Schedules the next cycle.

The Evolution Engine never rewrites the whole agent. It applies one focused, defined upgrade per cycle and lets the next cycle assess outcomes.

---

## The Five Maturity Levels

Each level is defined by capabilities, not lines of code. Promotion is binary — an agent either meets all level criteria or doesn't.

### L1 — SCOUT

The minimum viable agent. Gathers from a single source, runs the prompt, posts the output.

- Single data source, no fallback chain
- No persistent state between runs
- No quality self-rating
- No severity classification
- No cross-agent awareness

Sufficient for prototyping or single-domain monitors with low downside risk. Most agents start here.

### L2 — OPERATOR

A reliably-running agent that survives source outages and produces inspectable output.

- Multi-source fallback chain (primary → secondary → tertiary)
- Persistent state across runs (Step 0 load, Step 7 persist)
- Quality self-rating (1–10) in a health footer
- Standardized output format
- Graceful degradation — never hard-fails, always produces some output

The minimum bar for any agent that other agents depend on.

### L3 — ANALYST

An agent whose output is structured for downstream consumption, including cross-agent references.

- Severity classification (CRITICAL / HIGH / MEDIUM / LOW) per finding
- Execution scaffolding for threshold-triggered actions (see [`execution-scaffolding.md`](execution-scaffolding.md))
- Cross-agent state-store reads (uses context from other agents' state)
- Structured writes to a queryable data layer (not just text channels)
- Tested fallback paths under simulated failures

The level at which an agent meaningfully participates in the fleet, rather than running in isolation.

### L4 — SYNTHESIST

An agent that uses historical context to detect patterns rather than just snapshots.

- Queries the data layer for trend / delta / regression analysis
- Output references "what changed since the last N runs" rather than restating current state
- Identifies anomalies relative to its own baseline
- Predicts forward where the analysis warrants (with explicit confidence bands)
- Produces output that is not reproducible without history — i.e., re-running cold gives a worse result

Agents at L4 stop being snapshots and start being trend analysts.

### L5 — MASTER

An agent that contributes back to the fleet's self-improvement loop.

- Identifies upgrade opportunities in its own configuration
- Proposes prompt or schema changes to the Evolution Engine
- Cross-checks its own quality scores against operator engagement signals
- Can run controlled experiments against itself (A/B prompt variants, schedule changes)
- Survives a full Evolution Engine review with zero recommendations

L5 is rare and expected to be rare. Most fleets have a small number of L5 agents — typically the most operationally critical ones.

---

## Scoring and Promotion

Every cycle, the Evolution Engine produces a fleet matrix:

| Agent | Current Level | Next Level | Gap | Impact Estimate |
|-------|---------------|------------|-----|------------------|
| daily-brief | L4 | L5 | Self-experimentation capability | Medium |
| market-monitor | L3 | L4 | Historical trend analysis | High |
| edge-hunter | L4 | L5 | Self-experimentation capability | Low |
| onchain-watchlist | L2 | L3 | Severity classification, cross-agent reads | High |
| ... | ... | ... | ... | ... |

The single highest-impact gap is selected for implementation that cycle. Tie-breakers favor agents whose output is most frequently consumed by other agents (a fleet-internal dependency graph derived from state-store reads).

Impact is not a fixed metric — it's an operator-tunable function of:
- How much the agent's quality score lags the fleet average
- How many other agents depend on this agent's output
- How much operator engagement (e.g., emoji reactions, follow-up questions) the agent currently earns
- How recently the agent was last upgraded

---

## The Non-Negotiable Principle

One upgrade per cycle. No batch refactors.

The Evolution Engine is allowed to:
- Edit a single agent's prompt, configuration, or supporting templates
- Add a new section to one agent's output format
- Promote an agent from L2 → L3 (one level only)
- Add a new fallback source to one agent's chain

The Evolution Engine is forbidden from:
- Editing more than one agent per cycle
- Promoting an agent more than one level per cycle
- Restructuring shared infrastructure (config schemas, state-store conventions)
- Disabling or removing any agent

This is the core safety constraint: the operator can review the cycle's upgrade in minutes, roll it back if needed, and trust that no other agent was silently changed. The loop is autonomous *and* auditable.

---

## Experiment Tracking

Every upgrade is logged as a structured experiment:

```json
{
  "cycle_id": "C11",
  "cycle_date": "2026-05-13",
  "agent": "market-monitor",
  "from_level": "L3",
  "to_level": "L4",
  "upgrade_type": "historical_trend_analysis",
  "changes": ["Added Step 1.5: query agent_runs for last 14d", "Added trend block to output format"],
  "pre_upgrade_metrics": {
    "avg_quality_score": 7.2,
    "operator_engagement": 0.34,
    "avg_runtime_seconds": 38
  },
  "expected_post_upgrade_metrics": {
    "avg_quality_score": 8.0,
    "operator_engagement": 0.50,
    "avg_runtime_seconds": 55
  },
  "evaluation_due": "2026-05-27"
}
```

After the evaluation window (typically two weeks), the Evolution Engine compares actuals to expected and either confirms the promotion or rolls back. Rolled-back upgrades are kept in the experiment log so the same upgrade isn't retried verbatim.

---

## Why This Approach Wins

**Compounding quality without compounding scope.** Most upgrade processes either skip agents (the long-tail problem) or rewrite everything at once (the breakage problem). One-per-cycle hits a middle path: every agent eventually gets attention, but the operator's audit surface per cycle is small.

**Honest level definitions.** Because levels are binary (an agent meets all criteria or doesn't), there's no ambiguity about where an agent sits. The fleet matrix is reproducible — anyone running the assessment with the same definitions gets the same scores.

**Experiment discipline.** Tracking each upgrade as a hypothesis with pre/post metrics forces the operator (and the Engine) to acknowledge when an upgrade didn't pay off. Most agent upgrade processes have no such accountability.

**Bounded risk.** The one-upgrade-per-cycle constraint means a botched upgrade affects exactly one agent. Rollback is mechanical.

---

## Configuration

Typical Evolution Engine state:

```json
{
  "cycle_id": "C12",
  "scheduled_run": "2026-05-19T07:00:00Z",
  "previous_cycle": {
    "cycle_id": "C11",
    "agent_upgraded": "market-monitor",
    "from_level": "L3",
    "to_level": "L4",
    "evaluation_due": "2026-05-27"
  },
  "level_definitions_version": "1.0",
  "fleet_matrix_snapshot": "[link to last full matrix]",
  "evaluation_pending": ["C9-edge-hunter", "C10-onchain-watchlist"],
  "rollback_log": []
}
```

Operators can pin the next upgrade target via configuration if they want a specific agent advanced ahead of the impact-ranked default.

---

## Related Patterns

- [State Management](state-management.md) — the state store the Evolution Engine reads and writes
- [Self-Repair](self-repair.md) — the auto-repair loop the Evolution Engine builds on
- [Quality Self-Rating](quality-self-rating.md) — the score that feeds the impact estimate
- [JIT Budget Management](jit-budget-management.md) — the constraint envelope inside which evolution happens
