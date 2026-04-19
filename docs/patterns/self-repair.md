# Pattern: Autonomous Self-Repair

Fleet agents that scan the fleet, detect drift, and apply safe fixes without operator input.

---

## The Problem

A fleet of agents evolves over time. Models get retired. Integration endpoints change. State-store paths drift. Frontmatter conventions update. New anti-patterns emerge and need to be fixed retroactively across the fleet.

Doing this manually has two failure modes:

1. **It doesn't happen.** The operator is busy. Small drifts accumulate. The fleet degrades silently.
2. **It happens sporadically.** The operator cleans up one problem, misses three others, and the next cleanup round is triggered only after something breaks.

Neither produces a stable fleet. What a maturing fleet needs is an agent that takes on fleet maintenance itself — continuously scanning, detecting, and repairing.

---

## The Pattern

A dedicated auto-repair agent scans every other agent's configuration on a schedule (typically 3x daily), validates against a set of known-good patterns, classifies findings by repair safety, applies safe repairs autonomously, and escalates anything ambiguous to the operator.

The pattern has strict safety constraints: the agent never modifies prompt content, never deletes an agent, and always commits repairs with descriptive messages for auditability.

---

## The Classification Ladder

Every finding is classified into one of four severities, which determines what happens next.

### SAFE_AUTO

Can be fixed without any operator input. Examples:
- Frontmatter model reference points to a retired model → update to the current supported model
- State store subdirectory missing → create it
- Deprecated frontmatter field present → remove it
- Health footer format missing the `fallbacks` field → add it with default value 0

**Handling:** Apply the fix, log it in the repair log, commit to git with a descriptive message. No human notification beyond the run's output log.

### REVIEW_AUTO

Can be fixed but the operator should see the change. Examples:
- Slack channel reference has changed and needs updating to the new channel ID
- Upstream state-store path has moved and needs repointing
- MCP server reference has been renamed in the fleet config

**Handling:** Apply the fix, log it in the repair log with a REVIEW flag, and post a notification to the fleet operations channel naming the agent, the change, and the reason. The operator can revert if needed.

### ESCALATE

Requires operator judgment. Examples:
- Agent is apparently duplicating work another agent already does
- Agent has a scheduling conflict with a higher-priority agent
- Agent's prompt content contains a pattern that looks wrong but might be intentional
- Agent has been silently failing (zero output for N runs) and needs diagnosis

**Handling:** Do NOT auto-apply. Log in an escalation log. Post to the fleet operations channel with context and a recommended fix. Wait for operator decision.

### INFO

Worth noting but no action required. Examples:
- Agent's quality score has trended down 3 points over 10 runs
- Agent's fallback count has been >0 on the last 5 runs

**Handling:** Log only. No message. The data is available to the watchdog or feedback-harvester for trend analysis.

---

## Safety Constraints

The auto-repair agent operates under non-negotiable rules:

**Never modify prompt content.** The agent only touches structural fields: frontmatter, paths, integration references, state-store conventions, health footer format. The actual prompt text — the agent's logic and instructions — is never rewritten. That's the operator's domain.

**Never delete an agent.** If the agent folder is orphan-looking (no recent runs, no clear purpose), escalate. Don't remove.

**Always commit with a descriptive message.** Every repair produces a git commit scoped to just that repair, with a message explaining what changed and why. The repo becomes a chronological audit log of fleet evolution.

**Classify before acting.** A repair never bypasses classification. If the agent can't confidently classify a finding, it escalates. Better to escalate a true SAFE_AUTO case than to misclassify an ESCALATE case.

**Escalate ambiguity.** If a pattern is novel or the repair approach is unclear, escalate rather than guess. Novel patterns become new entries in the repair-pattern ruleset, but only after operator review.

---

## The Repair Pattern Ruleset

The auto-repair agent operates against an explicit ruleset — the list of what it knows how to check and fix. Starting set:

| Pattern | Check | Fix |
|---------|-------|-----|
| `retired_model_reference` | Frontmatter model points to a retired model ID | Update to current supported model |
| `missing_state_dir` | AGENT.md references state/ but state/ doesn't exist | mkdir state/ |
| `missing_reports_dir` | AGENT.md references reports/ but reports/ doesn't exist | mkdir reports/ |
| `deprecated_frontmatter_field` | Frontmatter contains a field no longer in the convention | Remove field |
| `missing_fallback_chain_section` | AGENT.md has data-gathering steps but no Fallback Chain section | ESCALATE |
| `missing_health_footer_format` | No health footer format defined in AGENT.md | ESCALATE |
| `dead_channel_reference` | Slack channel ID returns 404 on API check | ESCALATE |
| `dead_state_store_reference` | Upstream agent state path doesn't exist | REVIEW_AUTO (repoint if obvious) or ESCALATE |
| `duplicate_work_pattern` | Agent's gather step overlaps with another agent's | ESCALATE |
| `silent_failure` | Agent has zero outputs in channel for N runs | ESCALATE |
| `quality_trend_degraded` | quality_history last 5 runs show steady decline | INFO (log for trend analysis) |

The ruleset grows over time. Every new pattern added goes through operator approval first.

---

## The Repair Log

Every repair is logged with enough detail to audit later:

```json
{
  "repair_id": "repair-2026-04-19-001",
  "agent": "regulatory-oracle",
  "file": "examples/regulatory-oracle/AGENT.md",
  "change_type": "frontmatter_update",
  "pattern_matched": "retired_model_reference",
  "before": "model: claude-opus-3-5",
  "after": "model: claude-opus-4-6[1m]",
  "reason": "Opus 3.5 was retired 2026-03-15; updating to current supported model",
  "timestamp": "2026-04-19T14:22:18Z",
  "git_commit": "a1b2c3d"
}
```

Over time, the repair log becomes the institutional memory of fleet evolution — every small fix recorded, every pattern shift captured.

---

## Why This Pattern Works

**Maintenance is continuous.** Small issues get fixed before they compound. The fleet stays clean without a scheduled maintenance window.

**Auditability is free.** Every fix is a git commit. The operator can always ask "when did this change?" and get a precise answer.

**It scales with fleet size.** One auto-repair agent can maintain 5 agents or 50 agents with the same effort. Manual maintenance doesn't scale.

**It catches what humans miss.** Running structural validation 3x/day catches drift that would take weeks for an operator to notice during ad-hoc review.

**It trains the operator.** Reading repair commits over time teaches the operator what structural patterns matter and how the fleet is evolving.

---

## Anti-Patterns to Avoid

**Over-aggressive classification.** Classifying everything as SAFE_AUTO defeats the safety constraint. When in doubt, escalate.

**Silent fixes.** Every SAFE_AUTO fix must land in git with a clear commit message. A fix that isn't committed doesn't exist.

**Modifying logic.** The auto-repair agent stays structural. The moment it touches prompt content, the operator can no longer trust what the fleet actually does.

**Chasing false positives.** A pattern that produces more false positives than true hits costs operator attention on reviewing escalations. Remove patterns that don't pay for themselves.

---

## Related Patterns

- [State Management](state-management.md) — state-store conventions the auto-repair agent enforces
- [Fallback Chains](fallback-chains.md) — required section whose absence triggers ESCALATE
- [JIT Budget Management](jit-budget-management.md) — the watchdog and auto-repair together form the fleet's operations layer
