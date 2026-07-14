# Restore Points

Durable revert anchors for major changes. Each entry records a commit you can
return to if a later change needs to be undone. Because the remote rejects tag
pushes in this environment, restore points are tracked here by commit SHA (which
**is** pushed and durable) rather than by git tag.

> **How to revert the working tree to a restore point**
> ```bash
> # inspect the state without moving your branch
> git checkout <sha>
>
> # restore specific paths to that state (keeps history; makes a normal change)
> git checkout <sha> -- showcase/slack-workspace schemas/slack-*.md
>
> # restore the entire tree to that state, then commit the revert
> git checkout <sha> -- .
> git commit -m "Revert to restore point <sha>"
> ```

---

## `slack-env-snapshot-2026-06-14` — `fb8abd4`

**Date:** 2026-06-14 · **PR:** #3 · **Local tag (not pushable):** `slack-env-snapshot-2026-06-14`

The Slack environment layer in its **initial shipped form and layout** — the
state to return to if later enhancements need to be rolled back. Captures every
aspect as currently set up:

| Aspect | File(s) | Current form |
|--------|---------|--------------|
| Channel architecture | `schemas/slack-workspace-architecture.md` | 6 channel groups (`intel-*`, `#alerts`, `#fleet-ops`, `#digest`, `#ask-fleet`, `#lab`), routing matrix, threading discipline, per-channel furniture, notification strategy |
| Visual components | `schemas/slack-block-kit-templates.md` | Fixed block-order grammar + 5 Block Kit payloads (Intel Report, Alert Card, Daily Digest, Fleet Status, Quality Scorecard) |
| Interactive mockup | `showcase/slack-workspace/index.html` | 9-channel sidebar, Block Kit message rendering, alert cards, digest, Q&A, pinned canvases, dark/light toggle |
| Wiring | `showcase/index.html`, `showcase/README.md`, `README.md`, `CHANGELOG.md` | Mockup linked from landing page + README; schema docs in reference list and repo diagram |

To restore just the Slack environment to this exact state:

```bash
git checkout fb8abd4 -- schemas/slack-workspace-architecture.md \
  schemas/slack-block-kit-templates.md showcase/slack-workspace showcase/index.html
```
