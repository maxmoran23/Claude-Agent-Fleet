"""Evaluation harness: weighted structural scoring of published agent output.

Reference implementation of docs/patterns/evaluation-harness.md. The harness
is fully external to the agent -- nothing about the run is consulted, only the
artifact. Every check is a deterministic string operation: no model call, no
judgment, no variance between runs on the same input.

A rubric is a list of ``(name, weight, check)`` tuples where ``check`` is a
predicate ``Callable[[str], bool]``. Check factories cover the structural
failure modes worth catching (format drift, missing sections, placeholder
leaks, shrinkage):

- ``regex_present(pattern)``  -- pattern must match
- ``regex_absent(pattern)``   -- pattern must NOT match
- ``min_length(n)`` / ``max_length(n)`` -- shrinkage floor / runaway ceiling
- ``min_count(pattern, n)``   -- pattern must match at least n times
- ``count_between(pattern, lo, hi)`` -- match count within an inclusive range

``score_output`` computes ``100 * (weight of passed checks) / (total weight)``.
Example rubrics ship as data: ``BRIEFING_RUBRIC``, ``MARKET_BRIEF_RUBRIC``,
``REGULATORY_BRIEF_RUBRIC``. Stdlib only.
"""

from __future__ import annotations

import re
from typing import Callable

Check = Callable[[str], bool]
Rubric = list[tuple[str, int, Check]]


def regex_present(pattern: str) -> Check:
    """Check passes when the pattern matches anywhere in the artifact."""
    compiled = re.compile(pattern)
    return lambda text: compiled.search(text) is not None


def regex_absent(pattern: str) -> Check:
    """Check passes when the pattern matches nowhere -- placeholder/residue guard."""
    compiled = re.compile(pattern)
    return lambda text: compiled.search(text) is None


def min_length(n: int) -> Check:
    """Check passes when the artifact is at least n characters -- shrinkage floor."""
    return lambda text: len(text) >= n


def max_length(n: int) -> Check:
    """Check passes when the artifact is at most n characters -- runaway ceiling."""
    return lambda text: len(text) <= n


def min_count(pattern: str, n: int) -> Check:
    """Check passes when the pattern matches at least n times."""
    compiled = re.compile(pattern)
    return lambda text: len(compiled.findall(text)) >= n


def count_between(pattern: str, lo: int, hi: int) -> Check:
    """Check passes when the match count is within [lo, hi] inclusive."""
    compiled = re.compile(pattern)
    return lambda text: lo <= len(compiled.findall(text)) <= hi


def score_output(text: str, rubric: Rubric) -> dict:
    """Score an artifact against a rubric of weighted structural checks.

    Returns a dict mirroring the pattern's ``eval_scores`` row:

    - ``score`` -- 0-100, ``round(100 * passed_weight / total_weight)``
    - ``checks_passed`` / ``checks_total`` -- counts
    - ``passed_checks`` / ``failed_checks`` -- check names, rubric order

    A score of 0 on a present artifact is a valid result -- the harness
    working. What fails loudly instead: an empty rubric or a non-positive
    weight, both of which would make the score meaningless.
    """
    if not rubric:
        raise ValueError("rubric is empty -- a score against no checks is noise, not evidence")

    total_weight = 0
    passed_weight = 0
    passed_checks: list = []
    failed_checks: list = []

    for name, weight, check in rubric:
        if weight <= 0:
            raise ValueError(f"check {name!r} has non-positive weight {weight}")
        total_weight += weight
        if check(text):
            passed_weight += weight
            passed_checks.append(name)
        else:
            failed_checks.append(name)

    return {
        "score": round(100 * passed_weight / total_weight),
        "checks_passed": len(passed_checks),
        "checks_total": len(rubric),
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
    }


# --- Example rubrics (data, not code) -------------------------------------
# Each asserts the *shape* of a good artifact, not its conclusions.

#: Generic daily-briefing rubric: severity tags, a sources section, a
#: confidence rating, the standard health footer, and a sane section count.
BRIEFING_RUBRIC: Rubric = [
    ("severity_tags", 3, min_count(r"\b(CRITICAL|HIGH|MEDIUM|LOW)\b", 2)),
    ("sources_section", 2, regex_present(r"(?mi)^#{1,3}\s*Sources\b|^Sources:")),
    ("confidence_rating", 2, regex_present(r"Confidence:\s*(HIGH|MEDIUM|LOW)")),
    ("health_footer", 2, regex_present(r"Quality:\s*([1-9]|10)/10")),
    ("section_count_in_range", 2, count_between(r"(?m)^#{1,3}\s", 3, 15)),
    ("no_placeholders", 3, regex_absent(r"\{[A-Z_]+\}|\[INSERT|\bTBD\b")),
    ("substantive_length", 2, min_length(500)),
]

#: Market-brief rubric, mirroring the pattern doc's market-monitor example.
MARKET_BRIEF_RUBRIC: Rubric = [
    ("heat_index_present", 3, regex_present(r"Heat Index:\s*[0-9]+/100")),
    ("sentiment_named", 3, regex_present(r"Sentiment:\s*(RISK-ON|RISK-OFF|NEUTRAL)")),
    ("live_numbers", 3, min_count(r"\$[0-9][0-9,.]*", 3)),
    ("health_footer", 2, regex_present(r"Quality:\s*([1-9]|10)/10")),
    ("no_placeholders", 3, regex_absent(r"\{[A-Z_]+\}")),
    ("substantive_length", 2, min_length(700)),
]

#: Regulatory-brief rubric, mirroring the pattern doc's regulatory example.
REGULATORY_BRIEF_RUBRIC: Rubric = [
    ("severity_tags", 3, min_count(r"\b(CRITICAL|HIGH|MEDIUM|LOW)\b", 2)),
    ("deadline_section", 2, regex_present(r"(?m)^#{1,3}\s*Upcoming Deadlines")),
    ("citation_present", 3, min_count(r"\[Source:", 1)),
    ("no_template_residue", 3, regex_absent(r"\[INSERT|\bTBD\b|XXX")),
    ("not_truncated", 2, min_length(500)),
]
