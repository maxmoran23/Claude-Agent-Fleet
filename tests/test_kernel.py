"""Tests for fleet_core.kernel (state, outbox, eval_runner)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from fleet_core.kernel import (
    BRIEFING_RUBRIC,
    KERNEL_VERSION,
    claim,
    confirm,
    fail,
    load_state,
    min_length,
    persist_state,
    regex_present,
    score_output,
)
from fleet_core.kernel.state import HISTORY_RING_SIZE

# --- state: step 0 / step 7 pair -------------------------------------------


def test_state_round_trip(tmp_path):
    persist_state(tmp_path, {"watchlist": ["BTC", "ETH"], "covered_items": [1, 2]})

    result = load_state(tmp_path)

    assert result["status"] == "loaded"
    assert result["state"]["watchlist"] == ["BTC", "ETH"]
    assert result["state"]["covered_items"] == [1, 2]


def test_load_state_first_run_returns_empty_baseline(tmp_path):
    result = load_state(tmp_path)

    assert result["status"] == "first_run"
    assert result["state"] == {}


def test_persist_state_stamps_timestamp_and_kernel_version(tmp_path):
    stamped = persist_state(tmp_path, {"key": "value"})

    assert stamped["kernel_version"] == KERNEL_VERSION
    # ISO-8601, parseable, UTC
    parsed = datetime.fromisoformat(stamped["last_run_timestamp"])
    assert parsed.tzinfo is not None
    # Stamps land in the file too, so any state file found on disk self-identifies
    on_disk = json.loads((tmp_path / "state" / "state.json").read_text())
    assert on_disk["last_run_timestamp"] == stamped["last_run_timestamp"]
    assert on_disk["kernel_version"] == KERNEL_VERSION


def test_load_state_quarantines_corrupt_file(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("{not valid json", encoding="utf-8")

    result = load_state(tmp_path)

    assert result["status"] == "corrupt"
    assert result["state"] == {}
    # Original file moved aside with a timestamp suffix, content preserved
    assert not (state_dir / "state.json").exists()
    quarantined = list(state_dir.glob("state.json.corrupt-*"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "{not valid json"
    assert result["quarantined_to"] == str(quarantined[0])


def test_load_state_after_quarantine_is_first_run(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("garbage", encoding="utf-8")

    assert load_state(tmp_path)["status"] == "corrupt"
    assert load_state(tmp_path)["status"] == "first_run"


def test_load_state_treats_non_object_json_as_corrupt(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "state.json").write_text('["valid json, wrong shape"]', encoding="utf-8")

    assert load_state(tmp_path)["status"] == "corrupt"


def test_history_ring_capped(tmp_path):
    for i in range(HISTORY_RING_SIZE + 5):
        persist_state(tmp_path, {"run": i})

    snapshots = sorted((tmp_path / "state" / "history").glob("state-*.json"))
    assert len(snapshots) == HISTORY_RING_SIZE
    # The newest snapshot holds the latest run; the oldest 5 were pruned
    assert json.loads(snapshots[-1].read_text())["run"] == HISTORY_RING_SIZE + 4


def test_persist_state_leaves_no_temp_files(tmp_path):
    persist_state(tmp_path, {"key": "value"})

    leftovers = [p for p in (tmp_path / "state").rglob("*") if p.name.endswith(".tmp")]
    assert leftovers == []


def test_failed_persist_preserves_existing_state(tmp_path):
    persist_state(tmp_path, {"key": "good"})

    with pytest.raises(TypeError):
        persist_state(tmp_path, {"key": object()})  # not JSON-serializable

    result = load_state(tmp_path)
    assert result["status"] == "loaded"
    assert result["state"]["key"] == "good"


def test_persist_state_rejects_non_dict(tmp_path):
    with pytest.raises(TypeError):
        persist_state(tmp_path, ["not", "a", "dict"])


# --- outbox: claim/confirm/fail lifecycle -----------------------------------


def test_claim_succeeds_first_time(tmp_path):
    outbox = tmp_path / "outbox.json"

    assert claim(outbox, "digest-2026-06-09-am") is True


def test_double_claim_rejected(tmp_path):
    outbox = tmp_path / "outbox.json"

    assert claim(outbox, "digest-2026-06-09-am") is True
    # An unconfirmed claim must NOT be auto-retried as a send
    assert claim(outbox, "digest-2026-06-09-am") is False


def test_confirmed_claim_is_terminal(tmp_path):
    outbox = tmp_path / "outbox.json"
    claim(outbox, "digest-2026-06-09-am")
    confirm(outbox, "digest-2026-06-09-am")

    assert claim(outbox, "digest-2026-06-09-am") is False


def test_failed_claim_releases_for_retry(tmp_path):
    outbox = tmp_path / "outbox.json"
    claim(outbox, "digest-2026-06-09-am")
    fail(outbox, "digest-2026-06-09-am", "SMTP timeout")

    assert claim(outbox, "digest-2026-06-09-am") is True


def test_fail_records_reason(tmp_path):
    outbox = tmp_path / "outbox.json"
    claim(outbox, "digest-2026-06-09-am")
    fail(outbox, "digest-2026-06-09-am", "SMTP timeout")

    records = json.loads(outbox.read_text())
    record = records["digest-2026-06-09-am"]
    assert record["status"] == "failed"
    assert record["note"] == "SMTP timeout"
    assert record["resolved_at"] is not None


def test_outbox_persists_across_reopen(tmp_path):
    outbox = tmp_path / "outbox.json"
    claim(outbox, "digest-2026-06-09-am")
    confirm(outbox, "digest-2026-06-09-am")

    # Every call reloads from disk -- a fresh "session" sees the same record
    records = json.loads(outbox.read_text())
    assert records["digest-2026-06-09-am"]["status"] == "confirmed"
    assert claim(outbox, "digest-2026-06-09-am") is False
    assert claim(outbox, "digest-2026-06-10-am") is True


def test_stale_claim_reclaimable_after_window(tmp_path):
    outbox = tmp_path / "outbox.json"
    claim(outbox, "digest-2026-06-09-am")

    # Age the claim past the stale window (crash-recovery path)
    records = json.loads(outbox.read_text())
    stale_time = datetime.now(timezone.utc) - timedelta(hours=25)
    records["digest-2026-06-09-am"]["claimed_at"] = stale_time.isoformat()
    outbox.write_text(json.dumps(records))

    assert claim(outbox, "digest-2026-06-09-am") is True


def test_confirm_without_claim_raises(tmp_path):
    outbox = tmp_path / "outbox.json"

    with pytest.raises(KeyError):
        confirm(outbox, "never-claimed")


def test_fail_without_claim_raises(tmp_path):
    outbox = tmp_path / "outbox.json"

    with pytest.raises(KeyError):
        fail(outbox, "never-claimed", "reason")


# --- eval_runner: weighted structural scoring --------------------------------

GOOD_BRIEFING = """\
# Morning Briefing

