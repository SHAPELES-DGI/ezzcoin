#!/usr/bin/env python3
"""Build static player pages for Ezzcoins.

Writes p/<slug>-<id>/index.html for every player rated MIN_OVR or higher in
data/players.json, p/<slug>-<version>-<id>/index.html for every new special card in
data/newcards.json, a list page at p/index.html, p/cardnames.json (the name and nation shown on each special card,
taken from EA's card of the same player) and sitemap.xml at the site root.
FUT.GG card artwork is refreshed by scripts/fetch_card_art.py and cached in data/card-art.json.
Prices are not baked in: each page loads the newest price from data/prices.json
and data/topprices.json in the browser.

Usage: python3 scripts/build_pages.py [site root]   (standard library only)
GitHub runs it automatically (.github/workflows/player-pages.yml) whenever data/players.json or data/newcards.json changes.
"""
import html, json, os, re, shutil, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import meta  # noqa: E402  (same folder)

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = os.environ.get("EZZ_BASE", "https://shapeles-dgi.github.io/ezzcoin/")
MIN_OVR = 80
BANNER = "<!-- © 2026 Ezzcoins. All rights reserved. Copying or reuse of this code is not permitted. -->"
SLUG_MAP = {"ø": "o", "Ø": "o", "ß": "ss", "ł": "l", "Ł": "l", "æ": "ae", "Æ": "ae",
            "œ": "oe", "đ": "d", "Đ": "d", "ı": "i", "ð": "d", "þ": "th"}
