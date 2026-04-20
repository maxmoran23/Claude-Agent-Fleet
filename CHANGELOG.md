# Changelog

All notable changes to this framework are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Framework continues to evolve. See commit history for in-progress changes.

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
