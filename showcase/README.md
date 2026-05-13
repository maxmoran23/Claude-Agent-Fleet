# Showcase — Companion Analytical Surfaces

Static, single-file HTML dashboards that share the same domain focus as the agent fleet — crypto AML typologies and the digital-asset regulatory landscape. These are not produced by the agents directly. They are independent reference artifacts that illustrate the kind of analytical surface a fleet's synthesis layer would target as output.

Each dashboard is a self-contained HTML file — no build step, no backend, no dependencies. Open in a browser or serve locally.

---

## Crypto AML Typology Engine

![Crypto AML Typology Engine](images/crypto-aml-typology-engine.png)

Reference library of fifteen crypto AML typologies organized by category (sanctions evasion, money laundering, fraud, market manipulation). Each typology includes detection rules, behavioral indicators, enrichment steps, and regulatory citations.

- **Path:** [`crypto-aml-typology-engine/index.html`](crypto-aml-typology-engine/index.html)
- **Audience:** AML/compliance analysts, transaction-monitoring engineers, on-chain investigators
- **Use:** Reference during alert triage; reference for typology mapping during model validation; onboarding material for analysts new to crypto AML

## Digital Asset Regulatory Intelligence Tracker

![Digital Asset Regulatory Intelligence Tracker](images/regulatory-intelligence-tracker.png)

Filterable view of the active digital-asset regulatory landscape — proposed legislation, agency rulemaking, enforcement actions, and interpretive guidance. Status tracking (active / proposed / pending / revised / withdrawn) and category filters (legislation, FINCEN, OFAC, OCC, SEC, federal reserve).

- **Path:** [`regulatory-intelligence-tracker/index.html`](regulatory-intelligence-tracker/index.html)
- **Audience:** Compliance officers, policy analysts, fintech legal teams
- **Use:** Quarterly compliance program review; horizon scanning for upcoming rule changes; regulatory impact analysis

---

## Running Locally

Any static HTTP server works. From the repository root:

```bash
python3 -m http.server 8765 --directory showcase
# Then open:
#   http://localhost:8765/crypto-aml-typology-engine/
#   http://localhost:8765/regulatory-intelligence-tracker/
```

Both dashboards are dark-themed by default with a light-mode toggle. Tested in Chrome and Safari on macOS.

---

## Why These Are Here

The agents in this repository produce text intelligence — Slack posts, digest emails, briefing summaries. That is one half of an agent fleet's output surface. The other half is visual — interactive dashboards that present the same underlying data structures in a form better suited to ad-hoc query and visual pattern recognition. These companion artifacts illustrate what the visual half looks like when designed with the same audit-defensible, compliance-focused discipline as the agent prompts.

Both dashboards were built independently of the fleet and predate the runnable reference agents in `agents/`. They are included here as portfolio context: the same domain expertise that shaped the agent specs in `examples/` also shaped these analytical surfaces. Together they sketch the full output stack — text intelligence from agents, visual surfaces for the operator.
