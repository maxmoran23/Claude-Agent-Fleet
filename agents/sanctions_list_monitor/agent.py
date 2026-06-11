#!/usr/bin/env python3
"""Sanctions List Monitor — daily OFAC SDN list delta check, classified and briefed."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fleet_core import load_config, publish_to_slack, run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("sanctions_list_monitor")

PROMPT_PATH = Path(__file__).parent / "prompt.md"
STATE_PATH = Path(__file__).parent / "state" / "last-run.json"

SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
FETCH_TIMEOUT_SECONDS = 60
MAX_CHANGES_FOR_ANALYSIS = 200
REMARKS_MAX_CHARS = 300

# sdn.csv ships without a header row; column positions per OFAC's published file spec.
UID_COL = 0
NAME_COL = 1
TYPE_COL = 2
PROGRAM_COL = 3
REMARKS_COL = 11

NULL_FIELD = "-0-"


def fetch_sdn_csv(url: str = SDN_CSV_URL) -> str:
    """Download the current SDN list from the official public endpoint.

    Raises urllib.error.URLError (or a subclass) on network failure — the
    caller is responsible for the degraded-run fallback.
    """
    logger.info("fetching SDN list url=%s", url)
    request = urllib.request.Request(
        url, headers={"User-Agent": "claude-agent-fleet/0.2 (sanctions-list-monitor)"}
    )
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_programs(raw: str) -> list[str]:
    """Split the SDN program field ("CYBER2] [SDGT" style) into a clean list."""
    stripped = raw.strip().strip("[]")
    return [part.strip() for part in stripped.split("] [") if part.strip() and part.strip() != NULL_FIELD]


def parse_sdn_entries(csv_text: str) -> dict[str, dict]:
    """Parse SDN CSV text into {uid: {name, entry_type, programs, remarks, row_hash}}.

    Pure function — no network, no filesystem. Rows that are malformed or lack
    a numeric uid (blank lines, end-of-file markers) are skipped.
    """
    entries: dict[str, dict] = {}
    for row in csv.reader(io.StringIO(csv_text)):
        if len(row) <= PROGRAM_COL or not row[UID_COL].strip().isdigit():
            continue
        uid = row[UID_COL].strip()
        remarks = row[REMARKS_COL].strip() if len(row) > REMARKS_COL else ""
        if remarks == NULL_FIELD:
            remarks = ""
        entries[uid] = {
            "name": row[NAME_COL].strip(),
            "entry_type": row[TYPE_COL].strip().strip("-0").strip() or "unknown",
            "programs": _parse_programs(row[PROGRAM_COL]),
            "remarks": remarks[:REMARKS_MAX_CHARS],
            "row_hash": hashlib.sha256(",".join(row).encode("utf-8")).hexdigest()[:16],
        }
    return entries


def compute_delta(prior: dict[str, dict], current: dict[str, dict]) -> dict:
    """Compute added/removed/modified entries between two parsed snapshots.

    Pure function. Keys are SDN uids; modification means the uid persists but
    its row content hash changed (new aliases, identifiers, addresses).
    Results are sorted by numeric uid for deterministic output.
    """

    def _item(uid: str, entry: dict) -> dict:
        return {
            "uid": uid,
            "name": entry["name"],
            "entry_type": entry["entry_type"],
            "programs": entry["programs"],
            "remarks": entry["remarks"],
        }

    added_uids = sorted(set(current) - set(prior), key=int)
    removed_uids = sorted(set(prior) - set(current), key=int)
    modified_uids = sorted(
        (uid for uid in set(current) & set(prior) if current[uid]["row_hash"] != prior[uid]["row_hash"]),
        key=int,
    )

    return {
        "added": [_item(uid, current[uid]) for uid in added_uids],
        "removed": [_item(uid, prior[uid]) for uid in removed_uids],
        "modified": [_item(uid, current[uid]) for uid in modified_uids],
    }


def cap_delta(delta: dict, limit: int = MAX_CHANGES_FOR_ANALYSIS) -> tuple[dict, bool]:
    """Cap the delta to at most `limit` total changes for analysis.

    Pure function. Additions are kept first, then modifications, then removals.
    Returns the capped delta and whether truncation occurred.
    """
    capped: dict = {"added": [], "removed": [], "modified": []}
    remaining = limit
    for key in ("added", "modified", "removed"):
        capped[key] = delta[key][:remaining]
        remaining -= len(capped[key])
    truncated = sum(len(delta[k]) for k in delta) > limit
    return capped, truncated


def load_state(path: Path) -> dict | None:
    """Load the prior snapshot state, or None if no baseline exists yet."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as err:
        logger.warning("could not read state file %s: %s — treating as baseline run", path, err)
        return None


