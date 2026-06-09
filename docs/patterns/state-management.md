# Pattern: State Authority and Projections

Persistent agent state with one local source of truth and multiple non-authoritative projections for display, history, and cross-agent context.

---

## The Problem

A scheduled agent runs, produces output, and exits. The next run has no memory of the previous one. Without persistent state:

- The agent can't report deltas ("BTC moved 3% since last pulse")
- The agent can't deduplicate findings ("we already flagged this enforcement action")
- The agent can't maintain tracked items across runs (watchlists, deadlines, open matters)
- The fleet as a whole has no institutional memory
- Historical queries are impossible ("what was X at Y point in time?")

There is a second-order problem that only shows up at fleet scale: state has multiple consumers with conflicting needs. The agent itself needs durable, machine-readable truth. The operator wants something glanceable. Other agents want cross-agent context. Trend analysis wants append-only history. One store cannot serve all four well — and whichever store you pick as truth, its failure modes become the fleet's failure modes.

---

## The Motivating Failure

An earlier generation of this fleet used platform-hosted canvases (structured markdown documents in the chat workspace) as the authoritative state store. It worked — until the busiest canvases hit the platform's write-saturation limit (~1M characters) and began rejecting appends.

Because canvases were authoritative, dozens of agents silently lost persistence. Runs completed, reports posted, health footers looked normal — but the Step 7 write was failing, so every subsequent run loaded stale state. Deltas went quiet, deduplication broke, and nothing in any single run looked wrong. The failure was only visible in aggregate, weeks in.

The fix was architectural, not a workaround: designate a local file as the authority and demote everything remote to a projection. Saturation can still happen — it now degrades a display, not the fleet's memory.

---

## The Pattern

One authority, three projections:

```
AUTHORITY    {agent}/state/state.json    local, durable, atomic writes, history/

PROJECTIONS  Slack canvases              display mirror + cross-agent context
                                         (writes non-fatal)
             SQLite data layer           append-only run history + domain tables
             archive database            findings archive (severity >= MEDIUM)
```

Three rules govern the split:

1. **The authority write must succeed.** If `state/state.json` cannot be written, the run fails loudly. There is no acceptable degraded mode for losing memory.
2. **Projection writes are best-effort.** A failed canvas, data-layer, or archive write is logged in the health footer and never aborts the run.
3. **Projections are never read back as truth.** Cross-agent canvas reads at Step 0 are advisory context, not state. An agent's own truth comes only from its own state file.

---

## The Authority Tier: Local State File

Per-agent layout:

```
{agent}/state/
  state.json      current authoritative state
  history/        timestamped snapshots, pruned after 30 days
```

Every state file is stamped with `agent`, `last_run` (ISO timestamp), and `kernel_version`, so any file found on disk self-identifies. Writes are atomic — temp file, then rename — so a crash mid-persist leaves the previous state intact rather than a truncated file.

### Writer and reader interfaces

Agents do not hand-roll file IO. The kernel helpers own both ends (see [agent-kernel.md](agent-kernel.md)):

- **`kernel/step0.py --agent {name}`** — run initialization. Loads `state/state.json` plus the agent's last 3 runs from the SQLite data layer in one JSON call. Returns an explicit status: `loaded`, `FIRST_RUN`, or `corrupt — treat as first_run, do not overwrite`.
- **`kernel/step7.py --agent {name} --state '{json}'`** — run persistence. Atomic write, metadata stamping, history snapshot, registry upsert, then the optional non-fatal canvas mirror.

### The state index

`step7.py` also upserts a fleet-wide `state-index.json` registry: which agents have state, when each last persisted, and how many keys each holds. The watchdog reads one file to answer "which agents have stopped persisting" — the question the canvas-saturation incident proved nobody was asking.

### Corruption handling

A JSON decode error at load time returns `corrupt — treat as first_run, do not overwrite`. The agent proceeds with empty state; the loader never repairs, truncates, or replaces the corrupt file in place, and `state/history/` retains the recent good snapshots. Recovery — diffing snapshots, restoring the last good one — is an operator decision, not something an agent improvises mid-run. The anti-pattern this prevents: a loader that swallows the error and lets the end-of-run persist blow away the only recoverable copy.

---

## The Projection Tiers

### Slack canvases — display mirror and cross-agent context

Demoted from truth, still earning their keep:

- **Human glanceability.** The operator reads an agent's current state in the workspace without tooling. No projection failure changes what the fleet knows; it only staleness-dates what the operator sees.
- **Cross-agent context.** At Step 0, agents read other agents' canvases for context ("what is the regulatory agent currently tracking?"). This stays cheap and platform-native — and because it is advisory, a saturated or stale canvas degrades context quality, not correctness.

