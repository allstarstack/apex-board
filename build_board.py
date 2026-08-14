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
<title>APEX board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#faf9f5;--card:#f1efe8;--ink:#2c2c2a;--sub:#5f5e5a;--mut:#888780;
--line:#d3d1c7;--warnbg:#faeeda;--warnink:#854f0b;--dot:#2c2c2a}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a18;--card:#262624;--ink:#eceae4;
--sub:#b4b2a9;--mut:#888780;--line:#444441;--warnbg:#412402;--warnink:#fac775;--dot:#eceae4}}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
#board{padding:24px 16px 48px;max-width:640px;margin:0 auto}
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
/* ── Tabs (board / signals). Board CSS above is unchanged; everything Signals is scoped to #signals. ── */
nav.tabs{max-width:640px;margin:0 auto;padding:16px 16px 4px;display:flex;gap:8px;align-items:baseline}
nav.tabs a{font:600 13px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;text-decoration:none;color:var(--sub);padding:7px 14px;border:1px solid var(--line);border-radius:999px}
nav.tabs a[aria-selected="true"]{color:var(--ink);border-color:var(--ink)}
nav.tabs a:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.tabpanel[hidden]{display:none}
body.tab-signals{background:#0d0c0a}
body.tab-signals nav.tabs{max-width:900px}
body.tab-signals nav.tabs a{color:#8a8275;border-color:#2a2620;font-family:'IBM Plex Mono',monospace}
body.tab-signals nav.tabs a[aria-selected="true"]{color:#c8a05e;border-color:#c8a05e}
/* ── Signals — ported from stack.html, every selector scoped to #signals, vars scoped to the panel ── */
#signals{--bg:#0d0c0a;--panel:#16140f;--line:#2a2620;--text:#e8e4d8;--dim:#8a8275;--mute:#5a5448;
--gold:#c8a05e;--amber:#b8804a;--rust:#a05438;--sage:#7a8a6e;--danger:#8b1a1a;--blue:#5a7a8c;--violet:#7d6b9e;--nv:#76b900;--grey:#6b5d45;
font-family:'IBM Plex Mono',monospace;font-size:14px;line-height:1.6;color:var(--text);-webkit-font-smoothing:antialiased}
#signals *{box-sizing:border-box;margin:0;padding:0}
#signals .wrap{max-width:900px;margin:0 auto;padding:0 20px}
@media(min-width:700px){#signals .wrap{padding:0 40px}}
#signals .eyebrow{font-size:10px;letter-spacing:.2em;color:var(--mute);text-transform:uppercase}
#signals a{color:var(--gold);text-decoration:none;border-bottom:1px solid rgba(200,160,94,.3)}
#signals a:hover{border-bottom-color:var(--gold)}
#signals a:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
#signals header{border-bottom:1px solid var(--line);padding:32px 0 24px}
#signals h1{font-family:'Instrument Serif',serif;font-size:44px;line-height:1;font-weight:400;margin:8px 0 0;color:var(--text)}
#signals h1 em{color:var(--gold)}
#signals .sub{color:var(--dim);font-size:12px;margin-top:12px;max-width:56ch}
#signals .navrow{display:flex;gap:16px;flex-wrap:wrap;align-items:baseline;margin-top:18px;font-size:11px;color:var(--mute)}
#signals section{padding:32px 0;border-bottom:1px solid var(--line)}
#signals h2{font-family:'Instrument Serif',serif;font-size:26px;font-style:italic;font-weight:400;margin:6px 0 4px}
#signals .lede{color:var(--dim);font-size:12px;max-width:64ch;margin-bottom:18px}
#signals .stale{background:linear-gradient(180deg,rgba(184,128,74,.10),transparent);border-left:3px solid var(--amber);padding:14px 16px;margin-top:18px}
#signals .stale b{color:var(--text)}
#signals .stale table{width:100%;border-collapse:collapse;margin-top:10px;font-size:11px}
#signals .stale td{padding:3px 0;color:var(--dim)}
#signals .stale td:last-child{text-align:right}
#signals .ok{color:var(--sage)} #signals .old{color:var(--amber)}
#signals .unavail{color:var(--amber);font-size:11px;margin-top:12px}
#signals .cards{display:grid;gap:10px}
@media(min-width:700px){#signals .cards{grid-template-columns:1fr 1fr}}
#signals .card{background:var(--panel);border-left:3px solid var(--grey);padding:14px 16px}
#signals .card h3{font-family:'Instrument Serif',serif;font-size:18px;font-weight:400;margin-bottom:6px}
#signals .card p{font-size:11px;color:var(--dim)}
#signals .card .tag{font-size:9px;letter-spacing:.2em;float:right}
#signals .card .lesson{font-size:10px;color:var(--mute);font-style:italic;border-top:1px solid var(--line);margin-top:8px;padding-top:7px}
#signals .zone{margin-bottom:34px}
#signals .zonehead{background:var(--panel);border-left:4px solid var(--gold);padding:12px 16px;display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:12px}
#signals .zonehead .t{font-family:'Instrument Serif',serif;font-size:24px;font-style:italic}
#signals .zonehead .s{font-size:10px;color:var(--dim);margin-top:2px}
#signals .theme{background:var(--bg);border:1px solid var(--line);border-left:3px solid var(--grey);padding:14px 16px;margin-bottom:9px}
#signals .theme.held{border-color:var(--gold)}
#signals .theme .top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:0}
#signals .theme .name{font-family:'Instrument Serif',serif;font-size:19px}
#signals .theme .score{font-family:'Instrument Serif',serif;font-size:21px}
#signals .theme .act{font-family:'Instrument Serif',serif;font-size:15px;font-style:italic;margin-top:6px}
#signals .theme .when{font-size:10px;color:var(--dim);float:right;margin-top:9px}
#signals .theme .why{font-size:11px;color:var(--dim);margin-top:5px;clear:both}
#signals .badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}
#signals .b{font-size:8px;letter-spacing:.15em;padding:2px 6px;border:1px solid currentColor}
#signals .tk{display:flex;gap:5px;flex-wrap:wrap;margin-top:9px}
#signals .tk span{font-size:10px;font-weight:400;color:var(--dim);padding:1px 6px;background:var(--panel);border:1px solid var(--line)}
#signals .tk span.own{color:var(--gold);border-color:var(--gold)}
#signals .px{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
#signals .pc{font-size:10px;color:var(--dim);padding:1px 6px;background:var(--bg);border:1px dashed var(--line)}
#signals .pc b{color:var(--text);font-weight:500}
#signals .pc em{font-style:normal;margin-left:3px}
#signals .pc em.pos{color:var(--sage)} #signals .pc em.neg{color:var(--rust)}
#signals .pc.na{color:var(--amber);border-color:var(--amber);border-style:solid}
#signals details{margin-top:9px}
#signals summary{font-size:10px;color:var(--mute);cursor:pointer;list-style:none}
#signals summary::-webkit-details-marker{display:none}
#signals summary:hover{color:var(--dim)}
#signals .trail{margin-top:8px;border-top:1px solid var(--line)}
#signals .sig{display:grid;grid-template-columns:52px 1fr 34px;gap:8px;padding:5px 0;border-bottom:1px solid var(--line);font-size:10px;align-items:baseline}
#signals .sig .t{color:var(--text)}
#signals .sig .src{font-size:8px;letter-spacing:.1em;color:var(--mute)}
#signals .sig .d{color:var(--dim)}
#signals .sig .n{text-align:right;font-family:'Instrument Serif',serif;font-size:12px}
#signals .pos{color:var(--sage)} #signals .neg{color:var(--rust)}
#signals .rules{display:grid;gap:9px}
@media(min-width:700px){#signals .rules{grid-template-columns:1fr 1fr}}
#signals .rule{background:var(--panel);border-left:2px solid var(--grey);padding:12px 14px;margin:0}
#signals .rule .w{font-size:11px;color:var(--text)}
#signals .rule .t{font-family:'Instrument Serif',serif;font-size:14px;font-style:italic;margin:6px 0 4px}
#signals .rule .n{font-size:10px;color:var(--dim)}
#signals .mgr{background:var(--bg);border:1px solid var(--line);border-left:3px solid var(--sage);padding:16px;margin-bottom:12px}
#signals .mgr.north{border-left-color:var(--gold)} #signals .mgr.strat{border-left-color:var(--nv)}
#signals .mgr .h{display:flex;gap:9px;align-items:baseline;flex-wrap:wrap}
#signals .mgr .nm{font-family:'Instrument Serif',serif;font-size:20px}
#signals .mgr .who{font-size:10px;color:var(--mute)}
#signals .mgr .pill{font-size:9px;letter-spacing:.15em;padding:2px 7px;border:1px solid currentColor}
#signals .mgr .val{font-size:10px;color:var(--mute);margin-top:5px}
#signals .mgr .note{font-size:11px;color:var(--dim);font-style:italic;margin:9px 0}
#signals .mgr .cols{display:grid;gap:12px;margin-top:10px}
@media(min-width:700px){#signals .mgr .cols{grid-template-columns:1fr 1fr}}
#signals .mgr .cols h4{font-size:9px;letter-spacing:.2em;font-weight:400;margin-bottom:5px}
#signals .mgr .cols div{font-size:10px;color:var(--dim);line-height:1.7}
#signals footer{padding:28px 0 40px;text-align:center;font-size:10px;color:var(--mute)}
#signals footer .how{background:var(--panel);border-left:3px solid var(--line);padding:12px 14px;text-align:left;font-size:11px;color:var(--dim);margin-bottom:20px;line-height:1.8}
#signals footer .sig-line{font-family:'Instrument Serif',serif;font-style:italic;letter-spacing:.15em}
@media(prefers-reduced-motion:no-preference){#signals section{animation:sigfade .5s ease both}
@keyframes sigfade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}}
</style></head><body class="tab-board">
<nav class="tabs" aria-label="Views">
<a id="tab-board" href="#board" aria-selected="true">Board</a>
<a id="tab-signals" href="#signals" aria-selected="false">Signals</a>
</nav>
<div id="board" class="tabpanel">
<div class="top"><h1>APEX board</h1><span class="stamp">updated __UPDATED__</span></div>
<p class="rule">A gate hit means open a Board Review in Claude &mdash; gates are hurdles, not green lights.</p>
<p class="tagmeta">A trigger is a pre-set price or event that makes us look again &mdash; never an automatic buy.</p>
<div class="sec">This week</div><div class="week">__WEEK__</div>
__ATGATE__
__NEAR__
__FAR__
__FRESH__
__LEFT__
<p class="body" style="margin-top:16px">__FOOT__</p>
__CYCLEMAP__
__TRIGGERS__
<div class="foot"><a href="#cyclemap" style="color:var(--sub)">Cycle map &rarr;</a><br><br>Rebuilds each market night after US close. Manual refresh: repo &rarr; Actions &rarr; Update board &rarr; Run workflow. For underwriting, open the APEX project in Claude.</div>
</div>
__SIGNALS__
<script>
(function(){
  var pb=document.getElementById('board'),ps=document.getElementById('signals');
  var lb=document.getElementById('tab-board'),ls=document.getElementById('tab-signals');
  function show(w){
    if(w!=='signals'||!ps)w='board';
    pb.hidden=w!=='board'; if(ps)ps.hidden=w!=='signals';
    lb.setAttribute('aria-selected',w==='board'); ls.setAttribute('aria-selected',w==='signals');
    document.body.className='tab-'+w;
  }
  function fromHash(){show(location.hash==='#signals'?'signals':'board');}
  window.addEventListener('hashchange',fromHash); fromHash();
})();
</script>
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

# Signals tab: ported from stack.html. The panel is static; the scoring engine and
# renderers are the verbatim stack.html JS, reading inputs from signals.json (embedded
# as JSON) instead of inline consts, plus live price chips from a second JSON blob.
SIGNALS_SECTION = r"""<div id="signals" class="tabpanel" hidden>
<div class="wrap">
<header>
  <div class="eyebrow">Stack &mdash; signal layer, upstream of APEX</div>
  <h1>Theme <em>Map</em></h1>
  <div class="sub">Six concentrated managers, insider clusters, congressional trades, NVDA strategic capital, and price. Generates candidates. Never verdicts &mdash; APEX decides.</div>
  <div class="navrow"><span id="sig-meta"></span><span>__PRICE_STAMP__</span></div>
</header>
<section>
  <div class="eyebrow">Data freshness &mdash; read this first</div>
  <h2>What this page actually knows</h2>
  <div class="lede">Positions are point-in-time snapshots from 13F filings, not live. A manager could have exited the day after the reporting date.</div>
  <div class="stale"><span id="stale-intro"></span>
    <table><tbody id="stale-rows"></tbody></table>
  </div>
  __SIGNALS_UNAVAIL__
</section>
<section>
  <div class="eyebrow" id="audit-eyebrow"></div>
  <h2>What the engine got right and wrong</h2>
  <div class="lede">Two refresh windows were missed, which left the May calls untouched long enough to score honestly. Every miss below produced a rule change, and those rules are now live in the scoring.</div>
  <div class="cards" id="audit"></div>
</section>
<section>
  <div class="eyebrow">What changed</div>
  <h2 id="changed-h2"></h2>
  <div class="cards" id="changed"></div>
</section>
<section>
  <div class="eyebrow">Zones</div>
  <h2>Sorted by what to do about it</h2>
  <div class="lede">Zone order adapts: urgent exits lead when you hold something in them, otherwise opportunity leads. Within a zone &mdash; exits by urgency, buys by score, watch by recency. Anything you already hold sorts first.</div>
  <div id="zones"></div>
</section>
<section>
  <div class="eyebrow">Exit timing &mdash; recalibrated from the audit</div>
  <h2>How long you have, by trigger</h2>
  <div class="rules" id="rules"></div>
</section>
<section>
  <div class="eyebrow">Seven sources</div>
  <h2>Who we track, what they hold</h2>
  <div id="mgrs"></div>
</section>
<footer>
  <div class="how">
    <b style="color:var(--text)">Refreshing this page</b> &mdash; quarterly, about five business days after each 13F deadline:
    <b style="color:var(--text)">Feb 24 &middot; May 22 &middot; Aug 21 &middot; Nov 23</b>.
    Open the Stack project in Claude, say <b style="color:var(--text)">refresh theme map</b>, then edit <code>signals.json</code> in the apex-board repo and push. GitHub Pages redeploys on commit; the nightly job keeps the prices current.
    <br><br>
    The APEX board rebuilds itself nightly and needs none of this.
  </div>
  <div class="sig-line">whale rock 1.5&times; &middot; nvda strategic 2.0&times; &middot; signals expire</div>
</footer>
</div>
</div>
<script type="application/json" id="signals-data">__SIGNALS_JSON__</script>
<script type="application/json" id="signals-prices">__SIGNALS_PRICES__</script>
<script>
(function(){
  var el0=document.getElementById('signals-data');
  if(!el0) return;
  var DATA,PRICES;
  try{ DATA=JSON.parse(el0.textContent);
       PRICES=JSON.parse(document.getElementById('signals-prices').textContent); }
  catch(e){ return; }
  var W=DATA.manager_weights, HELD=DATA.held, S=DATA.signals,
      AUDIT=DATA.audit, CHANGED=DATA.changed, RULES=DATA.rules, MGRS=DATA.managers;

  // ── scoring (verbatim from stack.html) ──────────────
  const themes={};
  S.forEach(s=>{
    const k=s.th;
    themes[k]=themes[k]||{n:k,sig:[],tk:new Set(),src:new Set(),who:new Set(),raw:0,old:0,fresh:999,nu:false,nv:false};
    const t=themes[k];
    t.sig.push(s); t.tk.add(s.t); t.src.add(s.src);
    s.by.split('+').forEach(x=>{if(s.v>0)t.who.add(x.trim())});
    t.raw+=s.v*(W[s.by]||1);
    t.old=Math.max(t.old,s.w); t.fresh=Math.min(t.fresh,s.w);
    if(s.nu)t.nu=true;
    if(s.by==='NVDA Corp'&&s.v>0)t.nv=true;
  });

  const list=Object.values(themes).map(t=>{
    const wr=t.sig.some(s=>s.by.indexOf('Whale Rock')===0&&s.v>0);
    const wrTrim=t.sig.some(s=>s.by.indexOf('Whale Rock')===0&&s.v<0);
    t.score=Math.round(t.raw+t.src.size*2+(wr?3:0)+(t.nv?4:0));
    t.wr=wr; t.wrTrim=wrTrim;
    t.own=[...t.tk].filter(x=>HELD.includes(x));

    const pos=t.sig.filter(s=>s.v>0).reduce((a,s)=>a+s.v,0);
    const neg=Math.abs(t.sig.filter(s=>s.v<0).reduce((a,s)=>a+s.v,0));
    t.contested=pos>=12&&neg>=6;

    const insider=t.sig.some(s=>s.src==='insider'&&s.v<=-6);
    const broke=t.sig.some(s=>s.src==='price'&&s.v<=-6);
    const left=t.sig.some(s=>/exited|cut \d|top sell/i.test(s.a))&&t.score<5;

    if(t.contested){t.stage='CONTESTED';t.col='--violet';t.zone='watch';t.when='Resolve before acting';
      t.act=t.own.length?'Hold — resolve the disagreement':'APEX must pick a side';
      t.why='Bull and bear signals are both strong. The score hides a real disagreement — underwrite the specific tension rather than treating this as a mild positive.';t.u=50;}
    else if(left){t.stage='EXPIRED';t.col='--grey';t.zone='exit';t.when='Already gone';
      t.act=t.own.length?'Review':'Drop from the watchlist';
      t.why='The manager whose conviction created this signal has left. Carrying it forward is stale-data risk.';t.u=30;}
    else if(insider&&broke){t.stage='COLLAPSING';t.col='--danger';t.zone='exit';t.when='Immediate — 1 to 7 days';
      t.act=t.own.length?'Exit now':'Avoid';
      t.why='Insider selling is now confirmed by price. Distribution phase.';t.u=100;}
    else if(t.score<0){t.stage='DECAYING';t.col='--rust';t.zone='exit';t.when='3 to 6 months';
      t.act=t.own.length?'Trim 30% over 3–6 months':'Avoid';
      t.why='Net negative. Smart money is rotating out.';t.u=40;}
    else if(t.score>=25&&t.nu){t.stage='EMERGING · HIGH CONVICTION';t.col='--gold';t.zone='buy';
      t.when='Entry window open now';
      t.act=t.own.length?'Add to the position':'Top candidate — run APEX first';
      t.why='A high score built from fresh positions, not aged ones. Several managers moved into this in the same quarter, which is conviction forming rather than consensus already priced.';t.u=90;}
    else if(t.score>=25&&t.sig.length>=4){t.stage='ESTABLISHED';t.col='--amber';t.zone='hold';
      t.when=wrTrim?'6 to 12 months — watch the north star':'6 to 18 months until decay';
      t.act=t.own.length?(wrTrim?'Hold — plan a trim in 6–12 months':'Hold'):'Reference only';
      t.why=wrTrim?'The north star is taking profits. The easy money is over.':'Consensus, and nothing new this quarter. No edge left unless it is mispriced.';t.u=20;}
    else if(t.score>=10&&(t.src.size>=2||t.who.size>=2)){t.stage='EMERGING';t.col='--gold';t.zone='buy';t.when='8 to 26 weeks to established';
      t.act=t.own.length?'Add to the position':'New candidate — run APEX';
      t.why='More than one independent source confirming. Asymmetric entry window.';t.u=60;}
    else if(t.score>=10){t.stage='EMERGING · ONE SOURCE';t.col='--gold';t.zone='buy';t.when='8 to 26 weeks';
      t.act='New candidate — run APEX, single source';
      t.why='Strong conviction, but from one source only. Unconfirmed — size accordingly.';t.u=55;}
    else if(t.score>=5){t.stage='DEVELOPING';t.col='--sage';t.zone='watch';t.when='Waiting on a second source';
      t.act='Watch';t.why='One source so far. Wait for confirmation.';t.u=15;}
    else{t.stage='WATCH';t.col='--blue';t.zone='watch';t.when='Not enough signal';
      t.act='Watch';t.why='Too early to call.';t.u=10;}
    return t;
  });

  const held=(a,b)=>(b.own.length>0)-(a.own.length>0);
  const byU=a=>a.sort((x,y)=>held(x,y)||y.u-x.u);
  const byS=a=>a.sort((x,y)=>held(x,y)||y.score-x.score);
  const byR=a=>a.sort((x,y)=>held(x,y)||x.fresh-y.fresh);
  const z=n=>list.filter(t=>t.zone===n);

  const ZONES=[
  {k:'buy',t:'Buy zone',s:'Best entry windows — highest score first',c:'--gold',a:byS(z('buy'))},
  {k:'watch',t:'Watch zone',s:'Forming or contested — most recent first',c:'--blue',a:byR(z('watch'))},
  {k:'hold',t:'Hold zone',s:'Consensus and reference — highest score first',c:'--amber',a:byS(z('hold'))},
  {k:'exit',t:'Exit zone',s:'Trim, avoid or expired — most urgent first',c:'--rust',a:byU(z('exit'))}];
  const order=ZONES[3].a.some(t=>t.own.length)?[ZONES[3],ZONES[0],ZONES[1],ZONES[2]]:ZONES;

  const esc=s=>String(s).replace(/&(?!\w+;)/g,'&amp;').replace(/</g,'&lt;');

  // ── live prices (added): chip under each theme's tickers ──
  function money(v){return v.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});}
  function priceChip(x){
    var q=PRICES[x];
    if(!q||q.price==null) return '<span class="pc na">'+esc(x)+' — quote unavailable</span>';
    var s='<span class="pc">'+esc(x)+' <b>$'+money(q.price)+'</b>';
    if(q.pct!=null){var neg=q.pct<=0;s+=' <em class="'+(neg?'neg':'pos')+'">'+(neg?'':'+')+Math.round(q.pct)+'% vs 52w high</em>';}
    return s+'</span>';
  }

  // ── data-driven copy (dated strings live in signals.json) ──
  var m=document.getElementById('sig-meta'); if(m)m.textContent=DATA.meta||'';
  var si=document.getElementById('stale-intro'); if(si)si.innerHTML=(DATA.freshness&&DATA.freshness.intro)||'';
  var sr=document.getElementById('stale-rows');
  if(sr)sr.innerHTML=((DATA.freshness&&DATA.freshness.rows)||[]).map(r=>
    '<tr><td>'+esc(r.src)+'</td><td class="'+(r.cls||'')+'">'+esc(r.state)+'</td></tr>').join('');
  var ae=document.getElementById('audit-eyebrow'); if(ae)ae.textContent=(DATA.copy&&DATA.copy.audit_eyebrow)||'Signal audit';
  var ch=document.getElementById('changed-h2'); if(ch)ch.textContent=(DATA.copy&&DATA.copy.changed_h2)||'What changed';

  // ── rendering (verbatim from stack.html, + price chips in card) ──
  document.getElementById('audit').innerHTML=AUDIT.map(a=>
  `<div class="card" style="border-left-color:var(${a.col})">
  <span class="tag" style="color:var(${a.col})">${a.v.toUpperCase()}</span>
  <h3>${a.c}</h3><p>${a.o}</p><div class="lesson">${a.l}</div></div>`).join('');

  document.getElementById('changed').innerHTML=CHANGED.map(x=>
  `<div class="card" style="border-left-color:var(${x.col})">
  <span class="tag" style="color:var(${x.col})">${x.tag}</span>
  <h3>${x.h}</h3><p>${x.p}</p></div>`).join('');

  document.getElementById('rules').innerHTML=RULES.map(r=>
  `<div class="rule" style="border-left-color:var(${r.col})">
  <div class="w">${r.w}</div><div class="t" style="color:var(${r.col})">${r.t}</div>
  <div class="n">${r.n}</div></div>`).join('');

  const badges=t=>{
    let b='';
    if(t.nu)b+=`<span class="b" style="color:var(--gold)">NEW</span>`;
    if(t.contested)b+=`<span class="b" style="color:var(--violet)">CONTESTED</span>`;
    if(t.nv)b+=`<span class="b" style="color:var(--nv)">NVDA</span>`;
    if(t.wr)b+=`<span class="b" style="color:var(--gold)">WHALE ROCK</span>`;
    if(t.wrTrim)b+=`<span class="b" style="color:var(--amber)">WR TRIMMING</span>`;
    if(t.own.length)b+=`<span class="b" style="color:var(--gold)">YOU HOLD ${t.own.join(', ')}</span>`;
    return b?`<div class="badges">${b}</div>`:'';
  };

  const card=t=>`<div class="theme${t.own.length?' held':''}" style="border-left-color:var(${t.col})">
  <div class="top"><span class="name">${t.n}</span><span class="score" style="color:var(${t.col})">${t.score>0?'+':''}${t.score}</span></div>
  ${badges(t)}
  <div class="act" style="color:var(${t.col})">${t.act}<span class="when">${t.when}</span></div>
  <div class="why">${t.why}</div>
  <div class="tk">${[...t.tk].map(x=>`<span class="${HELD.includes(x)?'own':''}">${x}</span>`).join('')}</div>
  <div class="px">${[...t.tk].map(priceChip).join('')}</div>
  <details><summary>${t.stage} · ${t.sig.length} signals · ${t.src.size} sources · latest ${t.fresh===0?'this week':t.fresh+'w ago'} ▾</summary>
  <div class="trail">${t.sig.map(s=>`<div class="sig"><span class="t">${s.t}</span><span><span class="src">${s.src.toUpperCase()}</span> <span class="d">${esc(s.by)}: ${esc(s.a)}</span></span><span class="n ${s.v>0?'pos':'neg'}">${s.v>0?'+':''}${s.v}</span></div>`).join('')}</div>
  </details></div>`;

  document.getElementById('zones').innerHTML=order.map(zn=>
  `<div class="zone"><div class="zonehead" style="border-left-color:var(${zn.c})">
  <div><div class="t" style="color:var(${zn.c})">${zn.t}</div><div class="s">${zn.s}</div></div>
  <div class="eyebrow">${zn.a.length} ${zn.a.length===1?'theme':'themes'}</div></div>
  ${zn.a.length?zn.a.map(card).join(''):'<div style="padding:16px;text-align:center;font-size:11px;color:var(--mute);border:1px dashed var(--line)">Nothing here right now</div>'}
  </div>`).join('');

  document.getElementById('mgrs').innerHTML=MGRS.map(m=>{
    const c=m.cls==='north'?'--gold':m.cls==='strat'?'--nv':'--sage';
    const stale=m.as.indexOf('Q4')===0;
    return `<div class="mgr ${m.cls}"${stale?' style="opacity:.8"':''}>
  <div class="h"><span class="nm">${m.n}</span><span class="who">${m.who}</span>
  <span class="pill" style="color:var(${c})">${m.role} · ${m.w}</span>
  <span class="pill" style="color:var(${stale?'--amber':'--sage'})">${m.as}</span></div>
  <div class="val">${m.val}</div><div class="note">${m.note}</div>
  <div class="cols">${m.cols.map(([h,v])=>`<div><h4 style="color:var(--mute)">${h.toUpperCase()}</h4><div>${v}</div></div>`).join('')}</div></div>`;
  }).join('');
})();
</script>"""

def signals_html():
    """Build the Signals tab: embed signals.json + a live-price blob, mounted by the
    stack.html engine client-side. Defensive — any problem yields an empty section so
    the nightly board is never blocked. Signals quote failures are kept out of the
    board's blind-board guard; they surface via the tab's own 'Quotes unavailable'."""
    try:
        sig = json.load(open("signals.json"))
    except FileNotFoundError:
        print("signals.json not found -- building board only")
        return ""
    except Exception as e:
        print(f"signals.json unreadable ({e}) -- building board only")
        return ""
    seen, tickers = set(), []
    for s in sig.get("signals", []):
        if s["t"] not in seen:
            seen.add(s["t"]); tickers.append(s["t"])
    prices, sig_failed = {}, []
    for t in tickers:
        q = quote(t)
        if not q or not q.get("price"):
            sig_failed.append(t); continue
        p = q["price"]; yh = q.get("yearHigh")
        prices[t] = {"price": p, "pct": ((p - yh) / yh * 100) if yh else None}
    data_json = json.dumps(sig, ensure_ascii=False).replace("</", "<\\/")
    prices_json = json.dumps(prices).replace("</", "<\\/")
    unavail = (f'<div class="unavail">Quotes unavailable: {", ".join(sig_failed)}.</div>'
               if sig_failed else "")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %H:%M UTC")
    print(f"signals.json: {len(prices)} priced, {len(sig_failed)} unavailable"
          + (f" ({', '.join(sig_failed)})" if sig_failed else ""))
    return (SIGNALS_SECTION.replace("__SIGNALS_JSON__", data_json)
            .replace("__SIGNALS_PRICES__", prices_json)
            .replace("__SIGNALS_UNAVAIL__", unavail)
            .replace("__PRICE_STAMP__", f"prices {stamp}"))

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
    fresh = []
    board_date = cfg.get("board_date")            # ISO date of the most recent Board
    for n in cfg["names"]:
        q = quote(n["t"])
        if not q:
            failed.append(n["t"]); continue
        p = q["price"]; d = (p - n["gate"]) / n["gate"] * 100
        n2 = dict(n, price=p, dist=d)
        if n.get("at_gate") or d <= 10: at_html += atgate_card(n2)
        elif d <= 30: near.append(n2)
        elif d <= 80: far.append(n2)
        elif n.get("verdict_date") and n["verdict_date"] == board_date:
            fresh.append(n2)          # armed at the latest Board — deep by design, not "ran away"
        else:
            left.append(n2)
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

    fresh_html = ""
    if fresh:
        lst = ", ".join(f'{x["t"]} (gate ${x["gate"]:,}, +{x["dist"]:.0f}%)'
                        for x in sorted(fresh, key=lambda x: -x["dist"]))
        fresh_html = (f'<div class="sec">Freshly armed &mdash; deep by design</div><p class="body">'
                      f'Set at the latest Board ({esc(board_date)}) at hurdle-derived levels: {lst}. '
                      f'The gap is the verdict, not a stale gate &mdash; not a culling candidate.</p>')

    left_html = ""
    if left:
        lst = ", ".join(f'{x["t"]} (+{x["dist"]:.0f}%)' for x in sorted(left, key=lambda x: x["dist"]))
        left_html = (f'<div class="sec">Review for culling</div><p class="body">'
                     f'{lst} sit far above older gates. Review at the culling pass (agenda item 5) &mdash; '
                     f'distance is not a verdict; confirm no new proof before retiring.</p>')

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
            .replace("__FRESH__", fresh_html)
            .replace("__LEFT__", left_html).replace("__CYCLEMAP__", cyclemap_html(cyclemap_json))
            .replace("__TRIGGERS__", triggers_html(cfg))
            .replace("__FOOT__", esc_foot(foot))
            .replace("__SIGNALS__", signals_html()))
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
