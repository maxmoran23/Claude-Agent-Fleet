"""Tests for fleet_core.publisher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from fleet_core.config import Config
from fleet_core.publisher import SlackPublisher, publish_to_slack


def _make_config(default_channel: str = "C0DEFAULT") -> Config:
    return Config(
        anthropic_api_key="sk-test",
        slack_bot_token="xoxb-test",
        slack_default_channel=default_channel,
        anthropic_model="claude-opus-4-6",
    )


@patch("fleet_core.publisher.WebClient")
def test_publish_to_slack_posts_to_default_channel(mock_webclient_cls):
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ts": "1234.5678", "ok": True}
    mock_webclient_cls.return_value = mock_client

    ts = publish_to_slack(_make_config("C0DEFAULT"), "hello world")

    assert ts == "1234.5678"
    kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert kwargs["channel"] == "C0DEFAULT"
    assert kwargs["text"] == "hello world"


@patch("fleet_core.publisher.WebClient")
def test_publish_to_slack_respects_channel_override(mock_webclient_cls):
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient_cls.return_value = mock_client

    SlackPublisher(_make_config("C0DEFAULT")).post("msg", channel="C0OVERRIDE")

    assert mock_client.chat_postMessage.call_args.kwargs["channel"] == "C0OVERRIDE"


@patch("fleet_core.publisher.WebClient")
def test_publish_to_slack_reraises_slack_errors(mock_webclient_cls):
    mock_client = MagicMock()
    error_response = {"error": "channel_not_found", "ok": False}
    mock_client.chat_postMessage.side_effect = SlackApiError(
        message="channel_not_found", response=error_response
    )
    mock_webclient_cls.return_value = mock_client

    with pytest.raises(SlackApiError):
        publish_to_slack(_make_config(), "msg")
