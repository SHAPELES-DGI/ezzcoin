#!/usr/bin/env python3
"""Write the latest market read, SBC list and news from data/snapshot.json into index.html.

The home page fills these sections with JavaScript, so without this, search engines and link
previews that don't run scripts only see "Loading". Each section sits between markers such as
<!--pre:read--> ... <!--/pre:read--> on its own line, so this script never touches the rest of
the page. The browser replaces the text with the live version as soon as the page loads.

Usage: python3 scripts/prerender_home.py [site root]   (standard library only)
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
TOKEN = re.compile(r"\{\{t:([^}]+)\}\}")


def esc(value):
    return html.escape(str(value or ""), quote=True)


def plain(text):
    """Turn {{t:ISO}} time tokens into a fixed UTC time; the page shows local time once it loads."""
    def one(m):
        try:
            t = datetime.fromisoformat(m.group(1).strip().replace("Z", "+00:00"))
        except ValueError:
            return ""
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        t = t.astimezone(timezone.utc)
        return f"{t.day} {t.strftime('%b %H:%M')} UTC"
    return TOKEN.sub(one, str(text or "")).strip()


def saved_at(snap):
    """'Saved update from 19 Oct 18:42 UTC' as a <time data-pre> the page turns into local time
    if the live data can't load. Empty when the snapshot has no valid time."""
    try:
        t = datetime.fromisoformat(str(snap.get("updatedAt") or "").replace("Z", "+00:00"))
    except ValueError:
        return ""
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    t = t.astimezone(timezone.utc)
    stamp = t.isoformat().replace("+00:00", "Z")
    return f'Saved update from <time data-pre datetime="{esc(stamp)}">{t.day} {t.strftime("%b %H:%M")} UTC</time>'


def read_block(snap):
    v = snap.get("verdict") or {}
    head = plain(v.get("headline")) or "Latest market read"
    return f'<h3 id="readHead">{esc(head)}</h3><p id="readDetail">{esc(plain(v.get("detail")))}</p>'


def sbc_block(snap):
    sbcs = [s for s in snap.get("sbcs") or [] if s.get("name")]
    if not sbcs:
        return '<div class="empty">Active SBCs load with the market read.</div>'
    items = ", ".join(esc(plain(s["name"])) + (f" ({esc(s['cost'])})" if s.get("cost") not in (None, "", "–") else "") for s in sbcs[:8])
    when = saved_at(snap)
    return f'<div class="empty">{when + " · " if when else ""}Active SBCs: {items}.</div>'


def news_block(snap):
    news = [n for n in snap.get("news") or [] if n.get("title")]
    if not news:
        return '<li class="muted">No news in this update.</li>'
    when = saved_at(snap)
    out = [f'<li class="muted" style="display:block">{when}.</li>'] if when else []
    for n in news[:6]:
        kind = n.get("kind")
        cls = "official" if kind == "official" else "leak" if kind == "leak" else ""
        src = (f'<span class="src {cls}">{esc(n["source"])}{" · unconfirmed" if kind == "leak" else ""}</span>' if n.get("source") else "")
        out.append(f'<li style="display:block"><div style="font-weight:600">{esc(plain(n["title"]))}{src}</div>'
                   f'<div class="muted" style="font-size:.9rem">{esc(plain(n.get("detail")))}</div></li>')
    return "".join(out)


def main():
    path = os.path.join(ROOT, "index.html")
    try:
        snap = json.load(open(os.path.join(ROOT, "data", "snapshot.json"), encoding="utf-8"))
    except (OSError, ValueError) as err:
        print(f"Skipped: data/snapshot.json unreadable ({err})")
        return
    page = open(path, encoding="utf-8").read()
    new = page
    for name, block in (("read", read_block(snap)), ("sbc", sbc_block(snap)), ("news", news_block(snap))):
        pattern = re.compile(r"(<!--pre:%s-->).*?(<!--/pre:%s-->)" % (name, name), re.S)
        if not pattern.search(new):
            print(f"Skipped: marker pre:{name} missing from index.html")
            return
        new = pattern.sub(lambda m: m.group(1) + block + m.group(2), new, count=1)
    if new == page:
        print("Home pre-render unchanged")
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    os.replace(tmp, path)
    print("Home pre-render updated from snapshot", snap.get("updatedAt"))


if __name__ == "__main__":
    main()
