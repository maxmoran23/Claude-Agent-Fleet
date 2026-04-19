# Case Study: On-Chain Sanctions Hit

End-to-end walkthrough showing how a sanctions-exposure event on a monitored address gets detected, enriched, and escalated with full context in minutes.

> This case study uses fabricated addresses, entity names, and event details for illustration. No real sanctions action or address is referenced.

---

## Scenario

A configured address in the on-chain watchlist sends funds to a counterparty that appears on a sanctions list. The fleet needs to:

1. Detect the transfer quickly
2. Enrich with counterparty context
3. Classify severity
4. Escalate to operator via multiple channels
5. Trigger an incident-response package for potential filing action

Total elapsed time from on-chain event to operator notification: under 10 minutes.

---

## Timeline

### T+00:00 — On-chain event

Address `0xABC...4001` (in the watchlist, labeled `monitored-entity-04`, risk category HIGH) executes a transfer of 250,000 USDT to counterparty address `0xDEF...9999`. The event is confirmed on-chain.

### T+00:00 to T+06:00 — Watchlist agent runs

On-Chain Watchlist agent's next scheduled run (every 4 hours for HIGH-risk addresses). Runs Step 0 through Step 2:

**Step 0:** Loads state, reads the prior `address_state` for `0xABC...4001`.

**Step 1:** Gathers activity via chain explorer. Sees the new transfer.

**Step 2:** Classifies:
- Transfer value: 250,000 USDT — above configured threshold
- Counterparty: `0xDEF...9999` — NEW counterparty, not seen in history
- Sanctions-list check: **HIT** — counterparty is on the configured sanctions list (example: OFAC SDN list reference `EXAMPLE-SDN-2026-042`)

Severity assignment: **CRITICAL** (sanctions-list touch + above-threshold value).

### T+06:00 to T+08:00 — Enrichment

Agent enriches the counterparty with available context:
- Sanctions-list entry metadata: name, jurisdiction, date added, program reference
- Counterparty's public on-chain history (how many transactions, total volume, other counterparties)
- Check against `flagged_counterparties` state — was this address seen in prior events?
- Check for any pass-through pattern — funds moved quickly in-then-out after receipt

---

## The Output

### Main channel post (to blockchain-analytics channel)

```markdown
# On-Chain Watchlist — [DATE] [TIME]
Addresses monitored: 18 | Events this run: 3 | Critical: 1

## Critical Events
### monitored-entity-04 (Ethereum)
Address: `0xABC...4001`
Event: Outgoing transfer to SANCTIONS-LIST counterparty
Counterparty: `0xDEF...9999` (Sanctions list: EXAMPLE-SDN-2026-042)
Value: 250,000 USDT
Timestamp: [ISO]
Typology flag: Direct sanctions exposure
Sanctions touch: YES — OFAC SDN list, added [DATE]

**Counterparty context:**
- First seen: [DATE] (public on-chain history)
- Total prior volume: ~4.2M USDT across 87 transactions
- Primary activity pattern: Fast in-then-out (median hold time < 2 hours)
- Other prior counterparties: Include 2 known mixing services and 1 address flagged
  on a separate sanctions designation

**Recommended assessment:**
- Material sanctions-exposure event
- Counterparty has pattern consistent with sanctions evasion typology (pass-through)
- Required review and potential regulatory filing assessment within 24 hours

---
Health: Chain data: Blockscout | Sanctions source: OFAC SDN | Fallbacks: 0 | Quality: 9/10
```

### Critical alerts channel post (the "red phone")

```markdown
:rotating_light: CRITICAL — On-Chain Sanctions Exposure

monitored-entity-04 sent 250,000 USDT to sanctions-listed address.
Full context in #blockchain-analytics.
```

### Operator DM

```markdown
Critical on-chain event: monitored-entity-04 → sanctions-listed counterparty, 250,000 USDT.
See #blockchain-analytics for full context. Execution scaffold package generating.
```

### T+08:00 to T+10:00 — Execution Scaffold triggers

The Execution Scaffold agent runs its periodic check. Sees the CRITICAL event from the On-Chain Watchlist state. Threshold matched:

