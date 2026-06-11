# Case Study: Regulatory Enforcement Response

End-to-end walkthrough showing how an OFAC enforcement action moves from detection through pre-filled response package to operator approval.

> This case study uses fabricated entities and data for illustration. No real enforcement action is referenced.

---

## Scenario

A regulatory agency (OFAC in this example) announces an enforcement settlement against a crypto exchange for sanctions violations. The fleet needs to:

1. Detect the announcement quickly
2. Assess severity and relevance
3. Draft an internal response brief
4. Surface deadlines and required actions
5. Route to the operator for approval

Total elapsed time from regulator announcement to operator's desk: under 30 minutes.

---

## Timeline

### T+00:00 — Announcement published

OFAC publishes a press release and settlement document: `EXAMPLE-SETTLEMENT-001`. The settlement identifies compliance program deficiencies and requires corrective actions within 90 days.

### T+00:00 to T+10:00 — Breaking News Monitor catches it

The Breaking News Monitor agent's next scheduled run (every ~3 hours during active hours) picks up the announcement from its regulatory-news query. It posts to the command-center channel:

```
# Flash — [DATE] [TIME]

[BREAKING] OFAC announces settlement with crypto exchange, cites sanctions program deficiencies
Full press release and settlement document published. 90-day corrective action timeline.
Source: treasury.gov/news

---
Health: Sources: Web search, news | Fallbacks: 0 | Quality: 9/10 | Topic: regulatory
```

### T+10:00 to T+30:00 — Regulatory Oracle runs its cycle

The Regulatory Oracle agent's next scheduled run (daily morning) already includes the new enforcement action because the headline is already in the flash stream. The oracle:

1. Reads the full press release and settlement document
2. Classifies severity as **CRITICAL** based on:
   - Material penalty amount
   - Precedent-setting compliance program findings
   - Cross-industry impact (similar programs at peer firms)
   - Fixed 90-day corrective action timeline
3. Threads the finding into its regulatory landscape state
4. Adds a new entry to `upcoming_deadlines` for the 90-day deadline
5. Posts its regular morning brief with the enforcement action as the Top Signal

Regulatory Oracle output snippet:

```markdown
## Top Signal
OFAC settlement [EXAMPLE-SETTLEMENT-001] with [crypto exchange] cites sanctions program
deficiencies: inadequate screening controls, insufficient geographic restrictions, weak
customer-identification for high-risk jurisdictions. 90-day corrective action timeline.
Peer firms with similar compliance structures should expect increased scrutiny.

## Developments

### [CRITICAL] OFAC Settlement — Sanctions Program Deficiencies
Authority: OFAC
Matter: EXAMPLE-SETTLEMENT-001
Action required: 90-day corrective action plan; internal review of sanctions screening posture
Source: https://home.treasury.gov/... (fabricated citation)

...

## Upcoming Deadlines (next 60 days)
- [+30 days] — EXAMPLE-SETTLEMENT-001 — Initial corrective action response
- [+90 days] — EXAMPLE-SETTLEMENT-001 — Full remediation plan submission
```

### T+30:00 — Execution Scaffold triggers

The Execution Scaffold agent, running every 30 minutes, checks the Regulatory Oracle's state. Finds the new CRITICAL finding. Checks threshold configuration:

```json
{
  "trigger_sources": ["regulatory-oracle"],
  "threshold_config": {
    "regulatory-oracle": {
      "trigger": "severity == CRITICAL AND action_required is not null",
      "package_type": "Response brief"
    }
  }
}
```

Threshold met. Scaffold generates a pre-filled response package.

---

## The Generated Package

