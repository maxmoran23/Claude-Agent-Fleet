# Changelog

All notable changes to this framework are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Framework continues to evolve. See commit history for in-progress changes.

---

## [1.4.0] — 2026-06-10

Compliance-operations expansion: a dedicated tier of example agent specs covering the second-line and assurance side of a compliance program at a financial institution, plus a professional-naming pass on two existing examples. Examples grow from 15 to 22.

### Added

- `examples/sanctions-list-monitor/` — daily sanctions-list delta agent: diffs current OFAC SDN / consolidated list publications against the prior stored snapshot, classifies additions/removals/modifications by program, escalates same-day designations.
- `examples/control-testing/` — independent control-testing agent: executes test procedures against sampled evidence, produces workpaper-style results with exceptions by severity, tracks remediation re-tests across runs.
- `examples/risk-register-keeper/` — maintains a living compliance risk register: re-scores inherent/residual ratings as findings arrive, flags appetite breaches, produces period delta reports.
- `examples/model-governance-monitor/` — monitors models, rule sets, and AI-assisted tools in production processes: inventory, validation calendar, performance-drift and override-rate signals, human-in-the-loop control health.
- `examples/committee-pack-assembler/` — assembles governance committee reporting packs from sibling-agent state: KPI/KRI metrics, escalations, prior-action status, decisions-sought vs items for noting.
- `examples/exam-response-coordinator/` — on-demand examination/information-request coordinator: request register with owners and due dates, evidence mapping, open-item tracking, pre-submission completeness QC.
- `examples/compliance-intelligence-hub/` — aggregator across regulatory, sanctions, and on-chain monitoring agents: composite Compliance Pressure Index (0–100), jurisdiction tiering, consolidated dashboard-style report.

### Changed

- `examples/alpha-lab/` renamed to `examples/defi-protocol-monitor/` and `examples/headline-flash/` renamed to `examples/breaking-news-monitor/` — descriptive, institution-appropriate names; all repository references updated.
- `README.md` — new "Compliance operations" tier in the example catalog; counts and directory tree updated.

---

## [1.3.0] — 2026-06-09

Architecture refresh reflecting a full production re-foundation: state authority inversion, a shared agent kernel, gated self-modification, generated inventory, and independent quality measurement. Five new pattern docs; the state-management pattern rewritten.

### Added

- `docs/patterns/agent-kernel.md` — versioned kernel contract + shared CLI helpers (state load/persist, health footer, idempotency guard, fleet-wide FTS5 recall) replacing per-agent boilerplate. Pattern improvements become one-file edits; quality-scale validation gets a single choke point.
- `docs/patterns/idempotency-outbox.md` — claim/confirm/fail dedup protocol for non-idempotent external actions (email, posts, trades), motivated by a production triple-send incident where only the send *confirmation* was lost, never the send.
- `docs/patterns/propose-and-gate.md` — human-gated self-modification: complete proposal packages (proposed file + rationale + diff) on a dedicated branch, reaction-vote approval, isolated one-commit applications with one-commit rollback, 14-day expiry, and post-apply experiment measurement.
- `docs/patterns/evaluation-harness.md` — independent measured-quality scoring (0–100) of published output via weighted structural rubrics; complements (never replaces) per-run self-rating; supplies before/after evidence for upgrade experiments.
- `docs/patterns/generated-registry.md` — fleet inventory generated from six primary sources with an auto-computed drift section (model drift, schedule drift, instrumentation drift, kernel-adoption lag); includes the 4-tier model-policy intent design and the out-of-band deadman liveness check.

### Changed