```json
{
  "trigger_sources": ["onchain-watchlist"],
  "threshold_config": {
    "onchain-watchlist": {
      "trigger": "severity == CRITICAL AND sanctions_touch == true",
      "package_type": "Incident response package"
    }
  }
}
```

Generates the package.

---

## The Incident Response Package

```markdown
# DRAFT: Incident Response Package — On-Chain Sanctions Exposure
Generated: [DATE] [TIME]
Triggered by: On-Chain Watchlist — event ID onchain-critical-2026-04-19-001
Urgency: Initial review and internal escalation within 4 hours; regulatory filing
assessment within 24 hours.

## Context
A monitored address (watchlist category: HIGH) executed a transfer of 250,000 USDT to a
counterparty address identified on the OFAC SDN list. The counterparty's public on-chain
history exhibits a pattern consistent with sanctions-evasion typology (rapid pass-through,
prior counterparties include mixing services and another sanctioned address). This represents
a material sanctions-exposure event requiring documented internal review and likely
regulatory filing assessment.

## Draft Incident Report — Internal Distribution

### Subject: On-Chain Sanctions Exposure Event — Initial Incident Report

### Event Summary
On [DATE] at [TIME UTC], internal monitoring identified an outgoing transfer from
monitored-entity-04 (`0xABC...4001`) to a counterparty (`0xDEF...9999`) listed on
the OFAC SDN list (designation reference `EXAMPLE-SDN-2026-042`, added [DATE]).

Transfer details:
- Value: 250,000 USDT
- Chain: Ethereum
- Block: [block number]
- Transaction hash: [hash]
- Confirmed on-chain: [ISO timestamp]

### Counterparty Risk Profile
The counterparty address exhibits a pattern consistent with sanctions-evasion typology:
- On-chain history: 87 transactions since [DATE], total volume ~4.2M USDT
- Activity pattern: Rapid pass-through (median hold time < 2 hours)
- Prior counterparties include two known mixing-service addresses and one
  address designated under a separate sanctions program

### Initial Assessment Framework
Required evaluation (to be completed):
1. Was the transfer initiated in the normal course of business, or in response to
   any customer instruction that should have been flagged?
2. What sanctions-screening controls are in place at the point of transfer initiation,
   and did those controls operate as designed?
3. Was the counterparty designation in place at the time of transfer? (Timeline check)
4. Does this event warrant a suspicious activity report filing?
5. Does this event warrant a voluntary self-disclosure to OFAC?

### Preliminary Containment
- Address `0xABC...4001` flagged for enhanced monitoring
- Any subsequent outgoing transfers from this address require pre-approval pending
  initial assessment
- Counterparty address `0xDEF...9999` added to flagged_counterparties state for
  fleet-wide awareness

## Supporting Research

**The sanctions designation:**
- List: OFAC SDN
- Reference: EXAMPLE-SDN-2026-042
- Program: [relevant sanctions program]
- Added: [DATE]
- Reason: [designation reason per OFAC publication]

**Related OFAC guidance:**
- OFAC FAQs on virtual-currency sanctions compliance
- OFAC 2021 Sanctions Compliance Guidance for Virtual Currency Industry
- OFAC Framework for Compliance Commitments (May 2019)

**Relevant filing frameworks:**
- FinCEN suspicious activity reporting requirements for money service businesses
- OFAC voluntary self-disclosure framework
- Reporting window: 30 days from detection for SAR; voluntary self-disclosure
  favorable but no fixed window

**Precedent enforcement in this domain:**
- [DATE]: [ENTITY] — failure to screen against SDN list, $[amount] penalty
- [DATE]: [ENTITY] — pass-through to sanctioned address, $[amount] penalty

## Recommended Actions
1. Route this incident report to compliance leadership within 4 hours of this draft
2. Engage legal counsel to assess filing obligations and privilege considerations
3. Complete initial-assessment framework evaluation within 24 hours
4. Prepare SAR filing draft in parallel with legal assessment (retain regardless of
   final filing decision for audit trail)
5. Document screening-control operation at the point of the transfer (was the
   designation in place at transfer time?)
6. Preserve all transaction and screening logs

## Open Questions (operator decides)
- Is the 4-hour compliance-leadership escalation window appropriate, or does firm
  protocol call for immediate notification?
- Should legal counsel be engaged internal or external given the potential voluntary
  self-disclosure pathway?
- Are there upstream customer-facing disclosures required pending the assessment?
- Does the pattern of prior counterparties (mixing services + separate sanctioned
  address) elevate this beyond a single-event incident to a counterparty-pattern
  investigation?

## Timeline
- Initial escalation: within 4 hours
- Initial assessment complete: within 24 hours
- SAR filing decision: within 30 days (regulatory window)
- Voluntary self-disclosure decision: before any regulator inquiry, no fixed window

---

## Reaction Schema
React with one of:
:white_check_mark: — Approved, executing as drafted
:no_entry_sign: — Skipped, no action needed
:pencil2: — Modified, executed with changes
:warning: — Needs more work before approval

---
Health: Trigger source: onchain-watchlist | Research depth: full | Quality: 9/10
```

