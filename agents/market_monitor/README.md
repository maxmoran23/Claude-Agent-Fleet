# Market Monitor Agent

Crypto market snapshot — prices, sentiment, narrative, notable movements — delivered to Slack.

## What It Does

- Runs every 8 hours via GitHub Actions (00:00, 08:00, 16:00 UTC)
- Calls the Anthropic Messages API with the system prompt in `prompt.md`
- Posts the briefing to the Slack channel specified by `SLACK_DEFAULT_CHANNEL`

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
python agent.py
```

## Run in CI

Runs automatically via `.github/workflows/market-monitor.yml`. Required secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`

## Extending with Live Data

To upgrade from LLM-only reasoning to live market data, add an HTTP fetch step before the prompt call. Recommended sources:

- **CoinGecko** — free public API for prices (`https://api.coingecko.com/api/v3/simple/price`)
- **Crypto.com Exchange** — public ticker endpoint
- **DefiLlama** — free TVL and protocol data

Pass the fetched JSON into the `user_input` parameter as context for the LLM.

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — loads config, runs prompt, publishes to Slack |
| `prompt.md` | System prompt defining scope, severity, and output format |
| `README.md` | This file |