ST_OUT = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
ST_GK = ["DIV", "HAN", "KIC", "REF", "SPD", "POS"]
CSS_V = "24"
SPECIAL = 1000000000  # special-card ids on the site: SPECIAL + FUT.GG card id (gid) or FUTBIN card id (fid)
CARD_ART = {}
CARD_IDS = json.load(open(os.path.join(ROOT, "data", "card-ids.json")))
CARD_RENDERS = json.load(open(os.path.join(ROOT, "data", "card-renders.json"), encoding="utf-8"))
REGULAR_PLAYSTYLES = {}


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
       "[hidden]{display:none!important}*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--fb)}"
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
       ".v-totw{--fc-bg:linear-gradient(160deg,#3A3A3A,#0E0E0E 55%,#3D3112);--fc-ink:#F3D27A}.v-potm{--fc-bg:linear-gradient(160deg,#4C7BEA,#1B2F70 70%);--fc-ink:#fff}"
       ".v-icon{--fc-bg:linear-gradient(160deg,#FFFFFF,#E5DCC2 60%,#BFAF83);--fc-ink:#3a2f12}.v-hero{--fc-bg:linear-gradient(160deg,#7A55E0,#2B1A63 70%);--fc-ink:#fff}"
       ".v-sbc{--fc-bg:linear-gradient(160deg,#26C49A,#0B4D3E 70%);--fc-ink:#fff}.v-promo{--fc-bg:linear-gradient(160deg,#D24C8F,#3A1C6E 70%);--fc-ink:#fff}"
       ".tag{display:inline-block;background:linear-gradient(90deg,#FFDA7A,#E3A93A);color:#15201A;font:700 .8rem var(--fd);letter-spacing:.08em;text-transform:uppercase;padding:3px 9px;border-radius:5px;margin-bottom:8px}"
       ".nostats{margin-top:18px;color:var(--muted);font-size:.92rem;max-width:520px}"
       ".side{display:grid;gap:10px;justify-items:center;width:184px}"
       ".card-art{display:block;width:214px;max-width:100%;height:auto;filter:drop-shadow(0 12px 22px rgb(0 0 0/.42));border-radius:18px}"
       ".fcard{text-align:left}.fc-photo{position:absolute;z-index:-1;top:0;right:0;width:76%;height:80%;object-fit:cover;object-position:50% 14%;"
       "-webkit-mask-image:linear-gradient(to bottom,#000 58%,transparent 97%),linear-gradient(to right,transparent 0,#000 34%);-webkit-mask-composite:source-in;"
       "mask-image:linear-gradient(to bottom,#000 58%,transparent 97%),linear-gradient(to right,transparent 0,#000 34%);mask-composite:intersect}"
       ".fc-name.long{font-size:1.15rem}.fc-name.xl{font-size:.98rem}"
       ".side{width:214px}.credit{width:214px}.hero{grid-template-columns:214px minmax(0,1fr)}"
       ".playstyles{width:214px;display:flex;flex-wrap:wrap;justify-content:center;gap:5px;margin-top:2px}.playstyles-title{width:100%;text-align:center;color:var(--muted);font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin:2px 0}.playstyle{display:inline-flex;align-items:center;gap:4px;padding:4px 6px;border:1px solid #343c3b;border-radius:999px;background:#171d1c;color:#e8eeea;font-size:.68rem;line-height:1.2;white-space:nowrap}.playstyle i{display:grid;place-items:center;width:15px;height:15px;border-radius:50%;background:#c7e37c;color:#101511;font-size:9px;font-style:normal;font-weight:900}"
       ".card-xl{width:214px;height:330px;padding:16px 14px 12px;border-radius:20px 20px 40px 40px;text-align:center}"
       ".card-xl .fc-tl{position:absolute;left:16px;top:16px;z-index:1;text-align:center;line-height:1}"
       ".card-xl .fc-ovr{font-size:2.9rem}.card-xl .fc-pos{font-size:1.05rem;margin-top:2px}"
       ".card-xl .fc-photo{left:22%;right:auto;top:6px;width:74%;height:58%;object-position:50% 14%;"
       "-webkit-mask-image:radial-gradient(ellipse 60% 66% at 50% 40%,#000 50%,transparent 94%);-webkit-mask-composite:source-over;"
       "mask-image:radial-gradient(ellipse 60% 66% at 50% 40%,#000 50%,transparent 94%);mask-composite:add}"
       ".card-xl .fc-sil{right:6px;bottom:auto;top:18px;width:150px;height:166px;-webkit-mask-image:linear-gradient(#000 60%,transparent 98%);mask-image:linear-gradient(#000 60%,transparent 98%)}"
       ".card-xl .fc-name{margin-top:auto;font-size:1.45rem;text-transform:none;letter-spacing:.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".card-xl .fc-name.long{font-size:1.25rem}.card-xl .fc-name.xl{font-size:1.08rem}"
       ".fc-stats{display:grid;grid-template-columns:repeat(6,1fr);margin-top:6px;padding-top:6px;border-top:1px solid color-mix(in srgb,currentColor 22%,transparent)}"
       ".fc-stats small{display:block;font:700 .62rem/1.1 var(--fd);letter-spacing:.06em;opacity:.8}.fc-stats b{display:block;font:700 1.12rem/1.15 var(--fd)}"
       ".fc-foot{display:flex;justify-content:center;align-items:center;gap:8px;margin-top:8px;font:700 .68rem var(--fd);letter-spacing:.06em;text-transform:uppercase;opacity:.85;min-height:16px}"
       ".fc-foot img{width:22px;height:16px;border-radius:2px;box-shadow:0 0 0 1px rgb(0 0 0/.2)}.fc-foot span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:150px}"
       "@media(max-width:640px){.side,.credit{width:214px}}"
       ".fcard.has-photo .fc-name,.fcard.has-photo .fc-club{text-shadow:0 1px 6px var(--fc-glow,rgb(255 255 255/.45))}"
       ".v-totw,.v-potm,.v-hero,.v-sbc,.v-promo{--fc-glow:rgb(0 0 0/.6)}"
       ".credit{width:184px;font-size:.72rem;line-height:1.4;color:var(--muted);overflow-wrap:anywhere;text-align:left}"
       ".credit summary{cursor:pointer;margin-top:2px}.credit details p{margin:4px 0 0}"
       ".fc-ovr{font:italic 800 3rem/1 var(--fd)}.fc-pos{font:700 1.05rem/1 var(--fd);letter-spacing:.06em;margin-top:2px}"
       ".fc-flag{margin-top:8px;line-height:0}.fc-flag img{width:30px;height:22px;border-radius:3px;box-shadow:0 0 0 1px rgb(0 0 0/.2)}"
       ".fc-sil{position:absolute;right:-14px;bottom:52px;z-index:-1;width:140px;height:154px;fill:currentColor;opacity:.3;"
       "-webkit-mask-image:linear-gradient(#000 50%,transparent 96%);mask-image:linear-gradient(#000 50%,transparent 96%)}"
       ".fc-sil .collar{fill:none;stroke:currentColor;stroke-width:3}"
       ".fc-name{margin-top:auto;font:800 1.45rem/1.05 var(--fd);text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       ".fc-club{font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;opacity:.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
       "h1{font:800 2.5rem/1.02 var(--fd);text-transform:uppercase;margin:0}.sub{color:var(--muted);margin-top:6px}"
       ".flag{width:16px;height:12px;border-radius:2px;vertical-align:-1px;margin-right:5px;box-shadow:0 0 0 1px rgb(255 255 255/.16)}"
       ".px{margin-top:16px;display:inline-grid;gap:8px;max-width:100%;background:#101813;border:1px solid #506344;border-radius:12px;padding:14px 18px}"
       ".px b{font:700 clamp(1.75rem,4vw,2.25rem)/1.15 var(--fb);font-variant-numeric:tabular-nums;letter-spacing:.01em;color:#ffe08a;overflow-wrap:anywhere}.px span{font:400 .8rem/1.5 var(--fb);color:#bac6bd;overflow-wrap:anywhere}.px .none{max-width:420px}"
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
       ".kv{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;align-items:stretch}.kv .px{margin-top:0}"
       ".mt{display:grid;grid-template-columns:auto 1fr;column-gap:12px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:8px 14px;text-align:left}"
       ".mt b{grid-row:span 2;font:700 2.1rem/1 var(--fd);color:var(--gold)}.mt span{font:700 .78rem var(--fd);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}"
       ".mt i{font-style:normal;font-size:.82rem;color:var(--muted)}.mt i em{font-style:normal;color:var(--ink)}"
       ".up{color:var(--buy)}.dn{color:var(--sell)}.mtnote{margin:14px 0 0;font-size:.82rem;color:var(--muted);max-width:560px;text-align:left}"
       "@font-face{font-family:'Ezz Sig';src:url(../fonts/allison-sig.woff) format('woff');font-display:swap}"
       ".fcard .fc-name.sig,.card-xl .fc-name.sig{font:400 2.9rem/1 'Ezz Sig','Segoe Script',cursive;text-transform:none;letter-spacing:0;padding:10px 8px 0;margin:auto -8px -9px;"
       "transform:rotate(-5deg);text-overflow:clip}.card-xl .fc-name.sig.long{font-size:2.5rem}.card-xl .fc-name.sig.xl{font-size:2.15rem}.card-xl .fc-name.sig.xxl{font-size:1.8rem}"
       ".credits{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:8px;font-size:.9rem}.credits li{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:8px 12px;overflow-wrap:anywhere}"
       ".credits summary{cursor:pointer;color:var(--muted);font-size:.82rem}.credits details p{margin:4px 0 0;color:var(--muted);font-size:.8rem}"
       "footer{max-width:980px;margin:0 auto;padding:16px 16px 32px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line)}footer a{color:var(--muted)}"
       ".st i{display:block;font:500 .7rem/1.2 var(--fm);color:var(--buy);font-style:normal;min-height:1.2em}"
       ".chem{margin-top:20px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 14px;max-width:560px;text-align:left}"
       ".chem h2{font:700 1.1rem var(--fd);text-transform:uppercase;letter-spacing:.04em;margin:0 0 8px}"
       ".chem-top{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.chem-sel{display:flex;align-items:center;gap:8px;flex:1 1 220px;min-width:0}"
       ".chem-sel span{font:700 .78rem var(--fd);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}"
       ".chem select{flex:1;min-width:0;background:var(--sunk);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font:inherit}"
       ".chem-lv{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}"
       ".chem-lv button{background:var(--sunk);color:var(--muted);border:0;border-left:1px solid var(--line);padding:8px 11px;font:700 .85rem var(--fd);letter-spacing:.04em;text-transform:uppercase;cursor:pointer}"
       ".chem-lv button:first-child{border-left:0}.chem-lv button[aria-pressed=true]{background:linear-gradient(90deg,#FFDA7A,#E3A93A);color:#15201A}"
       ".chem-best{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;font-size:.84rem;color:var(--muted);align-items:center}"
       ".chem-best button{background:var(--sunk);border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:4px 11px;font:600 .82rem var(--fb);cursor:pointer}"
       ".chem-best button b{color:var(--gold);font:700 .95rem var(--fd);margin-left:3px}.chem-best button[aria-pressed=true]{border-color:var(--gold);background:color-mix(in srgb,var(--gold) 14%,var(--sunk))}"
       ".chem-boost{margin:10px 0 0;font-size:.84rem}.chem-note{margin:8px 0 0;font-size:.78rem;color:var(--muted)}"
       "@media(max-width:640px){.hero{grid-template-columns:1fr;justify-items:center;text-align:center}.stats{grid-template-columns:repeat(3,minmax(0,1fr));margin-inline:auto}.chem{margin-inline:auto}"
       ".facts{text-align:left}h1{font-size:2.1rem}.kv{justify-content:center}}")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;1,800&family=Barlow:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">')
