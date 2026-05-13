# Regulatory Oracle Agent

Daily briefing on digital-asset and AML/CFT regulatory developments, delivered to Slack.

## What It Does

- Runs once daily on a GitHub Actions cron schedule (08:00 ET / 12:00 UTC)
- Calls the Anthropic Messages API with the system prompt in `prompt.md`
- Posts a severity-rated briefing to the Slack channel specified by `SLACK_DEFAULT_CHANNEL`
- Covers enforcement, rulemaking, guidance, legislation, policy statements, and deadlines across U.S. federal agencies (FinCEN, OFAC, OCC, SEC, CFTC, Federal Reserve) plus material international developments

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
python agent.py
```

## Run in CI

This agent runs automatically via `.github/workflows/regulatory-oracle.yml`. Required repository secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — loads config, runs prompt, publishes to Slack |
| `prompt.md` | System prompt defining the agent's role, classification framework, and output format |
| `README.md` | This file |

## Stateless vs. Stateful

This is a stateless one-shot agent — every run is independent, with no persistent state between runs. The longer-form Claude Code variant in [`examples/regulatory-oracle/AGENT.md`](../../examples/regulatory-oracle/AGENT.md) includes full state management (tracked matters, covered developments, quality history), which is the recommended pattern when running this agent as a scheduled Claude Code task rather than via the Anthropic Messages API.
