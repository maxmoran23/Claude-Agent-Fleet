"""Slack publishing helper used by reference agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class SlackPublisher:
    config: Config

    def post(
        self,
        text: str,
        channel: str | None = None,
        thread_ts: str | None = None,
        unfurl_links: bool = False,
    ) -> str:
        """Post a message to Slack. Returns the message timestamp."""
        client = WebClient(token=self.config.slack_bot_token)
        target = channel or self.config.slack_default_channel

        try:
            response = client.chat_postMessage(
                channel=target,
                text=text,
                thread_ts=thread_ts,
                unfurl_links=unfurl_links,
            )
        except SlackApiError as err:
            logger.error("slack post failed channel=%s error=%s", target, err.response["error"])
            raise

        ts = response["ts"]
        logger.info("posted to slack channel=%s ts=%s", target, ts)
        return ts


def publish_to_slack(config: Config, text: str, channel: str | None = None) -> str:
    """Convenience wrapper for one-off posts."""
    return SlackPublisher(config).post(text, channel=channel)
