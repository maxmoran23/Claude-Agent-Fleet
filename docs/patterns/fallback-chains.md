# Pattern: Fallback Chains

Graceful source degradation so no agent hard-fails on a missing input.

---

## The Problem

Every agent depends on external data — web search, MCP servers, APIs, file reads, other agents' state stores. Any of these can fail:

- MCP server down
- Network hiccup
- Rate limit hit
- Upstream state store missing
- API returning empty
- Source-specific query returning nothing

Naive behavior: agent throws, run fails silently, no output, no record, downstream consumers have nothing to work with. In a scheduled fleet, a hard-failed run is worse than a degraded run — the fleet thinks nothing happened when in fact something broke.

---

## The Pattern

Every data-gathering step defines an ordered fallback chain. The agent tries primary first, falls back to secondary on failure, then tertiary, and always produces *some* output.

Each fallback level comes with an honest framing: the output includes a health-footer field indicating which tier was used.

---

## Canonical Fallback Chain

```
Primary:    Best data source available (dedicated MCP, real-time API)
Secondary:  Alternative source (web search, secondary API, cached data)
Tertiary:   State-only output (report what was last known, with freshness caveat)
```

Only step outside the chain with an explicit escalation — never fail silently.

---

## Concrete Examples

### Market pulse agent

```
Primary:    Dedicated crypto price MCP + sentiment MCP (real-time)
Secondary:  Web search for prices + news-tone-inferred sentiment
Tertiary:   Prior-snapshot state-only report with "DATA STALE" flag
```

If Primary works: `Quality: 9/10, Sources: Crypto.com MCP, LunarCrush MCP`
If Secondary: `Quality: 6/10, Sources: Web search, Fallback: MCP unavailable`
If Tertiary: `Quality: 2/10, Sources: State store, WARNING: prices as of [timestamp]`

### Regulatory oracle agent

```
Primary:    Agency websites + legal publications + news search
Secondary:  News search only (agency sites unreachable)
Tertiary:   State-only — report status of tracked matters, note all-quiet
```

### On-chain watchlist agent

```
Primary:    Dedicated chain-explorer MCP (Blockscout, Etherscan)
Secondary:  Alternative chain explorer via web search
Tertiary:   State-only with freshness caveat, no new event detection
```

---

## Implementation Rules

**Rule 1: Every data-gathering step has a documented fallback chain.**

If the agent's AGENT.md doesn't include a Fallback Chain section under the relevant step, it is not compliant with the pattern. The auto-repair agent flags missing fallback chain sections as ESCALATE findings.

**Rule 2: The fallback tier used is recorded in the health footer.**

Every output ends with:

```
Health: Sources: [list] | Fallbacks: [count] | Quality: [score]/10
```

Fallback count > 0 is a signal for the watchdog agent to monitor — chronic fallback use on primary sources indicates a degraded or dead source.

**Rule 3: Tertiary fallback always produces output.**

Even when everything is broken, the agent produces a minimal output saying so. The fleet must be able to distinguish "agent ran but everything was broken" from "agent didn't run at all" — only the former is visible in channels and state stores.

**Rule 4: Fallback use reduces quality score.**

Quality self-assessment explicitly penalizes fallback tier usage:

| Tier Used | Quality Score Range |
|-----------|--------------------|
| Primary   | 7–10 |
| Secondary | 5–7 |
| Tertiary  | 1–3 |

This makes quality score a useful proxy for source health over time.

**Rule 5: Chronic fallback use escalates to repair.**

If the watchdog agent observes an agent hitting Secondary or Tertiary on N consecutive runs, it escalates to the fleet operations channel. Either:
- The primary source is dead and needs fixing
- Something in the agent's configuration has drifted
- The agent's primary source choice was wrong from the start

---

## Why Fallback Beats Fail-Fast

In production software, fail-fast is often correct — let errors propagate so you catch them. In a scheduled autonomous fleet, fail-fast is usually wrong, because:

1. The operator is not watching logs in real time
2. A failed agent produces nothing — no signal that anything is wrong
3. Downstream agents (daily brief, synthesis engine) have nothing to consume
4. The fleet appears healthy while being silently broken

Fallback chains trade perfection for observability. A Tertiary-fallback output is a loud signal — it appears in channels labeled as degraded, the quality score drops, the watchdog catches the trend. The operator sees the problem. Fail-fast would have masked it.

---

## When NOT to Use This Pattern

Fallback chains do not apply to:

- **Destructive actions** — never fall back on a write. If a state persist fails, escalate loudly rather than writing something partial.
- **Compliance-critical output** — never fall back on a sanctions-list enrichment. If the sanctions source is down, the finding cannot be emitted; escalate instead.
- **Trading / execution** — execution steps (which should always be human-approved anyway) never degrade; they wait for primary data or abort.

The fallback pattern is for *observability* and *intelligence output*. Anything with downstream external effects uses a different pattern: strict preconditions, explicit refusal, loud escalation.

---

## Related Patterns

- [Quality Self-Rating](quality-self-rating.md) — the scoring that captures fallback-tier usage
- [Self-Repair](self-repair.md) — how chronic fallback use gets diagnosed and addressed
- [State Management](state-management.md) — fallback chain for the state store itself (Load State never hard-fails)
