#!/usr/bin/env python3
"""Pull 13F-HR information tables from SEC EDGAR for the managers the Signals
tab tracks, and write them to holdings/.

Run by hand once a quarter, about a week after each 13F deadline
(Feb 26 · May 22 · Aug 21 · Nov 23). It is NOT part of the nightly job.

    export SEC_USER_AGENT="Your Name you@example.com"   # SEC requires a contact
    python3 fetch_13f.py

Writes:
    holdings/<manager>_<period>.json   one file per filer per quarter
    holdings/diff_<period>.md          latest quarter vs the one before
    holdings/cusip_tickers.json        CUSIP -> ticker cache (hand-editable)

Standard library only. EDGAR fair-access rules: a descriptive User-Agent with
contact details, and no more than 10 requests per second (we stay well under).
Tickers are looked up by CUSIP through OpenFIGI's free public mapping API; a
CUSIP it cannot resolve keeps ticker null rather than a guess. Add or correct
entries in cusip_tickers.json by hand and they win on the next run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MANAGERS = [
    # slug (file name),  display name,                       CIK
    ("whale_rock",   "Whale Rock Capital Management",   1387322),
    ("altimeter",    "Altimeter Capital Management",    1541617),
    ("duquesne",     "Duquesne Family Office",          1536411),
    ("d1",           "D1 Capital Partners",             1747057),
    ("light_street", "Light Street Capital Management", 1569049),
    ("srs",          "SRS Investment Management",       1503174),
    ("nvda_corp",    "NVIDIA Corp",                     1045810),
]

OUT = Path(__file__).resolve().parent / "holdings"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"
OPENFIGI = "https://api.openfigi.com/v3/mapping"
MIN_INTERVAL = 0.25          # seconds between EDGAR requests (4/s; SEC cap is 10/s)
RETRIES = 5


# ---------------------------------------------------------------- HTTP

class Edgar:
    """Throttled GET with backoff on 429/5xx. Mirrors the pattern in
    activist-accumulation-scanner/edgar_client.py, on urllib (no new deps)."""

    def __init__(self, ua: str):
        self.ua = ua
        self._last = 0.0

    def get(self, url: str) -> bytes:
        err = None
        for attempt in range(RETRIES):
            wait = MIN_INTERVAL - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            req = urllib.request.Request(url, headers={
                "User-Agent": self.ua, "Accept-Encoding": "identity"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                err = e
                if e.code not in (403, 429) and e.code < 500:
                    raise
            except urllib.error.URLError as e:
                err = e
            time.sleep(min(30, 2 ** attempt))
        raise RuntimeError(f"EDGAR GET failed after {RETRIES} tries: {url} :: {err}")

    def json(self, url: str):
        return json.loads(self.get(url).decode())


# ---------------------------------------------------------------- filings

def latest_13f(edgar: Edgar, cik: int, n: int = 2):
    """The n most recent 13F-HR filings, one per period (newest filing wins if a
    period was filed twice). 13F-HR/A amendments are listed separately so the
    diff file can flag them; they are not merged."""
    sub = edgar.json(SUBMISSIONS.format(cik=cik))
    r = sub["filings"]["recent"]
    rows = [dict(form=r["form"][i], acc=r["accessionNumber"][i],
                 filed=r["filingDate"][i], period=r["reportDate"][i])
            for i in range(len(r["form"]))]
    picked, seen = [], set()
    for row in rows:                                   # EDGAR lists newest first
        if row["form"] == "13F-HR" and row["period"] not in seen:
            seen.add(row["period"])
            picked.append(row)
        if len(picked) == n:
            break
    amends = [row for row in rows if row["form"] == "13F-HR/A" and row["period"] in seen]
    return sub["name"], picked, amends


def strip_ns(root):
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def txt(el, path, default=None):
    node = el.find(path)
    return node.text.strip() if node is not None and node.text else default


def fetch_filing(edgar: Edgar, cik: int, acc: str):
    base = ARCHIVE.format(cik=cik, acc=acc.replace("-", ""))
    items = edgar.json(base + "index.json")["directory"]["item"]
    xmls = [it["name"] for it in items if it["name"].lower().endswith(".xml")]
    cover = info = None
    for name in xmls:
        root = strip_ns(ET.fromstring(edgar.get(base + name)))
        if root.tag == "informationTable":
            info = root
        elif root.tag == "edgarSubmission":
            cover = root
    if info is None:
        raise RuntimeError(f"no information table in {acc}")
    summary = {}
    if cover is not None:
        s = cover.find(".//summaryPage")
        if s is not None:
            summary = {
                "table_entry_total": int(txt(s, "tableEntryTotal", "0")),
                "table_value_total": int(txt(s, "tableValueTotal", "0")),
            }
    rows = []
    for it in info.findall("infoTable"):
        rows.append({
            "issuer": txt(it, "nameOfIssuer"),
            "class": txt(it, "titleOfClass"),
            "cusip": (txt(it, "cusip") or "").upper(),
            "value": int(float(txt(it, "value", "0"))),
            "shares": int(float(txt(it, "shrsOrPrnAmt/sshPrnamt", "0"))),
            "share_type": txt(it, "shrsOrPrnAmt/sshPrnamtType"),
            "put_call": (txt(it, "putCall") or "").capitalize() or None,
        })
    return summary, rows


def aggregate(rows):
    """One position per (CUSIP, put/call): a manager often splits the same
    holding across discretion/other-manager lines."""
    pos = {}
    for r in rows:
        k = (r["cusip"], r["put_call"])
        if k not in pos:
            pos[k] = dict(r, lines=0, value=0, shares=0)
        p = pos[k]
        p["value"] += r["value"]
        p["shares"] += r["shares"]
        p["lines"] += 1
    return list(pos.values())


# ---------------------------------------------------------------- tickers

def _figi(jobs, ua):
    """One OpenFIGI mapping request (max 10 jobs without an API key)."""
    req = urllib.request.Request(OPENFIGI, data=json.dumps(jobs).encode(), headers={
        "Content-Type": "application/json", "User-Agent": ua})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.loads(r.read().decode())
            time.sleep(2.6)                            # 25 requests/minute
            return res
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(15 * (attempt + 1))
    return [{}] * len(jobs)


def _pick(hit):
    data = hit.get("data") or []
    us = [d for d in data if d.get("exchCode") == "US"] or data
    tick = us[0].get("ticker") if us else None
    tick = re.sub(r"[^A-Z0-9.]", "", tick.replace("/", ".").upper()) if tick else ""
    return tick or None


def resolve_tickers(cusips, cache_path: Path, ua: str, use_figi: bool):
    """CUSIP -> ticker. Pass 1 asks for the US composite listing; pass 2 retries
    misses as CINS (foreign issuers) or without the exchange filter. Misses stay
    null and are retried next run; a hand-entered ticker in the cache is kept."""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = sorted(c for c in set(cusips) if c and cache.get(c) is None)
    if use_figi and todo:
        print(f"  OpenFIGI: resolving {len(todo)} CUSIPs", file=sys.stderr)
        for i in range(0, len(todo), 10):
            batch = todo[i:i + 10]
            res = _figi([{"idType": "ID_CUSIP", "idValue": c, "exchCode": "US"} for c in batch], ua)
            for c, hit in zip(batch, res):
                cache[c] = _pick(hit)
        miss = [c for c in todo if cache.get(c) is None]
        for i in range(0, len(miss), 10):
            batch = miss[i:i + 10]
            res = _figi([{"idType": "ID_CINS" if c[0].isalpha() else "ID_CUSIP", "idValue": c}
                         for c in batch], ua)
            for c, hit in zip(batch, res):
                cache[c] = _pick(hit)
        cache_path.write_text(json.dumps(dict(sorted(cache.items())), indent=1) + "\n")
    return cache


# ---------------------------------------------------------------- output

def label(p):
    t = p.get("ticker") or p["issuer"]
    return f"{t} {p['put_call'].upper()}S" if p["put_call"] else t


def fmt_usd(v):
    if abs(v) >= 1e9:
        return f"${v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v / 1e3:.0f}K"


def diff_manager(name, cur, prev):
    # Match on ticker where resolved, so a CUSIP change (redomicile, reorg) is not
    # misread as an exit plus a new position. Falls back to CUSIP.
    def index(positions):
        out = {}
        for p in positions:
            k = (p["ticker"] or p["cusip"], p["put_call"])
            if k in out:
                q = out[k]
                out[k] = dict(q, shares=q["shares"] + p["shares"], value=q["value"] + p["value"],
                              weight=q["weight"] + p["weight"])
            else:
                out[k] = p
        return out
    c, o = index(cur["positions"]), index(prev["positions"])
    new = [c[k] for k in c if k not in o]
    gone = [o[k] for k in o if k not in c]
    adds, trims, flat = [], [], []
    for k in c.keys() & o.keys():
        a, b = o[k]["shares"], c[k]["shares"]
        (adds if b > a else trims if b < a else flat).append((o[k], c[k]))
    byw = lambda p: -p["weight"]
    out = [f"## {name}", "",
           f"{cur['period']}: {len(cur['positions'])} positions, {fmt_usd(cur['total_value'])} "
           f"(accession {cur['accession']}, filed {cur['filed']}) · "
           f"{prev['period']}: {len(prev['positions'])} positions, {fmt_usd(prev['total_value'])}", ""]
    if cur.get("check"):
        out += [f"> **Check:** {cur['check']}", ""]

    def table(title, rows, cols, fn):
        out.append(f"**{title} ({len(rows)})**")
        out.append("")
        if not rows:
            out.extend(["none", ""])
            return
        out.append("| " + " | ".join(cols) + " |")
        out.append("|" + "---|" * len(cols))
        out.extend("| " + " | ".join(fn(r)) + " |" for r in rows)
        out.append("")

    table("New", sorted(new, key=byw), ["Position", "Shares", "Value", "Weight"],
          lambda p: [label(p), f"{p['shares']:,}", fmt_usd(p["value"]), f"{p['weight']:.2f}%"])
    table("Exited", sorted(gone, key=byw), ["Position", "Prior shares", "Prior value", "Prior weight"],
          lambda p: [label(p), f"{p['shares']:,}", fmt_usd(p["value"]), f"{p['weight']:.2f}%"])
    chg = lambda pr: [label(pr[1]), f"{pr[0]['shares']:,}", f"{pr[1]['shares']:,}",
                      f"{(pr[1]['shares'] / pr[0]['shares'] - 1) * 100:+.1f}%" if pr[0]["shares"] else "n/a",
                      f"{pr[0]['weight']:.2f}%", f"{pr[1]['weight']:.2f}%"]
    hdr = ["Position", "Prior shares", "Shares", "Change", "Prior weight", "Weight"]
    table("Added", sorted(adds, key=lambda pr: -pr[1]["weight"]), hdr, chg)
    table("Trimmed", sorted(trims, key=lambda pr: -pr[1]["weight"]), hdr, chg)
    table("Unchanged share count", sorted(flat, key=lambda pr: -pr[1]["weight"]), hdr, chg)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--no-figi", action="store_true", help="skip OpenFIGI; use cache only")
    ap.add_argument("--only", help="comma-separated manager slugs")
    args = ap.parse_args()

    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in ua:
        sys.exit("Set SEC_USER_AGENT to a name and contact email, e.g.\n"
                 '  export SEC_USER_AGENT="Jane Doe jane@example.com"\n'
                 "SEC blocks requests without one.")
    edgar = Edgar(ua)
    OUT.mkdir(exist_ok=True)
    managers = [m for m in MANAGERS if not args.only or m[0] in args.only.split(",")]

    filings = {}
    for slug, name, cik in managers:
        sec_name, picked, amends = latest_13f(edgar, cik)
        print(f"{name} ({sec_name}): " + ", ".join(f"{f['period']} {f['acc']}" for f in picked),
              file=sys.stderr)
        docs = []
        for f in picked:
            summary, rows = fetch_filing(edgar, cik, f["acc"])
            docs.append((f, summary, rows))
        filings[slug] = (name, cik, sec_name, docs, amends)

    cusips = [r["cusip"] for v in filings.values() for _, _, rows in v[3] for r in rows]
    tickers = resolve_tickers(cusips, OUT / "cusip_tickers.json", ua, not args.no_figi)

    periods, diffs = set(), []
    for slug, (name, cik, sec_name, docs, amends) in filings.items():
        built = []
        for f, summary, rows in docs:
            # Some filers (Duquesne) still report value in $ thousands despite the
            # 2023 switch to whole dollars. A median implied share price under $1
            # gives it away; scale those filings so every file is in dollars.
            px = sorted(r["value"] / r["shares"] for r in rows
                        if r["share_type"] == "SH" and not r["put_call"] and r["shares"])
            units = "USD"
            if px and px[len(px) // 2] < 1.0:
                units = "USD (filer reported $ thousands; scaled x1000)"
                for r in rows:
                    r["value"] *= 1000
                if summary.get("table_value_total"):
                    summary["table_value_total"] *= 1000
            pos = aggregate(rows)
            total = sum(p["value"] for p in pos)
            for p in pos:
                p["ticker"] = tickers.get(p["cusip"])
                p["weight"] = round(p["value"] / total * 100, 4) if total else 0.0
            pos.sort(key=lambda p: -p["value"])
            check = []
            if summary.get("table_value_total") not in (None, total):
                check.append(f"cover page total {summary['table_value_total']:,} != table sum {total:,}")
            if summary.get("table_entry_total") not in (None, len(rows)):
                check.append(f"cover page entries {summary['table_entry_total']} != table rows {len(rows)}")
            doc = {
                "manager": name, "sec_name": sec_name, "cik": cik,
                "period": f["period"], "form": f["form"], "accession": f["acc"], "filed": f["filed"],
                "line_items": len(rows), "total_value": total,
                "value_units": units,
                "weight_basis": "% of total reported 13F value; option rows count at the value reported (underlying notional)",
                "amendments": [a["acc"] for a in amends if a["period"] == f["period"]],
                "check": "; ".join(check) or None,
                "positions": [{
                    "issuer": p["issuer"], "cusip": p["cusip"], "ticker": p["ticker"],
                    "class": p["class"], "put_call": p["put_call"], "shares": p["shares"],
                    "share_type": p["share_type"], "value": p["value"],
                    "weight": p["weight"], "lines": p["lines"],
                } for p in pos],
            }
            (OUT / f"{slug}_{f['period']}.json").write_text(json.dumps(doc, indent=1) + "\n")
            built.append(doc)
            periods.add(f["period"])
        if len(built) == 2:
            diffs += diff_manager(name, built[0], built[1])
            if any(built[0]["amendments"] + built[1]["amendments"]):
                diffs += [f"> Amendments on file (not merged): "
                          f"{', '.join(built[0]['amendments'] + built[1]['amendments'])}", ""]

    latest = max(periods)
    head = [f"# 13F diff — period ending {latest}", "",
            "Generated by `fetch_13f.py` from SEC EDGAR information tables. Adds and trims are by "
            "share count. Weight = share of the manager's total reported 13F value. Options rows "
            "(CALLS/PUTS) are separate positions, valued at the underlying notional as filed. "
            "A ticker shown as an issuer name means the CUSIP did not resolve.", ""]
    (OUT / f"diff_{latest}.md").write_text("\n".join(head + diffs) + "\n")
    print(f"wrote {len(filings) * 2} holdings files and diff_{latest}.md to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
