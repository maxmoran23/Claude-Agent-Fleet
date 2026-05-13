# Changelog

All notable changes to this framework are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Framework continues to evolve. See commit history for in-progress changes.

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
  - `headline-flash` — real-time intelligence drops
  - `market-pulse` — lightweight market snapshot
  - `regulatory-oracle` — regulatory landscape monitoring
  - `calendar-alerts` — time-sensitive deadline routing
  - `daily-intelligence-brief` — multi-agent consolidation
  - `meeting-prep` — calendar-aware context aggregation
  - `onchain-watchlist` — address monitoring with sanctions screening
  - `synthesis-engine` — meta-analyst across the fleet
  - `alpha-lab` — DeFi protocol risk monitoring
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
