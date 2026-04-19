# Pattern: Execution Scaffolding

Threshold-triggered pre-filled action packages. The agent does the prep; the human approves.

---

## The Problem

Many intelligence findings suggest an action. A regulatory enforcement action might warrant a response brief. An on-chain sanctions hit might warrant an incident escalation. A critical market event might warrant a stakeholder comms draft. The pattern is: finding → action.

Two naive approaches both fail:

**Full automation** — the agent takes the action itself. This is dangerous for anything with external effects: sending messages, filing documents, committing funds, triggering operational workflows. Irreversible mistakes become the norm rather than the exception.

**Zero scaffolding** — the agent reports the finding, and the human does 100% of the downstream work. This is where most intelligence systems live, and it's why most intelligence never actually gets acted on. The cost of translating a finding into an action is high, and humans are busy. Findings rot.

Execution scaffolding is the middle path: the agent does 90% of the work (research, drafting, formatting, supporting context), and the human does the remaining 10% (final judgment, approval, external action).

---

## The Pattern

When an upstream agent produces a finding that exceeds a configured threshold, a scaffold agent generates a complete pre-filled action package. The package is labeled DRAFT, delivered to a specific operator, and includes a reaction schema so the operator can approve, skip, or modify with a single click.

The package contains everything the human would need to compose manually, already composed. The human's remaining job is judgment and execution.

---

## Anatomy of an Action Package

Every package has the same structure regardless of domain:

### 1. DRAFT label (visible, non-removable)

The header unambiguously indicates this is a draft awaiting approval. No package ever reaches an external system as the draft itself.

### 2. Context

What happened (the upstream finding), why this package was generated, what action is proposed. 2–4 sentences.

### 3. Primary artifact

The actual thing to be executed — a written response, a draft email, a decision memo, a remediation plan — fully drafted and ready to review. If approved without changes, this is what ships.

### 4. Supporting research

Precedent, prior related events, relevant citations, anything the operator would need to evaluate the primary artifact. Reduces the "let me look that up" overhead to zero.

### 5. Recommended actions

A numbered list of concrete steps to take if the package is approved. Often includes actions outside the primary artifact — notify X, update Y, file Z.

### 6. Open questions

Anything the agent could not resolve. Explicit list of judgment calls the operator must make. Forces the operator to notice these rather than gloss over them.

### 7. Timeline

Urgency framing. Suggested action window. Drop-dead deadline if applicable. Helps the operator prioritize.

### 8. Reaction schema

Explicit emoji-reaction options for the operator to respond:

- :white_check_mark: — Approved, executing as drafted
- :no_entry_sign: — Skipped, no action needed
- :pencil2: — Modified, executed with changes
- :warning: — Needs more work before approval

---

## Threshold Configuration

Thresholds determine when a package is generated. They are agent-specific and use-case-specific. Examples:

| Trigger Agent | Threshold | Package Type |
|--------------|-----------|--------------|
| Regulatory oracle | severity == CRITICAL | Response brief |
| On-chain watchlist | sanctions_touch == true | Incident response package |
| Market monitor | severity == CRITICAL AND delta > 15% | Stakeholder comms draft |
| Fleet watchdog | health_status == RED | Remediation plan |
| Synthesis engine | contradiction_materiality == high | Resolution proposal |

Thresholds are stored in the scaffold agent's state and can be tuned based on outcome tracking (see below).

---

## Delivery Semantics

Packages are not broadcast. Every package has exactly one audience — the operator or operators authorized to approve the action. Typically:

- Slack DM for sensitive packages
- A dedicated action-items channel with restricted membership for team packages
- Never a general-audience channel

Packages are posted as single-message items (or single threads) so they can be reacted to with clean emoji semantics.

---

## The Reaction Feedback Loop

Every operator reaction is persisted. Over time, the reaction log becomes training data for threshold tuning:

**If approval rate is high (>80%):** The threshold is tight. Loosen it — the agent can generate more packages without overwhelming the operator.

**If skip rate is high (>60%):** The threshold is loose. Tighten it — the agent is generating noise that wastes operator attention.

**If modification rate is high (>40%):** The draft quality is insufficient. Review the scaffold agent's drafting logic — something is systematically wrong with what it produces.

**If time-to-reaction is very long:** The operator isn't treating this package type as important. Either raise the priority (escalate delivery) or downgrade the threshold (stop generating these).

A companion feedback-harvester agent can automate this review on a weekly cadence.

---

## Why This Pattern Works

**It removes the activation energy for action.** Findings that would otherwise rot in a channel get acted on because the work to act has already been done.

**It preserves human judgment where it matters.** The agent never takes an external action. Every package is a proposal, and the human is the gate.

**It creates outcome measurability.** Unlike pure intelligence, scaffolding has binary outcomes — executed or skipped. The fleet can measure its own impact.

**It scales operator attention.** One operator can process 20 well-formed packages in the time it would take to compose one from scratch.

**It enforces format discipline.** Packages have rigid structure. Every one is scannable the same way. Operators learn the pattern and move through them faster than ad-hoc items.

---

## What This Pattern Is NOT

- **Not full automation.** Nothing ever ships without human approval. A package is always a draft.
- **Not for routine items.** Thresholds are tuned so only material findings generate packages. Daily market updates are reported, not scaffolded.
- **Not for low-confidence findings.** If the upstream agent self-scored <5, no package is generated — the input quality is too low to draft from.
- **Not a substitute for primary intelligence.** The scaffold agent has no independent information. It is downstream of real analysis.

---

## Anti-Patterns to Avoid

**Flooding the operator.** If the threshold is too loose, the operator stops reading packages. The pattern is useful only while every package is meaningful. Start conservative.

**Forking judgment into the agent.** Resist the temptation to have the scaffold agent resolve open questions itself. Open questions are the whole point — they ensure the human engages.

**Making the draft too good.** Counterintuitively, a draft that's too polished can get rubber-stamped without review. Including a few deliberately flagged open questions forces the operator to actually read.

**Skipping the reaction schema.** Without explicit reaction options, reactions are ambiguous. "Thumbs up" on a 20-paragraph package means what, exactly? The explicit schema (approved / skipped / modified / needs work) produces auditable, unambiguous operator intent.

---

## Related Patterns

- [Quality Self-Rating](quality-self-rating.md) — only high-quality upstream findings trigger packages
- [State Management](state-management.md) — where packages and reactions are persisted
- [Case Study: Regulatory Enforcement Response](../case-studies/regulatory-enforcement-response.md) — full end-to-end example
