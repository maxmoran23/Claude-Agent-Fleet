"""State authority helpers: the step 0 (load) / step 7 (persist) pair.

Reference implementation of the authority tier described in
docs/patterns/state-management.md and docs/patterns/agent-kernel.md:

- ``load_state`` returns an explicit status (``loaded`` / ``first_run`` /
  ``corrupt``) instead of guessing. A corrupt state file is quarantined with a
  timestamp suffix -- preserved for manual recovery, never repaired or
  overwritten in place -- and the agent proceeds with an empty baseline.
- ``persist_state`` writes atomically (temp file + ``os.replace``), stamps the
  payload with an ISO-8601 ``last_run_timestamp`` and ``kernel_version``, and
  keeps a ring of the last 30 run snapshots under ``state/history/``.

Stdlib only. The per-agent layout these helpers own:

    {agent_dir}/state/
      state.json      current authoritative state
      history/        last-30-runs snapshot ring
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

KERNEL_VERSION = "2.0"

STATUS_LOADED = "loaded"
STATUS_FIRST_RUN = "first_run"
STATUS_CORRUPT = "corrupt"

HISTORY_RING_SIZE = 30

_STATE_FILENAME = "state.json"


def _state_path(agent_dir: str | Path) -> Path:
    return Path(agent_dir) / "state" / _STATE_FILENAME


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _file_stamp(now: datetime) -> str:
    """Sortable, filename-safe UTC timestamp (microsecond precision)."""
    return now.strftime("%Y%m%dT%H%M%S%f")


def _quarantine(state_path: Path) -> Path:
    """Move a corrupt state file aside, preserving it for manual recovery."""
    quarantine_path = state_path.with_name(f"{_STATE_FILENAME}.corrupt-{_file_stamp(_utc_now())}")
    counter = 1
    while quarantine_path.exists():
        quarantine_path = quarantine_path.with_name(f"{quarantine_path.name}-{counter}")
        counter += 1
    os.replace(state_path, quarantine_path)
    return quarantine_path


def load_state(agent_dir: str | Path) -> dict:
    """Load an agent's authoritative state with an explicit status (step 0).

    Returns a dict with:

    - ``status`` -- ``"loaded"``, ``"first_run"``, or ``"corrupt"``
    - ``state`` -- the parsed state dict (empty baseline on first run or corruption)
    - ``quarantined_to`` -- only on corruption: where the bad file was preserved

    Never raises on a missing or undecodable state file. A file that exists but
    fails to parse (or does not contain a JSON object) is renamed to
    ``state.json.corrupt-{timestamp}`` so the next persist cannot blow away the
    only possibly-recoverable copy.
    """
    state_path = _state_path(agent_dir)

    if not state_path.exists():
        logger.info("no state file at %s -- first run", state_path)
        return {"status": STATUS_FIRST_RUN, "state": {}}

    try:
        with open(state_path, encoding="utf-8") as fh:
            loaded = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError):
        loaded = None

    if not isinstance(loaded, dict):
        quarantined_to = _quarantine(state_path)
        logger.warning(
            "corrupt state file quarantined %s -> %s -- treating as first run",
            state_path,
            quarantined_to,
        )
        return {"status": STATUS_CORRUPT, "state": {}, "quarantined_to": str(quarantined_to)}

    return {"status": STATUS_LOADED, "state": loaded}


def persist_state(agent_dir: str | Path, state: dict) -> dict:
    """Persist an agent's authoritative state atomically (step 7).

    In order:

    1. Stamps the payload with ``last_run_timestamp`` (ISO-8601 UTC) and
       ``kernel_version``, so any state file found on disk self-identifies.
    2. Serializes before touching disk -- a non-serializable payload fails
       loudly with the previous state file intact.
    3. Writes atomically: temp file in the same directory, then ``os.replace``
       over ``state/state.json``. A crash mid-write leaves the previous state
       untouched, never a half-written file.
    4. Snapshots the new state into ``state/history/`` and prunes the ring to
       the most recent ``HISTORY_RING_SIZE`` runs.

    Returns the stamped state dict. Raises on any authority-write failure --
    per the pattern, there is no acceptable degraded mode for losing memory.
    """
    if not isinstance(state, dict):
        raise TypeError(f"state must be a dict, got {type(state).__name__}")

    now = _utc_now()
    stamped = dict(state)
    stamped["last_run_timestamp"] = now.isoformat()
    stamped["kernel_version"] = KERNEL_VERSION

    payload = json.dumps(stamped, indent=2, sort_keys=True)

    state_path = _state_path(agent_dir)
    history_dir = state_path.parent / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    _atomic_write(state_path, payload)
    _snapshot_history(history_dir, payload, now)

    logger.info("persisted state to %s (%d keys)", state_path, len(stamped))
    return stamped


def _atomic_write(target: Path, payload: str) -> None:
    """Write payload to target via temp file + os.replace; clean up on failure."""
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_name, target)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise


def _snapshot_history(history_dir: Path, payload: str, now: datetime) -> None:
    """Append a snapshot to the history ring and prune to HISTORY_RING_SIZE."""
    snapshot_path = history_dir / f"state-{_file_stamp(now)}.json"
    counter = 1
    while snapshot_path.exists():
        snapshot_path = history_dir / f"state-{_file_stamp(now)}-{counter}.json"
        counter += 1

    _atomic_write(snapshot_path, payload)

    snapshots = sorted(history_dir.glob("state-*.json"))
    for stale in snapshots[:-HISTORY_RING_SIZE]:
        stale.unlink()
