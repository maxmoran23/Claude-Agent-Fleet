# Architecture

System design documentation for the Claude Agent Fleet — a 38-agent autonomous system built on Claude Code.

---

## Design Philosophy

Three principles guided every architectural decision:

1. **Zero-infrastructure** — no servers, no databases, no deployment pipelines. The entire system runs on Claude Code scheduled tasks and commodity SaaS tools (Slack, Gmail, Notion, Google Calendar).

2. **Self-contained agents** — every agent is a complete, independent unit. No agent depends on another agent's files, output, or availability. Any agent can fail, be modified, or be removed without cascading effects.

3. **The fleet maintains itself** — observability and repair are not bolted-on afterthoughts. They are agents in the fleet, running the same architecture, following the same patterns.

---

## Runtime Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE PLATFORM                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SCHEDULED TASK ENGINE                        │   │
│  │                                                          │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │Task 1  │ │Task 2  │ │Task 3  │ │Task N  │  (35+)    │   │
│  │  │cron:8h │ │cron:4h │ │cron:1d │ │cron:3h │           │   │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │   │
│  │      │          │          │          │                  │   │
│  │      ▼          ▼          ▼          ▼                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │Agent   │ │Agent   │ │Agent   │ │Agent   │           │   │
│  │  │Config  │ │Config  │ │Config  │ │Config  │           │   │
│  │  │(AGENT  │ │(AGENT  │ │(AGENT  │ │(AGENT  │           │   │
│  │  │.md)    │ │.md)    │ │.md)    │ │.md)    │           │   │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │   │
│  │      │          │          │          │                  │   │
│  └──────┼──────────┼──────────┼──────────┼──────────────────┘   │
│         │          │          │          │                       │
│         ▼          ▼          ▼          ▼                       │
│    REMOTE EXECUTION (always-on, laptop-independent)             │
└─────────────────────────────────────────────────────────────────┘
```

**Key property:** The agents execute remotely on Anthropic's infrastructure via scheduled tasks. The system does not depend on a laptop being open, a server running, or any local process. This is not cron-on-a-Mac — it's cloud-native agent execution.

---

## State Management

### The Problem
Agents are stateless by default — each scheduled run is a fresh invocation with no memory of previous runs. But useful intelligence agents need to know what they reported last time, what positions they hold, what they've already seen.

### The Solution: Slack Canvases as State Stores

```
┌──────────────────────────────────────────────────┐
│              4 PERSISTENT STATE STORES            │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐               │
│  │   Market     │  │ Regulatory  │               │
│  │   State      │  │   State     │               │
│  │             │  │             │               │
│  │ Prices      │  │ Active      │               │
│  │ Positions   │  │ Rules       │               │
│  │ Sentiment   │  │ Enforcement │               │
│  │ Last seen   │  │ Deadlines   │               │
│  └─────────────┘  └─────────────┘               │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐               │
│  │   Fleet      │  │  Betting    │               │
│  │   State      │  │   State     │               │
│  │             │  │             │               │
│  │ Run logs    │  │ Edges       │               │
│  │ Health      │  │ Records     │               │
│  │ Quality     │  │ Sizing      │               │
│  │ Cross-agent │  │ History     │               │
│  └─────────────┘  └─────────────┘               │
│                                                  │
│  PROTOCOL:                                       │
│  • Step 0: Read own section from canvas          │
│  • Step 7: Write back run log + state changes    │
│  • Section-level writes only (never full canvas) │
│  • Human-readable at all times                   │
└──────────────────────────────────────────────────┘
```

**Why Slack Canvases instead of a database?**
- No infrastructure to maintain
- Human-readable — I can open a canvas and see exactly what any agent "remembers"
- Agents can read and write via existing Slack MCP tools
- Survives agent restarts, reconfigurations, and failures
- Multiple agents can share state without file coupling

---

## Data Flow Architecture

```
LAYER 1: SOURCES
    Crypto.com (prices) ──┐
    LunarCrush (social) ──┤
    Blockscout (chain) ───┤
    MT Newswires (news) ──┼──▶ AGENTS (gather with fallback chains)
    Bigdata.com (finance)─┤
    Gmail (email) ────────┤
    Google Calendar ──────┘

