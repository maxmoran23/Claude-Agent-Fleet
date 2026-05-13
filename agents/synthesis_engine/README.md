# Synthesis Engine Agent

Daily meta-analysis over the rest of the agent fleet's output. The synthesis-layer "capstone" agent — only useful once multiple sibling agents are producing intelligence.

## What It Does

- Runs once daily on a GitHub Actions cron schedule (21:00 ET / 01:00 UTC), after sibling agents have delivered their day's output
- Queries GitHub Actions for recent run history from `research_digest`, `market_monitor`, and `regulatory_oracle`
- Calls the Anthropic Messages API with the synthesis prompt — meta-analyst voice, four-pass analytical framework (cross-cutting themes, contradictions, coverage gaps, novel connections)
- Posts the resulting synthesis to the Slack channel specified by `SLACK_DEFAULT_CHANNEL`

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
python agent.py
```

If `GITHUB_TOKEN` is unset, the agent runs without fleet history and produces a fleet-health synthesis flagged in its output. It does not fail.

## Run in CI

This agent runs automatically via `.github/workflows/synthesis-engine.yml`. Required repository secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`
- `GITHUB_TOKEN` (auto-provided by GitHub Actions runtime)

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — loads config, gathers sibling-agent run history via `gh`, runs synthesis prompt, publishes to Slack |
| `prompt.md` | System prompt defining the four-pass analytical framework and output format |
| `README.md` | This file |

## Stateless vs. Stateful

This is a stateless one-shot synthesizer. It reads only what GitHub Actions exposes (run titles, conclusions, timestamps) — a minimal proxy for actual fleet output.

The stateful production variant in [`examples/synthesis-engine/AGENT.md`](../../examples/synthesis-engine/AGENT.md) reads sibling agents' Slack canvas state stores, persists a 14-day theme log, tracks a contradiction register, and audits its own coverage gaps over time. That variant is the right form when running this agent as a scheduled Claude Code task with a real multi-agent deployment.

The stateless variant here is sufficient to demonstrate the synthesis pattern and validate the prompt's analytical structure.

## Why This Is The "Capstone"

The synthesis engine has no value on its own. It only earns its keep when sibling agents are producing output worth synthesizing. Run it before you have 3+ sibling agents reliably delivering daily and it will produce thin, repetitive results.

The point of including it as a reference agent is to show what the apex of the fleet pattern looks like — every other agent generates intelligence; the synthesis engine generates intelligence about the intelligence.
