#!/usr/bin/env python3
"""Build static player pages for Ezzcoins.

Writes p/<slug>-<id>/index.html for every player rated MIN_OVR or higher in
data/players.json, a list page at p/index.html and sitemap.xml at the site root.
Prices are not baked in: each page loads the newest price from data/prices.json
and data/topprices.json in the browser.

Usage: python3 scripts/build_pages.py [site root]   (standard library only)
"""
import html, json, os, re, shutil, sys, unicodedata

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = os.environ.get("EZZ_BASE", "https://shapeles-dgi.github.io/ezzcoin/")
MIN_OVR = 80
BANNER = "<!-- © 2026 Ezzcoins. All rights reserved. Copying or reuse of this code is not permitted. -->"
SLUG_MAP = {"ø": "o", "Ø": "o", "ß": "ss", "ł": "l", "Ł": "l", "æ": "ae", "Æ": "ae",
            "œ": "oe", "đ": "d", "Đ": "d", "ı": "i", "ð": "d", "þ": "th"}
ST_OUT = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
ST_GK = ["DIV", "HAN", "KIC", "REF", "SPD", "POS"]
CSS_V = "3"


def slug(s):
    """Same rules as pageSlug() in index.html: map special letters, lowercase, drop accents."""
    s = "".join(SLUG_MAP.get(ch, ch) for ch in str(s or "")).lower()
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.category(ch).startswith("M"))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "player"


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def q(v):
    return "" if v is None else "q1" if v >= 85 else "q2" if v >= 75 else "q3" if v >= 65 else "q4"


