"""Integration tests for the three reference agents."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fleet_core.runner import AgentResult

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_VARS = ("ANTHROPIC_API_KEY", "SLACK_BOT_TOKEN", "SLACK_DEFAULT_CHANNEL")


@pytest.fixture
def mock_env(monkeypatch):
    """Provide valid env vars for agents to start up."""
    for var in REQUIRED_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_DEFAULT_CHANNEL", "C0TEST")
    monkeypatch.setattr("fleet_core.config.load_dotenv", lambda: None)


def _make_agent_result(text: str = "sample output") -> AgentResult:
    return AgentResult(
        text=text,
        input_tokens=100,
        output_tokens=50,
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )


# --- Research Digest ---------------------------------------------------------


def test_research_digest_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "research_digest" / "prompt.md").is_file()


@patch("fleet_core.publisher.WebClient")
@patch("fleet_core.runner.Anthropic")
def test_research_digest_main_posts_to_slack(mock_anthropic, mock_webclient, mock_env):
    from unittest.mock import MagicMock
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="digest body")],
        usage=MagicMock(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.research_digest.agent import main as research_main

    assert research_main() == 0
    assert slack.chat_postMessage.called
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Research Digest" in posted
    assert "digest body" in posted


# --- Market Monitor ----------------------------------------------------------


def test_market_monitor_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "market_monitor" / "prompt.md").is_file()


@patch("fleet_core.publisher.WebClient")
@patch("fleet_core.runner.Anthropic")
def test_market_monitor_main_posts_to_slack(mock_anthropic, mock_webclient, mock_env):
    from unittest.mock import MagicMock
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="market body")],
        usage=MagicMock(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.market_monitor.agent import main as market_main

    assert market_main() == 0
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Market Monitor" in posted
    assert "market body" in posted


# --- Fleet Watchdog ----------------------------------------------------------


def test_fleet_watchdog_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "fleet_watchdog" / "prompt.md").is_file()


def test_collect_workflow_health_returns_empty_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    from agents.fleet_watchdog.agent import collect_workflow_health

    assert collect_workflow_health() == []


@patch("agents.fleet_watchdog.agent.subprocess.check_output")
def test_collect_workflow_health_parses_gh_output(mock_check_output, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghs-test")
    mock_check_output.return_value = json.dumps(
        [{"status": "completed", "conclusion": "success", "createdAt": "2026-04-19T00:00:00Z", "displayTitle": "test"}]
    )

    from agents.fleet_watchdog.agent import collect_workflow_health

    result = collect_workflow_health()
    assert len(result) == 2  # one entry per tracked workflow
    assert all("runs" in entry for entry in result)
    assert all(len(entry["runs"]) == 1 for entry in result)


@patch("agents.fleet_watchdog.agent.subprocess.check_output")
def test_collect_workflow_health_handles_gh_errors(mock_check_output, monkeypatch):
    import subprocess

    monkeypatch.setenv("GITHUB_TOKEN", "ghs-test")
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "gh")

    from agents.fleet_watchdog.agent import collect_workflow_health

    result = collect_workflow_health()
    assert all("error" in entry for entry in result)
    assert all(entry["runs"] == [] for entry in result)
