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
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px 16px 48px;max-width:640px;margin:0 auto}
/* Five text styles — every text node maps to one of these. */
h1{font-size:18px;font-weight:600;color:var(--ink)}                                                 /* t1 */
.sec{font-size:12px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--sub);margin:22px 0 8px} /* sec */
.tk,.wcard .t,.cm-name{font-size:14px;font-weight:600;color:var(--ink)}                             /* body1 */
p.body,.ds,.rule,.wcard .s,.cm-action,.cm-unplaced-note{font-size:13.5px;font-weight:400;color:var(--sub)} /* body2 */
.stamp,.rl,.legend,.foot,.stg,.cm-stamp,.cm-stage,.tagmeta,.cm-unplaced,.wcard .d{font-size:12px;font-weight:400;color:var(--mut)} /* meta */
/* One card style: calendar cards, gate/trigger rows, theme cards. */
.wcard,.rows,.cm-card{border:1px solid var(--line);border-radius:12px}
.top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:18px}
.rule{margin:-8px 0 4px}.tagmeta{margin:0 0 18px}
.week{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.wcard{padding:11px 14px}.wcard .t{margin:2px 0}
/* Decision-needed card — one of the three amber slots; children inherit warnink. */
.atgate{background:var(--warnbg);border-radius:12px;padding:11px 14px;color:var(--warnink)}
.atgate .h{display:flex;justify-content:space-between;font-size:14px;font-weight:600}
.atgate .z{font-size:12px;font-weight:400}
.atgate .n{font-size:13.5px;font-weight:400;margin-top:4px}
.rows{overflow:hidden}.row{padding:11px 14px}.row+.row{border-top:1px solid var(--line)}
.rh{display:flex;justify-content:space-between;align-items:baseline}
.track{display:flex;align-items:center;gap:8px;margin-top:8px}
.wall{width:3px;height:14px;background:var(--sub);border-radius:1px}
.rail{flex:1;position:relative;height:2px;background:var(--line)}
.pt{position:absolute;top:-4px;width:10px;height:10px;border-radius:50%;background:var(--dot)}
.rl{display:flex;justify-content:space-between;margin-top:5px}
.legend{margin:0 0 8px}
.foot{border-top:1px solid var(--line);margin-top:22px;padding-top:12px}
.chart{margin:6px 0 4px}
svg{display:block;width:100%;height:auto}
.curve{fill:none;stroke:var(--sub);stroke-width:2;stroke-linecap:round}
.tick{stroke:var(--line);stroke-width:1}
.stg{fill:var(--mut)}
.lead{stroke:var(--line);stroke-width:1}
.dot{fill:var(--dot);opacity:0;animation:pop .5s ease .15s forwards}
.lbl{font-size:12.5px;font-weight:600;fill:var(--ink)}                                              /* SVG theme label */
@keyframes pop{to{opacity:1}}
@media (prefers-reduced-motion:reduce){.dot{animation:none;opacity:1}}
.cm-stamp{margin:2px 0 12px}
.cm-note{font-size:13.5px;font-weight:400;font-style:italic;color:var(--sub);margin:2px 0 12px}    /* body2 — the one allowed italic */
#cm-reads{display:flex;flex-direction:column;gap:10px}
.cm-card{padding:11px 14px}
.cm-h{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.cm-stage{margin-top:2px}
.cm-action{margin-top:6px}
.cm-nm{margin-top:5px}.cm-nm .ds{margin-left:2px}
.cm-win{font-size:11px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;padding:2px 8px;border-radius:999px;white-space:nowrap} /* window pill */
.cm-unplaced-note{margin:22px 0 4px}
</style></head><body>
<div class="top"><h1>APEX board</h1><span class="stamp">updated __UPDATED__</span></div>
<p class="rule">A gate hit means open a Board Review in Claude &mdash; gates are hurdles, not green lights.</p>
<p class="tagmeta">A trigger is a pre-set price or event that makes us look again &mdash; never an automatic buy.</p>
<div class="sec">This week</div><div class="week">__WEEK__</div>
__ATGATE__
__NEAR__
__FAR__
__LEFT__
<p class="body" style="margin-top:16px">__FOOT__</p>
__CYCLEMAP__
__TRIGGERS__
<div class="foot"><a href="#cyclemap" style="color:var(--sub)">Cycle map &rarr;</a><br><br>Rebuilds each market night after US close. Manual refresh: repo &rarr; Actions &rarr; Update board &rarr; Run workflow. For underwriting, open the APEX project in Claude.</div>
</body></html>"""

CYCLEMAP_SECTION = """<div class="sec" id="cyclemap">Cycle map</div>
<p class="cm-stamp" id="cm-stamp">Board read &mdash;</p>
<p class="cm-note" id="cm-note"></p>
<div class="chart">
<svg viewBox="0 0 640 320" role="img" aria-label="Theme positions on the stealth to despair cycle curve">
  <path id="cm-curve" class="curve" d="M 12 236
    C 120 234, 200 212, 268 172
    C 330 134, 372 94, 428 76
    C 468 63, 486 70, 508 114
    C 532 158, 548 196, 578 210
    C 600 218, 618 214, 632 204"/>
  <line class="tick" x1="115" y1="268" x2="115" y2="276"/>
  <line class="tick" x1="265" y1="268" x2="265" y2="276"/>
  <line class="tick" x1="400" y1="268" x2="400" y2="276"/>
  <line class="tick" x1="520" y1="268" x2="520" y2="276"/>
  <text class="stg" x="57"  y="292" text-anchor="middle">stealth</text>
  <text class="stg" x="190" y="292" text-anchor="middle">awareness</text>
  <text class="stg" x="332" y="292" text-anchor="middle">mania</text>
  <text class="stg" x="460" y="292" text-anchor="middle">blow-off</text>
  <text class="stg" x="580" y="292" text-anchor="middle">despair</text>
  <g id="cm-marks"></g>
</svg>
</div>
<div id="cm-reads"></div>
<p class="cm-unplaced-note">Not yet placed &mdash; needs a fresh read at a review session.</p>
<p class="cm-unplaced" id="cm-unplaced"></p>
<script type="application/json" id="cycle-data">__CYCLEMAP_JSON__</script>
<script>
(function(){
  var el0 = document.getElementById('cycle-data');
  if (!el0) return;
  var data;
  try { data = JSON.parse(el0.textContent); } catch(e){ return; }
  var stamp = document.getElementById('cm-stamp');
  stamp.textContent = 'Board read ' + data.read_date;
  if (data.read_date_iso) {
    var days = Math.floor((Date.now() - new Date(data.read_date_iso + 'T00:00:00Z')) / 864e5);
    if (days > 35) {
      stamp.textContent += ' · ' + days + 'd old — refresh due';
      stamp.style.color = 'var(--warnink)';
    }
  }
  if (data.note) document.getElementById('cm-note').textContent = data.note;

  var NS = 'http://www.w3.org/2000/svg';
  var path = document.getElementById('cm-curve');
  var marks = document.getElementById('cm-marks');
  var L = path.getTotalLength();
  var pts = [];
  for (var i = 0; i <= 600; i++) pts.push(path.getPointAtLength(L * i / 600));
  function atX(x){
    var best = pts[0];
    for (var j = 1; j < pts.length; j++)
      if (Math.abs(pts[j].x - x) < Math.abs(best.x - x)) best = pts[j];
    return best;
  }
  function el(tag, attrs){
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function winStyle(w){
    w = w || '';
    if (w.indexOf('OPEN') > -1) return ['var(--warnbg)', 'var(--warnink)'];
    if (w.indexOf('WATCH') > -1) return ['var(--card)', 'var(--sub)'];
    if (w.indexOf('CLOSED') > -1) return ['var(--card)', 'var(--mut)'];
    return ['var(--card)', 'var(--sub)'];
  }
  var reads = document.getElementById('cm-reads');
  (data.themes || []).forEach(function(t){
    var p = atX(t.x * 640);
    var lx = (t.lx != null) ? t.lx : p.x + 10;
    var ly = (t.ly != null) ? t.ly : p.y - 14;
    var anchor = t.anchor || 'start';
    var tx = lx + (anchor === 'start' ? 2 : anchor === 'end' ? -2 : 0);
    marks.appendChild(el('line', {x1:p.x, y1:p.y, x2:tx, y2:ly + 4, 'class':'lead'}));
    marks.appendChild(el('circle', {cx:p.x, cy:p.y, r:5, 'class':'dot'}));
    var txt = el('text', {x:lx, y:ly, 'text-anchor':anchor, 'class':'lbl'});
    txt.textContent = t.name;
    marks.appendChild(txt);
    var card = document.createElement('div'); card.className = 'cm-card';
    var h = document.createElement('div'); h.className = 'cm-h';
    var nm = document.createElement('span'); nm.className = 'cm-name'; nm.textContent = t.name;
    var wl = document.createElement('span'); wl.className = 'cm-win'; wl.textContent = t.window || '';
    var ws = winStyle(t.window);
    wl.style.background = ws[0]; wl.style.color = ws[1];
    h.appendChild(nm); h.appendChild(wl); card.appendChild(h);
    var st = document.createElement('div'); st.className = 'cm-stage'; st.textContent = t.stage || ''; card.appendChild(st);
    if (t.action){ var ac = document.createElement('div'); ac.className = 'cm-action'; ac.textContent = t.action; card.appendChild(ac); }
    (t.names || []).forEach(function(n){
      var row = document.createElement('div'); row.className = 'cm-nm';
      var tk = document.createElement('span'); tk.className = 'tk'; tk.textContent = n.t;
      var ds = document.createElement('span'); ds.className = 'ds'; ds.textContent = '— ' + n.hook;
      row.appendChild(tk); row.appendChild(ds);
      card.appendChild(row);
    });
    reads.appendChild(card);
  });
  document.getElementById('cm-unplaced').textContent = (data.unplaced || []).join(' · ');
})();
</script>"""

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build():
    cfg = json.load(open("gates.json"))
    try:
        cyclemap_json = open("cycle_map.json").read()
    except FileNotFoundError:
        cyclemap_json = ""
    today = datetime.date.today()
    week = ""
    for c in cfg["calendar"]:
        if not c.get("date"):
            continue  # recurring entries (e.g. first_monday) drive the alert banner, not dated cards
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
                     '<div class="legend">dot = today&#39;s price &middot; wall = your trigger price &middot; full bar = 30% away</div>'
                     f'<div class="rows">{rows}</div>')

    far_html = ""
    if far:
        lst = ", ".join(x["t"] for x in sorted(far, key=lambda x: x["dist"]))
        lo, hi = min(x["dist"] for x in far), max(x["dist"] for x in far)
        far_html = (f'<div class="sec">Far away &mdash; nothing to do</div><p class="body">'
                    f'{len(far)} gates sit {lo:.0f}&ndash;{hi:.0f}% below today&#39;s price: {lst}. '
                    f'They only matter on a big drop or a proof trigger.</p>')

    left_html = ""
    if left:
        lst = ", ".join(f'{x["t"]} (+{x["dist"]:.0f}%)' for x in sorted(left, key=lambda x: x["dist"]))
        left_html = (f'<div class="sec">Ran away without us &mdash; delete these triggers?</div><p class="body">'
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
            .replace("__ATGATE__", ('<div class="sec">At the trigger &mdash; decision needed</div>' + at_html) if at_html else "")
            .replace("__NEAR__", near_html).replace("__FAR__", far_html)
            .replace("__LEFT__", left_html).replace("__CYCLEMAP__", cyclemap_html(cyclemap_json))
            .replace("__TRIGGERS__", triggers_html(cfg))
            .replace("__FOOT__", esc_foot(foot)))
    open("index.html", "w").write(html)
    print(f"index.html written: {len(at_html and 'x')} at-gate, {len(near)} near, {len(far)} far, {len(left)} left-behind")

def esc_foot(s):
    return s

def triggers_html(cfg):
    trigs = cfg.get("triggers", [])
    if not trigs:
        return ""
    rows = "".join(
        f'<div class="row"><span class="tk">{esc(tr["t"])}</span> '
        f'<span class="ds">{esc(tr["event"])}</span></div>'
        for tr in trigs)
    return ('<div class="sec">Waiting on news, not prices</div>'
            f'<div class="rows">{rows}</div>')

def cyclemap_html(json_text):
    """Cycle map merged into the board: same SVG curve + dot JS as the old
    standalone page, but the list below is rendered in array order (the focus
    ranking) with window / stage / action / names. Data injected at build time."""
    if not json_text.strip():
        return ""
    return CYCLEMAP_SECTION.replace("__CYCLEMAP_JSON__", json_text)

def atgate_card(n):
    return (f'<div class="atgate"><div class="h"><span>{n["t"]} &middot; ${n["price"]:,.2f}</span>'
            f'<span class="z">{esc(n.get("zone", "gate $" + format(n["gate"], ",")))}</span></div>'
            f'<div class="n">{esc(n["note"]) or "At its gate. Open a Board Review."}</div></div>')

if __name__ == "__main__":
    build()
