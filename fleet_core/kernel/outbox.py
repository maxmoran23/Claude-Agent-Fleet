"""Idempotency outbox: claim/confirm/fail protocol for non-idempotent actions.

Reference implementation of docs/patterns/idempotency-outbox.md, backed by a
JSON file instead of the production SQLite ``send_log`` table.

The ordering is the entire pattern: **claim before the attempt, confirm only
after verifiable success.** From inside a run, "the send failed" and "the send
succeeded but the confirmation was lost" are indistinguishable -- so
deduplication lives in this durable file, not in the agent's perception of the
result.

State machine per action key:

- ``claim`` returns True and records the intent, or returns False if the key
  is already confirmed (terminal) or carries an unresolved claim younger than
  ``STALE_CLAIM_HOURS``. **False means skip -- an unconfirmed claim must never
  be auto-retried as a send.**
- ``confirm`` marks verified success. Terminal: all future claims return False.
- ``fail`` records an explicit, diagnosed failure -- the claim releases
  immediately so a retry can proceed.
- A claim left unresolved (crash, lost confirmation) blocks re-claims for
  ``STALE_CLAIM_HOURS``, then becomes re-claimable so a wedged key cannot
  block tomorrow's action.

An unreadable outbox file raises rather than guessing: when the outbox cannot
be consulted, the safe default is to not send. Stdlib only.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

STATUS_CLAIMED = "claimed"
STATUS_CONFIRMED = "confirmed"
STATUS_FAILED = "failed"

STALE_CLAIM_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load(outbox_path: Path) -> dict:
    """Load the outbox file. Raises on undecodable content -- never send blind."""
    if not outbox_path.exists():
        return {}
    with open(outbox_path, encoding="utf-8") as fh:
        records = json.load(fh)
    if not isinstance(records, dict):
        raise ValueError(f"outbox file {outbox_path} does not contain a JSON object")
    return records


def _write(outbox_path: Path, records: dict) -> None:
    """Atomic write: temp file in the same directory, then os.replace."""
    outbox_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=outbox_path.parent, prefix=f".{outbox_path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(records, indent=2, sort_keys=True))
        os.replace(tmp_name, outbox_path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise


def _claim_is_stale(record: dict) -> bool:
    claimed_at = datetime.fromisoformat(record["claimed_at"])
    return _now() - claimed_at > timedelta(hours=STALE_CLAIM_HOURS)


def claim(outbox_path: str | Path, action_key: str) -> bool:
    """Record intent to perform a non-idempotent action. Call BEFORE the attempt.

    Returns True if the claim was recorded and the action may proceed.
    Returns False if the action must be skipped:

    - the key is already confirmed (terminal -- the action already happened), or
    - an unresolved claim younger than ``STALE_CLAIM_HOURS`` exists (an earlier
      attempt may have succeeded with its confirmation lost; do not re-send).

    A failed claim or a stale unresolved claim is re-claimable.
    """
    path = Path(outbox_path)
    records = _load(path)
    existing = records.get(action_key)

    if existing is not None:
        status = existing.get("status")
        if status == STATUS_CONFIRMED:
            logger.info("outbox: %s already confirmed -- skip", action_key)
            return False
        if status == STATUS_CLAIMED and not _claim_is_stale(existing):
            logger.info("outbox: %s has an unresolved claim -- skip, do not re-send", action_key)
            return False

    records[action_key] = {
        "status": STATUS_CLAIMED,
        "claimed_at": _now().isoformat(),
        "resolved_at": None,
        "note": None,
    }
    _write(path, records)
    logger.info("outbox: claimed %s", action_key)
    return True


def confirm(outbox_path: str | Path, action_key: str) -> None:
    """Mark an action as verifiably succeeded. Call only AFTER verified success.

    Terminal state: every future claim on this key returns False. Raises
    KeyError if the key was never claimed -- confirming an unclaimed action is
    a protocol violation worth surfacing.
    """
    path = Path(outbox_path)
    records = _load(path)
    if action_key not in records:
        raise KeyError(f"cannot confirm unclaimed action key: {action_key!r}")

    records[action_key]["status"] = STATUS_CONFIRMED
    records[action_key]["resolved_at"] = _now().isoformat()
    _write(path, records)
    logger.info("outbox: confirmed %s", action_key)


def fail(outbox_path: str | Path, action_key: str, reason: str) -> None:
    """Record an explicit, diagnosed failure, releasing the claim for retry.

    Only call this for failures the agent has actually diagnosed (e.g. an SMTP
    timeout). A lost confirmation is NOT a diagnosed failure -- leave the claim
    standing and let the stale-claim window handle recovery. Raises KeyError if
    the key was never claimed.
    """
    path = Path(outbox_path)
    records = _load(path)
    if action_key not in records:
        raise KeyError(f"cannot fail unclaimed action key: {action_key!r}")

    records[action_key]["status"] = STATUS_FAILED
    records[action_key]["resolved_at"] = _now().isoformat()
    records[action_key]["note"] = reason
    _write(path, records)
    logger.info("outbox: failed %s (%s)", action_key, reason)
