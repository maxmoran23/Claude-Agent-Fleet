# Pattern: Evaluation Harness

A measured-quality harness, independent of the agent, that scores published outputs against per-agent structural rubrics — catching format drift, placeholder leaks, and shrinkage that self-rating structurally cannot see.

---

## The Problem

Fleet agents already self-rate output quality 1–10 (see [Quality Self-Rating](quality-self-rating.md)). That signal is valuable, but it measures **process health as perceived by the agent itself**: "my primary sources were up, I completed all analysis steps, I didn't fall back." It is the agent's view of its run.

Self-rating structurally cannot detect:

- **Format drift** — the output's structure slowly diverging from the standard (a section renamed, a table dropped, the health footer reformatted) while every run still "completes all steps"
- **Missing sections** — an agent that stops producing its trend block scores its sources as healthy and rates itself 8/10
- **Placeholder leaks** — `{TICKER}` or `[INSERT ANALYSIS]` surviving into production output; the run completed, the template just didn't fill
- **Gradual shrinkage** — outputs quietly thinning from 1,200 characters to 400 over a month of "successful" runs

And after an upgrade — a prompt change, a new output section, a promotion through the maturity framework — you need **before/after evidence, not vibes**. "The output seems better" is not an experiment verdict.

The agent grading its own artifact has the same trust problem as the agent rating its own run, except worse: the artifact is the thing that was supposed to be checked.

---

## The Pattern

A harness, fully external to the agent, runs **per-agent rubrics of weighted structural checks** against the agent's latest published output. Nothing about the run is consulted — only the artifact.

```
score = 100 × (weight of passed checks) / (total weight)
```

Each evaluation writes one row to an `eval_scores` table:

```sql
CREATE TABLE IF NOT EXISTS eval_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name      TEXT NOT NULL,
    score           INTEGER NOT NULL,        -- 0–100
    checks_passed   INTEGER NOT NULL,
    checks_total    INTEGER NOT NULL,
    failed_checks   TEXT,                    -- comma-separated check names
    source          TEXT,                    -- where the evaluated output came from
    eval_timestamp  TEXT NOT NULL            -- ISO 8601 UTC
);
```

The rubric lives in a JSON file per agent, versioned alongside the agent's configuration. The harness is a single runner script; the rubric is the only per-agent artifact.

---

## Check Types

Five check types cover the structural failure modes worth catching:

| Type | Semantics | Typical use |
|------|-----------|-------------|
| `regex` | Pattern must match | Required section headers, health footer present, severity tags present |
| `regex_absent` | Pattern must NOT match | Leftover `\{[A-Z_]+\}` placeholder braces, `TODO`, `INSERT`, lorem text |
| `min_length` | Output ≥ N characters | Shrinkage floor |
| `max_length` | Output ≤ N characters | Runaway/duplicated output ceiling |
| `min_count` | Pattern must match ≥ N times | "At least 3 `$`-figures in a market brief", "at least 2 findings" |

All five are deterministic string operations. No model call, no judgment, no variance between runs on the same input.

---

## Example Rubrics

A market agent's rubric — the checks assert the *shape* of a good brief, not its conclusions:

```json
{
  "agent": "market-monitor",
  "version": 3,
  "checks": [
    { "name": "heat_index_present",   "type": "regex",        "pattern": "Heat Index: [0-9]+/100",                  "weight": 3 },
    { "name": "sentiment_named",      "type": "regex",        "pattern": "Sentiment: (RISK-ON|RISK-OFF|NEUTRAL)",   "weight": 3 },
    { "name": "live_numbers",         "type": "min_count",    "pattern": "\\$[0-9][0-9,.]+", "min": 3,              "weight": 3 },
    { "name": "health_footer",        "type": "regex",        "pattern": "Quality: [0-9]+/10",                      "weight": 2 },
    { "name": "no_placeholders",      "type": "regex_absent", "pattern": "\\{[A-Z_]+\\}",                           "weight": 3 },
    { "name": "substantive_length",   "type": "min_length",   "min": 700,                                           "weight": 2 }
  ]
}
```

A regulatory agent's rubric, same machinery, different shape:

```json
{
  "agent": "regulatory-oracle",
  "version": 1,
  "checks": [
    { "name": "severity_tags",        "type": "min_count",    "pattern": "(CRITICAL|HIGH|MEDIUM|LOW)", "min": 2,    "weight": 3 },
    { "name": "deadline_section",     "type": "regex",        "pattern": "## Upcoming Deadlines",                   "weight": 2 },
    { "name": "citation_present",     "type": "min_count",    "pattern": "\\[Source:",                "min": 1,    "weight": 3 },
    { "name": "no_template_residue",  "type": "regex_absent", "pattern": "\\[INSERT|TBD|XXX",                       "weight": 3 },
    { "name": "not_truncated",        "type": "min_length",   "min": 500,                                           "weight": 2 }
  ]
}
```

