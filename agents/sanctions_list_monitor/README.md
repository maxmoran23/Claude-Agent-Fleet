# Sanctions List Monitor Agent

Daily OFAC SDN list delta check — downloads the current list, diffs against the prior snapshot, classifies additions/removals/modifications with Claude, and posts the briefing to Slack.

## What It Does

- Runs once daily on a GitHub Actions cron schedule (22:15 UTC / 18:15 ET, after OFAC's typical afternoon publication window)
- Downloads the current SDN list from the official public endpoint (`https://www.treasury.gov/ofac/downloads/sdn.csv`)
- Computes the delta against the prior stored snapshot by SDN uid — added, removed, and modified entries with name and program tags
- Passes the structured delta (capped at 200 changes) to Claude with the system prompt in `prompt.md` for classification — digital-asset-related designations, program clustering, severity (CRITICAL/HIGH/MEDIUM/LOW)
- Posts the briefing to the Slack channel specified by `SLACK_DEFAULT_CHANNEL`
- Persists the new snapshot (uid map + content hash + timestamp) to `state/last-run.json`

## Fallback Chain

| Condition | Behavior |
|-----------|----------|
| First run (no prior snapshot) | Baseline mode — snapshot stored, "baseline established" posted, no delta claimed |
| Content hash matches prior snapshot | Single-line "no changes" post; no Claude call |
| Network failure fetching the list | Degraded-run notice posted to Slack; prior snapshot retained; exit 0 (the next successful run computes the catch-up delta) |
| Delta larger than 200 changes | Truncated for analysis, additions first; truncation flagged in the briefing |

The hash check is what makes daily running cheap: most days nothing changed and the run completes in seconds without an API call.

## State

Unlike the stateless siblings, this agent is stateful — a delta engine needs yesterday's list. State lives in `state/last-run.json` (uid-keyed entry map, content hash, timestamp), following the repo's standard local-state-file pattern. In CI, the `state/` directory is carried between scheduled runs via the GitHub Actions cache; if the cache is ever evicted, the agent simply re-establishes a baseline rather than failing.

## Run Locally

```bash
pip install -r ../../requirements.txt
cp ../../.env.example ../../.env  # edit with your keys
python agent.py   # first run establishes the baseline; run again to see a delta
```

No extra dependencies — the list fetch uses the standard library.

## Run in CI

This agent runs automatically via `.github/workflows/sanctions-list-monitor.yml`. Required repository secrets:

- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_DEFAULT_CHANNEL`

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Entry point — fetches the list, diffs snapshots, runs prompt, publishes to Slack, persists state |
| `prompt.md` | System prompt defining the classification framework and output format |
| `state/last-run.json` | Prior snapshot (generated at runtime; not committed) |
| `README.md` | This file |

## Stateless vs. Stateful

This is the stateful member of the runnable set — the diff requires persistent memory. The longer-form Claude Code variant in [`examples/sanctions-list-monitor/AGENT.md`](../../examples/sanctions-list-monitor/AGENT.md) adds multi-list coverage, press-release enrichment, a configurable watchlist, and a verification queue, which is the recommended pattern when running this agent as a scheduled Claude Code task rather than via the Anthropic Messages API.
