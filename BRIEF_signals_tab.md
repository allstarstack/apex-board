# Brief — merge Signals into the APEX board as a tab

**Repo:** `allstarstack/apex-board`
**Goal:** one URL (`allstarstack.github.io/apex-board/`) with two tabs — Board and Signals — rebuilt by the existing nightly job.

---

## Read before you write

Do not start implementing. First read the repo and report back:

1. What generates `index.html`? Script, template engine, or inline HTML strings?
2. Where does it fetch quotes, and what function/client does it use?
3. What does the nightly workflow in `.github/workflows/` run, and on what schedule?
4. Is there existing CSS, or is it inline?
5. Does anything already read a JSON data file, or is all state in code?

Then propose an approach and wait for approval. Only after that, implement.

---

## What is being added

A second tab of content that changes on a **different cadence** to the board:

- **Board tab** — gates, triggers, cycle map. Rebuilt nightly from live data. Unchanged by this work.
- **Signals tab** — hedge fund 13F themes. Scores and narrative change **quarterly**. Prices under them should refresh nightly.

The source of truth for the Signals tab is a new file, `signals.json`, committed to the repo and hand-updated four times a year (five business days after each 13F deadline: Feb 24, May 22, Aug 21, Nov 23).

The nightly build reads `signals.json`, enriches it with live quotes, and renders it.

---

## Reference implementation

`stack.html` (provided separately) is a working standalone version of the Signals tab. It contains the exact scoring logic, stage ladder, sort rules, copy, and styling to reproduce. Treat it as the spec for behaviour and appearance.

Port it — do not redesign it. Specifically preserve:

- The scoring formula: `weighted signal strength + (2 × distinct source types) + 3 if Whale Rock + 4 if NVDA strategic`
- Manager weights, including Whale Rock 1.5×, NVDA Corp 2.0×, single director 0.4×
- The stage ladder in order: CONTESTED → EXPIRED → COLLAPSING → DECAYING → EMERGING·HIGH CONVICTION → ESTABLISHED → EMERGING → EMERGING·ONE SOURCE → DEVELOPING → WATCH
- Adaptive zone ordering: exits lead when a held ticker sits in the exit zone, otherwise buys lead
- Per-zone sorts: exit by urgency, buy by score, watch by recency, hold by score; held tickers always sort first within a zone
- The data-freshness panel and the signal audit section — both are load-bearing, not decoration

---

## `signals.json` shape

Derive the exact schema from the `S`, `AUDIT`, `CHANGED`, `RULES`, and `MGRS` arrays in `stack.html`. Roughly:

```json
{
  "as_of": "2026-08-14",
  "next_refresh": "2026-11-23",
  "held": ["BTC","PLTR","CRDO","VRT","TSLA"],
  "manager_weights": { "Whale Rock": 1.5, "...": 1.0 },
  "freshness": [
    { "sources": "Whale Rock · Altimeter · Druckenmiller · NVDA Corp",
      "state": "Q1 — positions as of Mar 31", "stale": true }
  ],
  "signals":  [ { "t":"SNDK", "src":"manager", "by":"Whale Rock",
                  "a":"top buy +$270M — now the #2 holding",
                  "v":9, "th":"AI Memory & Compute", "w":19, "nu":true } ],
  "audit":    [ ... ],
  "changed":  [ ... ],
  "rules":    [ ... ],
  "managers": [ ... ]
}
```

Scoring stays in the generator, not in the JSON. The JSON holds inputs and judgment; the code computes.

---

## Live price enrichment

For every unique ticker in `signals[].t`, fetch the current quote using whatever the board already uses. Render under each theme's ticker chips: last price, and percent from the 52-week high.

Failure handling must match the board's existing convention — it already prints `Quotes unavailable: 2454.TW`, so follow that pattern. **Never** let a failed quote silently render as zero or drop the ticker.

---

## Tabs

Client-side toggle in one `index.html`. No routing library, no framework.

- Tab state in the URL hash (`#board`, `#signals`) so a tab can be linked and survives reload
- Default to `#board`
- Keyboard accessible, visible focus ring
- Board content must render identically to today — if the diff on the Board tab is anything other than the added nav, something is wrong

---

## Constraints

- **Do not break the nightly board.** It works. Any regression there outweighs the value of this feature.
- No build step, no bundler, no framework. The board is static HTML and stays static.
- No API keys in committed files.
- If a change requires editing `.github/workflows/`, stop and say so — the fine-grained PAT is missing the Workflows permission and the push will fail.
- Run the generator locally and diff the output against the current live page before pushing.

---

## Done when

1. `allstarstack.github.io/apex-board/` shows two tabs
2. Board tab is byte-identical to today except for the nav
3. Signals tab reproduces `stack.html` with live prices added
4. Nightly job runs green and updates prices on both tabs
5. Updating `signals.json` and pushing is the only step needed for a quarterly refresh
