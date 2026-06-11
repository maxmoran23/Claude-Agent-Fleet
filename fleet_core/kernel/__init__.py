"""Agent-kernel reference implementations (KERNEL_VERSION = "2.0").

Runnable, stdlib-only reference implementations of the production patterns
documented in docs/patterns/. They exist so the pattern docs are backed by
working code, not just prose:

- ``state``       -- step 0 / step 7 state authority pair
                     (docs/patterns/state-management.md, agent-kernel.md)
- ``outbox``      -- claim/confirm/fail idempotency protocol
                     (docs/patterns/idempotency-outbox.md)
- ``eval_runner`` -- weighted structural scoring of published output
                     (docs/patterns/evaluation-harness.md)

The production fleet ships these as CLI helpers (prompt-driven agents invoke
shell commands more reliably than they import modules); this package is the
library variant noted in the agent-kernel pattern, suited to agents that share
a Python runtime.
"""

from .eval_runner import (
    BRIEFING_RUBRIC,
    MARKET_BRIEF_RUBRIC,
    REGULATORY_BRIEF_RUBRIC,
    count_between,
    max_length,
    min_count,
    min_length,
    regex_absent,
    regex_present,
    score_output,
)
from .outbox import claim, confirm, fail
from .state import KERNEL_VERSION, load_state, persist_state

__all__ = [
    "BRIEFING_RUBRIC",
    "KERNEL_VERSION",
    "MARKET_BRIEF_RUBRIC",
    "REGULATORY_BRIEF_RUBRIC",
    "claim",
    "confirm",
    "count_between",
    "fail",
    "load_state",
    "max_length",
    "min_count",
    "min_length",
    "persist_state",
    "regex_absent",
    "regex_present",
    "score_output",
]
