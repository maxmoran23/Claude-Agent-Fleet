# Pattern: Quality Self-Rating

Agents assessing their own output quality 1–10, with the rating persisted to state and surfaced in the output itself.

---

## The Problem

In a fleet of autonomous agents running on a schedule, how does the operator know which outputs to trust? Some runs are strong — fresh data, clean synthesis, high-confidence findings. Other runs are degraded — fallback sources, thin coverage, low-confidence calls. Without a quality signal on each output, the operator has to skim everything critically every time.

External quality evaluation (a separate evaluator agent judging each output) is expensive and introduces its own trust problem. A cheaper, more direct pattern: ask the agent to rate itself.

---

## The Pattern

At the end of every run, the agent performs an explicit Quality Self-Assessment step. It produces a 1–10 score based on a rubric scoped to that agent's domain, and the score appears:

1. In the output itself (health footer)
2. In the persisted state (for trend analysis)
3. In the data layer (for aggregation across runs and agents)

The operator learns to read the score first and decide whether to read the rest.

---

## The Rubric Structure

Each agent's rubric is domain-specific but follows a common structure:

| Score | Criteria |
|-------|----------|
| **9–10** | Best case: primary sources active, strong signal, clear synthesis, multiple high-severity findings (if any exist) |
| **7–8** | Solid: good source coverage, reliable output, minor gaps |
| **5–6** | Adequate: some data gaps, thin coverage, or mostly lower-severity findings |
| **3–4** | Degraded: significant fallback use, limited coverage, quality compromised |
| **1–2** | Minimal: primary sources down, state-only output, output is near-placeholder |

The rubric is written in the agent's AGENT.md so it is consistent across runs and auditable.

---

## What Goes Into the Score

Generally, the score combines three dimensions:

**Source quality:**
- Primary source active? → points
- Fallback tier used? → points lost
- Source freshness within expected window? → points

**Output density:**
- Did the agent produce enough findings to be useful?
- Were the findings substantive or padding?
- Is the synthesis actually saying something?

**Confidence:**
- Can the agent defend each finding with a citation?
- Were there conflicts between sources? Resolved or flagged?
- Is the language hedging too much (low confidence) or over-claiming (unwarranted confidence)?

An agent scoring itself high must be able to defend each dimension. The pattern is trustworthy not because the agent is objective, but because the rubric is explicit and the scores are tracked over time.

---

## Where the Score Appears

### In the output

Every agent's output ends with a health footer:

```
---
Health: Sources: [list] | Fallbacks: [count] | Quality: [score]/10 | Runtime: [duration]
```

The quality score is the most visible signal. An operator scanning a channel can filter mentally: "9/10, read; 4/10, skim; 1/10, skip."

### In persisted state

Every agent persists the current run's score:

```json
{
  "quality_score": 8,
  "quality_history": [7, 8, 9, 8, 6]  // last 5 runs
}
```

The `quality_history` field lets the agent itself detect drift: if the last 5 runs trend 9 → 8 → 7 → 6 → 5, something is degrading and the agent can call that out in its next run.

### In the data layer

Every run's quality score is written to `agent_runs`:

```sql
INSERT INTO agent_runs (
  agent_name, run_timestamp, quality_score, fallbacks_triggered, ...
) VALUES ( ... );
```

This enables fleet-wide aggregation:

```sql
-- Average quality by agent over the last 30 days
SELECT agent_name, AVG(quality_score), COUNT(*)
FROM agent_runs
WHERE run_timestamp > date('now', '-30 days')
GROUP BY agent_name
ORDER BY AVG(quality_score) DESC;
```

---

## Downstream Uses

**Watchdog agent** watches quality trends across the fleet. Sustained quality drops for a specific agent trigger an escalation — something is broken upstream of that agent, or the agent's configuration has drifted.

**Synthesis engine** deprioritizes findings from agents that self-scored below 5. If a market monitor run scored itself 3/10, the synthesis engine treats that run's findings as low-confidence.

**Fleet query agent** surfaces quality when citing sources:

```
Answer: [x]
Source: market-monitor run at [timestamp], quality: 8/10
```

**Operator** learns the signal. A 9/10 health footer is different from a 6/10 on the same agent the previous day — the delta itself is information.

---

## Why Self-Rating Works

Counterintuitively, asking an agent to score its own output produces meaningful signal because:

1. **The rubric constrains the rating.** The agent isn't making up a number; it's answering specific questions about sources, fallbacks, and coverage.
2. **The score is persisted and cross-checked.** Operators can audit historical scores against actual usefulness, and the agent's own quality_history catches drift.
3. **Low scores are self-penalizing.** An agent that scores itself 9/10 consistently while the operator ignores its output is measurably miscalibrated, and the miscalibration shows up in data-layer queries.
4. **High scores aren't gaming.** There's no external incentive to inflate. The agent isn't rewarded for high scores. The rubric explicitly requires fallback-tier usage to reduce the score.

Self-rating is not a substitute for human review. It is a *triage signal* so human review can be efficient.

---

## Calibration Over Time

Over weeks and months, the score distribution itself becomes a signal:

- Is the agent's score distribution narrow (always 7–8) or healthy (3–10)? Narrow distribution means the agent isn't distinguishing good runs from bad ones — recalibrate the rubric.
- Does quality correlate with operator engagement (emoji reactions, click-throughs if measurable)? If 9/10 runs get more engagement than 5/10 runs, the scoring is tracking reality.
- Do fallback counts predict score? They should. If an agent has fallbacks=3 but scored itself 8/10, the rubric isn't being applied.

The auto-repair agent catches miscalibration cases and flags them for operator review.

---

## Related Patterns

- [Fallback Chains](fallback-chains.md) — fallback usage directly feeds the quality score
- [Self-Repair](self-repair.md) — quality drift detection triggers repair
- [State Management](state-management.md) — where the score is persisted
