# Pattern: Idempotency Outbox

A transactional outbox in the fleet's data layer that deduplicates non-idempotent external actions across retries, using a claim/confirm/fail protocol keyed on deterministic action identifiers.

---

## The Problem

Autonomous agents retry. That is usually the right instinct — transient failures are common, and an agent that gives up on the first error produces gaps. But when the failed step is a **non-idempotent external action** (sending an email, posting to a channel, creating a calendar event, placing a simulated trade), a retry after an ambiguous failure duplicates the action.

The motivating incident, told generically: a digest agent sent its morning email, and the send succeeded — but the *result* of the send call failed to render back into the agent's context. From inside the run, this looked identical to a failed send. The agent retried the visible "failure." Same outcome: send succeeded, confirmation lost. It retried again. The recipient received the same digest three times. Every send had worked; only the confirmations were lost.

The lesson is structural, not behavioral:

> From inside a run, you cannot distinguish "the send failed" from "the send succeeded but the result didn't come back." Therefore deduplication cannot live inside the run. It must live in durable state outside the run.

Prompt-level guidance ("don't retry sends") is not a fix. It trades duplicate sends for missed sends, and it depends on the agent correctly diagnosing an ambiguous failure under exactly the conditions where its context is degraded.

---

## The Pattern

A `send_log` table in the fleet's SQLite data layer acts as a transactional outbox. Every non-idempotent action is wrapped in a three-step protocol driven by a small CLI:

```
outbox.py claim   --agent daily-brief --action email --key digest-2026-06-09-am
  # exit 0 → no prior claim exists, row inserted, proceed with the send
  # exit 9 → an unresolved or confirmed claim already exists — skip, do not send

outbox.py confirm --agent daily-brief --action email --key digest-2026-06-09-am
  # after verified success (e.g., SMTP accepted, message ID returned)

outbox.py fail    --agent daily-brief --action email --key digest-2026-06-09-am \
                  --note "SMTP timeout"
  # explicit, diagnosed failure — releases the claim so a retry can proceed
```

The ordering is the entire pattern: **claim before the attempt, confirm only after verifiable success.** If the run crashes or the confirmation is lost, the claim remains — and the claim, not the agent's perception of the result, is what gates the next attempt.

---

## The Schema

```sql
CREATE TABLE IF NOT EXISTS send_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name   TEXT NOT NULL,
    action_type  TEXT NOT NULL,            -- email | channel_post | calendar_event | sim_trade
    dedup_key    TEXT NOT NULL,            -- deterministic identifier for the logical action
    status       TEXT NOT NULL,            -- claimed | confirmed | failed
    note         TEXT,                     -- failure reason, message ID, etc.
    claimed_at   TEXT NOT NULL,            -- ISO 8601 UTC
    resolved_at  TEXT,                     -- set on confirm/fail
    UNIQUE(action_type, dedup_key)
);
```

The `UNIQUE(action_type, dedup_key)` constraint is the enforcement mechanism. Two concurrent claims for the same logical action cannot both insert — the database, not the agents, resolves the race.

---

## The State Machine

```
                    claim (INSERT succeeds)
        INIT ────────────────────────────────► CLAIMED
                                                  │
                       ┌──────────────────────────┼──────────────────────────┐
                       │                          │                          │
                  confirm                       fail                  no resolution
                       │                          │                   (crash / lost
                       ▼                          ▼                    confirmation)
                  CONFIRMED                    FAILED                       │
                  (terminal —              (re-claimable                    │
                   all future               immediately)                    ▼
                   claims exit 9)                                  STALE CLAIM
                                                                   (re-claimable
                                                                    after 24h)
```

- **CONFIRMED** is terminal. Any future claim on the same key exits 9 forever.
- **FAILED** is an explicit, diagnosed failure — the claim releases immediately and the next claim proceeds.
- **A stale CLAIMED row** is the crash-recovery path: the attempt died (or its confirmation was lost) without resolution. After 24 hours the claim becomes re-claimable, so a permanently wedged key cannot block tomorrow's action. The window is deliberately long — for a daily digest, a duplicate 24 hours later is a new edition, not a duplicate.

---

## Dedup Key Discipline

Keys are **deterministic for the logical action**, never random. A random key (UUID per attempt) defeats the entire pattern — every retry would mint a fresh key and claim successfully.

