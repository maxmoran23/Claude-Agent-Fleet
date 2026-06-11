"""Structural lint tests for the prompt-only agent specs in examples/.

Every examples/<name>/AGENT.md follows a canonical skeleton. These tests
enforce the elements verified to hold for all 22 specs (checked 2026-06-10):

- YAML frontmatter (``---`` fences) containing a ``model:`` key
- Exactly one H1 title
- A ``> `` blockquote descriptor between the H1 and the Role section
- A ``## Role`` section
- A ``## Step 0 — Load State`` section (exact heading in all specs)
- A ``## Step N — Quality Self-Assessment`` section
- A ``## Step N — Persist State`` section
- A ``## Configuration`` section
- At least one mention of a fallback (fallback chain / fallback handling)
- Load State appears before Quality Self-Assessment before Persist State

Step numbering for Quality Self-Assessment (Step 3/4/5) and Persist State
(Step 6/7/8) legitimately varies with each agent's pipeline length, so the
rules pin the section names, not the step numbers.

Content hygiene rules (also verified clean across all 22):
- No emoji characters (typographic symbols like — ▲ ▼ ─ → ± Δ are allowed)
- No word-boundary "EDD" or "Enhanced Due Diligence" strings
- No real Slack IDs (channel/file/team/user/DM ID shapes)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

EXAMPLE_SPECS = sorted(EXAMPLES_DIR.glob("*/AGENT.md"))

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
H1_RE = re.compile(r"^# .+$", re.MULTILINE)
SLACK_ID_RE = re.compile(r"\b[CFTUD]0[A-Z0-9]{8,}\b")
EDD_RE = re.compile(r"\bEDD\b|Enhanced Due Diligence", re.IGNORECASE)

# Emoji blocks only — deliberately excludes the typographic symbols the specs
# legitimately use (em/en dashes, arrows U+2192, box drawing U+2500,
# triangles U+25B2/U+25BC, plus-minus, Greek letters).
EMOJI_RE = re.compile(
    "["
    "\U0001f000-\U0001faff"  # emoji, symbols, pictographs, supplemental
    "☀-➿"  # misc symbols + dingbats (covers checkmarks, warning signs)
    "⬀-⯿"  # misc symbols and arrows (covers blue circle, stars)
    "\U0001f1e6-\U0001f1ff"  # regional indicators (flags)
    "️"  # variation selector-16 (emoji presentation)
    "]"
)


FENCED_BLOCK_RE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)


def _spec_id(path: Path) -> str:
    return path.parent.name


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so template headings (e.g. the report
    skeleton inside Step 4 — Format Output) don't count as document
    structure."""
    return FENCED_BLOCK_RE.sub("", text)


def test_examples_directory_is_populated():
    assert len(EXAMPLE_SPECS) >= 20, (
        f"Expected the full example library under {EXAMPLES_DIR}, "
        f"found {len(EXAMPLE_SPECS)} AGENT.md files"
    )


@pytest.fixture(params=EXAMPLE_SPECS, ids=_spec_id)
def spec_text(request) -> str:
    return request.param.read_text(encoding="utf-8")


# --- Canonical skeleton --------------------------------------------------------


def test_frontmatter_with_model_key(spec_text):
    match = FRONTMATTER_RE.match(spec_text)
    assert match, "Spec must open with a ----fenced YAML frontmatter block"
    assert re.search(
        r"^model:\s*\S+", match.group(1), re.MULTILINE
    ), "Frontmatter must declare a model: key"


def test_exactly_one_h1(spec_text):
    assert len(H1_RE.findall(_strip_code_fences(spec_text))) == 1


def test_blockquote_descriptor_after_h1(spec_text):
    h1 = H1_RE.search(spec_text)
    role = spec_text.find("\n## Role")
    assert role != -1, "Spec must have a ## Role section"
    between = spec_text[h1.end() : role]
    assert re.search(
        r"^> .+$", between, re.MULTILINE
    ), "Spec must have a > blockquote descriptor between the H1 and ## Role"


def test_required_sections_present(spec_text):
    assert re.search(r"^## Role$", spec_text, re.MULTILINE)
    assert re.search(r"^## Step 0 — Load State$", spec_text, re.MULTILINE)
    assert re.search(
        r"^## Step \d+ — Quality Self-Assessment$", spec_text, re.MULTILINE
    )
    assert re.search(r"^## Step \d+ — Persist State$", spec_text, re.MULTILINE)
    assert re.search(r"^## Configuration$", spec_text, re.MULTILINE)


def test_mentions_fallback(spec_text):
    assert re.search(r"fallback", spec_text, re.IGNORECASE)


def test_pipeline_section_ordering(spec_text):
    load = spec_text.index("## Step 0 — Load State")
    quality = re.search(
        r"^## Step \d+ — Quality Self-Assessment$", spec_text, re.MULTILINE
    ).start()
    persist = re.search(
        r"^## Step \d+ — Persist State$", spec_text, re.MULTILINE
    ).start()
    assert load < quality < persist


# --- Content hygiene -----------------------------------------------------------


def test_no_emoji(spec_text):
    hits = sorted({hex(ord(c)) for c in EMOJI_RE.findall(spec_text)})
    assert not hits, f"Emoji characters found: {hits}"


def test_no_edd_terminology(spec_text):
    hits = [m.group() for m in EDD_RE.finditer(spec_text)]
    assert not hits, f"EDD terminology found: {hits}"


def test_no_real_slack_ids(spec_text):
    hits = [m.group() for m in SLACK_ID_RE.finditer(spec_text)]
    assert not hits, f"Slack-ID-shaped strings found: {hits}"