- `docs/patterns/state-management.md` — rewritten as "State Authority and Projections": local per-agent state files are the single source of truth (atomic writes, 30-day history, explicit corruption handling); Slack canvases demoted to non-fatal display mirrors; SQLite remains the append-only ledger. Motivated by production canvas write-saturation that silently broke persistence under the old canvases-as-truth design.
- `ARCHITECTURE.md` — state-management section rewritten around the authority/projection split; pattern index extended to 13 docs; agent-coupling section explains how the kernel shares mechanical helpers without coupling domain logic; JIT section updated for declared model-policy tiers.
- `FLEET-OPS.md` — production cycle updated (Step 0/Step 7 now local-file-first via kernel helpers); observability layer extended with deadman liveness, measured-quality evals, and the generated registry; self-repair section split into autonomous fixes vs declared-intent drift flags; JIT section gains the 4-tier model policy with per-tier run weighting; fleet scaling checklist updated (manifest declaration, eval rubric, kernel adoption).
- `README.md` — Core Patterns table extended from eight to thirteen; Key Design Decisions extended with inventory, external-send, observability, and gated-change rows; production pattern diagram updated for local-state authority.
- `QUICKSTART.md` — Steps 0/7 updated for local-state authority.
- `schemas/slack-canvas-structure.md` — retitled to display-canvas conventions with an authority note pointing at the new state-management pattern.

---

## [1.2.0] — 2026-05-13

Two new runnable reference agents, companion analytical dashboards, and the Fleet Evolution pattern.

### Added

- `agents/regulatory_oracle/` — fourth runnable reference agent. Daily digital-asset and AML/CFT regulatory briefing covering FinCEN, OFAC, OCC, SEC, CFTC, Federal Reserve, plus material international developments (MiCA, FCA, FATF, BIS). Severity-rated findings (CRITICAL / HIGH / MEDIUM), upcoming-deadlines section, watchlist. Stateless one-shot variant of the longer-form `examples/regulatory-oracle/AGENT.md`.
- `.github/workflows/regulatory-oracle.yml` — daily 12:00 UTC cron
- `agents/synthesis_engine/` — fifth runnable reference agent. Daily meta-analysis over the rest of the fleet's output — four analytical passes (cross-cutting themes, contradictions, coverage gaps, novel connections). Reads sibling agents' GitHub Actions run history via `gh` CLI as a minimal stateless proxy for fleet output. Capstone agent — only earns its keep with multiple sibling agents producing daily intelligence.
- `.github/workflows/synthesis-engine.yml` — daily 01:00 UTC cron (21:00 ET, after sibling agents have run)
- `tests/test_agents.py` — five additional tests covering the two new agents (prompt existence, no-token degradation, end-to-end mock run). Test count: 18 → 23.
- `docs/patterns/fleet-evolution.md` — new pattern doc covering the five-level maturity framework (L1 SCOUT → L5 MASTER), one-upgrade-per-cycle discipline, experiment tracking, and rollback protocol. Eighth core pattern.
- `showcase/` — companion analytical dashboards:
  - `crypto-aml-typology-engine/` — 15-typology reference library (sanctions evasion, money laundering, fraud, market manipulation) with detection rules and regulatory citations
  - `regulatory-intelligence-tracker/` — filterable view of the active digital-asset regulatory landscape
  - `images/` — screenshots embedded in the main README
- README "Showcase — Companion Analytical Surfaces" section with embedded screenshot and links to the visual half of the output stack

### Changed

- README runnable-agents table extended from three to five agents
- README Core Patterns table extended from seven to eight patterns (added Fleet Evolution)
- README repository-structure tree updated to reflect new agent directories and the `showcase/` tree, and the five-workflow count
- `FLEET-OPS.md` Fleet Evolution Engine section expanded with link to the new pattern doc and detail on the one-upgrade-per-cycle constraint
- `agents/fleet_watchdog/agent.py` `TRACKED_WORKFLOWS` extended to include the two new agent workflows so the watchdog reports across the full runnable fleet
- `tests/test_agents.py` lint cleanup — redundant `MagicMock` imports consolidated to the module-level import; updated `test_collect_workflow_health_parses_gh_output` expected-length to match the extended `TRACKED_WORKFLOWS`

