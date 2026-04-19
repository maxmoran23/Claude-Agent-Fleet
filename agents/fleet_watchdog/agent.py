#!/usr/bin/env python3
"""Fleet Watchdog — monitors health of sibling agents via GitHub Actions run history."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fleet_core import load_config, publish_to_slack, run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fleet_watchdog")

PROMPT_PATH = Path(__file__).parent / "prompt.md"

TRACKED_WORKFLOWS = ("research-digest.yml", "market-monitor.yml")


def collect_workflow_health() -> list[dict]:
    """Query GitHub Actions for recent run results on tracked workflows."""
    repo = os.environ.get("GITHUB_REPOSITORY", "maxmoran23/Claude-Agent-Fleet")
    gh_token = os.environ.get("GITHUB_TOKEN")

    if not gh_token:
        logger.warning("GITHUB_TOKEN not set — returning empty health data")
        return []

    env = {**os.environ, "GH_TOKEN": gh_token}
    health = []

    for workflow in TRACKED_WORKFLOWS:
        try:
            output = subprocess.check_output(
                [
                    "gh",
                    "run",
                    "list",
                    "--repo", repo,
                    "--workflow", workflow,
                    "--limit", "5",
                    "--json", "status,conclusion,createdAt,displayTitle",
                ],
                env=env,
                text=True,
                timeout=30,
            )
            runs = json.loads(output)
            health.append({"workflow": workflow, "runs": runs})
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as err:
            logger.warning("could not query workflow=%s: %s", workflow, err)
            health.append({"workflow": workflow, "runs": [], "error": str(err)})

    return health


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    health = collect_workflow_health()
    user_input = (
        f"Produce the fleet watchdog report for {timestamp}.\n\n"
        f"Workflow run history (JSON):\n```json\n{json.dumps(health, indent=2)}\n```\n\n"
        "Assess fleet health and report per the format in your system prompt."
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    header = f":mag: *Fleet Watchdog — {timestamp}*"
    body = f"{header}\n\n{result.text}"

    publish_to_slack(config=config, text=body)
    logger.info(
        "done workflows_checked=%d input_tokens=%d output_tokens=%d",
        len(health),
        result.input_tokens,
        result.output_tokens,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
