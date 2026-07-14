# Schema: Slack Workspace Architecture

How the fleet's Slack workspace is organized — the channel taxonomy, naming
conventions, routing matrix, threading discipline, and per-channel furniture
(canvases, bookmarks, sections) that turn a pile of agent posts into a calm,
glanceable operator surface.

> **Companion specs:**
> - [slack-canvas-structure.md](slack-canvas-structure.md) — the state/display canvas layer
> - [slack-block-kit-templates.md](slack-block-kit-templates.md) — the visual message components posted *into* these channels
> - [docs/patterns/visual-cards.md](../docs/patterns/visual-cards.md) — dynamic image cards embedded in posts

---

## Design Goals

A fleet of 15–30 agents posting on independent schedules will, without
structure, produce an undifferentiated firehose. The workspace architecture
exists to make the output **scannable, routable, and quiet by default**:

1. **One glance answers "is anything on fire?"** — critical signal is isolated from routine signal.
2. **Topic lives with topic.** — a reader looking for market intelligence sees only market intelligence.
3. **Notifications are earned, not default.** — most channels are muted; only escalation and digest channels notify.
4. **Every channel has a "what is this" surface.** — a pinned canvas + bookmarks so a newcomer (or the operator after a week away) orients in seconds.
5. **Routing is mechanical, not judgment.** — each agent declares its channel and severity routing in config; no per-post decision.

---

## Channel Taxonomy

Channels are grouped by **function**, with a consistent prefix per group so
the Slack sidebar self-sorts alphabetically into clean clusters.

```
🛰  intel-*       Topic intelligence feeds   (the bulk of agent output)
🚨  alerts        Critical escalation only    (notifies; nothing routine here)
📊  fleet-ops     Fleet health, runs, budget  (operational telemetry)
🗞  digest        Consolidated daily briefs   (the "if you read one thing" channel)
💬  ask-fleet     Interactive Q&A             (operator ↔ Fleet Query agent)
🧪  lab           Staging for new/unstable agents
📥  inbox-raw     Optional firehose mirror    (muted; everything, for audit)
```

### `intel-*` — Topic Intelligence Feeds

The primary output surface. One channel per coherent topic domain, **not** one
per agent — multiple agents can post to the same `intel-*` channel when their
output belongs to the same reader's mental model.

| Channel | Posting Agents | Cadence |
|---------|----------------|---------|
| `#intel-markets` | Market Monitor, Market Pulse | 4×/day active hours |
| `#intel-regulatory` | Regulatory Oracle, Model Governance Monitor | Daily + on-event |
| `#intel-onchain` | On-Chain Watchlist, Sanctions List Monitor, DeFi Protocol Monitor | Continuous |
| `#intel-research` | Research Digest, Breaking News Monitor | Morning + on-event |
| `#intel-compliance` | Compliance Intelligence Hub, Risk Register Keeper, Control Testing | Daily |

**Rule of thumb:** if a reader would want to mute one agent but not another,
they belong in different channels. If they always read both together, same channel.

### `#alerts` — Critical Escalation

