#!/usr/bin/env python3
"""Builds index.html for the APEX board (GitHub Pages).
Static, self-contained, dark-mode aware. Fails loudly on bad data."""
import datetime, json, os, time, urllib.parse, urllib.request

FMP_KEY = os.environ.get("FMP_API_KEY", "")
BASE = "https://financialmodelingprep.com/stable/"

def fetch(path, **params):
    params["apikey"] = FMP_KEY
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"FMP unreachable: {path} :: {err}")

def quote(sym, crypto=False):
    endpoints = ("quote", "cryptocurrency-quote") if crypto else ("quote",)
    for ep in endpoints:
        try:
            rows = fetch(ep, symbol=sym)
        except RuntimeError:
            continue
        if isinstance(rows, list) and rows and rows[0].get("price"):
            return rows[0]
    return None

TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>APEX board</title><style>
:root{--bg:#faf9f5;--card:#f1efe8;--ink:#2c2c2a;--sub:#5f5e5a;--mut:#888780;
--line:#d3d1c7;--warnbg:#faeeda;--warnink:#854f0b;--dot:#2c2c2a}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a18;--card:#262624;--ink:#eceae4;
--sub:#b4b2a9;--mut:#888780;--line:#444441;--warnbg:#412402;--warnink:#fac775;--dot:#eceae4}}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px 16px 48px;max-width:640px;margin:0 auto}
h1{font-size:18px;font-weight:600}.top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:18px}
.stamp{font-size:12px;color:var(--mut)}.sec{font-size:12px;font-weight:600;letter-spacing:.03em;
text-transform:uppercase;color:var(--sub);margin:22px 0 8px}.sec.warn{color:var(--warnink)}
.week{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.wcard{background:var(--card);border-radius:10px;padding:10px 12px}
.wcard .d{font-size:12px;color:var(--mut)}.wcard .t{font-size:14px;font-weight:600;margin:2px 0}
.wcard .s{font-size:12px;color:var(--sub)}
.atgate{background:var(--warnbg);border-radius:12px;padding:12px 14px;color:var(--warnink)}
.atgate .h{display:flex;justify-content:space-between;font-size:15px;font-weight:600}
.atgate .z{font-size:12px;font-weight:400}.atgate .n{font-size:13px;margin-top:4px}
.rows{border:1px solid var(--line);border-radius:12px;overflow:hidden}
.row{padding:11px 14px}.row+.row{border-top:1px solid var(--line)}
.rh{display:flex;justify-content:space-between;align-items:baseline}
.rh .tk{font-size:14px;font-weight:600}.rh .ds{font-size:13px;color:var(--sub)}
.track{display:flex;align-items:center;gap:8px;margin-top:8px}
.wall{width:3px;height:14px;background:var(--sub);border-radius:1px}
.rail{flex:1;position:relative;height:2px;background:var(--line)}
.pt{position:absolute;top:-4px;width:10px;height:10px;border-radius:50%;background:var(--dot)}
.rl{display:flex;justify-content:space-between;font-size:11.5px;color:var(--mut);margin-top:5px}
p.body{font-size:13.5px;color:var(--sub)}.legend{font-size:12px;color:var(--mut);margin:0 0 8px}
.foot{border-top:1px solid var(--line);margin-top:22px;padding-top:12px;font-size:12px;color:var(--mut)}
.rule{font-size:12.5px;color:var(--sub);margin:-8px 0 16px}
</style></head><body>
<div class="top"><h1>APEX board</h1><span class="stamp">updated __UPDATED__</span></div>
<p class="rule">A gate hit means open a Board Review in Claude &mdash; gates are hurdles, not green lights.</p>
<div class="sec">This week</div><div class="week">__WEEK__</div>
__ATGATE__
__NEAR__
__FAR__
__LEFT__
<div class="foot"><a href="cycle-map.html" style="color:var(--sub)">Cycle map &rarr;</a><br><br>__FOOT__<br><br>Rebuilds each market night after US close. Manual refresh: repo &rarr; Actions &rarr; Update board &rarr; Run workflow. For underwriting, open the APEX project in Claude.</div>
</body></html>"""

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build():
    cfg = json.load(open("gates.json"))
    today = datetime.date.today()
    week = ""
    for c in cfg["calendar"]:
        if datetime.date.fromisoformat(c["date"]) >= today:
            week += (f'<div class="wcard"><div class="d">{esc(c["label"])}</div>'
                     f'<div class="t">{esc(c["title"])}</div><div class="s">{esc(c["sub"])}</div></div>')
    if not week:
        week = '<div class="wcard"><div class="s">No dated catalysts on file &mdash; sync gates.json at next Board.</div></div>'

    at_html, near, far, left, failed = "", [], [], [], []
    for n in cfg["names"]:
        q = quote(n["t"])
        if not q:
            failed.append(n["t"]); continue
        p = q["price"]; d = (p - n["gate"]) / n["gate"] * 100
        n2 = dict(n, price=p, dist=d)
        if n.get("at_gate") or d <= 10: at_html += atgate_card(n2)
        elif d <= 30: near.append(n2)
        elif d <= 80: far.append(n2)
        else: left.append(n2)
    if failed and len(failed) >= len(cfg["names"]) // 2:
        raise RuntimeError(f"quotes failed for {failed} -- refusing to publish a blind board")

    near_html = ""
    if near:
        rows = ""
        for n in sorted(near, key=lambda x: x["dist"]):
            pos = min(96, n["dist"] / 30 * 100)
            sub = esc(n["note"]) if n["note"] else f'${n["price"]:,.2f} now'
            rows += (f'<div class="row"><div class="rh"><span class="tk">{n["t"]}</span>'
                     f'<span class="ds">{n["dist"]:.0f}% above its gate</span></div>'
                     f'<div class="track"><span class="wall"></span><span class="rail">'
                     f'<span class="pt" style="left:{pos:.0f}%"></span></span></div>'
                     f'<div class="rl"><span>gate ${n["gate"]:,}</span><span>{sub}</span></div></div>')
        near_html = ('<div class="sec">Approaching</div>'
                     '<div class="legend">dot = last close &middot; wall = your gate &middot; full track = 30% away</div>'
                     f'<div class="rows">{rows}</div>')

    far_html = ""
    if far:
        lst = ", ".join(x["t"] for x in sorted(far, key=lambda x: x["dist"]))
        lo, hi = min(x["dist"] for x in far), max(x["dist"] for x in far)
        far_html = (f'<div class="sec">Far away &mdash; nothing to do</div><p class="body">'
                    f'{len(far)} gates sit {lo:.0f}&ndash;{hi:.0f}% below last close: {lst}. '
                    f'They only matter on a big drop or a proof trigger.</p>')

    left_html = ""
    if left:
        lst = ", ".join(f'{x["t"]} (+{x["dist"]:.0f}%)' for x in sorted(left, key=lambda x: x["dist"]))
        left_html = (f'<div class="sec">Left behind &mdash; retire these gates?</div><p class="body">'
                     f'{lst} ran without you; their gates are effectively dead. Culling decision at Board.</p>')

    foot = ""
    b = quote("BTCUSD", crypto=True)
    if b:
        bp = b["price"]; z = cfg["btc"]
        state = ("armed above the trigger zone, pending Board ratification" if bp >= z["trigger_low"]
                 else "below the trigger zone" if bp > z["falsifier"]
                 else "NEAR FALSIFIER \u2014 Board review")
        foot += f'BTC ${bp:,.0f} \u2014 {state}.'
    if failed:
        foot += f' Quotes unavailable: {", ".join(failed)}.'

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %H:%M UTC")
    html = (TEMPLATE.replace("__UPDATED__", now).replace("__WEEK__", week)
            .replace("__ATGATE__", ('<div class="sec warn">At the gate &mdash; action owed</div>' + at_html) if at_html else "")
            .replace("__NEAR__", near_html).replace("__FAR__", far_html)
            .replace("__LEFT__", left_html).replace("__FOOT__", esc_foot(foot)))
    open("index.html", "w").write(html)
    print(f"index.html written: {len(at_html and 'x')} at-gate, {len(near)} near, {len(far)} far, {len(left)} left-behind")

def esc_foot(s):
    return s

def atgate_card(n):
    return (f'<div class="atgate"><div class="h"><span>{n["t"]} &middot; ${n["price"]:,.2f}</span>'
            f'<span class="z">{esc(n.get("zone", "gate $" + format(n["gate"], ",")))}</span></div>'
            f'<div class="n">{esc(n["note"]) or "At its gate. Open a Board Review."}</div></div>')

if __name__ == "__main__":
    build()