If `market-monitor` ships a brief with no dollar figures and a leftover `{HEAT_INDEX}`, it scores 50 — regardless of how the run felt from the inside.

---

## The Runner

```
cat latest_post.txt | eval_runner.py --agent market-monitor --write
```

- Reads the artifact from stdin (channel post, canvas section, report body — whatever the agent publishes)
- Loads `rubrics/market-monitor.json`, applies every check, computes the weighted score
- `--write` appends the row to `eval_scores`; without it, prints the scorecard and exits (dry-run for rubric authoring)
- Exit code reflects evaluation completion, not the score — a 40/100 is a successful evaluation of a bad artifact

The harness runs wherever output already flows: as a post-publish step in the agent's wrapper, or as a sweep by the auto-repair agent over each agent's latest published output.

---

## Failure Modes

The harness fails **loud**, never soft. A silent zero would poison trend data; a silent skip would let an unevaluated agent look unmonitored-but-fine.

| Condition | Behavior |
|-----------|----------|
| No rubric file for `--agent` | Fatal, non-zero exit, message names the expected path and a minimal starter rubric. Never a silent 0, never a skip. |
| Empty stdin | Fatal — "no artifact" is a pipeline bug upstream, not a 0-score output |
| Malformed rubric JSON | Fatal with the parse location — a broken rubric must not half-apply |
| Invalid regex in a check | Fatal naming the check — same reasoning |
| Artifact present, all checks fail | Valid result: score 0, written normally. This is the harness working. |

The distinction in the last row matters: a score of 0 is *evidence*; a fabricated 0 from a missing rubric is *noise wearing evidence's clothes*.

---

## Self-Rating vs Measured Quality

The two signals are complements, never substitutes:

| | Quality self-rating | Evaluation harness |
|---|---|---|
| Vantage point | Inside the run | Outside, artifact-only |
| Measures | Process health (sources, fallbacks, completion) | Structural health of the published output |
| Scale | 1–10, rubric in AGENT.md | 0–100, weighted JSON rubric |
| Catches | Source outages, degraded coverage | Format drift, missing sections, placeholder leaks, shrinkage |
| Blind to | What the artifact actually looks like | Whether the run struggled to produce it |

The disagreement cases are the interesting ones. Self-rating 9/10 with eval 55/100 means the agent thinks it ran well but its output drifted — a template or prompt regression. Self-rating 3/10 with eval 95/100 means the fallback chain worked: degraded inputs, intact output. Both quadrants are invisible to either signal alone.

---

## Not LLM-as-Judge

This is deliberately **not** semantic evaluation. Structural rubrics are:

- **Cheap** — string operations, zero token cost, runs in milliseconds
- **Deterministic** — the same artifact scores identically every time; trend deltas are real deltas, not judge variance
- **Audit-defensible** — every score decomposes into named checks with explicit weights; "why 67?" has a mechanical answer

An LLM judge can assess what regexes cannot — coherence, insight, correctness — but it reintroduces cost, variance, and a second model whose own quality needs monitoring. The right layering: structural rubrics as the always-on floor, semantic judging added later for the agents whose stakes justify it. Don't start with the expensive, noisy layer.

---

## Consequences

**Drift detection.** Rubric scores trend over time per agent. A 95 → 90 → 80 slide across three weeks is a regression signal no single run reveals, and it triggers the watchdog the same way a self-rating slide does — but for artifact shape rather than source health.

**Experiment verdicts.** The harness gives the [Fleet Evolution](fleet-evolution.md) engine its evidence: compare the `eval_scores` window before an upgrade against the window after, and the verdict — IMPROVED / NEUTRAL / REGRESSED — is computed from measured scores rather than asserted from impressions. A promotion that drops measured quality gets rolled back on data.

**Rubrics as contracts.** Writing the rubric forces an explicit answer to "what must this agent's output always contain?" — which doubles as the output-format specification new prompt revisions are tested against.

---

## Related Patterns

- [Quality Self-Rating](quality-self-rating.md) — the inside-the-run signal this pattern complements
- [Fleet Evolution](fleet-evolution.md) — consumes eval windows for upgrade verdicts
- [Self-Repair](self-repair.md) — score-drift escalation path
- [State Management](state-management.md) — the data layer hosting `eval_scores`

---

**Reference implementation:** [`fleet_core/kernel/eval_runner.py`](../../fleet_core/kernel/eval_runner.py) — stdlib-only `score_output` with weighted predicate checks and example rubrics shipped as data.
