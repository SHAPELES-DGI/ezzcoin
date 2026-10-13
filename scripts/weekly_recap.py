#!/usr/bin/env python3
"""Ezzcoins' automatic weekly market recap, written from the site's own data with no AI involved.

- recap/<monday>/index.html  one page per finished week (Monday to Sunday, UK time), written once
- recap/index.html           this week so far, rewritten at most once an hour, plus links to past weeks

Each recap has: how the 84/85/86 floors and the Top 100 index moved, the week's biggest risers and
fallers among cards worth 10,000+ coins (console), new special cards, the trade calls graded that week
and how prices moved around each evening's 6 PM UK drop. Sources: data/history.json and
data/market-index.json (floors and index), data/price-history/ (card prices), data/newcards.json,
data/ledger.json (calls and the 6 PM drop log). scripts/build_pages.py adds the pages to sitemap.xml.

Usage: python3 scripts/weekly_recap.py [site root]   (standard library only)
"""
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk  # noqa: E402
from site_page import BASE, e, page, write  # noqa: E402

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIRST_WEEK = date(2026, 10, 12)   # card price history starts on this Monday
MOVER_MIN = 10000                 # movers: cards worth this many coins at the start of the week
MOVERS = 6
PUBLISHER = {"@type": "Organization", "name": "Ezzcoins", "url": BASE, "logo": {"@type": "ImageObject", "url": BASE + "icon-512.png"}}


def week_start(day):
    return day - timedelta(days=day.weekday())


def bounds(monday):
    """UTC start and end of a UK Monday-to-Sunday week (correct across the clock change)."""
    a = datetime(monday.year, monday.month, monday.day, tzinfo=desk.UK).astimezone(timezone.utc)
    n = monday + timedelta(days=7)
    return a, datetime(n.year, n.month, n.day, tzinfo=desk.UK).astimezone(timezone.utc)


def label(monday):
    sun = monday + timedelta(days=6)
    left = f"{monday.day} {monday:%B}" if monday.month != sun.month else str(monday.day)
    return f"{left}–{sun.day} {sun:%B} {sun.year}"


def pct(a, b):
    return round((b / a - 1) * 100, 1) if a and b else None


def fmt_pct(v):
    return "–" if v is None else f"{v:+.1f}%"


def coins(n):
    return f"{int(round(n)):,}"


# ---------------------------------------------------------------- data

def floors(a, b):
    """84/85/86 floors at the start and end of the window, and the Top 100 index from its current chain."""
    pts = [p for p in desk.readings() if a <= p[0] <= b]
    out = {}
    for k in ("f84", "f85", "f86"):
        vals = [(t, v[k]) for t, v in pts if v.get(k)]
        if len(vals) >= 2:
            out[k] = (vals[0][1], vals[-1][1], pct(vals[0][1], vals[-1][1]))
    # The index basket was re-based in the past; only market-index.json's chain-linked points are comparable.
    idx = [(desk.parse(r[0]), r[1]) for r in desk.read("market-index.json", {}).get("points", []) if r and r[1]]
    idx = [(t, v) for t, v in idx if t and a <= t <= b]
    if len(idx) >= 2 and idx[0][0] - a <= timedelta(hours=36):
        out["i100"] = (idx[0][1], idx[-1][1], pct(idx[0][1], idx[-1][1]))
    return out


def page_paths():
    """EA item id -> player page path, from the folders in p/."""
    card_ids = desk.read("card-ids.json", {})
    newcards = desk.read("newcards.json", {}).get("cards", []) + desk.read("legends.json", {}).get("cards", [])
    out = {}
    try:
        names = os.listdir(os.path.join(ROOT, "p"))
    except OSError:
        return out
    for name in names:
        m = re.search(r"-(\d+)$", name)
        if m:
            item = desk.item_for(int(m.group(1)), card_ids, newcards)
            if item:
                out.setdefault(int(item), f"p/{name}/")
    return out


