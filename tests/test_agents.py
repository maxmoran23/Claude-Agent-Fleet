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


# --- Regulatory Oracle -------------------------------------------------------


def test_regulatory_oracle_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "regulatory_oracle" / "prompt.md").is_file()


@patch("fleet_core.publisher.WebClient")
@patch("fleet_core.runner.Anthropic")
def test_regulatory_oracle_main_posts_to_slack(mock_anthropic, mock_webclient, mock_env):
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="regulatory body")],
        usage=MagicMock(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.regulatory_oracle.agent import main as oracle_main

    assert oracle_main() == 0
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Regulatory Oracle" in posted
    assert "regulatory body" in posted


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
        [
            {
                "status": "completed",
                "conclusion": "success",
                "createdAt": "2026-04-19T00:00:00Z",
                "displayTitle": "test",
            }
        ]
    )

    from agents.fleet_watchdog.agent import collect_workflow_health

    result = collect_workflow_health()
    assert len(result) == 4  # one entry per tracked workflow
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


# --- Synthesis Engine --------------------------------------------------------


def test_synthesis_engine_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "synthesis_engine" / "prompt.md").is_file()


def test_synthesis_engine_collect_returns_empty_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    from agents.synthesis_engine.agent import collect_fleet_run_history

    assert collect_fleet_run_history() == []


@patch("fleet_core.publisher.WebClient")
@patch("fleet_core.runner.Anthropic")
def test_synthesis_engine_main_posts_to_slack(mock_anthropic, mock_webclient, mock_env, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="synthesis body")],
        usage=MagicMock(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.synthesis_engine.agent import main as synthesis_main

    assert synthesis_main() == 0
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Fleet Synthesis" in posted
    assert "synthesis body" in posted


# --- Sanctions List Monitor ---------------------------------------------------

SDN_CSV_V1 = (
    '1001,"ALPHA TRADING CO.","-0- ","SDGT",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
    '1002,"BRAVO, Carlos","individual","CYBER2",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
)

SDN_CSV_V2 = (
    '1001,"ALPHA TRADING CO.","-0- ","SDGT",-0-,-0-,-0-,-0-,-0-,-0-,-0-,'
    '"Digital Currency Address - XBT 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa."\n'
    '1003,"CHARLIE EXCHANGE LLC","-0- ","DPRK3] [CYBER2",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
)


@pytest.fixture
def sanctions_state_path(tmp_path, monkeypatch):
    """Redirect the monitor's state file into a temp directory."""
    path = tmp_path / "state" / "last-run.json"
    monkeypatch.setattr("agents.sanctions_list_monitor.agent.STATE_PATH", path)
    return path


def test_sanctions_list_monitor_prompt_file_exists():
    assert (REPO_ROOT / "agents" / "sanctions_list_monitor" / "prompt.md").is_file()


@patch("fleet_core.publisher.WebClient")
@patch("agents.sanctions_list_monitor.agent.fetch_sdn_csv")
def test_sanctions_monitor_baseline_run(mock_fetch, mock_webclient, mock_env, sanctions_state_path):
    mock_fetch.return_value = SDN_CSV_V1
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.sanctions_list_monitor.agent import main as sanctions_main

    assert sanctions_main() == 0
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Baseline established" in posted
    state = json.loads(sanctions_state_path.read_text())
    assert state["list_snapshots"]["ofac_sdn"]["entry_count"] == 2
    assert set(state["entries"]) == {"1001", "1002"}


@patch("fleet_core.publisher.WebClient")
@patch("fleet_core.runner.Anthropic")
@patch("agents.sanctions_list_monitor.agent.fetch_sdn_csv")
def test_sanctions_monitor_delta_posts_to_slack(
    mock_fetch, mock_anthropic, mock_webclient, mock_env, sanctions_state_path
):
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="delta briefing body")],
        usage=MagicMock(input_tokens=1, output_tokens=2),
        stop_reason="end_turn",
        model="claude-opus-4-6",
    )
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.sanctions_list_monitor.agent import main as sanctions_main

    mock_fetch.return_value = SDN_CSV_V1
    assert sanctions_main() == 0  # baseline
    mock_fetch.return_value = SDN_CSV_V2
    assert sanctions_main() == 0  # delta

    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "Sanctions List Monitor" in posted
    assert "delta briefing body" in posted
    state = json.loads(sanctions_state_path.read_text())
    assert state["last_delta"] == {"added": 1, "removed": 1, "modified": 1}
    assert set(state["entries"]) == {"1001", "1003"}


@patch("fleet_core.publisher.WebClient")
@patch("agents.sanctions_list_monitor.agent.fetch_sdn_csv")
def test_sanctions_monitor_no_change_run(mock_fetch, mock_webclient, mock_env, sanctions_state_path):
    mock_fetch.return_value = SDN_CSV_V1
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.sanctions_list_monitor.agent import main as sanctions_main

    assert sanctions_main() == 0  # baseline
    assert sanctions_main() == 0  # identical content
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "No changes" in posted


@patch("fleet_core.publisher.WebClient")
@patch("agents.sanctions_list_monitor.agent.fetch_sdn_csv")
def test_sanctions_monitor_degraded_on_fetch_failure(
    mock_fetch, mock_webclient, mock_env, sanctions_state_path
):
    import urllib.error

    mock_fetch.side_effect = urllib.error.URLError("connection refused")
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ts": "1.2", "ok": True}
    mock_webclient.return_value = slack

    from agents.sanctions_list_monitor.agent import main as sanctions_main

    assert sanctions_main() == 0
    posted = slack.chat_postMessage.call_args.kwargs["text"]
    assert "DEGRADED RUN" in posted
    assert not sanctions_state_path.exists()  # prior snapshot untouched
