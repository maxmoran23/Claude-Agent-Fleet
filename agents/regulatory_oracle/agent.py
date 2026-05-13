#!/usr/bin/env python3
"""Regulatory Oracle — daily digital-asset and AML/CFT regulatory briefing."""

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
logger = logging.getLogger("regulatory_oracle")

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_input = (
        f"Produce today's regulatory briefing for {today}. "
        "Cover digital-asset and AML/CFT developments. "
        "Aim for 3–6 findings, severity-rated. Keep under 450 words."
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    header = f":scales: *Regulatory Oracle — {today}*"
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