SIL = ('<svg class="fc-sil" viewBox="0 0 100 110" aria-hidden="true"><ellipse cx="50" cy="35" rx="17" ry="20"/><path d="M42 52h16v12H42z"/>'
       '<path d="M6 110c3-29 19-45 44-47 25 2 41 18 44 47z"/><path class="collar" d="M39 64l11 13 11-13"/></svg>')


def card_variant(version, ovr, special=False):
    """Card colours by version; a special card never gets the gold/silver/bronze look (its version may not be known yet)."""
    v = str(version or "").lower()
    if re.search(r"team of the week|totw", v): return "totw"
    if re.search(r"month|potm", v): return "potm"
    if "icon" in v: return "icon"
    if "hero" in v: return "hero"
    if re.search(r"sbc|objective|evolution|reward", v): return "sbc"
    if special: return "promo"
    if not v or re.search(r"rare|common|gold|base", v): return "gold" if (ovr or 0) >= 75 else "silver" if (ovr or 0) >= 65 else "bronze"
    return "promo"


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def day(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""


def photo(credits, pid, name, up):
    """(image for inside the card, credit line for under it) or ("", "") when there is no photo."""
    c = credits.get(str(pid)) if pid is not None else None
    if not c:
        return "", ""
    img = f'<img class="fc-photo" src="{up}photos/{e(c["img"])}" alt="Photo of {e(name)}" width="155" height="205">'
    credit = (f'<div class="credit">Photo (cropped): {e(c["author"])} \u00b7 {e(c["licence"])} \u00b7 Wikimedia Commons'
              f'<details><summary>Photo source</summary><p>{e(c["page"])}</p><p>Licence: {e(c["licenceUrl"])}</p></details></div>')
    return img, credit



def card_art_image(item, name, fallback):
    """Full FC item render from Fodder; show the designed fallback if an item render is missing."""
    if item in (None, ""):
        return fallback
    item = CARD_IDS.get(str(item), item)
    record = CARD_RENDERS.get(str(item)) or CARD_RENDERS.get("f:" + str(item))
    if record and record.get("url"):
        src = record["url"]
    else:
        # Official layered cards are filled by card-art.js.
        return f'<div class="card-art" aria-label="{e(name)} FC 27 card"></div><div class="card-fallback" hidden>{fallback}</div>'
    return (f'<img class="card-art" src="{src}" alt="{e(name)} FC 27 Ultimate Team card" width="240" height="336" '
            f'loading="eager" decoding="async" onerror="this.hidden=true;this.nextElementSibling.hidden=false">'
            f'<div class="card-fallback" hidden>{fallback}</div>')


def card_art_photo(url, name):
    """Use the FUT.GG player render inside the site's designed card frame."""
    if not url:
        return ""
    return f'<img class="fc-photo" src="{e(url)}" alt="{e(name)} FC 27 player image" width="155" height="205" loading="eager" decoding="async">'


def card_name(name):
    """Last word of the name, or the last two when it ends in a suffix such as "Jr." (same rule as cardName() in index.html)."""
    w = str(name or "").split()
    if not w:
        return ""
    last = w[-1]
    return " ".join(w[-2:]) if len(w) > 1 and (len(last) <= 3 or re.match(r"^(jr|junior|filho|neto|sr)\.?$", last, re.I)) else last


def big_card(variant, ovr, pos, name, stats, lab, nat_flag, foot_text, pimg, sig=False):
    nm = name or ""
    size = (" xxl" if len(nm) > 14 else " xl" if len(nm) > 10 else " long" if len(nm) > 7 else "") if sig else (" xl" if len(nm) > 14 else " long" if len(nm) > 11 else "")
    size = (" sig" if sig else "") + size
    row = ""
    if any(v is not None for v in stats):
        row = '<div class="fc-stats">' + "".join(f'<div><small>{lab[i]}</small><b>{"–" if v is None else v}</b></div>' for i, v in enumerate(stats)) + "</div>"
    return (f'<div class="fcard card-xl v-{variant}{" has-photo" if pimg else ""}"><div class="fc-tl"><div class="fc-ovr">{ovr}</div><div class="fc-pos">{e(pos)}</div></div>'
            f'{pimg or SIL}<div class="fc-name{size}">{e(nm)}</div>{row}<div class="fc-foot">{nat_flag}<span>{e(foot_text)}</span></div></div>')


MT_NOTE = ("Meta rating: Ezzcoins' own estimate of how well this card plays in game, worked out from its stats for each position it can play, "
           "its skill moves, weak foot and PlayStyle+. An average card scores about its overall rating; higher means it plays above its rating.")


def meta_box(mt, ovr):
    """Meta rating panel next to the price, or "" when the card has no stats yet."""
    if not mt:
        return ""
    (bp, bv), rest = next(iter(mt.items())), list(mt.items())[1:]
    d = bv - (ovr or 0)
    delta = f' <em class="{"up" if d > 0 else "dn"}">{"+" if d > 0 else "−"}{abs(d)} vs overall</em>' if d else " <em>same as overall</em>"
    other = " · ".join(f"{p} {v}" for p, v in rest[:4])
    return (f'<div class="mt" id="mt" title="{e(MT_NOTE)}"><b>{bv}</b><span>Meta rating · {e(bp)}</span>'
            f'<i>{delta}{" · " + e(other) if other else ""}</i></div>')


def chem_box(x, up):
    """Chemistry style picker (filled in by p/chem.js), or "" when the card has no stats yet."""
    if any(v is None for v in x["s"]):
        return ""
    data = json.dumps([int(v) for v in x["s"]])
    return (f'<section class="chem" id="chem" data-s="{e(data)}" data-pos="{e(x["p"])}" data-alt="{e(x["a"] or "")}" data-ovr="{x["o"]}" '
            f'data-sm="{e(x["sm"] or "")}" data-wf="{e(x["wf"] or "")}" data-ps="{e(x["ps"] or "")}"><h2>Chemistry style</h2>'
            f'<p class="chem-note">Turn on JavaScript to see this card with each chemistry style.</p></section>'
            f'<script src="{up}market-data.js?v=20261006-fb1"></script><script src="{up}p/chem.js?v={CSS_V}" defer></script>')


ADSENSE = "<script async src=\"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5351346431839799\" crossorigin=\"anonymous\"></script>"


def head(title, desc, canon, up, image=None):
    return (f'<!doctype html>{BANNER}<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon)}">'
            f'<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{e(canon)}"><meta property="og:image" content="{e(image or BASE + "icon-512.png")}"><meta name="theme-color" content="#0A0D0C">'
            f'<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">'
            f'<script src="{up}card-art.js?v=20261006-ps1" defer></script><link rel="manifest" href="{up}manifest.webmanifest">{FONTS}<link rel="stylesheet" href="{up}p/style.css?v={CSS_V}">{ADSENSE}</head><body>'
            f'<header class="top"><a class="home" href="{up}"><img src="{up}mark.svg" alt="" width="34" height="34"><b>Ezz<span>coins</span></b></a>'
            f'<nav class="nav"><a href="{up}#players">Database</a><a href="{up}p/">All players</a></nav></header>')


def foot(up):
    return (f'<footer>Ratings: EA SPORTS FC 27. Prices: FUTBIN (backups: FUT.GG, FUTWIZ, EasySBC). Ezzcoins is a fan-made site and is not affiliated with EA SPORTS, FUTBIN, FUT.GG, FUTWIZ or EasySBC. '
            f'<a href="{up}p/credits/">Photo credits</a> · <a href="{up}privacy.html">Privacy and cookies</a></footer></body></html>')


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


def player_page(x, codes, by_club, by_nat, specials_of, credits):
    up = "../../"
    gk = x["p"] == "GK"
    lab = ST_GK if gk else ST_OUT
    tier = "gold" if x["o"] >= 75 else "silver" if x["o"] >= 65 else "bronze"
    where = " · ".join(v for v in (x["c"], x["l"]) if v)
    stats_txt = ", ".join(f"{lab[i]} {v}" for i, v in enumerate(x["s"]) if v is not None)
    title = f'{x["n"]} FC 27 – {x["o"]} {x["p"]} stats & price | Ezzcoins'
    mt = meta(x["p"], x["a"], x["s"], x["sm"], x["wf"], x["ps"])
    mt_txt = f'. Meta rating {next(iter(mt.values()))} ({next(iter(mt))})' if mt else ""
    desc = (f'{x["n"]}\'s EA SPORTS FC 27 Ultimate Team card: {x["o"]}-rated {x["p"]}'
            + (f' for {x["c"]}' if x["c"] else "") + (f' ({x["l"]})' if x["l"] else "") + (f', {x["nat"]}' if x["nat"] else "")
            + (f". {stats_txt}" if stats_txt else "") + mt_txt + ". Console price on Ezzcoins.")
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
    sp = specials_of.get(x["id"], [])
    if sp:
        more += f'<h2>{e(x["n"])}\'s special cards</h2>' + card_list(sp, codes, up, lambda y: y["ver"])
    if mates:
        more += f'<h2>More from {e(x["c"])}</h2>' + card_list(mates, codes, up, lambda y: y["p"])
    if natmates:
        more += f'<h2>More from {e(x["nat"])}</h2>' + card_list(natmates, codes, up, lambda y: y["c"])
    hint = ("Cards rated 84 or higher are priced in turns through the day." if x["o"] >= 84
            else "Add this player to your watchlist on Ezzcoins: the most-watched players get a price every hour.")
    script = ("<script>(()=>{const id=%s,el=document.getElementById('px'),g=f=>window.EzzcoinsMarket.fetchData(f).catch(()=>null);"
              "const load=()=>Promise.all([g('prices.json'),g('topprices.json'),g('live-prices.json')]).then(([a,b,live])=>{"
              "const row=live&&Array.isArray(live.rows)?live.rows.find(r=>Number(r[0])===Number(id)):null;"
              "const meta=live&&live.quoteMetadata&&live.quoteMetadata[String(id)]&&live.quoteMetadata[String(id)].console;const lp=row&&row[3]===0&&row[1]>0?{price:row[1],at:meta&&meta.at||live.publishedAt.console,src:meta&&meta.src||live.source}:null;"
              "const c=lp||[a&&a.players&&a.players[id],b&&b.players&&b.players[id]].filter(p=>p&&p.price>0&&Number.isFinite(Date.parse(p.at))).sort((x,y)=>Date.parse(y.at)-Date.parse(x.at))[0];"
              "if(!c)return;const m=Math.round((Date.now()-Date.parse(c.at))/6e4),h=Math.floor(m/60),ago=m<1?'just now':m<60?m+' min ago':h<48?h+' h ago':Math.floor(h/24)+' days ago';"
              "const label=c.src==='FUT.GG'?'FUT.GG feed updated':'Console price from '+(c.src||'FUTBIN');"
              "el.innerHTML='<b><i class=\"coin\"></i>'+Number(c.price).toLocaleString('en-US')+'</b><span>'+label+' \\u00b7 '+ago+'</span>'});load();setInterval(load,300000)})()</script>"
              ) % json.dumps(str(x["id"]))
    pc = credits.get(str(x["id"]))
    pimg, pcredit = photo(credits, x["id"], x["n"], up)
    art_photo = card_art_photo(CARD_ART.get(str(x["id"])), x["n"])
    if art_photo:
        pimg = art_photo
    fallback_card = big_card(tier, x["o"], x["p"], x["q"] or x["n"], x["s"], lab, flag(codes, x["nat"], up, True), x["c"], pimg)
    full_art = card_art_image(x["id"], x["n"], fallback_card)
    style_row = playstyle_row(x.get("pls"))
    return (head(title, desc, canon, up, BASE + "photos/" + pc["img"] if pc else None) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> › <a href="{up}p/">Player pages</a> › {e(x["n"])}</div>'
            f'<div class="hero"><div class="side">{full_art}{style_row}{"" if full_art or art_photo else pcredit}</div>'
            f'<div><h1>{e(x["n"])}</h1><div class="sub">{x["o"]} {e(x["p"])}' + (f" · {e(where)}" if where else "")
            + (f' · {flag(codes, x["nat"], up)}{e(x["nat"])}' if x["nat"] else "") + '</div>'
            f'<div class="kv"><div class="px" id="px"><span class="none">No console price yet. {e(hint)}</span></div>{meta_box(mt, x["o"])}</div>'
            f'<div class="stats">{stats}</div>{chem_box(x, up)}<dl class="facts">{dl}</dl>' + (f'<p class="mtnote">{e(MT_NOTE)}</p>' if mt else "") +
            f'<a class="btn" href="{up}#q={e(x["n"])}">Watch on Ezzcoins</a></div></div>'
            f'<section class="more">{more}</section></main>{script}' + foot(up))


# PlayStyle names in EA's spelling (FUTWIZ writes some as one word, e.g. "Quickstep", "GameChanger", "Deadball", "Precision").
PS_NAMES = ["Finesse Shot", "Chip Shot", "Power Shot", "Dead Ball", "Precision Header", "Low Driven Shot", "Gamechanger", "Acrobatic",
            "Incisive Pass", "Pinged Pass", "Long Ball Pass", "Tiki Taka", "Whipped Pass", "Inventive", "Technical", "Rapid", "Flair", "First Touch",
            "Trickster", "Press Proven", "Quick Step", "Relentless", "Long Throw", "Bruiser", "Enforcer", "Jockey", "Block", "Intercept", "Anticipate",
            "Slide Tackle", "Aerial Fortress", "Far Throw", "Footwork", "Cross Claimer", "Rush Out", "Far Reach", "Deflector", "1v1 Close Down"]
PS_KEY = {re.sub(r"[^a-z]", "", n.lower()): n for n in PS_NAMES}
PS_KEY.update({"precision": "Precision Header", "powerheader": "Precision Header", "lowdriven": "Low Driven Shot", "longball": "Long Ball Pass"})


def ps_norm(lst, plus):
    out = []
    for s in (t.strip() for t in str(lst or "").split(",")):
        if not s:
            continue
        n = PS_KEY.get(re.sub(r"[^a-z]", "", re.sub(r"plus$", "", s.lower())), s.rstrip("+").strip())
        out.append(n + "+" if plus else n)
    return ", ".join(out)


def ps_text(x):
    """PlayStyles+ line for a special card: its own once checked, else the base card's, marked as such."""
    own = ", ".join(t.strip() for t in str(x.get("ps") or "").split(",") if t.strip())
    if x.get("leg") or x.get("psChk"):
        return own or ("None" if x.get("psChk") else "")
    return f"{own} (base card; this card's are being checked)" if own else "Being checked"


PLAYSTYLE_ICON_SLUGS = {"acrobatic":"acrobatic","chip shot":"chip-shot","dead ball":"dead-ball","finesse shot":"finesse-shot","gamechanger":"game-changer","low driven shot":"low-driven-shot","power shot":"power-shot","precision header":"precision-header","incisive pass":"incisive-pass","inventive":"inventive","long ball pass":"long-ball-pass","pinged pass":"pinged-pass","tiki taka":"tiki-taka","whipped pass":"whipped-pass","first touch":"first-touch","press proven":"press-proven","rapid":"rapid","technical":"technical","trickster":"trickster","aerial fortress":"aerial-fortress","anticipate":"anticipate","block":"block","intercept":"intercept","jockey":"jockey","slide tackle":"slide-tackle","bruiser":"bruiser","enforcer":"enforcer","long throw":"long-throw","quick step":"quick-step","relentless":"relentless","1v1 close down":"rush-out","cross claimer":"cross-claimer","deflector":"deflector","far reach":"far-reach","far throw":"far-throw","footwork":"footwork"}
PLAYSTYLE_ICON_ALIASES = {"game changer": "gamechanger", "rush out": "1v1 close down", "tiki-taka": "tiki taka", "aerial": "aerial fortress", "power header": "precision header"}

def playstyle_row(lst):
    """Real named PlayStyle glyphs beneath verified player artwork."""
    names = [t.strip() for t in ps_norm(lst, False).split(",") if t.strip()]
    if not names:
        return ""
    badges = []
    for name in names:
        key = name.lower()
        slug = PLAYSTYLE_ICON_SLUGS.get(PLAYSTYLE_ICON_ALIASES.get(key, key))
        icon = (f'<svg class="playstyle-icon" viewBox="0 0 256 256" aria-hidden="true" focusable="false"><use href="../../playstyle-icons.svg?v=20261006-1#{slug}"></use></svg>' if slug else "")
        badges.append(f'<span class="playstyle">{icon}{e(name)}</span>')
    return '<div class="playstyles" aria-label="Regular PlayStyles"><div class="playstyles-title">PlayStyles</div>' + "".join(badges) + "</div>"


def special_page(x, codes, specials, credits):
    up = "../../"
    leg = x.get("leg")
    lab = ST_GK if x["p"] == "GK" else ST_OUT
    has = any(v is not None for v in x["s"])
    where = " · ".join(v for v in (x["c"], x["l"]) if v and not (leg and str(v).upper() == "ICON"))
    ver = x["ver"] or "Special card"
    stats_txt = ", ".join(f"{lab[i]} {v}" for i, v in enumerate(x["s"]) if v is not None)
    title = f'{x["n"]} {ver} FC 27 – {x["o"]} {x["p"]} stats & price | Ezzcoins'
    mt = meta(x["p"], x["a"], x["s"], x["sm"], x["wf"], x["ps"]) if has else {}
    mt_txt = f'. Meta rating {next(iter(mt.values()))} ({next(iter(mt))})' if mt else ""
    desc = (f'{x["n"]}\'s {ver} card in EA SPORTS FC 27 Ultimate Team: {x["o"]}-rated {x["p"]}'
            + (f' for {x["c"]}' if x["c"] else "") + (f', {x["nat"]}' if x["nat"] else "")
            + (f". {stats_txt}" if stats_txt else "") + mt_txt + ". Console price on Ezzcoins.")
    b = x["base"]
    facts = [("Card", ver), ("Full name", x.get("full") if x.get("full") and x.get("full") != x["n"] else ""), ("Added", day(x["added"])),
             ("Position", x["p"] + (f' (also {", ".join(t.strip() for t in x["a"].split(","))})' if x["a"] else "")),
             ("Club", x["c"]), ("League", x["l"]), ("Nation", x["nat"]),
             ("Skill moves", f'{x["sm"]}★' if x["sm"] else ""), ("Weak foot", f'{x["wf"]}★' if x["wf"] else ""),
             ("PlayStyles+", ps_text(x)), ("PlayStyles", ", ".join(t.strip() for t in str(x.get("pls") or "").split(",") if t.strip()))]
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in facts if v not in ("", None))
    if b:
        base_txt = f'{b["o"]} {b["p"]}'
        dl += f'<dt>Base card</dt><dd>' + (f'<a href="{up}p/{b["path"]}">{e(base_txt)} ›</a>' if b.get("path") else e(base_txt)) + '</dd>'
    stats = ("".join(f'<div class="st"><small>{lab[i]}</small><b class="{q(v)}">{"–" if v is None else v}</b></div>' for i, v in enumerate(x["s"]))
             if has else "")
    if leg:
        others = sorted((y for y in specials if y.get("leg") == leg and y["id"] != x["id"]), key=lambda y: -y["o"])[:8]
        more = (f'<h2>More {"Icons" if leg == "icon" else "Heroes"}</h2>' + card_list(others, codes, up, lambda y: f'{y["p"]} · {y["c"] or y["l"]}')) if others else ""
    else:
        others = [y for y in specials if y["id"] != x["id"] and not y.get("leg")][:8]
        more = f'<h2>Other new cards</h2>' + card_list(others, codes, up, lambda y: y["ver"]) if others else ""
    script = ("<script>(()=>{const n=document.querySelector('.fc-name.sig'),fit=()=>{if(!n||!n.clientWidth)return;n.style.fontSize='';"
              "let f=parseFloat(getComputedStyle(n).fontSize);while(n.scrollWidth>n.clientWidth+1&&f>16){f--;n.style.fontSize=f+'px'}};"
              "fit();document.fonts&&document.fonts.ready.then(fit)})()</script>"
              "<script>(()=>{const id=%s,key=%s,el=document.getElementById('px'),g=f=>window.EzzcoinsMarket.fetchData(f).catch(()=>null);"
              "const load=()=>Promise.all([g('card-ids.json'),g(%s),g('live-prices.json')]).then(([ids,b,live])=>{"
              "const n=b&&Array.isArray(b.cards)?b.cards.find(c=>String(c.gid!=null&&c.gid!==''?c.gid:c.fid)===key):null;"
              "const item=ids&&ids[key]||n&&n.eaId||n&&n.gid||Number(key);"
              "const row=live&&Array.isArray(live.rows)?live.rows.find(r=>Number(r[0])===Number(item)):null;"
              "if(!row||row[3]!==0||!(row[1]>0)){const state=row&&row[3];el.textContent=/FUT Champions/i.test(n&&n.version||'')?'Reward card · not tradeable':state===1?'SBC card · not tradeable':state===2?'Objective card · not tradeable':state===4?'Reward card · not tradeable':state===3?'Not tradeable':state===0?'No listings':'Price unavailable';return}"
              "const q=live.quoteMetadata&&live.quoteMetadata[String(item)]&&live.quoteMetadata[String(item)].console;const c={price:row[1],at:q&&q.at||live.publishedAt.console,src:q&&q.src||live.source};"
              "const m=Math.max(0,Math.round((Date.now()-Date.parse(c.at))/6e4)),h=Math.floor(m/60),ago=m<1?'just now':m<60?m+' min ago':h<48?h+' h ago':Math.floor(h/24)+' days ago';"
              "el.innerHTML='<b><i class=\\\"coin\\\"></i>'+Number(c.price).toLocaleString('en-US')+'</b><span>Console · '+c.src+' · '+ago+'</span>'});load();setInterval(load,300000)})()</script>"
              ) % (json.dumps(str(x["id"])), json.dumps(str(x["key"])), json.dumps("legends.json" if leg else "newcards.json"))
    bid = x.get("pid")
    pc = credits.get(str(bid)) if bid else None
    pimg, pcredit = photo(credits, bid, x["n"], up)
    art_photo = card_art_photo(CARD_ART.get(str(x["key"])), x["n"])
    if art_photo:
        pimg = art_photo
    fallback_card = big_card(card_variant(x["ver"], x["o"], True), x["o"], x["p"], x["cn"], x["s"], lab, flag(codes, x["nat"], up, True), ver, pimg, sig=True)
    full_art = card_art_image(x["key"], x["n"], fallback_card)
    style_row = playstyle_row(x.get("pls"))
    return (head(title, desc, BASE + "p/" + x["path"], up, BASE + "photos/" + pc["img"] if pc else None) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> › <a href="{up}p/">Player pages</a> › {e(x["n"])} ({e(ver)})</div>'
            f'<div class="hero"><div class="side">{full_art}{style_row}{"" if full_art or art_photo else pcredit}</div>'
            f'<div><div class="tag">{e(ver)}</div><h1>{e(x["n"])}</h1><div class="sub">{x["o"]} {e(x["p"])}' + (f" · {e(where)}" if where else "")
            + (f' · {flag(codes, x["nat"], up)}{e(x["nat"])}' if x["nat"] else "") + '</div>'
            f'<div class="kv"><div class="px" id="px"><span class="none">No console price yet. {"Icons and Heroes are" if leg else "New cards are"} priced every half hour while FUTBIN can be reached.</span></div>{meta_box(mt, x["o"])}</div>'
            + (f'<div class="stats">{stats}</div>{chem_box(x, up)}' if has else '<p class="nostats">This card\'s own stats appear here after one of the next ' + ("price" if leg else "hourly") + ' updates.</p>')
            + f'<dl class="facts">{dl}</dl>' + (f'<p class="mtnote">{e(MT_NOTE)}</p>' if mt else "") + f'<a class="btn" href="{up}#q={e(x["n"])}">Watch on Ezzcoins</a></div></div>'
            f'<section class="more">{more}</section></main>{script}' + foot(up))


