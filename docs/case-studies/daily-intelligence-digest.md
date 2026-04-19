# Case Study: Daily Intelligence Digest

End-to-end walkthrough showing how outputs from six different agents consolidate into a single actionable morning brief under 600 words.

> This case study uses fabricated events and data for illustration.

---

## Scenario

A busy operator starts the workday at 7:00 AM and has 10–15 minutes to absorb everything relevant that happened overnight across markets, regulation, on-chain activity, calendar, and fleet health. Reading six individual agent outputs in full would take 45+ minutes. A consolidated daily brief delivers the same information density in 5 minutes.

---

## The Upstream Agents

Six agents have produced output overnight or early morning:

### 1. Market Monitor (ran at 6:30 AM)
Detected: BTC moved +4.2% overnight on positive regulatory news; ETH lagging; sector rotation into layer-1 alternatives. Severity: MEDIUM. Quality: 8/10.

### 2. Regulatory Oracle (ran at 6:00 AM)
Detected: New SEC guidance on token classification published Friday afternoon (US time) during off-hours; Senate committee markup scheduled Tuesday. Severity: HIGH. Quality: 9/10.

### 3. On-Chain Watchlist (ran at 6:15 AM)
Detected: Routine activity across all 18 monitored addresses; one notable inflow on a CEX-custody address. No sanctions hits. Severity: MEDIUM (single notable event). Quality: 8/10.

### 4. Alpha Lab (ran at 4:00 AM)
Detected: Major DeFi protocol announced governance proposal for fee structure change; TVL shifted -3% in response; no exploit activity fleet-wide. Severity: MEDIUM. Quality: 8/10.

### 5. Calendar Alerts (ran at 6:30 AM)
Detected: Two regulatory deadlines within 7 days; one stakeholder meeting today; two congressional hearings this week. Severity: HIGH (one deadline in 3 days). Quality: 9/10.

### 6. Synthesis Engine (ran 9 PM previous day)
Detected (from yesterday's synthesis): Cross-cutting theme between regulatory guidance, market positioning, and protocol governance — the sector is repositioning ahead of anticipated regulatory clarity. Quality: 8/10.

---

## The Daily Brief Agent's Work

At 7:00 AM, the Daily Intelligence Brief agent runs.

### Step 0: Load State
Reads its own state (last brief date, running themes), plus reads state stores of all six upstream agents.

### Step 1: Gather
For each upstream agent:
- Reads its latest state
- Scans recent channel posts (overnight and early morning)

### Step 2: Prioritize and Thread
Identifies the top signal: the SEC guidance + Senate markup + market positioning together suggest a convergent regulatory moment. This is the thread.

Related items:
- Market repositioning is consistent with the guidance + markup context
- Protocol governance proposal timing is consistent
- Today's stakeholder meeting is directly relevant to how firms are responding

Today's time-critical:
- Stakeholder meeting at 10:30 AM (from meeting-prep cross-reference)
- Regulatory deadline in 3 days (from calendar-alerts)

Nothing CRITICAL this morning. Everything is HIGH or MEDIUM — a classic "major signal but no fire" morning.

### Step 3: Quality Self-Assessment
All six upstream agents active. Strong theme identification. Cross-agent threads clean. Quality: 9/10.

### Step 4: Format Output

The brief is delivered:

---

## The Daily Brief Output

```markdown
# Daily Brief — [DATE]

## Top Signal
Sector is repositioning ahead of a convergent regulatory moment. SEC guidance published
Friday on token classification + Senate committee markup scheduled Tuesday. Markets, DeFi
governance, and peer-firm activity are all consistent with front-running the clarity.
Expect elevated volatility around Tuesday's markup. Today's stakeholder meeting at 10:30
is directly relevant — see Meeting Prep for context.

## Critical
Nothing critical overnight.

## Today's Time-Critical
- 10:30 AM — Stakeholder meeting — see Meeting Prep for full context
- [+3 days] — Regulatory filing deadline — EXAMPLE-MATTER-037 — action: response due

## Threads in Motion

### Regulatory Clarity Window
SEC guidance on token classification (Friday PM, US) + Senate Banking Committee markup
(Tuesday) form a 4-day window of high regulatory signal. Markets are already repositioning
— BTC +4.2% overnight, sector rotation into layer-1 alternatives. Peer firms are
announcing stated positions ahead of the markup; expect more announcements through Monday.

### DeFi Governance Repricing
Major protocol governance proposal on fee structure announced overnight. TVL shifted -3%
in response. The pattern is visible in peer-protocol flows: capital is testing positions
rather than committing ahead of regulatory clarity. Watch Alpha Lab for follow-up as
protocols respond to the governance cascade.

## Markets
BTC +4.2% overnight on positive regulatory news; ETH lagging; sector rotation into
layer-1 alternatives. Market cap +2.1%. Volatility regime: active, not critical.
Full detail in #market.

## Regulatory
New SEC guidance on token classification (published Friday PM); Senate committee markup
Tuesday. Oracle flagged as HIGH — not CRITICAL — but it's the driver of this morning's
top signal. Full detail in #regulatory.

## On-Chain
18/18 watchlist addresses checked, routine activity. One notable inflow on a CEX-custody
address; no sanctions exposure. Full detail in #blockchain-analytics.

## Watchlist (no action yet)
- How Senate markup language compares to SEC guidance text (expect alignment or divergence)
- Protocol governance proposal voting window (opens Thursday)
- Whether CEX inflow pattern develops into sustained positioning

---
Health: Upstream sources: 6/6 active | Fallbacks: 0 | Quality: 9/10
```

---

## What the Operator Actually Does

The operator reads the brief in ~4 minutes. Takes away:

1. **One big thing:** Regulatory clarity window. Don't miss the Senate markup Tuesday.
2. **One today thing:** Prep for the 10:30 meeting (click to Meeting Prep brief for attendee and agenda detail).
3. **One 3-day thing:** Regulatory filing deadline — already on calendar, just a reminder.
4. **One watchlist thing:** Keep an eye on DeFi governance cascade.

The operator does NOT need to:
- Read the full Market Monitor post (mentioned inline, linked to channel)
- Read the full Regulatory Oracle post (mentioned inline, linked to channel)
- Read the On-Chain Watchlist (routine — flagged as quiet)
- Read the Synthesis Engine's yesterday-evening output (already folded into Top Signal)

Elapsed time from opening the brief to fully caught up: ~4 minutes.

Estimated time without the brief: ~45 minutes reading six individual posts in full.

---

## Where the Leverage Comes From

The Daily Intelligence Brief is the most-read agent in the fleet because it does three things other agents cannot:

**Synthesis across agents.** Each upstream agent sees its own domain. The brief is the only place where regulatory + market + on-chain + governance + calendar signals are threaded into a single narrative. Synthesis is the value.

**Density calibration.** The brief is ~500 words. The same content across six posts is ~4,000 words. Same information, 8x compression via prioritization and threading.

**Omission as a feature.** The brief skips what doesn't matter. "18/18 addresses routine, nothing to flag" is two lines. Without the brief, those two lines would be a full 400-word on-chain watchlist post the operator skims to confirm nothing happened.

**Anchored to today.** The brief's structure (Top Signal → Critical → Today's Time-Critical → Threads → Domains → Watchlist) maps directly to operator question hierarchy: what's most important, what's urgent, what's routine.