Canvas structure conventions are unchanged — see [schemas/slack-canvas-structure.md](../../schemas/slack-canvas-structure.md). What changed is the contract: the mirror write in Step 7 is explicitly allowed to fail.

### SQLite data layer — append-only historical record

A shared SQLite database remains the permanent answer to "what was true at point X in time?":

- Append-only — nothing updated or deleted
- Structured tables with consistent schemas: a universal `agent_runs` row every run, plus domain tables (market snapshots, regulatory events, portfolio state, predictions)
- Written at Step 6.5 (after delivery, before persist)
- Queryable for aggregation and trend analysis; migration-compatible with hosted Postgres when scale demands

```bash
# Universal agent_runs row on every run
sqlite3 {FLEET_ROOT}/_data-layer/fleet.db <<SQL
INSERT INTO agent_runs (
  agent_name, run_timestamp, quality_score,
  sources_used, fallbacks_triggered, findings_count
) VALUES (
  'regulatory-oracle', '$ISO_TIMESTAMP', $QUALITY,
  '$SOURCES', $FALLBACKS, $FINDINGS_COUNT
);
SQL
```

See [schemas/data-layer.sql](../../schemas/data-layer.sql) for the full table set. Note that `step0.py` reads this layer too — the agent's last 3 runs ride along with the state load, so trend-aware analysis costs no extra query.

### Archive database — findings archive

Findings rated MEDIUM or above are written to a shared archive database with structured metadata (title, agent, severity, category). It serves historical cross-referencing and inter-agent lookup — a data bus, not a notification channel, and never a state store.

---

## Why the Split

Each question has exactly one authoritative answer location:

| Question | Answered by |
|----------|-------------|
| "What does this agent currently know?" | Authority — `state/state.json` |
| "Is this finding a duplicate of last week's?" | Authority — covered-items in state |
| "What was BTC doing at 3pm last Tuesday?" | Data layer — SQLite query |
| "What's the quality-score trend over 90 days?" | Data layer — SQLite query |
| "What is the market agent tracking right now?" (asked by another agent) | Canvas projection — advisory |
| "Has the fleet ever flagged this entity?" | Archive database |
| Operator glancing at fleet status | Canvas projection |

A fact with two authoritative homes will eventually disagree with itself, and you will not notice until something downstream breaks. The hierarchy exists to make "where does truth live" a question with one answer per fact.

---

## Failure Modes

| Failure | Effect | Recovery |
|---------|--------|----------|
| Canvas saturated or API down | Stale dashboard; degraded cross-agent context | None needed — mirror catches up next successful run |
| SQLite locked or unreachable | Gap in run history; flagged in health footer | Run proceeds; gap is visible in `agent_runs` |
| `state.json` corrupt | First-run semantics for that run | Operator restores from `state/history/` |
| Authority write fails | Run fails loudly | Correct behavior — never downgrade to projection-only persistence |

The last row is the lesson of the saturation incident inverted: tolerating a failed authority write because a projection succeeded is exactly how a fleet loses its memory without noticing.

---

## Consequences

**Positive:**
- State survives every remote-platform failure mode — saturation, rate limits, outages cost display freshness, never memory
- Persistence failures are loud and immediate instead of silent and cumulative
- The state index makes fleet-wide persistence health a single-read question
- History snapshots give a real recovery path for corruption and bad writes
- Historical queries remain fast and structured (SQLite, indexed)

**Negative:**
- Four write destinations per run (authority plus three projections — still negligible per-run overhead)
- Mirrors can lag truth; humans reading canvases may see stale data (mitigated by last-updated timestamps in every mirror)
- Authority is machine-local: a multi-host fleet needs a shared filesystem or a database-backed authority, at which point revisit this design

---

## Migration Note

A previous revision of this document described a two-tier model with canvases as the live source of truth and SQLite as history. That architecture is superseded: canvases are now projections, and the local state file is the authority. If your fleet still treats a remote display surface as truth, migrate before a platform limit finds you — the failure mode is silent, and it compounds.

---

## When to Use This Pattern

- **Use when:** Agents run on a machine you control, you want persistence that cannot be broken by a third-party platform, and you still want glanceable dashboards and historical queryability
- **Skip when:** A single agent in isolation — `state/state.json` alone (without projections) may be enough
- **Variant:** Fleets without a chat platform can project to markdown files under version control instead of canvases; the authority/projection split is the load-bearing idea, not the specific display surface

---

## Related Patterns

- [Agent Kernel](agent-kernel.md) — step0.py / step7.py, the only sanctioned interfaces to the authority tier
- [Fallback Chains](fallback-chains.md) — what an agent does when a projection or context read is unavailable
- [Self-Repair](self-repair.md) — how state-store drift gets caught and fixed
- [Quality Self-Rating](quality-self-rating.md) — the quality_score field persisted to state and the data layer