LAYER 2: PROCESSING
    38 agents analyze, synthesize, cross-reference

LAYER 3: OUTPUT ROUTING
    ┌──▶ Slack topic channels (full reports, threaded)
    │
    ├──▶ Slack display canvases (living dashboards, section-updated)
    │
    ├──▶ Notion database (structured findings, severity-tagged)
    │
    ├──▶ Gmail (curated email digests for mobile)
    │
    ├──▶ Apple Notes (glanceable summaries synced to phone)
    │
    └──▶ Google Calendar (regulatory deadlines, market events)

LAYER 4: CROSS-POLLINATION
    Smart Thread Responder reads ALL state stores
    └──▶ enriches posts with cross-references between channels
    
    Synthesis Engine reads ALL channel output
    └──▶ generates fleet-wide meta-analysis daily

LAYER 5: ESCALATION
    Any agent can flag CRITICAL findings
    └──▶ bypasses normal routing → direct alerts + DM
```

---

## Agent Coupling Model

```
                    ┌─────────────────────┐
                    │  SHARED STATE LAYER  │
                    │  (Slack Canvases)    │
                    └──┬───┬───┬───┬───┬──┘
                       │   │   │   │   │
            ┌──────────┘   │   │   │   └──────────┐
            ▼              ▼   ▼   ▼              ▼
       ┌─────────┐   ┌─────────────────┐   ┌─────────┐
       │ Agent A  │   │   Agent B ...N  │   │ Agent Z  │
       │          │   │                 │   │          │
       │ Own dir  │   │   Own dirs      │   │ Own dir  │
       │ Own conf │   │   Own confs     │   │ Own conf │
       │ Own tmpl │   │   Own tmpls     │   │ Own tmpl │
       └─────────┘   └─────────────────┘   └─────────┘
       
       NO file dependencies between agents.
       Communication is via state stores + channel posts.
       Agent A can be deleted without affecting Agent Z.
```

This is a critical design choice. Traditional multi-agent systems often create tight coupling through shared utilities, common configs, or direct agent-to-agent calls. This fleet deliberately avoids all of that. The cost is some duplication across agent configs. The benefit is absolute fault isolation and the ability to modify any agent without risk.

---

## Delivery Architecture

The fleet delivers intelligence through 5 apps, optimized for different consumption patterns:

| Channel | Purpose | Consumption Pattern |
|---------|---------|-------------------|
| **Slack** | Full reports, threaded discussion, dashboards | Desktop deep-dive |
| **Gmail** | Curated digests (morning, midday, afternoon, evening, weekly) | Mobile scanning |
| **Apple Notes** | Glanceable daily reference | iPhone quick-check |
| **Google Calendar** | Regulatory deadlines, market events | iOS push notifications |
| **Notion** | Structured findings database (all agents write here) | Historical search |

**Daily volume:** ~40-50 automated touchpoints across all channels, 5 AM to 9 PM ET.

The brief agents (9 total) act as a **curation layer** — they don't gather their own data. Instead, they read what the Cortex and real-time agents have posted to Slack channels, synthesize it, and deliver formatted summaries to Gmail/Notes for mobile consumption.

---

## Why No Traditional Code?

This system contains zero Python, JavaScript, or any traditional programming language. Every agent is a structured Markdown prompt (AGENT.md) that Claude Code executes directly. This was a deliberate choice:

1. **Faster iteration** — modifying agent behavior means editing English, not debugging code
2. **No dependency management** — no packages, no versions, no breaking updates
3. **No deployment pipeline** — changes take effect on next scheduled run
4. **Lower barrier to modification** — the builder (me) is a compliance professional, not a software engineer
5. **Native tool integration** — Claude Code's MCP servers provide direct access to Slack, Gmail, Notion, etc. without API wrappers

The tradeoff is that the system depends on Claude Code's capabilities and Anthropic's platform reliability. This is an acceptable dependency given that the system is built to demonstrate and push the boundaries of what Claude can do.