def credits_page(credits, allp, legends_by_id=None):
    up = "../../"
    rows = []
    look = dict(allp)
    look.update(legends_by_id or {})
    for pid, c in sorted(credits.items(), key=lambda kv: (look.get(int(kv[0]), {}).get("n") or "")):
        x = look.get(int(pid))
        if not x:
            continue
        name = f'<a href="{up}p/{x["path"]}">{e(x["n"])}</a>' if x.get("path") else e(x["n"])
        rows.append(f'<li><b>{name}</b> \u00b7 {e(c["author"])} \u00b7 {e(c["licence"])} \u00b7 Wikimedia Commons'
                    f'<details><summary>Source</summary><p>{e(c["page"])}</p><p>Licence: {e(c["licenceUrl"])}</p></details></li>')
    title = "Photo credits | Ezzcoins"
    desc = "Authors and licences of the player photos used on Ezzcoins."
    return (head(title, desc, BASE + "p/credits/", up) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> \u203a Photo credits</div><h1>Photo credits</h1>'
            f'<p class="sub">Player photos come from Wikimedia Commons under free licences (public domain, CC0, CC BY, CC BY-SA or Attribution). '
            f'They are cropped and faded into the card design; under CC BY-SA the cropped versions are shared under the same licence. '
            f'Ezzcoins is not affiliated with the photographers or the players.</p>'
            f'<ul class="credits">{"".join(rows)}</ul></main>' + foot(up))