def movers(a, b, info):
    """(risers, fallers) by console price change across the window, cards worth MOVER_MIN+ at the start."""
    folder = desk.DATA / "price-history"
    rows = []
    for f in sorted(folder.glob("[0-9][0-9].json")):
        try:
            items = json.loads(f.read_text()).get("items", {})
        except (OSError, ValueError):
            continue
        for k, v in items.items():
            pts = [(datetime.fromtimestamp(t, timezone.utc), p) for t, p in v.get("console", []) if a <= datetime.fromtimestamp(t, timezone.utc) <= b]
            if len(pts) < 6:
                continue
            # The first and last three hourly readings must agree (within 25%); their middle value is the price.
            # A single mispriced listing can't then make a card look like it doubled or crashed.
            first, last = sorted(p for _, p in pts[:3]), sorted(p for _, p in pts[-3:])
            if first[-1] > first[0] * 1.25 or last[-1] > last[0] * 1.25 or pts[0][0] - a > timedelta(hours=36):
                continue
            p0, p1 = first[1], last[1]
            if p0 >= MOVER_MIN and int(k) in info:
                rows.append((pct(p0, p1), int(k), p0, p1))
    rows = [r for r in rows if r[0] is not None]
    rise = sorted((r for r in rows if r[0] > 0), key=lambda r: -r[0])[:MOVERS]
    fall = sorted((r for r in rows if r[0] < 0), key=lambda r: r[0])[:MOVERS]
    return rise, fall


def new_cards(a, b):
    groups = {}
    for c in desk.read("newcards.json", {}).get("cards", []):
        made = desk.parse(c.get("createdAt") or c.get("added"))
        if made and a <= made < b and c.get("version"):
            groups.setdefault(c["version"], []).append(c)
    out = []
    for ver, cards in groups.items():
        cards.sort(key=lambda c: -(c.get("ovr") or 0))
        out.append((ver, len(cards), cards[:4]))
    out.sort(key=lambda g: -g[1])
    return out


def calls(a, b):
    ledger = desk.read("ledger.json", {})
    graded = [c for c in ledger.get("calls", []) if c.get("status") in ("hit", "miss") and desk.parse(c.get("gradedAt")) and a <= desk.parse(c["gradedAt"]) < b]
    graded.sort(key=lambda c: c["gradedAt"])
    drops = [d for d in ledger.get("dropLog", []) if a.astimezone(desk.UK).date() <= date.fromisoformat(d["date"]) < b.astimezone(desk.UK).date()]
    return graded, drops


def week_data(monday, now):
    a, b = bounds(monday)
    end = min(b, now)
    info = desk.Market(now).info
    rise, fall = movers(a, end, info)
    graded, drops = calls(a, end)
    return {"monday": monday, "a": a, "b": b, "end": end, "partial": now < b, "floors": floors(a, end),
            "rise": rise, "fall": fall, "info": info, "new": new_cards(a, end), "calls": graded, "drops": drops}


# ---------------------------------------------------------------- writing

def summary(d):
    """Plain sentences from the numbers."""
    out = []
    fl = d["floors"]
    moves = [fl[k][2] for k in ("f84", "f85", "f86") if k in fl and fl[k][2] is not None]
    if moves:
        avg = sum(moves) / len(moves)
        how = "got cheaper" if avg <= -2 else "got dearer" if avg >= 2 else "held fairly steady"
        parts = ", ".join(f"{k[1:]}s {coins(fl[k][0])} → {coins(fl[k][1])}" for k in ("f84", "f85", "f86") if k in fl)
        out.append(f"SBC fodder {how}{' so far' if d['partial'] else ''}: {parts}.")
    if "i100" in fl:
        v = fl["i100"][2]
        out.append(f"Ezzcoins' Top 100 index of the most expensive cards {'rose' if v > 0.5 else 'fell' if v < -0.5 else 'barely moved'} ({fmt_pct(v)}).")
    name = lambda r: f"{d['info'][r[1]].get('name')} {d['info'][r[1]].get('ovr') or ''}".strip()
    if d["rise"] and d["fall"]:
        out.append(f"{name(d['rise'][0])} rose the most ({fmt_pct(d['rise'][0][0])}) and {name(d['fall'][0])} fell the most ({fmt_pct(d['fall'][0][0])}) among cards worth {coins(MOVER_MIN)}+ coins.")
    if d["new"]:
        total = sum(g[1] for g in d["new"])
        out.append(f"{total} new special card{'s' if total != 1 else ''} arrived, mostly {d['new'][0][0]}.")
    if d["calls"]:
        hits = sum(1 for c in d["calls"] if c["status"] == "hit")
        out.append(f"{hits} of the {len(d['calls'])} trade call{'s' if len(d['calls']) != 1 else ''} graded this week hit after the 5% tax.")
    else:
        out.append("No trade calls were graded this week.")
    if len(d["drops"]) >= 2:
        fod = lambda x: [x["chg"][k] for k in ("f84", "f85", "f86") if k in x["chg"]]
        ups = sum(1 for x in d["drops"] if fod(x) and sum(fod(x)) / len(fod(x)) > 1)
        out.append(f"Fodder rose after {ups} of {len(d['drops'])} evening drops.")
    return out


