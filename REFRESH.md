# Refreshing the Signals tab

The Signals tab shows what a handful of hedge funds (and NVIDIA) bought and sold, grouped into themes. Funds report their holdings to the SEC once a quarter in a filing called a **13F**, due 45 days after each quarter ends. So the Signals tab needs a refresh **four times a year**, about a week after each deadline, when the filings have all arrived:

| Refresh on | Covers holdings as of |
|---|---|
| **Feb 26** | Dec 31 |
| **May 22** | Mar 31 |
| **Aug 21** | Jun 30 |
| **Nov 23** | Sep 30 |

If a refresh is skipped, the page notices on its own: two quarter-ends after a filing, its signals stop counting and show **UNREFRESHED**.

The APEX board tab rebuilds itself every night and needs none of this.

---

## The short version

1. Set your contact details for the SEC.
2. Run `fetch_13f.py`.
3. Read the diff it writes.
4. Edit `signals.json`.
5. Push, then run **Update board**.

The easiest way to do steps 3 and 4 is to open Claude Code in this folder and say: *"Do the quarterly Signals refresh per REFRESH.md."*

---

## Step by step

All commands are typed in Terminal, in the `apex-board` folder.

### 1. Tell the SEC who you are — every time

The SEC asks every automated download to carry the name and email of a real person. **Use your own real name and email, every time you run the refresh.** Type:

```
export SEC_USER_AGENT="Your Name your@email.com"
```

This lasts until you close the Terminal window. Never put your email into a file in this folder — the repository is public.

### 2. Download the filings

```
python3 fetch_13f.py
```

It takes a minute or two and needs nothing installed beyond the Python that comes with the Mac. It prints one line per fund, showing which quarters it found, for example `Whale Rock … 2026-09-30 …, 2026-06-30 …`.

**Check that every fund shows the new quarter.** If one still shows the previous quarter, that fund hasn't filed yet: wait a few days and run it again.

It writes, in the `holdings` folder:

- one file per fund per quarter, for example `whale_rock_2026-09-30.json`: every position, with shares, value and percent of the fund
- `diff_<date>.md`: what each fund bought new, sold out of, added to and trimmed, in plain tables. **This is the file to read.**

### 3. Read the diff

Open `holdings/diff_<date>.md`. For each fund it lists new positions, exits, adds and trims, with each position's weight in the fund. Note anything flagged **Check:** at the top of a fund's section: it means the fund's own cover page and its table disagree slightly (usually rounding).

If a position shows a company name instead of a ticker, the ticker lookup failed. Add it by hand in `holdings/cusip_tickers.json` (the 9-character code → the ticker) and rerun step 2.

### 4. Update `signals.json`

This file is what the page reads. Each **signal** is one fund's move in one stock, with a score. The scoring rules are written into the file itself, in the `_rubric` field. The main ones:

- Only positions that are at least 1% of a fund count.
- New positions score by size (5%+ of the fund = 9, down to 1–2% = 4); adds score +3 to +6; trims −2 to −5; full exits −2 to −7 depending on how big the position was.
- A position held steady only counts if it is one of the fund's three largest.
- Several equal-sized new positions bought together count as one "basket" signal.
- A stake that only became visible because the company listed (it was bought privately before) scores 0: "newly visible, not newly bought".
- Options rows matter: **puts are bets against** (or hedges), not holdings.
- Every fund signal needs `ref_date` (the quarter-end of the filing where the move happened) and `trace` (which holdings file and ticker it came from). Never enter a number from a news site or aggregator; only from the holdings files.
- Retire congressional, insider, screen and earnings signals older than two quarters. Refresh the price signals to the latest close.

Also update the dated text: `as_of`, `next_refresh`, `meta`, `copy`, `freshness`, the `managers` cards, `changed` (what's new this quarter) and `audit` (how last quarter's calls turned out).

Check the file is still valid before saving your work:

```
python3 -m json.tool signals.json > /dev/null && echo OK
```

### 5. Publish

```
git add holdings signals.json
git commit -m "Signals refresh: Qx YYYY holdings"
git push
```

Pushing does not rebuild the page by itself. Either wait for the nightly build, or go to the repository on GitHub → **Actions** → **Update board** → **Run workflow**. It takes about a minute.

### 6. Look at the page

Open the board, switch to the **Signals** tab and check for:

- **Quotes unavailable** / **Reference prices unavailable** at the bottom: the price service missed some tickers. Usually temporary; check the next night.
- **UNREFRESHED** on a theme: a fund's signals are two or more quarter-ends old. You missed a fund in step 4.
- **CHECK: possible split**: the stock split after the filing date. The drift figure is still split-adjusted and correct. Only worry if you typed a `ref_price` by hand for that signal.

---

## What the badges mean

STALE and DISLOCATED only apply to buy signals; trims and exits show their price drift but are never adjusted.

| Badge | Meaning | Points |
|---|---|---|
| NEW | Fresh move this quarter | — |
| STALE −3 | On a buy: the price has run up more than 30% since the filing, so the entry is probably gone | −3 |
| DISLOCATED | On a buy: the price has dropped more than 15% since the filing. That could be a better entry, or the reason the fund has since sold. The filing can't tell | none |
| CONTESTED | Strong buying and strong selling in the same theme | — |
| NVDA | NVIDIA holds something in this theme. NVIDIA invests for supply-chain reasons, so it is shown as context, not scored | none |
| UNREFRESHED | Signals two or more quarter-ends old; not scored | none |

**High conviction** needs a score of 25 or more **and** buying from at least two different funds. Each fund counts at most its two biggest buys and two biggest sells per theme, so one fund can't carry a theme by volume alone.
