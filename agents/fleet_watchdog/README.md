# Fleet Watchdog Agent

Monitors the health of other agents in the fleet by reading GitHub Actions run history, then produces a health report to Slack.

## What It Does

- Runs every 6 hours via GitHub Actions (00:00, 06:00, 12:00, 18:00 UTC)
- Queries the GitHub API for recent runs of `research-digest.yml` and `market-monitor.yml`
- Passes that JSON into Claude for analysis
- Posts a health report to Slack

This is the fleet monitoring itself — if `research-digest` or `market-monitor` silently start failing, the watchdog flags it.

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
# Watchdog also needs a GitHub token in your env:
export GITHUB_TOKEN=$(gh auth token)
python agent.py
```

## Run in CI

Runs automatically via `.github/workflows/fleet-watchdog.yml`. The workflow injects the built-in `GITHUB_TOKEN` automatically. Required repository secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`

## Extending

To add more workflows to the watchdog's scope, edit `TRACKED_WORKFLOWS` in `agent.py`.

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — queries gh CLI, runs prompt, publishes to Slack |
| `prompt.md` | System prompt defining health analysis and output format |
| `README.md` | This file |