def list_page(groups, codes, total, specials, legends=()):
    up = "../"
    title = "FC 27 player pages: stats and prices | Ezzcoins"
    desc = f"Stats, PlayStyles and console prices for all {total} EA SPORTS FC 27 Ultimate Team players rated {MIN_OVR} or higher."
    body = (f'<h2>New special cards</h2>' + card_list(specials, codes, up, lambda y: y["ver"]) if specials else "")
    for leg, label in (("icon", "Icons"), ("hero", "Heroes")):
        items = sorted((y for y in legends if y.get("leg") == leg), key=lambda y: (-y["o"], y["n"]))
        if items:
            body += f'<h2>{label}</h2>' + card_list(items, codes, up, lambda y: f'{y["p"]} · {y["c"] or y["l"]}')
    body += "".join(f'<h2>{ovr} rated</h2>' + card_list(items, codes, up, lambda y: f'{y["p"]} · {y["c"]}') for ovr, items in groups)
    script = ("<script>(()=>{const f=document.getElementById('find'),k=s=>s.normalize('NFD').replace(/\\p{M}/gu,'').toLowerCase();"
              "f.addEventListener('input',()=>{const t=k(f.value.trim());for(const li of document.querySelectorAll('.more li'))li.hidden=!!t&&!k(li.textContent).includes(t);"
              "for(const h of document.querySelectorAll('.more h2')){const ul=h.nextElementSibling;h.hidden=ul&&![...ul.children].some(li=>!li.hidden)}})})()</script>")
    return (head(title, desc, BASE + "p/", up) +
            f'<main><div class="crumb"><a href="{up}">Ezzcoins</a> › Player pages</div><h1>FC 27 player pages</h1>'
            f'<p class="sub">All {total} players rated {MIN_OVR} or higher in EA SPORTS FC 27, with stats, PlayStyles+ and console prices.</p>'
            f'<input class="find" id="find" type="search" placeholder="Find a player" autocomplete="off"><section class="more">{body}</section></main>{script}' + foot(up))