def save_state(path: Path, entries: dict[str, dict], content_hash: str, delta: dict | None) -> None:
    """Persist the new snapshot (uid map + content hash + timestamp) for the next run."""
    now = datetime.now(timezone.utc).isoformat()
    state = {
        "last_run_timestamp": now,
        "list_snapshots": {
            "ofac_sdn": {
                "entry_count": len(entries),
                "content_hash": content_hash,
                "pulled_at": now,
            }
        },
        "last_delta": {
            "added": len(delta["added"]) if delta else 0,
            "removed": len(delta["removed"]) if delta else 0,
            "modified": len(delta["modified"]) if delta else 0,
        },
        "entries": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    logger.info("state persisted path=%s entries=%d", path, len(entries))


def main() -> int:
    config = load_config()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header = f":scroll: *Sanctions List Monitor — {today}*"

    try:
        csv_text = fetch_sdn_csv()
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        logger.error("SDN fetch failed: %s", err)
        publish_to_slack(
            config=config,
            text=(
                f"{header}\n\nDEGRADED RUN — could not retrieve the OFAC SDN list from "
                f"treasury.gov ({err}). Prior snapshot retained; the delta will be computed "
                "on the next successful run."
            ),
        )
        return 0

    content_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    current = parse_sdn_entries(csv_text)
    state = load_state(STATE_PATH)

    if state is None:
        save_state(STATE_PATH, current, content_hash, delta=None)
        publish_to_slack(
            config=config,
            text=(
                f"{header}\n\nBaseline established — {len(current)} SDN entries snapshotted "
                f"(content hash `{content_hash[:16]}`). Delta reporting starts next run."
            ),
        )
        logger.info("baseline established entries=%d", len(current))
        return 0

    prior_hash = state.get("list_snapshots", {}).get("ofac_sdn", {}).get("content_hash")
    prior_entries = state.get("entries", {})

    delta = compute_delta(prior_entries, current)
    total_changes = sum(len(delta[k]) for k in delta)

    if content_hash == prior_hash or total_changes == 0:
        save_state(STATE_PATH, current, content_hash, delta=delta)
        publish_to_slack(
            config=config,
            text=f"{header}\n\nNo changes — content hash matches prior snapshot ({len(current)} entries).",
        )
        logger.info("no changes entries=%d", len(current))
        return 0

    capped, truncated = cap_delta(delta)
    truncation_note = (
        f" The delta was truncated to the first {MAX_CHANGES_FOR_ANALYSIS} changes "
        f"of {total_changes} total — note this in the briefing."
        if truncated
        else ""
    )
    user_input = (
        f"Produce the sanctions list delta briefing for {today}.\n\n"
        f"List: OFAC SDN. Prior entries: {len(prior_entries)}. Current entries: {len(current)}. "
        f"Added: {len(delta['added'])}. Removed: {len(delta['removed'])}. "
        f"Modified: {len(delta['modified'])}.\n\n"
        f"Structured delta (JSON):\n```json\n{json.dumps(capped, indent=2)}\n```\n\n"
        f"Classify and brief per the format in your system prompt.{truncation_note}"
    )

    result = run_agent(
        config=config,
        system_prompt=prompt,
        user_input=user_input,
        max_tokens=2048,
    )

    body = f"{header}\n\n{result.text}"
    publish_to_slack(config=config, text=body)
    save_state(STATE_PATH, current, content_hash, delta=delta)
    logger.info(
        "done changes=%d input_tokens=%d output_tokens=%d model=%s",
        total_changes,
        result.input_tokens,
        result.output_tokens,
        result.model,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
