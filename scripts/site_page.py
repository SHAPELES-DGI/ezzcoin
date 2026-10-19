"""Shared page shell for Ezzcoins' article pages (trading guides and weekly market recaps).

Same look as the player pages (p/style.css) plus pages.css for article text, tables and live panels.
Standard library only.
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_nav import bottom_nav, nav_css  # noqa: E402  (phone tab bar shared with every page)

BASE = os.environ.get("EZZ_BASE", "https://ezzcoins.com/")
BANNER = "<!-- © 2026 Ezzcoins. All rights reserved. Copying or reuse of this code is not permitted. -->"
CSS_V = "28"            # p/style.css, same as scripts/build_pages.py
PAGES_V = "20261013-2"  # pages.css and guides.js
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;1,800&family=Barlow:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">')
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5351346431839799" '
           'crossorigin="anonymous"></script>')
TRUST = "Free and fan-made. Ezzcoins never sells coins, accounts or boosting."


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def ld(obj):
    """A JSON-LD block, safe inside <script>."""
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def breadcrumbs(items):
    """items: [(name, absolute url), ...]"""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def page(*, title, desc, path, up, body, crumbs, schema=(), scripts=(), image=None):
    """A full HTML page. path: the page's path from the site root ('guides/fodder-value/'); up: '../../'."""
    canon = BASE + path
    trail = " › ".join(f'<a href="{e(up + p)}">{e(n)}</a>' if p is not None else e(n) for n, p in crumbs)
    blocks = "".join(ld(s) for s in [breadcrumbs([(n, BASE + (path if p is None else p)) for n, p in crumbs]), *schema])
    js = "".join(f'<script src="{up}{s}" defer></script>' for s in scripts)
    return (f'<!doctype html>{BANNER}<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon)}">'
            f'<meta property="og:type" content="article"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{e(canon)}"><meta property="og:image" content="{e(image or BASE + "icon-512.png")}"><meta name="theme-color" content="#080d29">'
            f'<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">'
            f'<link rel="manifest" href="{up}manifest.webmanifest">{FONTS}<link rel="stylesheet" href="{up}p/style.css?v={CSS_V}">'
            f'<link rel="stylesheet" href="{up}pages.css?v={PAGES_V}">{blocks}{js}{nav_css(up)}{ADSENSE}<script src="{up}ezz-ads.js?v=1" defer></script></head><body class="ez-page has-bnav">'
            f'<header class="top"><a class="home" href="{up}"><img src="{up}mark.svg" alt="" width="34" height="34"><b>Ezz<span>coins</span></b></a>'
            f'<nav class="nav"><a href="{up}guides/">Guides</a><a href="{up}recap/">Recap</a><a href="{up}prices.html">Prices</a></nav></header>'
            f'<main><div class="crumb">{trail}</div>{body}<div class="ezz-ad" hidden aria-label="Advertisement"></div></main>'
            f'<footer><p class="trust">{e(TRUST)}</p>Ratings: EA SPORTS FC 27. Prices come from FUTBIN when it can be reached and from FUT.GG otherwise. Ezzcoins is not endorsed by or '
            f'affiliated with EA or its licensors, and not affiliated with FUTBIN, FUT.GG, FUTWIZ or EasySBC. '
            f'<a href="{up}privacy.html">Privacy and cookies</a></footer>' + bottom_nav(up) + '</body></html>\n')


def write(root, path, text):
    """Write root/path/index.html only when the content changed. Returns True if written."""
    d = os.path.join(root, path)
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, "index.html")
    try:
        with open(f, encoding="utf-8") as fh:
            if fh.read() == text:
                return False
    except OSError:
        pass
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text)
    return True
