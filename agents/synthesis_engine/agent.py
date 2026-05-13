#!/usr/bin/env python3
"""Synthesis Engine — daily meta-analysis over the rest of the fleet's output."""

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
logger = logging.getLogger("synthesis_engine")

PROMPT_PATH = Path(__file__).parent / "prompt.md"

SOURCE_WORKFLOWS = (
    "research-digest.yml",
    "market-monitor.yml",
    "regulatory-oracle.yml",
)


def collect_fleet_run_history() -> list[dict]:
    """Query GitHub Actions for recent run titles from sibling agent workflows.

    The run titles act as a minimal stateless proxy for fleet output. In a
    stateful production deployment, the synthesis engine reads actual agent
    state stores; here we work from what GitHub Actions exposes.
    """
    repo = os.environ.get("GITHUB_REPOSITORY", "maxmoran23/Claude-Agent-Fleet")
    gh_token = os.environ.get("GITHUB_TOKEN")

    if not gh_token:
        logger.warning("GITHUB_TOKEN not set — synthesis will operate without fleet history")
        return []

    env = {**os.environ, "GH_TOKEN": gh_token}
    history = []

    for workflow in SOURCE_WORKFLOWS:
        try:
            output = subprocess.check_output(
                [
                    "gh",
                    "run",
                    "list",
                    "--repo",
                    repo,
                    "--workflow",
                    workflow,
                    "--limit",
                    "3",
                    "--json",
                    "status,conclusion,createdAt,displayTitle",
                ],
                env=env,
                text=True,
                timeout=30,
            )
            history.append({"workflow": workflow, "recent_runs": json.loads(output)})
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            json.JSONDecodeError,
        ) as err:
            logger.warning("could not query workflow=%s: %s", workflow, err)
            history.append({"workflow": workflow, "recent_runs": [], "error": str(err)})

    return history


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history = collect_fleet_run_history()

    user_input = (
        f"Produce the daily fleet synthesis for {today}.\n\n"
        f"Sibling agents tracked: research_digest, market_monitor, regulatory_oracle.\n"
        f"Recent run history (JSON):\n```json\n{json.dumps(history, indent=2)}\n```\n\n"
        "Synthesize cross-cutting themes, contradictions, coverage gaps, and novel "
        "connections that span the fleet. If the run history is sparse, produce a "
        "fleet-health synthesis rather than fabricating findings. Keep under 500 words."
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    header = f":telescope: *Fleet Synthesis — {today}*"
    body = f"{header}\n\n{result.text}"

    publish_to_slack(config=config, text=body)
    logger.info(
        "done input_tokens=%d output_tokens=%d model=%s",
        result.input_tokens,
        result.output_tokens,
        result.model,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
