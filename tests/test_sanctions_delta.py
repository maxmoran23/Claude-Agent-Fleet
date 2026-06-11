"""Unit tests for the sanctions list monitor's pure parse/diff functions."""

from __future__ import annotations

from agents.sanctions_list_monitor.agent import (
    cap_delta,
    compute_delta,
    parse_sdn_entries,
)

CSV_PRIOR = (
    '1001,"ALPHA TRADING CO.","-0- ","SDGT",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
    '1002,"BRAVO, Carlos","individual","CYBER2",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
    '1003,"CHARLIE EXCHANGE LLC","-0- ","DPRK3] [CYBER2",-0-,-0-,-0-,-0-,-0-,-0-,-0-,'
    '"Digital Currency Address - XBT 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa."\n'
)

CSV_CURRENT = (
    '1001,"ALPHA TRADING CO.","-0- ","SDGT",-0-,-0-,-0-,-0-,-0-,-0-,-0-,'
    '"Digital Currency Address - ETH 0x7F367cC41522cE07553e823bf3be79A889DEbe1B."\n'
    '1003,"CHARLIE EXCHANGE LLC","-0- ","DPRK3] [CYBER2",-0-,-0-,-0-,-0-,-0-,-0-,-0-,'
    '"Digital Currency Address - XBT 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa."\n'
    '1004,"DELTA SHIPPING SA","-0- ","IFSR",-0-,-0-,-0-,-0-,-0-,-0-,-0-,-0-\n'
)


# --- parse_sdn_entries --------------------------------------------------------


def test_parse_extracts_uid_name_programs():
    entries = parse_sdn_entries(CSV_PRIOR)
    assert set(entries) == {"1001", "1002", "1003"}
    assert entries["1001"]["name"] == "ALPHA TRADING CO."
    assert entries["1001"]["programs"] == ["SDGT"]
    assert entries["1002"]["entry_type"] == "individual"


def test_parse_splits_multi_program_field():
    entries = parse_sdn_entries(CSV_PRIOR)
    assert entries["1003"]["programs"] == ["DPRK3", "CYBER2"]


def test_parse_normalizes_null_remarks():
    entries = parse_sdn_entries(CSV_PRIOR)
    assert entries["1001"]["remarks"] == ""
    assert "Digital Currency Address" in entries["1003"]["remarks"]


def test_parse_skips_malformed_and_marker_rows():
    noisy = CSV_PRIOR + "\nEnd of File\n,,,\nnot-a-uid,X,Y,Z\n"
    assert set(parse_sdn_entries(noisy)) == {"1001", "1002", "1003"}


def test_parse_row_hash_changes_with_content():
    prior = parse_sdn_entries(CSV_PRIOR)
    current = parse_sdn_entries(CSV_CURRENT)
    assert prior["1001"]["row_hash"] != current["1001"]["row_hash"]
    assert prior["1003"]["row_hash"] == current["1003"]["row_hash"]


# --- compute_delta -------------------------------------------------------------


def test_compute_delta_detects_added_removed_modified():
    delta = compute_delta(parse_sdn_entries(CSV_PRIOR), parse_sdn_entries(CSV_CURRENT))
    assert [item["uid"] for item in delta["added"]] == ["1004"]
    assert [item["uid"] for item in delta["removed"]] == ["1002"]
    assert [item["uid"] for item in delta["modified"]] == ["1001"]


def test_compute_delta_carries_name_and_programs():
    delta = compute_delta(parse_sdn_entries(CSV_PRIOR), parse_sdn_entries(CSV_CURRENT))
    added = delta["added"][0]
    assert added["name"] == "DELTA SHIPPING SA"
    assert added["programs"] == ["IFSR"]
    removed = delta["removed"][0]
    assert removed["name"] == "BRAVO, Carlos"


def test_compute_delta_modified_uses_current_content():
    delta = compute_delta(parse_sdn_entries(CSV_PRIOR), parse_sdn_entries(CSV_CURRENT))
    assert "ETH 0x7F367cC4" in delta["modified"][0]["remarks"]


def test_compute_delta_identical_snapshots_is_empty():
    entries = parse_sdn_entries(CSV_PRIOR)
    delta = compute_delta(entries, entries)
    assert delta == {"added": [], "removed": [], "modified": []}


def test_compute_delta_sorts_by_numeric_uid():
    prior: dict = {}
    current = {
        uid: {"name": f"E{uid}", "entry_type": "entity", "programs": [], "remarks": "", "row_hash": uid}
        for uid in ("99", "100", "12")
    }
    delta = compute_delta(prior, current)
    assert [item["uid"] for item in delta["added"]] == ["12", "99", "100"]


# --- cap_delta -------------------------------------------------------------------


def _synthetic_delta(added: int, modified: int, removed: int) -> dict:
    def items(prefix: str, count: int) -> list[dict]:
        return [
            {"uid": f"{prefix}{i}", "name": "X", "entry_type": "entity", "programs": [], "remarks": ""}
            for i in range(count)
        ]

    return {"added": items("a", added), "modified": items("m", modified), "removed": items("r", removed)}


def test_cap_delta_under_limit_is_untruncated():
    delta = _synthetic_delta(added=3, modified=2, removed=1)
    capped, truncated = cap_delta(delta, limit=10)
    assert not truncated
    assert capped == delta


def test_cap_delta_prioritizes_additions_then_modifications():
    delta = _synthetic_delta(added=4, modified=4, removed=4)
    capped, truncated = cap_delta(delta, limit=6)
    assert truncated
    assert len(capped["added"]) == 4
    assert len(capped["modified"]) == 2
    assert len(capped["removed"]) == 0
