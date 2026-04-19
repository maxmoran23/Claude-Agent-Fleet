"""Tests for fleet_core.config."""

from __future__ import annotations

import pytest

from fleet_core.config import Config, load_config

REQUIRED_VARS = ("ANTHROPIC_API_KEY", "SLACK_BOT_TOKEN", "SLACK_DEFAULT_CHANNEL")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Start each test with a clean environment."""
    for var in (*REQUIRED_VARS, "ANTHROPIC_MODEL"):
        monkeypatch.delenv(var, raising=False)
    # Prevent .env in repo root from leaking into test env
    monkeypatch.setattr("fleet_core.config.load_dotenv", lambda: None)


def test_load_config_returns_config_when_env_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_DEFAULT_CHANNEL", "C0TEST")

    config = load_config()

    assert isinstance(config, Config)
    assert config.anthropic_api_key == "sk-test"
    assert config.slack_bot_token == "xoxb-test"
    assert config.slack_default_channel == "C0TEST"
    assert config.anthropic_model == "claude-opus-4-6"


def test_load_config_respects_anthropic_model_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_DEFAULT_CHANNEL", "C0TEST")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    assert load_config().anthropic_model == "claude-sonnet-4-6"


def test_load_config_raises_when_required_var_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    # SLACK_BOT_TOKEN intentionally missing

    with pytest.raises(EnvironmentError) as exc_info:
        load_config()

    assert "SLACK_BOT_TOKEN" in str(exc_info.value)
    assert "SLACK_DEFAULT_CHANNEL" in str(exc_info.value)


def test_config_is_frozen(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_DEFAULT_CHANNEL", "C0TEST")

    config = load_config()
    with pytest.raises(AttributeError):
        config.anthropic_api_key = "changed"  # type: ignore[misc]