---

## [1.1.0] — 2026-04-20

Runnable Python reference implementations and full engineering scaffolding.

### Added

- `fleet_core/` shared library — config loader, Anthropic runner, Slack publisher
- Three runnable reference agents with prompts and per-agent READMEs:
  - `agents/research_digest/` — daily AI/ML research synthesis
  - `agents/market_monitor/` — crypto market snapshot and narrative
  - `agents/fleet_watchdog/` — fleet health report via GitHub Actions run history
- GitHub Actions workflows:
  - `ci.yml` — runs `pytest` on every push and PR
  - `research-digest.yml` — daily 11:00 UTC cron
  - `market-monitor.yml` — every 8h cron
  - `fleet-watchdog.yml` — every 6h cron (offset)
- Test suite — 18 unit and integration tests covering config, runner, publisher, and all three agents
- `pyproject.toml` with `setuptools` build backend and `ruff` + `pytest` configuration
- Pre-commit hooks (`ruff` format and lint, trailing whitespace, YAML/TOML validation)
- Dependabot configuration for `pip` and `github-actions` (weekly)
- Issue templates (bug, feature) and pull request template
- `CODEOWNERS`
- README badges: CI status, Python version, license

### Changed

- README reframed from "zero traditional code" to include runnable Python reference implementations alongside the prompt-only agent specs in `examples/`

---

## [1.0.0] — 2026-04-19

First publicly-documented release of the framework as a reference architecture.

### Added

- Twelve new example agents covering entry-level through advanced complexity tiers:
  - `breaking-news-monitor` — real-time intelligence drops
  - `market-pulse` — lightweight market snapshot
  - `regulatory-oracle` — regulatory landscape monitoring
  - `calendar-alerts` — time-sensitive deadline routing
  - `daily-intelligence-brief` — multi-agent consolidation
  - `meeting-prep` — calendar-aware context aggregation
  - `onchain-watchlist` — address monitoring with sanctions screening
  - `synthesis-engine` — meta-analyst across the fleet
  - `defi-protocol-monitor` — DeFi protocol risk monitoring
  - `execution-scaffold` — threshold-triggered action packages
  - `fleet-auto-repair` — autonomous configuration self-healing
  - `fleet-query` — conversational interface over the fleet

- Seven pattern documents in `docs/patterns/`:
  - `state-management.md`
  - `fallback-chains.md`
  - `quality-self-rating.md`
  - `execution-scaffolding.md`
  - `jit-budget-management.md`
  - `self-repair.md`
  - `visual-cards.md`

- Four end-to-end case studies in `docs/case-studies/`:
  - `regulatory-enforcement-response.md`
  - `onchain-sanctions-hit.md`
  - `daily-intelligence-digest.md`
  - `agent-self-repair.md`

- Four schema documents in `schemas/`:
  - `data-layer.sql` — full SQLite DDL for the historical archive
  - `slack-canvas-structure.md` — canvas state-store conventions
  - `notion-intelligence-feed.md` — archive database schema
  - `agent-skill-frontmatter.md` — AGENT.md frontmatter specification

- MIT License
- CONTRIBUTING.md with contribution guidelines and genericization requirements

### Changed

- README.md rewritten as a reference framework presentation rather than a description of a specific private deployment
- ARCHITECTURE.md and FLEET-OPS.md updated to remove deployment-specific metrics (agent counts, weekly run budgets, build-timeline details)

### Removed

- Deployment-specific content that referenced a single private production fleet
- Weekly run budget metrics (now presented as configurable targets)
- Agent-count specifics (now presented as categorical capacity)

---

## [0.x] — Pre-public history

Earlier iterations of this framework were developed as an internal production system and refined through continuous operation before being restructured as a publicly-documented reference architecture. The patterns, schemas, and example agents in this repository reflect lessons learned during that development period.

Pre-public history is not versioned in this changelog.
