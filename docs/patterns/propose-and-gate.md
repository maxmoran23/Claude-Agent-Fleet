# Pattern: Propose-and-Gate

A change-control loop for self-improving fleets: the evolution engine proposes upgrades as complete diffs, a human gates them by reaction vote, and the engine applies approved changes with one-commit reversibility.

---

## The Problem

A self-improving fleet has to modify its own agent definitions — that's the point. But ungated self-modification compounds errors. A bad "upgrade" doesn't fail loudly; it silently degrades output quality until someone notices three weeks later, by which point two more upgrades have been layered on top of it. And an autonomous edit to a live prompt is unreviewable after the fact: the operator can see *that* the agent behaves differently, but reconstructing *what changed and why* from behavior alone is archaeology.

This is a different problem from drift. The [self-repair pattern](self-repair.md) restores agents to their *declared* state — it fixes the gap between what an agent's definition says and what's actually on disk or in the scheduler. Propose-and-gate governs *changing* the declared state. Self-repair is the immune system; this is the germline editing protocol, and germline edits get reviewed.

The naive alternatives both fail:

1. **Full autonomy.** The engine edits live agents directly. Fast, and every regression is a forensic exercise.
2. **Full manual.** The operator hand-writes every upgrade. Doesn't scale past a dozen agents — which is exactly the long-tail problem the evolution loop exists to solve (see [Fleet Evolution](fleet-evolution.md)).

The middle path: the engine does all the work *except* the decision.

---

## The Pattern

Four phases per cycle. The engine proposes, the human gates, the engine applies, the engine measures.

```
                 +-----------+
                 |  PROPOSE  |  engine writes complete proposal packages
                 +-----+-----+  to a dedicated proposals branch
                       |
                       v
                 +-----------+
                 |   GATE    |  summary cards posted to the fleet channel;
                 +-----+-----+  operator votes by reaction
                       |
          +------------+------------+
          |            |            |
      approve       reject      no vote (14d)
          |            |            |
          v            v            v
    +-----------+  _rejected/   _expired/
    |   APPLY   |  (archived    (mentioned
    +-----+-----+   with         once,
          |         reason)      dropped)
          v
    +-----------+
    |  MEASURE  |  14-day baseline vs. 14-day post window;
    +-----------+  verdict feeds the next cycle's prioritization
```

Everything is git. Proposals live on a branch, applications are isolated commits on main, and every change names its own rollback before it ships.

---

## Phase 1: Propose

Each cycle the engine selects up to five agents — quality over quantity — and designs exactly one upgrade per agent, drawn from a universal skill tree: scoring models, prediction tracking, cross-agent feeds, adaptive thresholds, compound intelligence, and so on. One upgrade per agent keeps each proposal reviewable in minutes.

For each selected agent the engine writes a complete proposal package:

```
proposals/{date}/{agent}/
  AGENT.md.proposed    the full proposed agent file, ready to apply verbatim
  RATIONALE.md         what changed, why, expected metric movement, rollback note
  CHANGES.diff         unified diff: live file -> proposed file
```

`AGENT.md.proposed` is the entire file, not a patch description — the apply step is a copy, not an interpretation. `RATIONALE.md` is the human-facing argument:

```markdown
# Proposal: market-monitor — adaptive alert thresholds

## What changed
Static price-move threshold (3.0%) replaced with a rolling 30-run
volatility-scaled threshold (Step 2.4 added; output format gains a
`threshold_basis` field).

## Why
12 of the last 20 runs fired alerts during high-volatility windows
where 3.0% moves are noise. Operator engagement on those alerts: 0.08.

## Expected metric movement
alert precision 0.41 -> 0.65 (est.); operator engagement +0.15.

## Rollback
Revert the evolution-apply commit for this proposal. No state
migration required — the new field is additive.
```

Proposals are committed to a dedicated `fleet-evolution-proposals` branch — never main. Main only ever receives applied, approved changes.

---

## Phase 2: Gate

The engine posts one summary card per proposal to the fleet channel: agent, upgrade type, one-paragraph rationale, expected metric movement, link to the diff. The operator votes by reaction:

| Reaction | Meaning | Outcome |
|----------|---------|---------|
| `:white_check_mark:` | Approve | Applied at the start of the next cycle |
| `:no_entry_sign:` | Reject | Archived to `proposals/_rejected/` with the threaded reason |
| `:pencil2:` + threaded reply | Revise and resubmit | Engine redesigns against the feedback next cycle |
| (none, 14 days) | Expired | Moved to `proposals/_expired/`, mentioned once, dropped |

One convenience rule: a `:white_check_mark:` on the parent summary post approves **all** cards in that cycle, with per-card reactions overriding. The common case — "these all look fine" — costs one reaction; the careful case still works card by card.

The gate is the entire human surface area of the loop. The operator reviews diffs and rationales, not running agents.