def main():
    global CARD_ART, REGULAR_PLAYSTYLES
    try:
        CARD_ART = json.load(open(os.path.join(ROOT, "data", "card-art.json"), encoding="utf-8"))
    except (OSError, ValueError):
        CARD_ART = {}
    try:
        stored_playstyles = json.load(open(os.path.join(ROOT, "data", "playstyles.json"), encoding="utf-8"))
        REGULAR_PLAYSTYLES = stored_playstyles.get("cards", stored_playstyles) if isinstance(stored_playstyles, dict) else {}
    except (OSError, ValueError):
        REGULAR_PLAYSTYLES = {}

    data = json.load(open(os.path.join(ROOT, "data", "players.json"), encoding="utf-8"))
    codes = json.load(open(os.path.join(ROOT, "flags", "codes.json"), encoding="utf-8"))
    cpath = os.path.join(ROOT, "photos", "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    credits = {k: v for k, v in credits.items() if os.path.exists(os.path.join(ROOT, "photos", v.get("img", "")))}
    ci = {c: i for i, c in enumerate(data["cols"])}
    get = lambda r, c: r[ci[c]] if c in ci else None
    players, allp, byname, byfull = [], {}, {}, {}
    for r in data["rows"]:
        o = get(r, "ovr") or 0
        if get(r, "id") is None:
            continue
        x = {"id": int(get(r, "id")), "n": get(r, "name") or "", "f": get(r, "full") or "", "q": get(r, "q") or "", "o": int(o),
             "p": get(r, "pos") or "", "a": get(r, "alt") or "", "c": get(r, "club") or "", "l": get(r, "league") or "",
             "nat": get(r, "nation") or "", "g": get(r, "gender"), "sm": get(r, "sm"), "wf": get(r, "wf"), "ft": get(r, "foot") or "",
             "h": get(r, "height"), "age": get(r, "age"), "ps": get(r, "psp") or "",
             "s": [get(r, f"s{k}") for k in range(1, 7)]}
        x["pls"] = ps_norm(REGULAR_PLAYSTYLES.get(str(x["id"]), ""), False)
        x["path"] = f'{slug(x["n"])}-{x["id"]}/' if x["o"] >= MIN_OVR else ""
        allp[x["id"]] = x
        byname.setdefault(slug(x["n"]), []).append(x)
        if x["f"]:
            byfull.setdefault(slug(x["f"]), []).append(x)
        if x["o"] >= MIN_OVR:
            players.append(x)
    players.sort(key=lambda x: (-x["o"], x["n"]))
    specials, specials_of = [], {}
    npath = os.path.join(ROOT, "data", "newcards.json")
    cards = []
    if os.path.exists(npath):
        try:
            cards = json.load(open(npath, encoding="utf-8")).get("cards") or []
        except (ValueError, AttributeError):
            cards = []
    for c in cards:
        key = c.get("gid") if c.get("gid") not in (None, "") else c.get("fid")
        if not c.get("name") or key in (None, ""):
            continue
        try:
            key = int(key)
        except (TypeError, ValueError):
            continue
        b = allp.get(int(c["baseId"])) if str(c.get("baseId") or "").isdigit() else None
        if not b:
            # FUTBIN often lists the full legal name ("João Félix Sequeira"), so also match EA's full names.
            hits = byname.get(slug(c["name"]), []) or byfull.get(slug(c["name"]), [])
            b = next((h for h in hits if c.get("club") and h["c"] == c.get("club")), None) or (max(hits, key=lambda h: h["o"]) if hits else None)
        st = c.get("stats") if isinstance(c.get("stats"), list) and len(c["stats"]) == 6 else [None] * 6
        sx = {"id": SPECIAL + key, "key": key, "n": c["name"], "o": int(c.get("ovr") or 0), "p": c.get("pos") or (b["p"] if b else ""),
              "a": c.get("alt") or "", "c": (b["c"] if b else "") or c.get("club") or "", "l": c.get("league") or (b["l"] if b else ""),
              "nat": c.get("nation") or (b["nat"] if b else ""), "sm": c.get("sm"), "wf": c.get("wf"),
              "s": [None if v in (None, "") else v for v in st], "ver": c.get("version") or "", "added": c.get("added") or "", "base": b}
        # PlayStyles+: the card's own once a price run has checked them on a page that marks them ("psAt"); until then the
        # base card's, shown as such, when the base card is surely the same player (linked id or same club). Same rule as index.html.
        sx["psChk"] = bool(c.get("psAt"))
        sx["pls"] = ps_norm(c.get("pls"), False) if sx["psChk"] else ""
        if not sx["pls"]:
            sx["pls"] = ps_norm(REGULAR_PLAYSTYLES.get(str(key), ""), False)
        sx["ps"] = (ps_norm(c.get("ps"), True) if sx["psChk"] else
                    b["ps"] if b and (str(c.get("baseId") or "").isdigit() or (c.get("club") and b["c"] == c.get("club"))) else "")
        # Name on the card: EA's card name for the same player ("João Félix", "Álex Baena") when the base card is
        # certainly the same person (linked id, same club, or the only player with that name); else the last word.
        sure = b is not None and (str(c.get("baseId") or "").isdigit() or (c.get("club") and b["c"] == c.get("club"))
                                  or len(byname.get(slug(c["name"]), []) or byfull.get(slug(c["name"]), [])) == 1)
        sx["cn"] = (b["q"] or b["n"]) if sure else card_name(sx["n"])
        sx["pid"] = b["id"] if sure and str(b["id"]) in credits else None  # photo of the same player
        sx["path"] = f'{slug(sx["n"])}-{slug(sx["ver"]) if sx["ver"] else "special"}-{sx["id"]}/'
        specials.append(sx)
        if b:
            specials_of.setdefault(b["id"], []).append(sx)
    specials.sort(key=lambda y: (str(y["added"]), y["o"]), reverse=True)
    # Icons and Heroes (data/legends.json, filled by the price runs): special-card pages of their own, kept for good.
    legends = []
    lpath = os.path.join(ROOT, "data", "legends.json")
    lcards = []
    if os.path.exists(lpath):
        try:
            lcards = json.load(open(lpath, encoding="utf-8")).get("cards") or []
        except (ValueError, AttributeError):
            lcards = []
    seen = {y["id"] for y in specials}
    for c in lcards:
        try:
            key = int(c.get("gid") if c.get("gid") not in (None, "") else c.get("fid"))
        except (TypeError, ValueError):
            continue
        leg = "icon" if c.get("league") == "Icons" else "hero" if c.get("league") == "Heroes" else ""
        if not c.get("name") or not leg or SPECIAL + key in seen:
            continue
        seen.add(SPECIAL + key)
        st = c.get("stats") if isinstance(c.get("stats"), list) and len(c["stats"]) == 6 else [None] * 6
        ver = c.get("version") or ("Icon" if leg == "icon" else "Hero")
        lx = {"id": SPECIAL + key, "key": key, "leg": leg, "n": c["name"], "full": c.get("full") or "", "o": int(c.get("ovr") or 0),
              "p": c.get("pos") or "", "a": c.get("alt") or "", "c": c.get("club") or "", "l": c["league"], "nat": c.get("nation") or "",
              "sm": c.get("sm"), "wf": c.get("wf"), "s": [None if v in (None, "") else v for v in st], "ver": ver, "added": "",
              "base": None, "ps": ps_norm(c["ps"], True) if c.get("ps") else "", "cn": card_name(c["name"]) if len(c["name"]) > 14 else c["name"]}
        lx["pls"] = ps_norm(REGULAR_PLAYSTYLES.get(str(key), ""), False)
        lx["pid"] = lx["id"] if str(lx["id"]) in credits else None  # photo saved under the card's own id
        lx["path"] = f'{slug(lx["n"])}-{slug(ver)}-{lx["id"]}/'
        legends.append(lx)
    legends.sort(key=lambda y: (-y["o"], y["n"]))
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
    chem_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chem.min.js")
    if os.path.exists(chem_src):
        shutil.copyfile(chem_src, os.path.join(out, "chem.js"))
    for x in players:
        d = os.path.join(out, x["path"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(player_page(x, codes, by_club, by_nat, specials_of, credits))
    for x in specials:
        d = os.path.join(out, x["path"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(special_page(x, codes, specials, credits))
    for x in legends:
        d = os.path.join(out, x["path"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(special_page(x, codes, legends, credits))
    groups = []
    for x in players:
        if not groups or groups[-1][0] != x["o"]:
            groups.append((x["o"], []))
        groups[-1][1].append(x)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(list_page(groups, codes, len(players), specials, legends))
    with open(os.path.join(out, "cardnames.json"), "w", encoding="utf-8") as fh:
        json.dump({str(x["id"]): dict({"n": x["cn"], "nat": x["nat"], "art": CARD_IDS.get(str(x["key"]), x["key"])}, **({"ph": x["pid"]} if x["pid"] else {})) for x in specials + legends},
                  fh, ensure_ascii=False, separators=(",", ":"))
    # Short photo credits for the cards on the home page, and a page listing every photo's author, licence and source.
    with open(os.path.join(out, "photos.json"), "w", encoding="utf-8") as fh:
        json.dump({k: f'{v["author"]} \u00b7 {v["licence"]}' for k, v in credits.items()}, fh, ensure_ascii=False, separators=(",", ":"))
    os.makedirs(os.path.join(out, "credits"), exist_ok=True)
    with open(os.path.join(out, "credits", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(credits_page(credits, allp, {x["id"]: x for x in legends}))
    urls = [BASE, BASE + "privacy.html", BASE + "p/", BASE + "p/credits/"] + [BASE + "p/" + x["path"] for x in specials + legends + players]
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 + "".join(f"<url><loc>{e(u)}</loc></url>\n" for u in urls) + "</urlset>\n")
    print(f"OK: {len(players)} player pages ({sum(1 for x in players if str(x['id']) in credits)} with photos), {len(specials)} special card pages, {len(legends)} Icon and Hero pages, list page and sitemap ({len(urls)} URLs)")


if __name__ == "__main__":
    main()