### T+10:00 and beyond — Operator acts

The operator receives the package via DM within 10 minutes of the on-chain event. Three parallel threads kick off:

- Compliance leadership notified with the draft incident report in hand
- Legal counsel engaged with full context already prepared
- SAR filing draft started in parallel

The operator reacts to the package with :white_check_mark: after minor modifications to routing details. The Feedback Harvester logs the reaction. The Regulatory Oracle adds a related-matter entry for the pending filing assessment.

---

## Fleet-Wide Effects

**On-Chain Watchlist state updated:**
- `flagged_counterparties` now includes `0xDEF...9999` with metadata
- Any future event involving this address on ANY watchlisted entity will enrich with this history
- `address_state` for monitored-entity-04 reflects the enhanced monitoring flag

**Regulatory Oracle state updated:**
- `tracked_matters` now includes "Internal incident — sanctions exposure (monitored-entity-04)"
- `upcoming_deadlines` includes potential SAR filing window

**Synthesis Engine** will thread this incident into tomorrow's daily synthesis, noting the connection between the sanctions-list event and any related regulatory activity that follows.

**Fleet Query** can now answer questions like:
- "Any on-chain events involving sanctioned counterparties this month?"
- "What was the first time we saw address 0xDEF...9999?"
- "How many sanctions-exposure events has monitored-entity-04 been involved in historically?"

Data layer writes for this event:

```sql
INSERT INTO regulatory_events (agent_name, event_date, severity, jurisdiction,
  authority, matter, summary)
VALUES ('onchain-watchlist', '[DATE]', 'CRITICAL', 'US',
  'OFAC', 'Sanctions exposure — monitored-entity-04',
  '250k USDT transfer to SDN-listed counterparty 0xDEF...9999');

INSERT INTO agent_runs (agent_name, run_timestamp, quality_score,
  sources_used, fallbacks_triggered, findings_count)
VALUES ('onchain-watchlist', '[TIMESTAMP]', 9,
  'Blockscout,OFAC-SDN', 0, 1);
```

---

## What This Demonstrates

**Multi-channel escalation.** One event, three distinct notifications (main channel, red-phone alerts, DM), each tuned to its purpose. The main channel documents; the alerts channel signals; the DM activates the operator.

**Enrichment as a force multiplier.** The raw event (transfer to a sanctioned address) is the skeleton. The fleet adds all the flesh: prior pattern analysis, precedent events, regulatory framework, filing guidance. The operator starts with full context, not a bare alert.

**Speed plus completeness.** Under 10 minutes from on-chain event to operator-ready response package. Neither fast-but-thin (a simple alert) nor thorough-but-slow (manual report). Both.

**Learning across events.** The counterparty now lives in `flagged_counterparties`. If any other watched address ever touches this counterparty in the future, enrichment is automatic — the fleet accumulates knowledge per event.

---

## Related Patterns

- [Execution Scaffolding](../patterns/execution-scaffolding.md)
- [Fallback Chains](../patterns/fallback-chains.md)
- [State Management](../patterns/state-management.md)