def card_link(item, d, paths, up):
    c = d["info"].get(item, {})
    ver = c.get("version") or ""
    text = f'{e(c.get("name"))} <span class="r">{e(c.get("ovr") or "")}</span>' + (f' <small>{e(ver)}</small>' if ver and ver != "Rare" else "")
    return f'<a href="{up}{paths[item]}">{text}</a>' if item in paths else text


def body_html(d, up, paths, past=()):
    title = f"FC 27 market recap: {label(d['monday'])}" + (" (so far)" if d["partial"] else "")
    fl = d["floors"]
    stat = lambda k, name: (f'<div class="st"><small>{name}</small><b>{coins(fl[k][1]) if k != "i100" else f"{fl[k][1]:.1f}"}</b>'
                            f'<i class="{"up" if (fl[k][2] or 0) > 0 else "down" if (fl[k][2] or 0) < 0 else ""}">{fmt_pct(fl[k][2])}</i></div>') if k in fl else ""
    stats = "".join(stat(k, n) for k, n in (("f84", "84 floor"), ("f85", "85 floor"), ("f86", "86 floor"), ("i100", "Top 100 index")))
    table = lambda rows, cls: ('<table class="movers-t"><thead><tr><th>Card</th><th>Start</th><th>End</th><th>Change</th></tr></thead><tbody>'
                               + "".join(f'<tr><td>{card_link(r[1], d, paths, up)}</td><td>{coins(r[2])}</td><td>{coins(r[3])}</td><td class="{cls}">{fmt_pct(r[0])}</td></tr>' for r in rows)
                               + "</tbody></table>") if rows else '<p class="muted">Not enough recorded prices yet.</p>'
    news = ("<ul class=\"plain\">" + "".join(f"<li><b>{e(v)}</b>: {n} card{'s' if n != 1 else ''}, including "
                                             + ", ".join(f"{e(c['name'])} {e(c.get('ovr') or '')}" for c in top) + "</li>" for v, n, top in d["new"]) + "</ul>"
            ) if d["new"] else '<p class="muted">No new special cards recorded.</p>'
    calls_html = ("<ul class=\"plain calls\">" + "".join(
        f'<li><span class="chip {c["status"]}">{"Hit" if c["status"] == "hit" else "Miss"}</span> {e(c.get("title"))} '
        f'<span class="muted">({coins(c["entry"])} → {coins(c["exit"])}, {fmt_pct(c.get("result"))} after tax)</span></li>' for c in d["calls"]) + "</ul>"
                  ) if d["calls"] else '<p class="muted">No calls reached their check time this week.</p>'
    drops_html = ('<table class="movers-t"><thead><tr><th>Evening</th><th>84s</th><th>85s</th><th>86s</th><th>Top 100</th></tr></thead><tbody>'
                  + "".join(f'<tr><td>{date.fromisoformat(x["date"]):%a %d %b}</td>'
                            + "".join(f'<td class="{"up" if (x["chg"].get(k) or 0) > 1 else "down" if (x["chg"].get(k) or 0) < -1 else ""}">{fmt_pct(x["chg"].get(k))}</td>' for k in ("f84", "f85", "f86", "i100"))
                            + "</tr>" for x in d["drops"]) + "</tbody></table>"
                  + '<p class="muted">Change from just before 6 PM to about 8 PM UK.</p>') if d["drops"] else '<p class="muted">No evening drops recorded yet.</p>'
    updated = d["end"].astimezone(timezone.utc).strftime("%d %b %Y, %H:00 UTC")
    past_html = ("<h2>Past weeks</h2><ul class=\"plain weeks\">" + "".join(f'<li><a href="{up}recap/{m.isoformat()}/">Week of {label(m)}</a></li>' for m in past) + "</ul>") if past else ""
    return title, (
        f'<article class="recap"><p class="kicker">Weekly market recap{" · updated " + e(updated) if d["partial"] else ""}</p><h1>{e(title)}</h1>'
        + "".join(f'<p class="lead">{e(s)}</p>' if i == 0 else f"<p>{e(s)}</p>" for i, s in enumerate(summary(d)))
        + (f'<div class="stats recap-stats">{stats}</div>' if stats else "")
        + f'<h2>Biggest risers</h2>{table(d["rise"], "up")}<h2>Biggest fallers</h2>{table(d["fall"], "down")}'
        + f'<h2>New special cards</h2>{news}<h2>Trade calls graded</h2>{calls_html}<h2>Around the 6 PM drops</h2>{drops_html}'
        + f'<p class="muted method">Console prices from Ezzcoins\' own feed. Movers compare each card worth {coins(MOVER_MIN)}+ coins at its first recorded price of the week with its last. '
          'Floors are the cheapest card at each rating. Trade calls are made and graded automatically, after the 5% tax.</p>'
        + f'<p><a class="btn" href="{up}#trading">See today\'s trade calls</a></p></article>'
        + f'<nav class="related" aria-label="More"><p><a href="{up}guides/">FC 27 trading guides ›</a></p>{past_html}</nav>')