## Findings
- HIGH: Enforcement action announced against a major exchange [Source: agency release]
- MEDIUM: Stablecoin reserve attestation delayed a second consecutive quarter
- LOW: Minor protocol governance vote scheduled next week

## Analysis
Coverage was strong across primary feeds. The enforcement action is the
headline item; the attestation delay is a trend worth tracking because two
consecutive misses historically precede a restatement. Confidence: HIGH.

## Sources
- Agency press release
- Exchange status page
- Reserve attestation tracker

---
Health: Sources: 3 | Fallbacks: 0 | Quality: 9/10 | Runtime: 41s
""" + ("Context and supporting detail. " * 20)

DEGRADED_OUTPUT = "Brief unavailable. {HEAT_INDEX} [INSERT ANALYSIS] TBD"


def test_good_briefing_scores_high():
    result = score_output(GOOD_BRIEFING, BRIEFING_RUBRIC)

    assert result["score"] >= 85
    assert result["failed_checks"] == []
    assert result["checks_passed"] == result["checks_total"] == len(BRIEFING_RUBRIC)


def test_degraded_output_scores_low():
    result = score_output(DEGRADED_OUTPUT, BRIEFING_RUBRIC)

    assert result["score"] <= 25
    assert "no_placeholders" in result["failed_checks"]
    assert "substantive_length" in result["failed_checks"]


def test_score_weight_math():
    rubric = [
        ("passes_a", 3, regex_present(r"alpha")),
        ("passes_b", 2, min_length(5)),
        ("fails_c", 5, regex_present(r"omega")),
    ]

    result = score_output("alpha beta gamma", rubric)

    # passed weight 5 of total 10 -> exactly 50
    assert result["score"] == 50
    assert result["checks_passed"] == 2
    assert result["checks_total"] == 3
    assert result["passed_checks"] == ["passes_a", "passes_b"]
    assert result["failed_checks"] == ["fails_c"]


def test_all_checks_failing_is_a_valid_zero():
    rubric = [("never", 1, regex_present(r"zzz-not-present"))]

    assert score_output("artifact text", rubric)["score"] == 0


def test_empty_rubric_raises():
    with pytest.raises(ValueError):
        score_output("artifact text", [])


def test_non_positive_weight_raises():
    with pytest.raises(ValueError):
        score_output("artifact text", [("bad", 0, min_length(1))])
