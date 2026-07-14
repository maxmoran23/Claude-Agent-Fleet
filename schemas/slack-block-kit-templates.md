# Schema: Slack Block Kit Message Templates

The visual component library for everything agents post into channels. Every
root message in an `intel-*`, `#alerts`, `#digest`, or `#fleet-ops` channel is
assembled from these [Block Kit](https://api.slack.com/block-kit) templates — so
the operator learns one visual grammar and reads any agent's output instantly.

> **Companion specs:**
> - [slack-workspace-architecture.md](slack-workspace-architecture.md) — which channels these post into
> - [slack-canvas-structure.md](slack-canvas-structure.md) — the persistent canvas layer
> - [docs/patterns/visual-cards.md](../docs/patterns/visual-cards.md) — dynamic PNG cards embedded via `image` blocks

---

## Why Block Kit (not Markdown)

A free-text Slack post is a wall. Block Kit gives agent output the same UI
primitives a designed app has: section blocks with side accessories, field
grids, context rows (small muted metadata), dividers, buttons, overflow menus,
and inline images. The payoff:

- **Scannable structure.** Header → key fields → detail → actions, every time.
- **Pre-attentive severity.** Color via accessory cards and emoji, read before words.
- **Interactivity built in.** Buttons (Open Canvas, Acknowledge, Snooze) and overflow menus turn a post into a control surface, not just a readout.
- **Consistency = pattern recognition.** Same block order across 30 agents means the operator's eye knows where to look.

---

## The Shared Visual Grammar

Every root message follows the same block order. Agents fill the slots; the
skeleton never changes.

```
1. Header block          ← severity emoji + agent name + finding title
2. Context block         ← timestamp · run id · quality score · cadence  (small, muted)
3. Section block(s)      ← the finding: mrkdwn body, optional fields grid, optional accessory
4. Image block           ← optional dynamic card (see visual-cards.md)
5. Divider
6. Actions block         ← buttons + overflow menu (Open Canvas, Ack, Snooze, View Source)
7. Context block         ← fleet footer: agent · kernel version · home channel
```

This is the "every agent looks the same" contract. A reader scans the header
for severity, the field grid for numbers, and the actions row for what they can do.

---

## Severity Color Convention

Block Kit has no per-block background color, so severity is carried by a fixed
emoji + the [`attachment` color bar](https://api.slack.com/reference/messaging/attachments)
when a left-edge color stripe is wanted.

| Severity | Emoji | Attachment color | Used in |
|----------|:-----:|------------------|---------|
| CRITICAL | 🔴 | `#d7263d` | `#alerts`, home channel |
| HIGH | 🟠 | `#f46a25` | home channel, digest flag |
| MEDIUM | 🟡 | `#f4c025` | home channel |
| LOW | 🟢 | `#2eb872` | home channel |
| INFO / ops | 🔵 | `#3d7eff` | `#fleet-ops` |

---

## Templates

Each template below is a copy-paste-ready `blocks` payload. `{{...}}` markers are
agent-filled slots.

### Intel Report

The workhorse — the root post for a routine finding in an `intel-*` channel.

```json
{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🟡 Market Monitor — Sector rotation into L1 alternatives" }
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "*14:02 UTC* · run `mm-2026-0614-1402` · quality *8.6/10* · 4×/day" }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Capital is rotating out of BTC into large-cap L1 alternatives ahead of Tuesday's regulatory markup. ETH-BTC ratio at a 3-month low; SOL and AVAX leading inflows."
      },
      "fields": [
        { "type": "mrkdwn", "text": "*BTC*\n$62,400  🔻 2.1%" },
        { "type": "mrkdwn", "text": "*ETH*\n$3,200  🔺 1.4%" },
        { "type": "mrkdwn", "text": "*Total Cap*\n$2.41T  🔺 0.8%" },
        { "type": "mrkdwn", "text": "*Fear/Greed*\n61 (Greed)" }
      ]
    },
    {
      "type": "image",
      "image_url": "https://[deployment].vercel.app/api/market-snapshot?btc=62400&eth=3200&cap=2.41T&trend=up&delta=0.8&ts=2026-06-14T14:02:00Z",
      "alt_text": "Market snapshot card: BTC $62,400 down 2.1%, ETH $3,200 up 1.4%, total cap $2.41T up 0.8%"
    },
    { "type": "divider" },
    {
      "type": "actions",
      "elements": [
        { "type": "button", "text": { "type": "plain_text", "text": "📌 Open Canvas" }, "url": "https://slack.com/canvas/...", "action_id": "open_canvas" },
        { "type": "button", "text": { "type": "plain_text", "text": "📈 Live Dashboard" }, "url": "https://maxmoran23.github.io/Claude-Agent-Fleet/", "action_id": "open_dashboard" },
        {
          "type": "overflow",
          "action_id": "report_overflow",
          "options": [
            { "text": { "type": "plain_text", "text": "🔕 Snooze this topic 24h" }, "value": "snooze_24h" },
            { "text": { "type": "plain_text", "text": "🗂 View in archive" }, "value": "archive" },
            { "text": { "type": "plain_text", "text": "📖 Agent spec" }, "value": "spec" }
          ]
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Market Monitor · kernel v1.5 · #intel-markets · _reply in thread to enrich_" }
      ]
    }
  ]
}
```

### Alert Card

For `CRITICAL` findings routed to `#alerts`. High-contrast, minimal, action-first.
Wrapped in an `attachment` for the red left stripe. Links back to the full report
thread rather than duplicating it.

```json
{
  "attachments": [
    {
      "color": "#d7263d",
      "blocks": [
        {
          "type": "header",
          "text": { "type": "plain_text", "text": "🔴 CRITICAL — Sanctions hit on watched address" }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "Watched address `0xAB…01` transacted with newly-added OFAC SDN entry *EXAMPLE-SDN-2026-042*. Exposure: *1.2M USDT* across 3 hops within the configured 1M threshold window."
          },
          "fields": [
            { "type": "mrkdwn", "text": "*Source*\nSanctions List Monitor" },
            { "type": "mrkdwn", "text": "*Detected*\n14:06 UTC" },
            { "type": "mrkdwn", "text": "*Confidence*\nHIGH (direct match)" },
            { "type": "mrkdwn", "text": "*Topic home*\n#intel-onchain" }
          ]
        },
        {
          "type": "actions",
          "elements": [
            { "type": "button", "style": "danger", "text": { "type": "plain_text", "text": "🔎 Full report" }, "url": "https://slack.com/archives/...thread", "action_id": "open_thread" },
            { "type": "button", "style": "primary", "text": { "type": "plain_text", "text": "✅ Acknowledge" }, "action_id": "ack_alert", "value": "alert-2026-0614-1406" },
            { "type": "button", "text": { "type": "plain_text", "text": "📅 Add to calendar" }, "action_id": "calendar_alert" }
          ]
        },
        {
          "type": "context",
          "elements": [
            { "type": "mrkdwn", "text": "Escalation: #alerts + operator DM · acknowledge to clear from open-escalations count" }
          ]
        }
      ]
    }
  ]
}
```

### Daily Digest

The Synthesis Engine's once/twice-daily consolidated brief in `#digest`. One
post, cross-referencing the day across `intel-*` channels.

```json
{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🗞 Fleet Digest — Sat 14 Jun, AM brief" }
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Covering 06:00–14:00 UTC · 23 findings across 5 channels · 1 critical · 3 high" }
      ]
    },
    { "type": "divider" },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*🔴 Top of mind*\nSanctions hit on watched address `0xAB…01` (1.2M USDT exposure). Acknowledged 14:11 UTC. <https://slack.com/...|Full thread →>" }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*📈 Markets* — <https://slack.com/...|#intel-markets>\nSector rotation into L1 alternatives; ETH-BTC at 3-month low. No threshold breaches." }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*⚖️ Regulatory* — <https://slack.com/...|#intel-regulatory>\nTuesday markup confirmed on calendar. One interpretive guidance note flagged HIGH for compliance review." }
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*🔗 On-chain* — <https://slack.com/...|#intel-onchain>\n1 critical (above). 4 routine watchlist updates; no other threshold breaches." }
    },
    { "type": "divider" },
    {
      "type": "actions",
      "elements": [
        { "type": "button", "text": { "type": "plain_text", "text": "🗂 Full archive" }, "url": "https://...", "action_id": "digest_archive" },
        { "type": "button", "text": { "type": "plain_text", "text": "💬 Ask the fleet" }, "url": "https://slack.com/archives/ask-fleet", "action_id": "ask_fleet" }
      ]
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Synthesis Engine · next brief 22:00 UTC · reading all #intel-* channels" }
      ]
    }
  ]
}
```

### Fleet Status

Fleet Watchdog's health report in `#fleet-ops`. Field grid of agent health +
budget burn line.

```json
{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🔵 Fleet Watchdog — Health & Budget" }
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "*14:00 UTC* · 12 agents · burn rate *on target* (68% of weekly budget, day 6/7)" }
      ]
    },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "🟢 *Market Monitor*\nlast run 14:02 · q8.6" },
        { "type": "mrkdwn", "text": "🟢 *Regulatory Oracle*\nlast run 09:40 · q9.1" },
        { "type": "mrkdwn", "text": "🟡 *Research Digest*\nstale 4h · q7.1 · 1 fallback" },
        { "type": "mrkdwn", "text": "🟢 *Sanctions Monitor*\nlast run 14:06 · q8.9" },
        { "type": "mrkdwn", "text": "🔴 *DeFi Monitor*\nno run since 06-12 · ESCALATED" },
        { "type": "mrkdwn", "text": "🟢 *Synthesis Engine*\nlast run 06:00 · q8.4" }
      ]
    },
    { "type": "divider" },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*Auto-repair:* 1 open ESCALATE (DeFi Monitor — endpoint timeout, 3 consecutive failures). Proposed fix staged, awaiting operator gate." }
    },
    {
      "type": "actions",
      "elements": [
        { "type": "button", "style": "primary", "text": { "type": "plain_text", "text": "✅ Approve fix" }, "action_id": "approve_repair", "value": "defi-monitor-repair-014" },
        { "type": "button", "text": { "type": "plain_text", "text": "👀 Review diff" }, "url": "https://github.com/...", "action_id": "review_diff" },
        { "type": "button", "text": { "type": "plain_text", "text": "📊 Budget detail" }, "action_id": "budget_detail" }
      ]
    }
  ]
}
```

### Quality Scorecard

A compact context+image strip an agent can append to any post showing its
quality trend — feeds the [quality self-rating pattern](../docs/patterns/quality-self-rating.md).

```json
{
  "blocks": [
    {
      "type": "image",
      "image_url": "https://[deployment].vercel.app/api/score-gauge?title=Run+Quality&score=86&trend=up&delta=4&severity=low&ts=2026-06-14T14:02:00Z",
      "alt_text": "Quality gauge: 8.6 of 10, trending up 0.4 over last run, 10-run average 8.4"
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Last 10 runs: `9 8 9 8 9 7 8 9 8 9` · 10-run avg *8.4* · trend *stable→up*" }
      ]
    }
  ]
}
```

---

## Interactive Element Conventions

Buttons and menus turn a readout into a control surface. Conventions keep them predictable:

| Element | When | `action_id` pattern |
|---------|------|---------------------|
| **Open Canvas** button | Every intel report (links pinned canvas) | `open_canvas` |
| **Live Dashboard** button | When a showcase dashboard covers the topic | `open_dashboard` |
| **Acknowledge** button (`primary`) | Every `#alerts` card | `ack_alert` |
| **Full report** button (`danger`) | Alert cards linking back to home thread | `open_thread` |
| **Approve / Review diff** buttons | Propose-and-gate fleet-ops posts | `approve_*` / `review_diff` |
| **Overflow menu** | Snooze topic / view archive / agent spec | `*_overflow` |

**Button style discipline:** `primary` (green) = the one affirmative action;
`danger` (red) = destructive or critical-attention; default (grey) = navigation.
At most one `primary` per actions block.

**Interactivity is optional to *handle*.** Even with no backend wired to receive
the interaction payloads, buttons carrying `url` (Open Canvas, Live Dashboard,
View Source) work as pure navigation. Stateful buttons (Acknowledge, Approve)
require a Slack app endpoint to process the payload.

---

## Accessibility

- **Every `image` block carries `alt_text`** describing the data, not "chart". A card's numbers must survive in text for screen readers and for the [Digest Aggregator](../FLEET-OPS.md) that re-reads channel content.
- **Never encode meaning in color alone.** Severity always pairs the color with an emoji + a word (🔴 CRITICAL), so it reads on monochrome and to color-blind operators.
- **Context blocks carry the machine-readable facts** (run id, timestamps, quality) so downstream agents parse them without OCR-ing a card.

---

## Anti-Patterns

- **Free-text root posts.** If it's a root message in an operator channel, it's Block Kit. Prose goes in threads.
- **Decorative blocks.** A divider or image that conveys nothing is noise. Every block earns its place.
- **More than one `primary` button.** Dilutes "the action to take."
- **Color-only severity.** Always emoji + word.
- **Duplicating the card in text and image.** Pick the primary surface; don't render the same three numbers twice (see [visual-cards.md](../docs/patterns/visual-cards.md#anti-patterns-to-avoid)).
- **Inconsistent block order across agents.** Breaks the shared grammar that makes 30 agents readable. The skeleton is fixed; only the slots vary.
