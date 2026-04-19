#!/usr/bin/env python3
"""Research Digest — daily synthesis of noteworthy AI and ML developments."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from fleet_core import load_config, publish_to_slack, run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("research_digest")

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_input = (
        f"Produce today's research digest for {today}. "
        "Keep it under 400 words. Markdown formatting for Slack."
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    header = f":newspaper: *Research Digest — {today}*"
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
