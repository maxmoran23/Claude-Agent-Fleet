# Pattern: Agent Kernel

A versioned contract plus a small set of shared CLI helpers that replace per-agent boilerplate for the fleet's universal production patterns.

---

## The Problem

A production fleet converges on a handful of patterns that every agent must implement regardless of domain: state load, fallback chains, data-layer writes, health footers, quality self-rating, idempotency, state persistence. Seven patterns, every agent, every run.

The naive implementation copies each pattern as prose into every agent's prompt file. At 70+ agents this fails in two ways:

1. **Fan-out cost.** Improving a pattern means editing 70+ files. In practice the edit lands in the dozen agents someone remembered, and the rest keep the old version indefinitely.
2. **Drift.** Copies mutate independently. One agent's health footer gains a field, another's loses one. One agent self-rates 1–10, another 1–3, and the fleet-wide quality average silently becomes meaningless because the inputs are on different scales.

There is a third cost: prompt bloat. Hundreds of lines of mechanical instruction per agent that the model re-reads every run, none of it specific to the agent's actual job.

---

## The Pattern

Invert ownership. One canonical document — `KERNEL.md`, currently v2.0 — defines each pattern exactly once. Agents declare the contract version in their header and reference the kernel by path. The mechanical parts of each pattern stop being prose and become CLI helpers the agent calls.

```
BEFORE                                   AFTER
70+ AGENT.md files                       _data-layer/kernel/KERNEL.md    (contract, v2.0)
  each carries 7 patterns as prose         defines all 7 patterns once
  copies drift independently             _data-layer/kernel/*.py         (helpers)
  improvement = 70-file fan-out            step0  step7  health_footer
                                           outbox  recall
                                         70+ AGENT.md files
                                           declare: Kernel: v2.0
                                           call helpers, keep domain logic only
```

The agent header declaration:

```markdown
---
model: claude-opus-4-6[1m]
---
Kernel: v2.0 — universal patterns defined in `_data-layer/kernel/KERNEL.md`.
This file contains domain logic only.
```

Not every pattern gets a helper. Fallback chains and data-layer writes involve per-agent judgment, so they stay canonical-prose-in-KERNEL.md, referenced rather than copied. The patterns that are purely mechanical — load, persist, footer, dedup-guard, recall — become executables:

| Pattern | Defined in | Mechanics |
|---------|-----------|-----------|
| State load | KERNEL.md + helper | `step0.py` |
| State persistence | KERNEL.md + helper | `step7.py` |
| Health footer | KERNEL.md + helper | `health_footer.py` |
| Quality self-rating | KERNEL.md + helper | scale validated by `health_footer.py` |
| Idempotency | KERNEL.md + helper | `outbox.py` |
| Fallback chains | KERNEL.md (prose) | agent reasoning, see [fallback-chains.md](fallback-chains.md) |
| Data-layer writes | KERNEL.md (prose) | data-layer write helper + domain SQL |

---

## The Helpers

### step0.py — run initialization

```bash
python3 _data-layer/kernel/step0.py --agent market-monitor
```

Loads the agent's local `state/state.json` plus its last 3 runs from the SQLite data layer, returned as one JSON document. One call replaces what used to be three separate prose instructions (read file, handle missing file, query history).

The status field is explicit, not inferred:

| Status | Meaning | Agent behavior |
|--------|---------|----------------|
| `loaded` | State parsed cleanly | Proceed with prior state |
| `FIRST_RUN` | No state file exists | Proceed with empty state, do not fail |
| `corrupt — treat as first_run, do not overwrite` | File exists but failed to decode | Proceed with empty state; the corrupt file is preserved for manual recovery |

The third label matters. A loader that silently swallows a decode error and returns empty state invites the next persist to blow away the only copy of possibly-recoverable data. The kernel makes corruption loud and non-destructive.

### step7.py — run persistence

```bash
python3 _data-layer/kernel/step7.py --agent market-monitor --state '{"watchlist": [...], "covered_items": [...]}'
```

In order:

1. **Atomic write** — writes to a temp file, then renames over `state/state.json`. A crash mid-write leaves the previous state intact, never a half-written file.
2. **Stamping** — injects `agent`, `last_run` (ISO timestamp), and `kernel_version` into the payload. Every state file self-identifies.
3. **History snapshot** — copies the new state to `state/history/`, pruning snapshots older than 30 days. This is the recovery path when corruption or a bad write needs manual rollback.
4. **Registry upsert** — updates a fleet-wide `state-index.json`: which agents have state, how fresh it is, how many keys. The watchdog answers "which agents haven't persisted in 48 hours" with one read.
5. **Canvas mirror (optional, non-fatal)** — pushes a compact snapshot to the agent's display canvas. If this fails, the run still succeeds. Authority is the local file; the mirror is decoration. See [state-management.md](state-management.md).

### health_footer.py — standardized footer

```bash
python3 _data-layer/kernel/health_footer.py \
  --sources "exchange-api:OK,chain-explorer:FALLBACK" --quality 4 --runtime 38
```

Renders the one-line health footer every agent appends to its output. The interesting part is what it rejects: any quality score outside the fleet's declared scale (1–10 in this framework's reference implementation) fails loudly with a non-zero exit and an error naming the valid range.