The only channel that notifies aggressively (no mute). **Routine output never
lands here.** Only `CRITICAL` severity findings, posted as high-contrast
[alert cards](slack-block-kit-templates.md#alert-card). Each alert links back to
the full report in its home `intel-*` channel thread, so `#alerts` stays a thin,
high-signal index rather than a duplicate feed.

### `#fleet-ops` — Operational Telemetry

Where the fleet talks about itself: Fleet Watchdog health reports, run logs,
budget/burn-rate status, auto-repair findings, drift alerts. The operator
checks this channel deliberately, not reactively — it's muted but pinned.

### `#digest` — Consolidated Briefs

The Synthesis Engine and Digest Aggregator post once or twice a day here: a
single [digest block](slack-block-kit-templates.md#daily-digest) cross-referencing
the day's intelligence across all `intel-*` channels. Designed to be the one
channel an operator can read on mobile and feel caught up. Notifies on the
scheduled brief only.

### `#ask-fleet` — Interactive Q&A

Operator asks ad-hoc questions; the Fleet Query agent answers with data-cited
responses (reading state stores + the data layer). Threaded conversations;
each question is its own thread.

### `#lab` and `#inbox-raw`

- `#lab` — new agents post here until they've proven stable (quality ≥ threshold over N runs), then graduate to their `intel-*` home. Keeps unproven output out of the operator's main feed.
- `#inbox-raw` — optional. A muted mirror of *every* agent post for audit/replay. Most operators leave this off; it exists for compliance environments that want a single immutable stream.

---

## Naming Conventions

| Rule | Example |
|------|---------|
| Lowercase, hyphenated, group prefix first | `intel-markets`, not `MarketsIntel` |
| Singular topic noun | `intel-regulatory`, not `intel-regulations` |
| No agent names in channel names | `intel-onchain`, not `intel-sanctions-monitor` |
| Reserve emoji for the channel's set topic (Slack channel emoji), not the name | 🛰 set on `#intel-markets` |

Channel **descriptions** (the one-liner under the name) follow a fixed shape:

```
[what lands here] · [who posts] · [cadence] · canvas pinned
```

Example: `Market intelligence · Market Monitor + Market Pulse · 4×/day · canvas pinned`

---

## Routing Matrix

Each agent declares two routing facts in its config — its **home channel** and
its **escalation behavior**. Routing is then mechanical.

```yaml
# in an agent's config
output:
  home_channel: "#intel-onchain"
  thread_strategy: "one-thread-per-entity"   # see Threading Discipline
  escalation:
    HIGH:     ["home_channel", "digest_flag"]
    CRITICAL: ["home_channel", "#alerts", "operator_dm", "calendar_if_timed"]
```

This mirrors the [Escalation Protocol](../FLEET-OPS.md#escalation-protocol). The
severity → destination mapping is fleet-wide and identical for every agent, so a
`CRITICAL` from any agent behaves the same way. Agents never decide *where*
critical output goes — only *that* something is critical.

| Severity | `intel-*` home | `#alerts` | `#digest` | Operator DM | Calendar |
|----------|:--:|:--:|:--:|:--:|:--:|
| LOW / MEDIUM | ✅ | — | — | — | — |
| HIGH | ✅ | — | flagged | — | — |
| CRITICAL | ✅ | ✅ | flagged | ✅ | if time-sensitive |

---

## Threading Discipline

Threads are how a busy channel stays readable. The convention prevents the
channel-root from filling with follow-ups and duplicates.

- **Root message = the finding.** One self-contained post (header + cards + summary). Always [Block Kit](slack-block-kit-templates.md), never a wall of text.
- **Thread = everything downstream of that finding.** Enrichment, cross-references from the Smart Thread Responder, operator notes, agent follow-ups on the same item.
- **`thread_strategy`** declared per agent:
  - `one-thread-per-run` — each run's output is one root + threaded detail (most agents).
  - `one-thread-per-entity` — long-lived threads keyed to a watched entity/address/matter, so the full history of one thing lives in one thread (watchlist, regulatory matter tracking).
  - `flat` — no threading; rare, only for genuinely independent single-line alerts.
- **Cross-references go in-thread**, never as new root posts. The Smart Thread Responder replies inside the relevant thread linking related findings in other channels.

---

## Per-Channel Furniture

Every operator-facing channel ships with three orientation surfaces so it's
self-documenting:

### 1. Pinned State Canvas

Each `intel-*` and `#fleet-ops` channel has its agent's [state canvas](slack-canvas-structure.md)
pinned. The canvas is the living dashboard — current state, run log, watchlist,
quality history — always one click from the feed.

### 2. Bookmarks Bar

A fixed set of bookmarks per channel for fast navigation:

```
📌 State Canvas   📈 Live Dashboard   🗂 Archive (SQLite/Notion)   📖 Agent Spec
```

- **State Canvas** → the pinned canvas
- **Live Dashboard** → the relevant [showcase dashboard](../showcase/) (e.g., regulatory tracker)
- **Archive** → the queryable history surface
- **Agent Spec** → the agent's `AGENT.md` in the repo, so "why did it post this?" is answerable

### 3. Channel Topic = Health Line

The Slack channel **topic** (top of channel) is rewritten by the Fleet Watchdog
to a one-line health string, making channel health visible without opening the canvas:

```
🟢 healthy · last run 14:02 UTC · quality 8.6 · 0 open escalations
🟡 degraded · last run 09:40 UTC (stale 4h) · quality 7.1 · 1 fallback
🔴 down · no run since 2026-06-12 · auto-repair ESCALATED
```

---

## Notification Strategy

The default posture is **quiet**. Noise is the enemy of a fleet that posts dozens of times a day.

| Channel group | Default notification | Rationale |
|---------------|----------------------|-----------|
| `intel-*` | **Muted** (badge only) | Read on the operator's schedule, not the agents' |
| `#alerts` | **All messages** (incl. mobile push) | This is the interrupt channel — earned attention |
| `#digest` | **Mentions + scheduled brief** | One predictable notification per brief |
| `#fleet-ops` | **Muted** | Checked deliberately; Watchdog DMs on true emergencies |
| `#ask-fleet` | **All** (it's a live conversation) | Operator is actively waiting on replies |

The discipline: if everything notifies, nothing does. Keeping `intel-*` muted is
what lets `#alerts` mean something.

---

## Workspace Setup Checklist

Bootstrapping the workspace (or auditing an existing one):

- [ ] Create channel groups with the prefix convention; set channel emoji + description shape.
- [ ] Pin each agent's state canvas to its home channel.
- [ ] Add the four-bookmark bar to every operator-facing channel.
- [ ] Configure notification defaults per the strategy table (muted `intel-*`, loud `#alerts`).
- [ ] Set each agent's `home_channel` + `escalation` config to match the routing matrix.
- [ ] Point the Fleet Watchdog at every channel topic for the health-line rewrite.
- [ ] Verify `#alerts` receives *only* CRITICAL routing (no agent posts routine output there).
- [ ] Confirm `#lab` is the home channel for any agent below the graduation quality threshold.

---

## Anti-Patterns

- **One channel per agent.** Fragments the sidebar and breaks the "topic lives with topic" model. Group by reader's mental model, not by producer.
- **Routine posts in `#alerts`.** Trains the operator to mute the one channel that should never be muted.
- **Free-text root posts.** Defeats scannability. Roots are always Block Kit components.
- **Unpinned, unbookmarked channels.** A channel with no canvas/bookmarks is unreadable to anyone but its author after a week.
- **Per-post routing decisions.** Routing belongs in config and the fleet-wide severity map, never in an agent's per-run judgment.
- **Notifying everything.** The fastest way to make an operator stop reading the fleet entirely.
