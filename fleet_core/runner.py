"""Thin wrapper around the Anthropic Messages API for running agent prompts."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from anthropic import Anthropic

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None
    model: str


def run_agent(
    config: Config,
    system_prompt: str,
    user_input: str,
    max_tokens: int = 4096,
) -> AgentResult:
    """Send a prompt to Claude and return the structured result."""
    client = Anthropic(api_key=config.anthropic_api_key)

    logger.info("calling anthropic model=%s max_tokens=%d", config.anthropic_model, max_tokens)

    message = client.messages.create(
        model=config.anthropic_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}],
    )

    text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )

    logger.info(
        "anthropic response input_tokens=%d output_tokens=%d stop_reason=%s",
        message.usage.input_tokens,
        message.usage.output_tokens,
        message.stop_reason,
    )

    return AgentResult(
        text=text,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        stop_reason=message.stop_reason,
        model=message.model,
    )