```markdown
# DRAFT: Response Brief — OFAC Settlement EXAMPLE-SETTLEMENT-001
Generated: [DATE] [TIME]
Triggered by: Regulatory Oracle — finding ID reg-critical-2026-04-19-001
Urgency: Initial response recommended within 7 days; formal deadline in 30 days.

## Context
OFAC published a settlement with [crypto exchange] identifying sanctions program deficiencies.
The finding patterns are directly relevant to any firm operating a similar sanctions-screening
and customer-identification posture: screening cadence, geographic-restriction enforcement,
customer-identification for high-risk jurisdictions, training protocols, and escalation paths.
A documented internal response protects against similar findings if examined.

## Draft Response Brief — Internal Distribution

### Subject: OFAC Settlement EXAMPLE-SETTLEMENT-001 — Internal Review Initiated

### Executive Summary
On [DATE], OFAC announced a settlement with [exchange] citing sanctions program deficiencies
in five identified areas. Given structural similarities between the cited program and our
current posture, an internal review has been initiated across the following domains:

1. Sanctions screening cadence and coverage
2. Geographic-restriction enforcement at onboarding and ongoing
3. Customer identification for high-risk jurisdictions
4. Sanctions training program scope and documentation
5. Escalation pathways for potential hits

### Findings Review (to be populated)
- [Domain 1]: [Status]
- [Domain 2]: [Status]
- [Domain 3]: [Status]
- [Domain 4]: [Status]
- [Domain 5]: [Status]

### Remediation Timeline (placeholder)
- [+14 days]: Initial internal assessment complete
- [+30 days]: Remediation plan drafted where gaps identified
- [+60 days]: Remediation implementation underway
- [+90 days]: Full posture documented

### Contact
Compliance officer: [NAME]
For questions or relevant examples during internal review, contact: [CONTACT]

## Supporting Research

**Settlement document summary:**
[2-paragraph summary of the settlement's specific findings]

**Precedent enforcement actions in this domain (last 24 months):**
- [DATE]: OFAC vs [ENTITY] — similar findings on [specific topic], $[amount] penalty
- [DATE]: OFAC vs [ENTITY] — [topic], $[amount] penalty
- [DATE]: OFAC vs [ENTITY] — [topic], $[amount] penalty

**Peer firm response posture (publicly available):**
- [PEER 1]: Has documented sanctions program review in public disclosures ([date])
- [PEER 2]: Announced enhanced sanctions training program Q[N] 2026
- [PEER 3]: No public disclosure identified

**Relevant regulatory guidance:**
- OFAC Framework for Compliance Commitments (May 2019)
- FinCEN advisory [FIN-2024-A001] on sanctions evasion typologies
- [Any additional relevant guidance]

## Recommended Actions
1. Circulate this draft brief to compliance leadership within 24 hours
2. Initiate internal posture review across the five cited domains within 7 days
3. Log the matter to the firm's enforcement-tracker with 30-day and 90-day deadline entries
4. Schedule a compliance-team working session to assess each domain with documented findings
5. Prepare an external-facing statement template in case of regulator inquiry or press question

## Open Questions (operator decides)
- Is internal distribution of this brief appropriate at this time, or should initial review be
  limited to compliance leadership?
- Does the severity classification warrant notification to the audit committee, or is
  compliance-level handling sufficient?
- Are there firm-specific historical findings that should be referenced in the internal review
  to provide continuity?

## Timeline
- Suggested initial-response action: within 7 days
- Formal 30-day initial corrective action deadline (as noted in settlement)
- Formal 90-day full remediation deadline (as noted in settlement)

---

## Reaction Schema
React with one of:
:white_check_mark: — Approved, executing as drafted
:no_entry_sign: — Skipped, no action needed
:pencil2: — Modified, executed with changes
:warning: — Needs more work before approval

---
Health: Trigger source: regulatory-oracle | Research depth: full | Quality: 9/10
```

### T+30:00 to T+45:00 — Delivery

The package is posted to a designated action-items channel (restricted membership) and cross-posted as a DM to the compliance-officer role. A calendar event is created for the 30-day deadline.

### T+60:00 to end of day — Operator reviews

The operator receives the package. Reads it in ~3 minutes (the draft is already complete; the reading cost is just the context-switch). Makes three changes:
- Adds a specific peer firm whose recent disclosure is directly relevant
- Tightens the open questions to remove the audit-committee question (not relevant in this firm's governance)
- Reassigns the compliance-team session to a specific follow-up meeting

Reacts to the package with :pencil2: — Modified, executed with changes. The Feedback Harvester logs the reaction.

### T+90 minutes — Internal distribution

The operator circulates the modified brief internally. Total operator time from notification to internal distribution: roughly 15 minutes. Without the scaffold agent, the equivalent work (research + drafting + formatting) would have taken 2–4 hours.

---

## Outcomes Captured by the Fleet

The reaction log now contains:

```json
{
  "package_id": "scaffold-reg-critical-2026-04-19-001",
  "reaction": "pencil2",
  "reaction_time": "[ISO]",
  "time_to_reaction_minutes": 47,
  "package_type": "regulatory_response_brief"
}
```

The Feedback Harvester's weekly review will flag this as a successful package type — delivered in 30 minutes, approved-with-modifications in under an hour. Keep generating this package type.

The calendar alerts agent now holds a 30-day deadline event and will escalate it into daily briefs as the deadline approaches.

The Regulatory Oracle continues to track the matter in `tracked_matters`, updating status on each daily run until resolved.

---

## What This Demonstrates

**The 90/10 handoff in practice.** The agent did all the research, drafting, and formatting work — the 90% that takes hours. The operator did the 10% that genuinely required judgment: peer-specific context, governance nuances, meeting routing.

**Threshold discipline.** The package was generated only because the upstream finding was CRITICAL with a concrete action required. A finding rated HIGH or MEDIUM would not have triggered a full response brief — those get noted but not packaged.

**Institutional memory through state.** The matter is tracked across tracked_matters and upcoming_deadlines. Six months from now, if a related enforcement action appears, the fleet will surface the prior matter automatically.

**Feedback closing the loop.** The operator's :pencil2: reaction feeds the next threshold tuning pass. If the package type continues to be modified rather than approved, the drafting logic needs tightening.

---

## Related Patterns

- [Execution Scaffolding](../patterns/execution-scaffolding.md)
- [Quality Self-Rating](../patterns/quality-self-rating.md)
- [State Management](../patterns/state-management.md)
