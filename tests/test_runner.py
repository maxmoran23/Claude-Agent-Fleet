"""Tests for fleet_core.runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fleet_core.config import Config
from fleet_core.runner import AgentResult, run_agent


def _make_config() -> Config:
    return Config(
        anthropic_api_key="sk-test",
        slack_bot_token="xoxb-test",
        slack_default_channel="C0TEST",
        anthropic_model="claude-opus-4-6",
    )


def _fake_message(text: str = "hello", in_tok: int = 10, out_tok: int = 5) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )


@patch("fleet_core.runner.Anthropic")
def test_run_agent_returns_structured_result(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_message("response text", 42, 17)
    mock_anthropic_cls.return_value = mock_client

    result = run_agent(
        config=_make_config(),
        system_prompt="You are a test agent.",
        user_input="Say hello.",
    )

    assert isinstance(result, AgentResult)
    assert result.text == "response text"
    assert result.input_tokens == 42
    assert result.output_tokens == 17
    assert result.stop_reason == "end_turn"


@patch("fleet_core.runner.Anthropic")
def test_run_agent_passes_system_and_user_correctly(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_message()
    mock_anthropic_cls.return_value = mock_client

    run_agent(
        config=_make_config(),
        system_prompt="SYS",
        user_input="USR",
        max_tokens=1024,
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "SYS"
    assert call_kwargs["messages"] == [{"role": "user", "content": "USR"}]
    assert call_kwargs["max_tokens"] == 1024
    assert call_kwargs["model"] == "claude-opus-4-6"


@patch("fleet_core.runner.Anthropic")
def test_run_agent_concatenates_multiple_text_blocks(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="part one "),
            SimpleNamespace(type="text", text="part two"),
        ],
        usage=SimpleNamespace(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    mock_anthropic_cls.return_value = mock_client

    result = run_agent(
        config=_make_config(),
        system_prompt="x",
        user_input="y",
    )

    assert result.text == "part one part two"