def archived():
    try:
        names = os.listdir(os.path.join(ROOT, "recap"))
    except OSError:
        return []
    weeks = []
    for n in names:
        try:
            weeks.append(date.fromisoformat(n))
        except ValueError:
            pass
    return sorted(weeks, reverse=True)


def main():
    now = desk.now_utc()
    this_monday = week_start(now.astimezone(desk.UK).date())
    written = []
    # Finished weeks: written once, the first run after the week ends.
    m = FIRST_WEEK
    while m < this_monday:
        if not os.path.exists(os.path.join(ROOT, "recap", m.isoformat(), "index.html")):
            d = week_data(m, now)
            title, body = body_html(d, "../../", page_paths())
            path = f"recap/{m.isoformat()}/"
            text = page(title=f"{title} · Ezzcoins", path=path, up="../../", body=body,
                        desc=f"What moved the FC 27 Ultimate Team market in the week of {label(m)}: fodder floors, biggest risers and fallers, new promo cards and graded trade calls.",
                        crumbs=[("Ezzcoins", ""), ("Weekly recap", "recap/"), (f"Week of {label(m)}", None)],
                        schema=[{"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished": d["b"].date().isoformat(),
                                 "dateModified": d["b"].date().isoformat(), "author": PUBLISHER, "publisher": PUBLISHER, "mainEntityOfPage": BASE + path}])
            write(ROOT, path, text)
            written.append(path)
        m += timedelta(days=7)
    # This week so far: at most once an hour.
    hub = os.path.join(ROOT, "recap", "index.html")
    stamp = now.strftime("%Y-%m-%dT%H")
    try:
        with open(hub, encoding="utf-8") as fh:
            fresh = f"<!--recap:{stamp}-->" in fh.read()
    except OSError:
        fresh = False
    if not fresh or written:
        d = week_data(this_monday, now)
        title, body = body_html(d, "../", page_paths(), archived())
        text = page(title="FC 27 Weekly Market Recap · Ezzcoins", path="recap/", up="../", body=body,
                    desc="This week in the FC 27 Ultimate Team market, updated hourly: fodder floors, biggest risers and fallers, new promo cards and graded trade calls.",
                    crumbs=[("Ezzcoins", ""), ("Weekly recap", None)])
        write(ROOT, "recap/", text.replace("</body>", f"<!--recap:{stamp}--></body>"))
        written.append("recap/")
    print(f"Weekly recap: {', '.join(written) if written else 'nothing to write'}")


if __name__ == "__main__":
    main()
