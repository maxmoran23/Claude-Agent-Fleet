# Contributing

Guidelines for contributing example agents, patterns, or documentation to this framework.

---

## What Belongs in This Repository

This repository is a **reference framework** for building autonomous agent fleets on Claude Code. It contains:

- **Example agents** that demonstrate production-ready patterns
- **Pattern documentation** explaining reusable architectural approaches
- **Case studies** showing end-to-end flows
- **Schemas** defining data structures and conventions
- **Operational documentation** (architecture, fleet ops, quickstart)

Contributions that fit this scope are welcome. Contributions that are highly specific to one deployment (e.g., private integration credentials, specific Slack workspace setup) belong in your own downstream repository that builds on this framework.

---

## Contribution Types

### New Example Agent

A new example agent should:

- Demonstrate a distinct architectural pattern not already covered by existing examples
- Follow the full production pattern (Step 0 Load State through Step 7 Persist State)
- Include a fallback chain, quality self-assessment, and health footer
- Use generic, illustrative data — no personal, company-specific, or integration-specific references
- Be fully self-contained — no external dependencies beyond what Claude Code provides natively, OR clearly document optional MCP integrations

Structure:
```
examples/[agent-name]/
├── AGENT.md         # The skill file
└── README.md        # Optional: explains the pattern demonstrated
```

See existing examples for format and tone.

### New Pattern Document

A pattern document should:

- Describe a reusable architectural approach (not a specific implementation)
- Include: the problem, the pattern, concrete examples, consequences, when to use, when to skip
- Cross-reference related patterns
- Be standalone-readable (don't require reading the full repo to make sense)

Place in `docs/patterns/[pattern-name].md`.

### New Case Study

A case study should:

- Walk through an end-to-end scenario using the framework
- Use fabricated but plausible data — never real enforcement actions, real addresses, or real entities
- Show the timeline clearly (T+N minutes format for time-sensitive examples)
- Cross-reference the patterns demonstrated
- End with "what this demonstrates" distilling the takeaways

Place in `docs/case-studies/[scenario-name].md`.

### Schema Addition or Change

Schema changes (data-layer tables, frontmatter fields, canvas sections) require:

- Clear migration notes if it's a breaking change
- Update to the auto-repair ruleset if applicable
- Example usage in at least one of the example agents

---

## Style Conventions

### Tone

Direct and specific. No marketing fluff. Production-oriented framing.

### Formatting

- Markdown with standard GitHub-flavored extensions
- Tables for comparisons and parameter references
- Code blocks for literal schema, URLs, file paths
- Short paragraphs — if a paragraph runs over ~5 lines, consider splitting
- Bulleted lists for enumerations, prose for explanation

### Voice

Third-person neutral for documentation. "The agent does X" rather than "I do X" or "you do X".

Second-person ("you") is acceptable in how-to sections (CONTRIBUTING, QUICKSTART) where the reader is being guided.

### Headings

Use ATX-style (`#`) with sentence case. Progressive hierarchy: h1 for the document title, h2 for major sections, h3 for subsections. Avoid deeper nesting.

### Examples

All code and data examples must use generic, illustrative values:

- Addresses: `0xABC...1234`, `0xDEF...9999`
- Dates: `[DATE]`, `[ISO timestamp]`, `2026-04-19` (within the current year)
- Entity names: `[entity]`, `monitored-entity-01`, fictional company names
- Penalty amounts, TVL, prices: illustrative values only

Never use real enforcement matters, real addresses that exist, real entity names, or real regulatory case references as examples.

---

## The Genericization Firewall

This is non-negotiable: **no contribution may include**

- Personal names or identifiers
- Employer names or any company-specific references
- Slack channel IDs, canvas IDs, user IDs, workspace IDs from any specific deployment
- Notion database IDs, data source IDs, page IDs
- Calendar IDs or meeting references
- Email addresses (personal or professional)
- Real addresses (on-chain or off-chain)
- Real regulatory case references or real enforcement actions
- Real entity names from private workflows
- API keys, tokens, credentials, or any secret material

If a contribution references data from a private deployment, that reference must be replaced with a generic equivalent before submission.

---

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with clear commit messages
4. Run the genericization scan (see below) before opening the PR
5. Open a PR with a clear description of what's being added or changed
6. Address feedback in follow-up commits

### Commit Messages

Format:
```
[type]: [short summary]

[Longer explanation if needed — what changed and why.
Multiple paragraphs are fine for substantive changes.]
```

Types: `feat` (new content), `fix` (correction), `docs` (docs-only change), `refactor` (restructuring without content change).

### Genericization Scan

Before committing, scan your changes for personal or identifying information:

```bash
# Run from repo root
grep -rE "(@(gmail|outlook|icloud|yahoo)\.com|C0[A-Z0-9]{8,}|F0[A-Z0-9]{8,}|U0[A-Z0-9]{8,})" \
  --include="*.md" --include="*.sql" \
  examples/ docs/ schemas/
```

Any hit requires review before submission. The intent is to catch accidental leakage of IDs, email addresses, or deployment-specific references.

---

## What Gets Rejected

- Contributions that reference specific private deployments (your fleet, your channels, your matters)
- Example agents that are too specific to be reusable
- Documentation that reads as marketing rather than technical reference
- Additions that duplicate existing content without meaningfully extending it
- Breaking schema changes without migration notes

---

## Questions

If you're unsure whether a contribution fits, open a GitHub issue first to discuss scope before doing the work.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
