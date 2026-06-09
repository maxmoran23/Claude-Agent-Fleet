# Pattern: Generated Registry

Fleet inventory that is generated from primary sources on every maintenance cycle — never hand-written — with drift between declared and runtime state computed automatically.

---

## The Problem

Prose inventories of a 60+ agent fleet drift the moment they are written. README tables, ops docs, schedule lists — each one asserts facts ("the fleet has 58 agents", "market-monitor runs every 4 hours on the premium model") that stop being true the next time anything changes, and nothing forces the prose to change with it.

This isn't hypothetical. The audit that motivated this pattern found the fleet's documented agent count, its schedule table, and its model assignments had *all* diverged from runtime reality — the "spec-vs-runtime gap." The fleet's own documentation was the least reliable source of information about the fleet.

Hand-maintained inventory is a liability with a predictable failure mode: every doc that asserts a count is a future lie. The fix is not "update the docs more often." The fix is to stop writing inventory by hand at all.

---

## The Pattern

Inventory is *generated, never written*. A registry generator cross-joins the primary sources, each of which owns exactly one fact:

```
agent directories      what exists (dir basename = canonical agent name)
schedule manifest      what SHOULD run (declared cron, enabled, tier)
live scheduler state   what IS scheduled (snapshot captured each watchdog cycle)
model policy           what model each agent SHOULD use (4-tier intent)
run database           what actually ran (freshness, counts, quality)
state index            who has durable state and how fresh
```

No source duplicates another's fact. The directory tree doesn't claim schedules; the manifest doesn't claim what ran. The generator joins them on the canonical agent name (the directory basename) and emits two outputs:

- **`fleet-registry.json`** — machine-readable, consumed by the [self-repair agent](self-repair.md), the watchdog, and the evaluation harness. Other agents never re-derive inventory; they read the registry.
- **`SYSTEM-INDEX.md`** — the human view: one row per agent with schedule, tier, model intent, run freshness, and state freshness, plus an auto-computed **DRIFT** section at the top.

A registry entry:

```json
{
  "agent": "market-monitor",
  "exists": true,
  "manifest": { "cron": "0 */4 * * *", "enabled": true, "tier": "P1" },
  "scheduler": { "cron": "0 */4 * * *", "enabled": true, "snapshot_at": "2026-05-13T11:02:00Z" },
  "model_policy": "standard-locked",
  "last_run": { "at": "2026-05-13T08:01:44Z", "quality": 7.8, "runs_7d": 41 },
  "state": { "present": true, "updated_at": "2026-05-13T08:01:49Z" },
  "drift": []
}
```

Every prose doc in the repo that needs a count or a schedule points at `SYSTEM-INDEX.md` instead of asserting one.

---

## Drift Classes

The DRIFT section is the payoff: because declared and runtime sources sit side by side in one join, divergence is a column comparison, not an audit.

| Drift class | Detection | Severity | Typical cause |
|-------------|-----------|----------|---------------|
| Model drift | Run DB shows the agent ran on a model below its declared tier | HIGH | Scheduler reset to a default model; policy file updated without runtime follow-through |
| Schedule drift: manifest-not-live | Agent enabled in the manifest but absent from the live scheduler snapshot | HIGH | The signature of a scheduler wipe — declared truth survived, runtime didn't |
| Schedule drift: live-not-in-manifest | Agent scheduled at runtime but missing from the manifest | MEDIUM | Schedule created ad hoc and never declared |
| Schedule drift: cron-diff | Manifest cron and live cron disagree | MEDIUM | One side edited without the other |
| Schedule drift: enabled-diff | Enabled flag disagrees between manifest and scheduler | MEDIUM | Agent paused at runtime, never recorded (or vice versa) |
| Instrumentation drift | Scheduled and active, but never reporting to the run DB | HIGH | Agent runs without the standard run-logging step — invisible to every metric |
| Kernel-adoption lag | Agent definition predates the current kernel/convention version | LOW | New convention shipped; agent not yet migrated |

In `SYSTEM-INDEX.md`, the DRIFT section renders as findings, not prose:

```
## DRIFT (computed 2026-05-13T11:02Z)

HIGH    model-drift          regulatory-oracle   ran on efficient model; policy declares standard-locked
HIGH    manifest-not-live    headline-flash      enabled in manifest, absent from scheduler snapshot
MEDIUM  cron-diff            daily-brief         manifest 0 7 * * *, live 0 8 * * *
LOW     kernel-lag           onchain-watchlist   definition at kernel v1.2, current v2.0

4 findings across 61 agents. 57 clean.
```

Manifest-not-live deserves emphasis: when a scheduler's runtime database is wiped (a real and recurring failure class), every agent vanishes from the live snapshot while the manifest still declares them. The drift report lights up with one identical HIGH finding per agent — an unmistakable signature, caught within one cycle instead of discovered agent by agent as silence.