| Action | Key shape | Example |
|--------|-----------|---------|
| Daily digest email | `digest-{date}-{window}` | `digest-2026-06-09-am` |
| Bet slip post | `betslip-{game}-{date}` | `betslip-team-a-team-b-2026-06-09` |
| Calendar deadline event | `deadline-{rule-id}-{date}` | `deadline-reg-filing-2026-07-01` |
| Simulated trade | `trade-{symbol}-{signal-id}` | `trade-btc-momentum-0412` |

The test for a good key: if the agent runs twice for any reason — retry, duplicate schedule fire, operator re-trigger — both runs derive the *same* key for the *same* logical action. The second run claims, gets exit 9, and skips.

---

## The Claim Race

Two runs of the same agent can overlap (a retry fired while the original is still alive, or a schedule double-fire). Both attempt to claim. The `UNIQUE` constraint guarantees exactly one `INSERT` succeeds; the loser gets exit 9.

The critical rule: **exit 9 means "skip", not "error."** The losing run logs that the action was already claimed and moves on to its next step. If exit 9 were treated as a failure, the agent's retry logic would re-trip on it — recreating exactly the fail-open retry behavior the outbox exists to prevent. The runner's wrapper must branch on the exit code, not on stderr.

---

## Integration Sketch

An email-sending wrapper, claiming before SMTP and confirming after:

```python
import subprocess, sys

def send_with_outbox(agent, dedup_key, build_and_send):
    claim = subprocess.run(
        ["python3", "{FLEET_ROOT}/data-layer/outbox.py", "claim",
         "--agent", agent, "--action", "email", "--key", dedup_key])
    if claim.returncode == 9:
        print(f"[outbox] {dedup_key} already claimed/confirmed — skipping send")
        return "skipped"
    if claim.returncode != 0:
        sys.exit(f"[outbox] claim errored ({claim.returncode}) — refusing to send blind")

    try:
        message_id = build_and_send()          # SMTP send; returns server message ID
        subprocess.run(
            ["python3", "{FLEET_ROOT}/data-layer/outbox.py", "confirm",
             "--agent", agent, "--action", "email", "--key", dedup_key], check=True)
        return message_id
    except Exception as e:
        subprocess.run(
            ["python3", "{FLEET_ROOT}/data-layer/outbox.py", "fail",
             "--agent", agent, "--action", "email", "--key", dedup_key,
             "--note", str(e)[:200]])
        raise
```

Note the asymmetry: a *diagnosed* exception marks the claim `failed` (retry permitted), but a lost confirmation — process death between send and confirm — leaves the claim standing. That is correct behavior: the ambiguous case defaults to "do not send again," which is the entire point.

---

## Failure Modes

| Failure | Without outbox | With outbox |
|---------|----------------|-------------|
| Send succeeds, confirmation lost | Agent retries → duplicate delivery | Claim stands → retry exits 9, skips |
| Send genuinely fails (SMTP timeout) | Retry works, but indistinguishable from above | `fail` releases claim → retry proceeds |
| Run crashes mid-send | Next run re-sends blindly | Stale claim blocks for 24h, then recovers |
| Schedule double-fires | Two identical posts | Second claim loses the race, exits 9 |
| Outbox itself unreachable (db locked) | n/a | Claim errors (non-0, non-9) → wrapper refuses to send blind |
| Random/timestamped dedup key (bug) | n/a | Pattern silently defeated — every attempt claims fresh. Lint keys in review. |

The last two rows matter most. When the outbox cannot be consulted, the safe default is to **not send** — a missed digest is an investigation; a triple-sent digest is an incident. And the pattern's one true bypass is a non-deterministic key, which no constraint can catch — it has to be enforced at code-review time.

---

## When to Use — and When Not To

**Use the outbox for any side effect where "twice" is worse than "possibly investigate once":**

- Email and message delivery
- Channel posts that notify humans
- Calendar event creation
- Simulated (or real) trade placement
- Anything a recipient experiences as a discrete event

**Skip the outbox for idempotent writes**, where re-execution converges to the same state:

- Canvas/dashboard mirrors (each write overwrites the previous state)
- `INSERT OR REPLACE` state persistence
- File renders to a fixed path
- Append-only data-layer rows that already carry natural keys

For those, the outbox is pure overhead — three subprocess calls and a table row to protect an action that was already safe to repeat. The discriminator is the question: *if this ran twice in a row, would anyone notice?* If no, write freely. If yes, claim first.

---

## Related Patterns

- [State Management](state-management.md) — the data layer that hosts `send_log`
- [Self-Repair](self-repair.md) — the retry behavior that makes the outbox necessary
- [Execution Scaffolding](execution-scaffolding.md) — action packages are prime outbox candidates (a duplicate bet slip is a double-stake risk)