---

## Failure Modes Prevented

**Without the brief agent's existence:**

The operator would either read six posts (slow) or skim them quickly and miss the cross-cutting theme. The cross-cutting theme is the whole point — none of the individual agents see it. If the brief agent is down, the fleet loses its ability to produce synthesis at the morning-brief cadence, even though every upstream agent still produces its individual output.

**Fallback scenarios:**

- If Synthesis Engine didn't run overnight: the brief works from raw upstream state, loses the pre-threaded themes
- If one upstream agent didn't run: the brief explicitly notes "upstream agent X unavailable" in the health footer, the operator knows that domain is thin this morning
- If all upstream agents are degraded: the brief produces a reduced-quality version with a high fallback count, honest framing, and a lower quality self-rating

At no point does the brief silently skip a domain or fabricate synthesis. Degradation is visible.

---

## What This Demonstrates

**The capstone pattern.** The brief agent sits above everything else. It has no independent gathering capability. Its entire value is consolidation and synthesis. Without upstream agents, it has nothing to do. With them, it is the highest-leverage output the operator consumes each day.

**Information density over information volume.** More agents doesn't mean more reading. More agents + a good synthesis layer means less reading and better comprehension.

**Cross-domain thread discovery.** The "regulatory clarity window" theme is invisible to any individual agent. It's only visible when multiple agents' outputs are laid against each other. The brief's value IS this kind of pattern detection.

**Operator time as the scarce resource.** The fleet's budget manager is about token cost. The brief agent is about operator cost — arguably the scarcer of the two. A fleet that burns tokens to save operator time is a good trade.

---

## Related Patterns

- [State Management](../patterns/state-management.md) — how the brief reads across all upstream state stores
- [Quality Self-Rating](../patterns/quality-self-rating.md) — how degraded upstream quality surfaces in the brief
- [Fallback Chains](../patterns/fallback-chains.md) — how the brief handles missing upstream sources