This is deliberate choke-point enforcement. In the prose era, agents drifted onto mismatched scales, and those scores flowed into the data layer unlabeled — a 7 on a 0–10 scale averaged against a 4 on a 1–5 scale produces a fleet-wide quality number that means nothing, and nothing flags it. The kernel standardizes the fleet on one scale (the rubric pattern itself is unchanged — see [quality-self-rating.md](quality-self-rating.md)) and makes the footer renderer the single point where the scale is checked. An agent that drifts now gets an error at run time instead of corrupting averages for weeks.

### outbox.py — idempotency guard

Guards non-idempotent external actions (sends, posts, calendar writes) by recording intent before the attempt and confirming after. An agent that crashes between send and confirm does not re-send on retry. The full pattern, including the incident that motivated it, is documented in [idempotency-outbox.md](idempotency-outbox.md).

### recall.py — fleet-wide recall

```bash
python3 _data-layer/kernel/recall.py "canvas saturation incident"
```

Full-text search over the corpus agents actually cite when reasoning about the fleet: kernel docs, agent context files, local state files, fleet metadata, and operator memory notes. Implementation:

- SQLite FTS5 virtual table, porter/unicode61 tokenizer, BM25 ranking
- **Incremental reindex on every search** — changed files are re-ingested before the query runs, so results are never stale and there is no separate indexing job to forget
- Query terms are escaped individually, so hyphens and punctuation in a query cannot break the MATCH expression
- Returns path, source category, and a 300-character snippet per hit

Why this lives in the kernel: "has the fleet seen this before?" is a question every agent eventually asks. Without a shared answer path, each agent improvises with ad-hoc grep over directories it half-remembers. One indexed corpus, one CLI, one ranking function.

---

## Adoption Is Lazy, Migration Is Observable

There is no big-bang conversion. Agents adopt the kernel when next touched — through a gated evolution proposal (see [fleet-evolution.md](fleet-evolution.md)) or an operator edit. A mixed fleet is the expected steady state during migration.

What makes this safe is that progress is measured, not assumed: the generated fleet registry tracks a `kernel_v2` adoption count alongside each agent's declared version. "How far along is the migration" is a number in a report, and "which agents still carry the old prose" is a query.

---

## Failure Modes

**Helper unavailable.** Interpreter broken, path moved, kernel directory missing. The contract survives the helper: KERNEL.md still defines each pattern in prose, and an agent can execute the pattern manually for a run. A step0 failure specifically degrades to empty-state-and-proceed, per the fleet's no-hard-fail rule.

**Version skew.** An agent declares `Kernel: v2.0` after the kernel moves on. Mitigations: breaking changes require a major version bump with a changelog entry in KERNEL.md, the registry exposes which agents lag, and the auto-repair agent flags declarations against retired versions ([self-repair.md](self-repair.md)).

**Silent helper edits.** Changing helper behavior without bumping the contract version reintroduces drift one level up — every agent's behavior changes and no declaration reflects it. Rule: behavior change means version bump.

**Mirror masking authority failure.** The canvas mirror in step7 is allowed to fail; the local write is not. Inverting that — tolerating a failed authority write because the mirror succeeded — recreates the exact silent-persistence-loss incident the state-authority architecture exists to prevent.

---

## Consequences

**Positive:**
- Pattern improvements are one-file edits that reach every converted agent immediately
- Versioning the contract makes "which pattern version does this agent implement" a queryable fact instead of archaeology — grep the headers, read the registry count
- Prompt files shrink to domain logic; less mechanical text for the model to re-read, fewer places for instruction drift
- Choke-point validation kills whole classes of silent corruption (the quality-scale case is the proof)

**Negative:**
- The kernel is a shared failure point — a bug in step7 affects every converted agent at once (mitigated by the prose fallback and by testing helpers like any other production code)
- Each helper call is a process spawn per step (negligible at agent timescales)
- The contract demands real version discipline; a versioned document nobody bumps is worse than no version at all

---

## When to Use This Pattern

- **Use when:** 10+ agents share mechanical patterns and you have felt the fan-out cost at least once
- **Skip when:** Fewer than ~5 agents — copy-paste is still cheap; introduce the kernel at the first painful multi-file edit, not before
- **Variant:** The helpers can be a library instead of CLIs if agents share a runtime; CLIs were chosen here because prompt-driven agents invoke shell commands more reliably than they import modules

---

## Related Patterns

- [State Management](state-management.md) — the authority/projection architecture that step0.py and step7.py implement
- [Idempotency Outbox](idempotency-outbox.md) — the guard behind outbox.py
- [Quality Self-Rating](quality-self-rating.md) — the rubric whose scale the kernel enforces
- [Self-Repair](self-repair.md) — validates kernel declarations and flags version lag
- [Fleet Evolution](fleet-evolution.md) — the gated path by which agents adopt the kernel

---

**Reference implementation:** [`fleet_core/kernel/`](../../fleet_core/kernel/) — runnable, stdlib-only library variants of the kernel helpers (state, outbox, evaluation), exercised by `tests/test_kernel.py`.
