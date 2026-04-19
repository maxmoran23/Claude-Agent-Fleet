"""Environment-backed configuration for reference agents."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    slack_bot_token: str
    slack_default_channel: str
    anthropic_model: str


def load_config() -> Config:
    """Load config from environment. Raises if required values are missing."""
    load_dotenv()

    required = {
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN"),
        "SLACK_DEFAULT_CHANNEL": os.environ.get("SLACK_DEFAULT_CHANNEL"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in values, or set them "
            "as GitHub Actions secrets when running in CI."
        )

    return Config(
        anthropic_api_key=required["ANTHROPIC_API_KEY"],  # type: ignore[arg-type]
        slack_bot_token=required["SLACK_BOT_TOKEN"],  # type: ignore[arg-type]
        slack_default_channel=required["SLACK_DEFAULT_CHANNEL"],  # type: ignore[arg-type]
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6"),
    )