---

## Phase 3: Apply (Step 2.5)

Application happens at the start of the *next* cycle, as Step 2.5 — never in the same cycle as the proposal. This forces a minimum review window and means a missed gate simply delays, never blocks, the loop.

For each approved proposal:

1. Copy `AGENT.md.proposed` over the live agent file. The copy is idempotent — applying twice produces the same bytes, so a re-run after a crashed cycle is harmless.
2. Commit to main as an isolated `evolution-apply` commit — one commit per application, touching one agent. One commit per application means one-commit rollback: `git revert <sha>` restores the agent exactly, with no untangling.

Rejected proposals are archived to `proposals/_rejected/` together with the operator's threaded reason — the engine reads these archives so the same rejected idea isn't re-proposed verbatim. Unreacted proposals expire to `proposals/_expired/` after 14 days, get one mention in the next cycle's summary, and are dropped.

---

## Phase 4: Measure

Approval is a hypothesis, not a verdict. At apply time the engine captures a 14-day pre-upgrade baseline — quality scores, operator engagement — into an `upgrade_experiments` table:

```json
{
  "experiment_id": "exp-2026-05-13-market-monitor",
  "agent": "market-monitor",
  "upgrade_type": "adaptive_thresholds",
  "apply_commit": "f4e8a21",
  "baseline_window": { "from": "2026-04-29", "to": "2026-05-13", "avg_quality": 7.1, "engagement": 0.34 },
  "evaluation_due": "2026-05-27",
  "verdict": null
}
```

Fourteen days later the engine compares windows and records a verdict:

| Verdict | Threshold | Effect on next cycle |
|---------|-----------|----------------------|
| IMPROVED | ≥ 5% gain | Upgrade type gains priority for similar agents |
| NEUTRAL | within ±5% | Logged; upgrade type deprioritized for this agent class |
| REGRESSED | ≥ 5% loss | One-commit revert recommended; upgrade type flagged |

Verdicts feed the next cycle's proposal prioritization — the skill tree learns which branches pay off. The measurement mechanics (windows, metrics, significance) are the subject of the [Evaluation Harness](evaluation-harness.md) pattern; the upgrade selection logic is described in [Fleet Evolution](fleet-evolution.md).

---

## Guardrails

Non-negotiable constraints on every proposal:

- **Additive-only.** A proposal may add capabilities; it never removes working functionality. Deletions are an operator decision made outside this loop.
- **Preserve integration references exactly.** Channel references, state-store paths, data-layer table names, and cross-agent reads pass through proposals byte-identical. An upgrade that breaks an integration is a repair problem the fleet shouldn't create for itself.
- **Maximum 5 proposals per cycle.** The gate only works if reviewing a cycle takes minutes. Twenty cards get rubber-stamped; five get read.
- **Every change names its rollback.** `RATIONALE.md` must state the rollback procedure and whether any state migration is involved. A proposal that can't articulate its own undo is rejected by construction.

---

## Failure Modes

| Failure | Mitigation |
|---------|------------|
| Operator never votes | 14-day expiry to `proposals/_expired/`; the queue never silently grows, and expiry is mentioned once so inaction is a visible choice |
| Approval applied twice (crashed cycle, re-run) | Apply is an idempotent file copy; the second application is a no-op and produces no second commit |
| Proposal branch diverges from main | The branch is rebased onto main at the start of each cycle, before new proposals are written; stale diffs are regenerated |
| Approved upgrade regresses in production | One-commit `git revert` restores the agent; the experiment verdict records REGRESSED so the upgrade type is flagged, not retried |

---

## Why This Pattern Works

**The human reviews diffs, not behavior after the fact.** Every change to a live agent was a unified diff the operator saw before it shipped. Debugging a misbehaving agent starts with `git log` on its file, where every `evolution-apply` commit links back to a proposal package with its rationale — not with re-deriving intent from output.

**The approval queue is the change-control log.** The fleet channel thread of summary cards, reactions, and threaded reasons *is* the audit trail: what was proposed, what was approved, what was rejected and why, what expired. No separate record-keeping, and nothing reaches main without passing through it.

**Reversibility is structural, not aspirational.** One proposal, one commit, one revert. The rollback path is identical for every upgrade ever applied, so rolling back is never a judgment call about untangling.

**The engine keeps its autonomy where autonomy is cheap.** Selection, design, diff generation, application, measurement — all autonomous. Only the decision is human, and it costs one reaction per cycle in the common case.

---

## Related Patterns

- [Fleet Evolution](fleet-evolution.md) — the upgrade loop whose changes this pattern gates
- [Self-Repair](self-repair.md) — restores declared state; propose-and-gate changes it
- [Evaluation Harness](evaluation-harness.md) — the measurement machinery behind Phase 4
- [Quality Self-Rating](quality-self-rating.md) — the score tracked in upgrade experiments
