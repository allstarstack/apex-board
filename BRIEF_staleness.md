# Brief — price staleness adjustment for the Signals tab

**Repo:** `allstarstack/apex-board`
**Builds on:** the Signals tab merged in commit `de6e672` / published `006e806`

---

## The problem

Signal scores are frozen at the quarterly `signals.json` update. Prices move daily. Nothing connects them.

Concrete case, live on the board right now: the AI Memory & Compute theme scores +72 and renders as "Entry window open now." Its lead name, SNDK, was bought by Whale Rock as of the Q1 filing date (2026-03-31) and has since run to roughly $1,588 — up around 3,000% from its Feb 2025 spinoff and 33% off its June high. The signal was correct. The entry it implies is long gone. The board cannot tell the difference.

## The rule to implement

Already specified in the Inspo v4 framework, never built:

| Condition | Adjustment |
|---|---|
| Price up **more than 30%** since the signal's reference date | **−3** (stale — you are late) |
| Price down **more than 15%** since the signal's reference date | **+3** (dislocation — better entry than the manager got) |
| Between −15% and +30% | no adjustment |

Applied **per signal**, not per theme. A theme's score is the sum of its adjusted signals, so a theme with several run-away names decays further than one with a single stale leg.

---

## Read before you write

Report back before implementing:

1. How `signals_html()` currently fetches quotes and what fields it keeps from the FMP response.
2. Whether FMP's `stable/` endpoints expose a historical close for an arbitrary past date, and which endpoint — this is the one real unknown. If there is no clean historical endpoint on the current plan, say so and propose the fallback in section "If historical prices are unavailable" below.
3. How many extra API calls per nightly run this adds, and whether that risks the plan's rate limit.
4. Where in the client-side engine the per-signal `v` value is consumed, so the adjustment can be applied before theme reduction.

Then propose and wait for approval.

---

## Data model change

Each entry in `signals[]` gains an optional reference date:

```json
{ "t":"SNDK", "src":"manager", "by":"Whale Rock",
  "a":"top buy +$270M — now the #2 holding",
  "v":9, "th":"AI Memory & Compute", "w":19, "nu":true,
  "ref_date":"2026-03-31" }
```

Rules for `ref_date`:

- **Manager signals** — the 13F period end, not the filing date. Q1 2026 → `2026-03-31`. Q4 2025 → `2025-12-31`.
- **Insider signals** — the transaction date.
- **Price, earnings, screen and senate signals** — omit `ref_date` entirely. These are already current or are events rather than positions; they must not be adjusted.
- Signals with no `ref_date` pass through unchanged.

Backfill `ref_date` for every existing manager and insider signal in `signals.json` using the quarter labels already present in the `managers[]` block.

---

## Rendering

Each theme card currently shows the ticker chips with a live price line. Extend that so the drift is visible:

- Show the drift percentage next to the live price for any ticker carrying a `ref_date`
- Where an adjustment fired, mark it plainly on the theme — e.g. a small `STALE −3` or `DISLOCATED +3` badge next to the score, in the existing badge style
- The theme's score displays the **adjusted** total; the signal trail (the expandable detail) shows the raw `v`, the adjustment, and the result, so the arithmetic is auditable

Also revise the copy for the `EMERGING · HIGH CONVICTION` stage. It currently asserts "Entry window open now," which is a claim Stack is not entitled to make — Stack surfaces candidates, APEX decides whether the price still works. Replace with wording along the lines of "High conviction — APEX to verify the entry is still live." Keep the tone of the existing copy.

---

## If historical prices are unavailable

If the FMP plan has no usable historical-close endpoint, do **not** silently skip the feature or fabricate a reference price. Instead:

- Add an optional `ref_price` field to each signal, hand-filled in `signals.json` during the quarterly refresh
- Compute drift against `ref_price` when present
- Where neither `ref_date` resolves nor `ref_price` exists, render the theme with a visible `DRIFT UNKNOWN` marker rather than an unadjusted score presented as if it were adjusted

An honest gap beats a confident wrong number. This is the whole reason the rule is being built.

---

## Constraints

- **The nightly board must not break.** If the staleness lookup fails for any reason, fall back to unadjusted scores, log it, and publish. Never crash the build.
- Failed historical lookups follow the existing `Quotes unavailable:` convention — never render as 0, never silently drop a signal.
- Do not touch `.github/workflows/` — the fine-grained PAT lacks the Workflows permission.
- Do not change the Board tab. Verify it stays pixel-identical, same as last time.
- No new dependencies, no build step.
- Cache historical closes where possible — a 13F period-end price never changes, so it should be fetched once and reused, not re-requested nightly.

---

## Done when

1. Every manager and insider signal in `signals.json` carries a `ref_date`
2. The ±3 adjustments compute nightly and are visible on the theme cards
3. AI Memory & Compute reflects a stale penalty rather than reading as an open entry window
4. The signal trail shows raw value, adjustment, and adjusted result
5. A failed lookup degrades visibly and never blocks the board
6. Board tab unchanged