CSS = (":root{--bg:#0A0D0C;--surface:#141917;--sunk:#1C2320;--ink:#EEF2EF;--muted:#93A29A;--line:#25302B;--gold:#E9B949;"
       "--buy:#4DD08F;--sell:#F27E68;--fd:'Barlow Condensed','Arial Narrow',sans-serif;--fb:'Barlow',system-ui,-apple-system,'Segoe UI',sans-serif;"
       "--fm:'IBM Plex Mono',ui-monospace,Menlo,monospace;color-scheme:dark}"
       "*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--fb)}"
       "a{color:var(--gold)}.top{display:flex;align-items:center;justify-content:space-between;gap:12px;max-width:980px;margin:0 auto;padding:12px 16px;border-bottom:1px solid var(--line)}"
       ".home{display:flex;align-items:center;gap:8px;text-decoration:none;color:var(--ink);font:italic 800 1.55rem/1 var(--fd);text-transform:uppercase}"
       ".home img{width:34px;height:34px}.home b{font:inherit}.home span{background:linear-gradient(180deg,#FFE59A,#E3A93A);-webkit-background-clip:text;background-clip:text;color:transparent}"
       ".nav{display:flex;gap:16px}.nav a{font:700 .9rem var(--fd);letter-spacing:.08em;text-transform:uppercase;text-decoration:none;white-space:nowrap}"
       "@media(max-width:420px){.nav{gap:12px}.nav a{font-size:.8rem;letter-spacing:.05em}.home{font-size:1.35rem}.home img{width:30px;height:30px}}"
       "main{max-width:980px;margin:0 auto;padding:22px 16px 40px}"
       ".crumb{font-size:.85rem;color:var(--muted);margin-bottom:14px}.crumb a{color:var(--muted)}"
       ".hero{display:grid;grid-template-columns:184px minmax(0,1fr);gap:26px;align-items:start}"
       ".fcard{position:relative;width:184px;height:256px;border-radius:18px 18px 34px 34px;padding:14px 14px 16px;display:flex;flex-direction:column;overflow:hidden;"
       "color:var(--fc-ink);background:var(--fc-bg);box-shadow:0 10px 28px rgb(0 0 0/.45),inset 0 0 0 1.5px rgb(255 255 255/.18);isolation:isolate}"
       ".fcard:after{content:'';position:absolute;inset:0;z-index:-1;background:linear-gradient(115deg,transparent 30%,rgb(255 255 255/.22) 45%,transparent 60%)}"
       ".v-gold{--fc-bg:linear-gradient(160deg,#FFE7A0,#E2B04A 55%,#A9731A);--fc-ink:#2a1d05}"
       ".v-silver{--fc-bg:linear-gradient(160deg,#F1F3F5,#B9C1C9 55%,#7D8791);--fc-ink:#1d2329}"
       ".v-bronze{--fc-bg:linear-gradient(160deg,#F2C9A4,#C17F4A 55%,#7E4A22);--fc-ink:#2a1607}"
       ".fc-ovr{font:italic 800 3rem/1 var(--fd)}.fc-pos{font:700 1.05rem/1 var(--fd);letter-spacing:.06em;margin-top:2px}"
       ".fc-flag{margin-top:8px;line-height:0}.fc-flag img{width:30px;height:22px;border-radius:3px;box-shadow:0 0 0 1px rgb(0 0 0/.2)}"
       ".fc-sil{position:absolute;right:-14px;bottom:52px;z-index:-1;width:140px;height:154px;fill:currentColor;opacity:.3;"
       "-webkit-mask-image:linear-gradient(#000 50%,transparent 96%);mask-image:linear-gradient(#000 50%,transparent 96%)}"
       ".fc-sil .collar{fill:none;stroke:currentColor;stroke-width:3}"
       ".fc-name{margin-top:auto;font:800 1.45rem/1.05 var(--fd);text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".fc-club{font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;opacity:.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       "h1{font:800 2.5rem/1.02 var(--fd);text-transform:uppercase;margin:0}.sub{color:var(--muted);margin-top:6px}"
       ".flag{width:16px;height:12px;border-radius:2px;vertical-align:-1px;margin-right:5px;box-shadow:0 0 0 1px rgb(255 255 255/.16)}"
       ".px{margin-top:16px;display:inline-grid;gap:2px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 14px}"
       ".px b{font:500 1.5rem var(--fm)}.px span{font-size:.82rem;color:var(--muted)}.px .none{max-width:420px}"
       ".coin{display:inline-block;width:.85em;height:.85em;border-radius:50%;background:radial-gradient(circle at 35% 30%,#FFE9A6,#E3A834 55%,#94590B);"
       "box-shadow:inset 0 0 0 1.5px rgb(255 243 207/.7);vertical-align:-.08em;margin-right:7px}"
       ".stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin-top:18px;max-width:560px}"
       ".st{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:9px 4px;text-align:center}"
       ".st small{display:block;font:600 .74rem var(--fd);letter-spacing:.1em;color:var(--muted)}.st b{font:500 1.45rem var(--fm)}"
       ".q1{color:var(--buy);font-weight:600!important}.q2{color:var(--buy)}.q3{color:var(--gold)}.q4{color:var(--sell)}"
       ".facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:18px 0 0;font-size:.95rem}"
       ".facts dt{color:var(--muted);font:600 .82rem/1.9 var(--fd);letter-spacing:.08em;text-transform:uppercase}.facts dd{margin:0}"
       ".btn{display:inline-block;margin-top:20px;background:linear-gradient(90deg,#FFDA7A,#E3A93A);color:#15201A;font:700 1rem var(--fd);"
       "letter-spacing:.06em;text-transform:uppercase;padding:10px 16px;border-radius:10px;text-decoration:none}"
       ".more h2{font:700 1.25rem var(--fd);text-transform:uppercase;letter-spacing:.02em;margin:34px 0 10px}"
       ".more ul{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}"
       ".more a{display:flex;gap:10px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:8px 10px;text-decoration:none;color:var(--ink);min-width:0}"
       ".more .o{font:700 1.15rem var(--fd);color:var(--gold);width:26px;flex:none}.more .n{flex:1 1 0;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".more .m{color:var(--muted);font-size:.82rem;flex:0 0 auto;max-width:46%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".find{width:100%;max-width:420px;margin:4px 0 18px;background:var(--sunk);border:1px solid var(--line);border-radius:999px;padding:10px 16px;color:var(--ink);font:inherit}"
       "footer{max-width:980px;margin:0 auto;padding:16px 16px 32px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line)}footer a{color:var(--muted)}"
       "@media(max-width:640px){.hero{grid-template-columns:1fr;justify-items:center;text-align:center}.stats{grid-template-columns:repeat(3,minmax(0,1fr));margin-inline:auto}"
       ".facts{text-align:left}h1{font-size:2.1rem}}")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;1,800&family=Barlow:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">')
SIL = ('<svg class="fc-sil" viewBox="0 0 100 110" aria-hidden="true"><ellipse cx="50" cy="35" rx="17" ry="20"/><path d="M42 52h16v12H42z"/>'
       '<path d="M6 110c3-29 19-45 44-47 25 2 41 18 44 47z"/><path class="collar" d="M39 64l11 13 11-13"/></svg>')


def head(title, desc, canon, up):
    return (f'<!doctype html>{BANNER}<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon)}">'
            f'<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{e(canon)}"><meta property="og:image" content="{e(BASE)}icon-512.png"><meta name="theme-color" content="#0A0D0C">'
            f'<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">'
            f'<link rel="manifest" href="{up}manifest.webmanifest">{FONTS}<link rel="stylesheet" href="{up}p/style.css?v={CSS_V}"></head><body>'
            f'<header class="top"><a class="home" href="{up}"><img src="{up}mark.svg" alt="" width="34" height="34"><b>Ezz<span>coins</span></b></a>'
            f'<nav class="nav"><a href="{up}#players">Database</a><a href="{up}p/">All players</a></nav></header>')


def foot(up):
    return (f'<footer>Ratings: EA SPORTS FC 27. Prices: FUTBIN. Ezzcoins is a fan-made site and is not affiliated with EA SPORTS, FUTBIN or FUT.GG. '
            f'<a href="{up}privacy.html">Privacy and cookies</a></footer></body></html>')


def flag(codes, nation, up, big=False):
    c = codes.get(nation)
    if not c:
        return ""
    if big:
        return f'<img src="{up}flags/{c}.png" alt="{e(nation)}" width="30" height="22">'
    return f'<img class="flag" src="{up}flags/{c}.png" alt="" width="16" height="12">'


def card_list(items, codes, up, meta):
    lis = "".join(f'<li><a href="{up}p/{x["path"]}"><span class="o">{x["o"]}</span>{flag(codes, x["nat"], up)}'
                  f'<span class="n">{e(x["n"])}</span><span class="m">{e(meta(x))}</span></a></li>' for x in items)
    return f"<ul>{lis}</ul>"


def player_page(x, codes, by_club, by_nat):
    up = "../../"
    gk = x["p"] == "GK"
    lab = ST_GK if gk else ST_OUT
    tier = "gold" if x["o"] >= 75 else "silver" if x["o"] >= 65 else "bronze"
    where = " · ".join(v for v in (x["c"], x["l"]) if v)
    stats_txt = ", ".join(f"{lab[i]} {v}" for i, v in enumerate(x["s"]) if v is not None)
    title = f'{x["n"]} FC 27 – {x["o"]} {x["p"]} stats & price | Ezzcoins'
    desc = (f'{x["n"]}\'s EA SPORTS FC 27 Ultimate Team card: {x["o"]}-rated {x["p"]}'
            + (f' for {x["c"]}' if x["c"] else "") + (f' ({x["l"]})' if x["l"] else "") + (f', {x["nat"]}' if x["nat"] else "")
            + (f". {stats_txt}" if stats_txt else "") + ". Console price on Ezzcoins.")
    canon = BASE + "p/" + x["path"]
    facts = [("Position", x["p"] + (f' (also {", ".join(x["a"].split(","))})' if x["a"] else "")),
             ("Club", x["c"]), ("League", x["l"]), ("Nation", x["nat"]),
             ("Skill moves", f'{x["sm"]}★' if x["sm"] else ""), ("Weak foot", f'{x["wf"]}★' if x["wf"] else ""),
             ("Preferred foot", {"L": "Left", "R": "Right"}.get(x["ft"], "")),
             ("Height", f'{x["h"]} cm' if x["h"] else ""), ("Age", x["age"] or ""),
             ("PlayStyles+", ", ".join(x["ps"].split(",")) if x["ps"] else ""),
             ("Full name", x["f"] if x["f"] and x["f"] != x["n"] else ""),
             ("Football", "Women's football" if str(x["g"]) == "1" else "")]
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in facts if v not in ("", None))
    stats = "".join(f'<div class="st"><small>{lab[i]}</small><b class="{q(v)}">{"–" if v is None else v}</b></div>' for i, v in enumerate(x["s"]))
    mates = [y for y in by_club.get(x["c"], []) if y["id"] != x["id"]][:8]
    natmates = [y for y in by_nat.get(x["nat"], []) if y["id"] != x["id"] and y["c"] != x["c"]][:8]
    more = ""
    if mates:
        more += f'<h2>More from {e(x["c"])}</h2>' + card_list(mates, codes, up, lambda y: y["p"])
    if natmates:
        more += f'<h2>More from {e(x["nat"])}</h2>' + card_list(natmates, codes, up, lambda y: y["c"])
    hint = ("Cards rated 84 or higher are priced in turns through the day." if x["o"] >= 84
            else "Add this player to your watchlist on Ezzcoins: the most-watched players get a price every hour.")
    script = ("<script>(()=>{const id=%s,el=document.getElementById('px'),g=f=>fetch('../../data/'+f+'?t='+Date.now(),{cache:'no-store'})"
              ".then(r=>r.ok?r.json():null).catch(()=>null);Promise.all([g('prices.json'),g('topprices.json')]).then(([a,b])=>{"
              "const c=[a&&a.players&&a.players[id],b&&b.players&&b.players[id]].filter(p=>p&&p.price>0).sort((x,y)=>Date.parse(y.at)-Date.parse(x.at))[0];"
              "if(!c)return;const m=Math.round((Date.now()-Date.parse(c.at))/6e4),h=Math.floor(m/60),ago=m<1?'just now':m<60?m+' min ago':h<48?h+' h ago':Math.floor(h/24)+' days ago';"
              "el.innerHTML='<b><i class=\"coin\"></i>'+Number(c.price).toLocaleString('en-US')+'</b><span>Console price from FUTBIN \\u00b7 '+ago+'</span>'})})()</script>"
              ) % json.dumps(str(x["id"]))
    return (head(title, desc, canon, up) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> › <a href="{up}p/">Player pages</a> › {e(x["n"])}</div>'
            f'<div class="hero"><div class="fcard v-{tier}" aria-hidden="true"><div class="fc-ovr">{x["o"]}</div><div class="fc-pos">{e(x["p"])}</div>'
            f'<div class="fc-flag">{flag(codes, x["nat"], up, True)}</div>{SIL}<div class="fc-name">{e(x["q"] or x["n"])}</div><div class="fc-club">{e(x["c"])}</div></div>'
            f'<div><h1>{e(x["n"])}</h1><div class="sub">{x["o"]} {e(x["p"])}' + (f" · {e(where)}" if where else "")
            + (f' · {flag(codes, x["nat"], up)}{e(x["nat"])}' if x["nat"] else "") + '</div>'
            f'<div class="px" id="px"><span class="none">No console price yet. {e(hint)}</span></div>'
            f'<div class="stats">{stats}</div><dl class="facts">{dl}</dl>'
            f'<a class="btn" href="{up}#q={e(x["n"])}">Watch on Ezzcoins</a></div></div>'
            f'<section class="more">{more}</section></main>{script}' + foot(up))


def list_page(groups, codes, total):
    up = "../"
    title = "FC 27 player pages: stats and prices | Ezzcoins"
    desc = f"Stats, PlayStyles and console prices for all {total} EA SPORTS FC 27 Ultimate Team players rated {MIN_OVR} or higher."
    body = "".join(f'<h2>{ovr} rated</h2>' + card_list(items, codes, up, lambda y: f'{y["p"]} · {y["c"]}') for ovr, items in groups)
    script = ("<script>(()=>{const f=document.getElementById('find'),k=s=>s.normalize('NFD').replace(/\\p{M}/gu,'').toLowerCase();"
              "f.addEventListener('input',()=>{const t=k(f.value.trim());for(const li of document.querySelectorAll('.more li'))li.hidden=!!t&&!k(li.textContent).includes(t);"
              "for(const h of document.querySelectorAll('.more h2')){const ul=h.nextElementSibling;h.hidden=ul&&![...ul.children].some(li=>!li.hidden)}})})()</script>")
    return (head(title, desc, BASE + "p/", up) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> › Player pages</div><h1>FC 27 player pages</h1>'
            f'<p class="sub">All {total} players rated {MIN_OVR} or higher in EA SPORTS FC 27, with stats, PlayStyles+ and console prices.</p>'
            f'<input class="find" id="find" type="search" placeholder="Find a player" autocomplete="off"><section class="more">{body}</section></main>{script}' + foot(up))


def main():
    data = json.load(open(os.path.join(ROOT, "data", "players.json"), encoding="utf-8"))
    codes = json.load(open(os.path.join(ROOT, "flags", "codes.json"), encoding="utf-8"))
    ci = {c: i for i, c in enumerate(data["cols"])}
    get = lambda r, c: r[ci[c]] if c in ci else None
    players = []
    for r in data["rows"]:
        o = get(r, "ovr") or 0
        if o < MIN_OVR or get(r, "id") is None:
            continue
        x = {"id": int(get(r, "id")), "n": get(r, "name") or "", "f": get(r, "full") or "", "q": get(r, "q") or "", "o": int(o),
             "p": get(r, "pos") or "", "a": get(r, "alt") or "", "c": get(r, "club") or "", "l": get(r, "league") or "",
             "nat": get(r, "nation") or "", "g": get(r, "gender"), "sm": get(r, "sm"), "wf": get(r, "wf"), "ft": get(r, "foot") or "",
             "h": get(r, "height"), "age": get(r, "age"), "ps": get(r, "psp") or "",
             "s": [get(r, f"s{k}") for k in range(1, 7)]}
        x["path"] = f'{slug(x["n"])}-{x["id"]}/'
        players.append(x)
    players.sort(key=lambda x: (-x["o"], x["n"]))
    by_club, by_nat = {}, {}
    for x in players:
        by_club.setdefault(x["c"], []).append(x)
        by_nat.setdefault(x["nat"], []).append(x)
    out = os.path.join(ROOT, "p")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    with open(os.path.join(out, "style.css"), "w", encoding="utf-8") as fh:
        fh.write("/* \u00a9 2026 Ezzcoins. All rights reserved. */\n" + CSS)
    for x in players:
        d = os.path.join(out, x["path"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(player_page(x, codes, by_club, by_nat))
    groups = []
    for x in players:
        if not groups or groups[-1][0] != x["o"]:
            groups.append((x["o"], []))
        groups[-1][1].append(x)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(list_page(groups, codes, len(players)))
    urls = [BASE, BASE + "privacy.html", BASE + "p/"] + [BASE + "p/" + x["path"] for x in players]
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 + "".join(f"<url><loc>{e(u)}</loc></url>\n" for u in urls) + "</urlset>\n")
    print(f"OK: {len(players)} player pages, list page and sitemap ({len(urls)} URLs)")


if __name__ == "__main__":
    main()
