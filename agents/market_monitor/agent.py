#!/usr/bin/env python3
"""Market Monitor — crypto market snapshot and narrative analysis."""

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
logger = logging.getLogger("market_monitor")

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    user_input = (
        f"Produce the market monitor briefing for {timestamp}. "
        "Structure as snapshot → narrative → notable → watchlist. Keep under 350 words."
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    header = f":chart_with_upwards_trend: *Market Monitor — {timestamp}*"
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