---

## Where the Generator Runs

The generator runs inside the self-repair agent's cycle — every few hours, not on demand. Drift therefore surfaces within one cycle as ordinary findings in the repair flow (classified, logged, escalated per the [self-repair classification ladder](self-repair.md)) rather than waiting for a human to schedule an audit. The audit that motivated this pattern was a one-time event; the generator makes it a standing computation.

---

## Model Policy as Declared Intent

Runtime model assignment often lives only in a scheduler UI — there is no API to set it, so no generator can *enforce* it. The pattern accepts this: the model policy file declares **intent**, and drift detection closes the loop.

Four intent tiers:

| Tier | Meaning | Run-weighting |
|------|---------|---------------|
| premium-locked | Must run on the premium model; degradation is a HIGH drift finding | Heaviest |
| standard-locked | Must run on the standard model; no silent downgrades | Heavy |
| standard-preferred | Standard model preferred; efficient model acceptable under budget pressure | Medium |
| efficient-ok | Any model acceptable; first to downgrade | Light |

Per-tier run-weighting feeds the [JIT budget manager](jit-budget-management.md): a premium-locked agent's run costs more of the weekly budget than an efficient-ok agent's, so throttling decisions account for model cost, not just run count. When the run DB shows an agent executing below its declared tier, that's model drift — the human is alerted to fix the scheduler UI, and the policy file never silently loses authority.

---

## The Deadman Liveness Check

The registry has a blind spot: it runs inside the fleet. If the scheduler dies, the self-repair agent dies with it, and the registry that would have reported the outage is never generated. The companion is a **deadman liveness check that runs outside the fleet** — a separate scheduling mechanism (system cron, an external monitor) so the monitor doesn't die with the monitored.

Mechanics:

1. Derive a max-silence window per agent from its declared cron: daily → 30h, every-6h → 9h, weekly → 8 days — roughly one missed run plus a 6h grace period.
2. Check the freshest evidence of life across *both* the run DB and the state index (whichever is newer counts — an agent that updated state but failed to log a run is alive).
3. If the freshest evidence is older than the window, alert the operator's DM directly — not a fleet channel, which may itself be unmonitored if the fleet is down.

One necessary escape hatch: an explicit **exempt list** for agents whose work product legitimately never writes run records (e.g., an agent whose only output is a git commit or an external side effect). Exemption is declared, reviewed, and short — an exempt list that grows is instrumentation drift wearing a disguise.

---

## Rules

**Never hand-edit generated outputs.** Editing `SYSTEM-INDEX.md` or `fleet-registry.json` is pointless — the next cycle overwrites it. If the registry is wrong, a *source* is wrong: fix the manifest, the policy file, or the agent directory, and let regeneration propagate it.

**Prose docs point, they don't assert.** Any document tempted to say "the fleet has N agents" links to the generated index instead. Counts, schedules, and model assignments appear in exactly one human-readable place, and that place is regenerated.

**One source per fact.** When two sources claim the same fact, the join can't tell which one drifted. New facts get a single owning source before they appear in the registry.

---

## Failure Modes

| Failure | Mitigation |
|---------|------------|
| Generator itself breaks or stops running | The deadman check is out-of-band and treats the registry like any agent — a stale registry is itself a silence alert |
| Scheduler snapshot is stale (watchdog missed a cycle) | Snapshot timestamp is part of the registry; drift findings against a stale snapshot are downgraded until a fresh capture |
| Operator "fixes" drift by editing the generated index | Overwritten next cycle; the rule is fix-the-source, and the regenerating index makes hand-edits visibly futile |
| Exempt list absorbs genuinely broken agents | Exemptions are reviewed entries with a stated reason, not a dumping ground; growth in the list is flagged as a finding |

---

## Why This Pattern Works

**Documentation can't drift if it's computed.** The registry is exactly as current as its last generation — minutes to hours old, not months.

**Drift becomes a finding, not an audit.** The spec-vs-runtime gap that once required a deliberate fleet-wide audit is now recomputed every few hours and lands in the same triage flow as every other repair finding.

**Declared truth survives runtime loss.** Because the manifest and policy file are sources (in git) and the scheduler is merely a snapshot, a scheduler wipe is a recoverable, loudly-detected event instead of silent fleet death.

**The fleet and the humans read the same inventory.** Self-repair, the watchdog, evals, and the operator all consume one generated artifact, so there is no version of the fleet's shape that exists only in someone's head.

---

## Related Patterns

- [Self-Repair](self-repair.md) — hosts the generator; consumes drift findings through its classification ladder
- [JIT Budget Management](jit-budget-management.md) — consumes per-tier run-weighting from the model policy
- [Fleet Evolution](fleet-evolution.md) — reads the registry to scope upgrade candidates
- [State Management](state-management.md) — the state index joined for freshness evidence
