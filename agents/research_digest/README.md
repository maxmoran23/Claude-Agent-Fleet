# Research Digest Agent

Daily synthesis of noteworthy developments in AI and ML research, delivered to Slack.

## What It Does

- Runs once daily on a GitHub Actions cron schedule (07:00 ET / 11:00 UTC)
- Calls the Anthropic Messages API with the system prompt in `prompt.md`
- Posts the result to the Slack channel specified by `SLACK_DEFAULT_CHANNEL`

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
python agent.py
```

## Run in CI

This agent runs automatically via `.github/workflows/research-digest.yml`. Required repository secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — loads config, runs prompt, publishes to Slack |
| `prompt.md` | System prompt defining the agent's role and output format |
| `README.md` | This file |
