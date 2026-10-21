#!/usr/bin/env python3
"""Ezzcoins' trading guides: one page per playbook setup, plus the guides hub.

Writes guides/<slug>/index.html and guides/index.html. The text lives here; each page also has a live
panel that guides.js fills from the site's own data (fodder board, Rivals timing, strategy records,
the 6 PM drop record, a tax calculator or the day's biggest risers). Run after editing a guide:

    python3 scripts/build_guides.py [site root]

scripts/build_pages.py adds every guides/*/ page to sitemap.xml. Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_page import BASE, e, page, write  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
UPDATED = "2026-10-13"   # bump when a guide's text changes

PUBLISHER = {"@type": "Organization", "name": "Ezzcoins", "url": BASE, "logo": {"@type": "ImageObject", "url": BASE + "icon-512.png"}}

GUIDES = [
    {
        "slug": "fodder-value",
        "num": "01",
        "short": "Fodder value",
        "title": "FC 27 SBC Fodder: Which Ratings Are Cheapest per Item Score Point",
        "h1": "Fodder value",
        "desc": "How to find the cheapest FC 27 SBC fodder: compare 84 to 88 rated cards by coins per Item Score point, treat near-ties as ties, and use fodder instead of flipping it.",
        "lead": "SBC fodder is where most coins quietly disappear. The cheapest card is not always the cheapest way to finish a challenge: what matters is how many coins you pay for each point a challenge asks for.",
        "steps": [("Buy", "Use the Fodder board to compare coins per Item Score point."),
                  ("Use", "Choose the cheapest valid mix for your SBC."),
                  ("Check", "Fixed rating rules can go out of date.")],
        "sections": [
            ("Price per point, not price per card", [
                "SBCs that ask for an Item Score don't care which ratings you hand in, only the total. A higher-rated card costs more but also scores more, so the fair comparison is coins divided by Item Score points. Ezzcoins works this out for every rating from 81 to 91 at the cheapest current price.",
                "Often two or three ratings sit within a tenth of a coin per point of each other. Treat those as a tie and buy whichever you can get fastest: Ezzcoins' desk learned that chasing the \"cheapest\" rating in a near-tie only makes the answer flip back and forth during the day.",
            ]),
            ("Rating squads are a different puzzle", [
                "When an SBC asks for a team rating instead, the cheapest squad is usually a mix: a few higher-rated cards lift the average so most of the squad can be cheaper. The planner in Ezzcoins' Tools tab finds the cheapest mix of 81 to 91 rated cards from the current floors.",
            ]),
            ("Use fodder, don't flip it", [
                "The cheapest card at a rating sits at a hard floor most of the time. Buy it and sell it again and the 5% tax takes your margin, because the floor rarely moves enough to cover it. Fodder is worth buying for SBCs you will actually do.",
                "The exception is a temporary dump, such as the Thursday morning after Rivals rewards. Even then, wait for two price updates in a row before you trust a very low floor: one reading can be a single cheap listing that is gone a minute later.",
            ]),
            ("Fixed rules go out of date", [
                "Advice like \"84s are always the best value\" holds until a big SBC or a promo changes demand for one rating. Check the live board before every big fodder purchase instead of relying on last week's answer.",
            ]),
        ],
        "live": ("fodder", "Cheapest fodder right now"),
        "related": ["rivals-rewards-dip", "small-budget-bidding"],
    },
    {
        "slug": "rivals-rewards-dip",
        "num": "02",
        "short": "The rewards dip",
        "title": "Rivals Rewards and FC 27 Prices: Trading the Thursday Dip",
        "h1": "The rewards dip",
        "desc": "Why FC 27 fodder and player prices often dip on Thursday morning when Rivals rewards pay out, when to buy into it, and why you should wait for two price updates.",
        "lead": "Every Thursday morning (UK time) Rivals rewards pay out. Thousands of players open their packs at once and list what they don't need, so supply jumps and prices, fodder above all, often dip for a few hours.",
        "steps": [("Watch", "New pack listings can bring prices down."),
                  ("Buy", "Only when the current quote gives you a useful margin."),
                  ("Sell", "Recheck demand before the next promo.")],
        "sections": [
            ("What happens to the market", [
                "Extra supply arrives all at once, mostly mid-rated fodder and tradeable cards from the reward packs. Demand doesn't change at the same moment, so prices give way. As the morning goes on, SBC demand and the build-up to Champions weekend usually lift prices again.",
            ]),
            ("How to buy the dip", [
                "Buy what your SBCs need during the dip rather than later in the week. If you want to trade it, Ezzcoins' desk has a written strategy for it, the Rivals rewards dip: buy 86-rated fodder after the payout and sell or use it by Saturday. Its record is graded automatically below, after the 5% tax.",
                "Wait for two consecutive price updates before you believe a crash. In one tracked case the 86 floor showed 750 coins an hour after the payout and was back at 4,200 within the hour: that was a handful of cheap listings, not the market.",
            ]),
            ("When to sell", [
                "Recheck demand before the next promo or big SBC. A rise from Thursday to the weekend is common, but a new promo on Friday evening can flood the market again. Selling and buying back always costs the 5% tax, so only sell what you won't use.",
            ]),
        ],
        "live": ("rewards", "Next Rivals rewards and the strategy's record"),
        "related": ["fodder-value", "midweek-specials"],
    },
    {
        "slug": "midweek-specials",
        "num": "03",
        "short": "Midweek specials",
        "title": "Best Day to Buy FC 27 Cards: Midweek Buying for Champions Weekend",
        "h1": "Midweek specials",
        "desc": "Why Monday to Wednesday is usually the quietest time to buy FC 27 meta cards, how Champions weekend lifts demand, and how Ezzcoins grades its buy-before-the-weekend calls.",
        "lead": "Demand for meta cards follows the week. Players build their squads for Champions weekend, so the cards they play are usually wanted most from Friday evening, and least early in the week.",
        "steps": [("Watch", "Compare Monday–Wednesday quotes with recent prices."),
                  ("Buy", "Cards you understand, with room for tax."),
                  ("Check", "Live cards can move with real-world results.")],
        "sections": [
            ("The weekly rhythm", [
                "Sunday evening and Monday are when many players sell their weekend squads, which is why prices usually ease into the start of the week. Midweek is the quietest stretch. From Thursday, with Rivals rewards paid out and Champions weekend coming, demand for meta cards builds until the weekend starts on Friday evening.",
            ]),
            ("Buying for the weekend", [
                "If you want a card for Champions, buying it midweek is usually cheaper than on Friday evening. Ezzcoins' desk turns this into graded calls (\"Buy before the weekend\"): a meta card bought between Tuesday evening and Thursday and checked on Friday at 8 PM UK, with the 5% tax counted.",
                "Pick cards you understand: you should know why players want them. A card that only looks cheap often is cheap for a reason.",
            ]),
            ("Live cards and real football", [
                "Team of the Week and other in-form cards can move with real-world results and upgrades, so a midweek bargain can turn into a loss after one bad match. Leave room for the tax and don't put all your coins into one card.",
            ]),
        ],
        "live": ("weekend", "How \"Buy before the weekend\" has done"),
        "related": ["rivals-rewards-dip", "promo-night"],
    },
    {
        "slug": "promo-night",
        "num": "04",
        "short": "Promo-night patience",
        "title": "FC 27 Promo Nights: Why You Should Not Buy New Promo Cards in the First Hour",
        "h1": "Promo-night patience",
        "desc": "New FC 27 promos usually land on Friday at 6 PM UK. Why first-hour prices are a trap, what pack supply does to the market, and what Ezzcoins measures around each drop.",
        "lead": "New promos usually arrive on Friday at 6 PM UK, and EA drops new content every evening at the same time. The first hour after a big drop is when prices are least reliable.",
        "steps": [("Avoid", "Chasing a new promo card in its first hour."),
                  ("Watch", "Supply and price changes after packs open."),
                  ("Check", "A price drop alone does not make a bargain.")],
        "sections": [
            ("Why the first hour is a trap", [
                "A new promo card has almost no supply at first: only the few that have been packed are listed, so early prices are set by a handful of sellers. As packs are opened through the evening, supply grows and prices usually settle lower. Paying the first-hour price means paying for being early.",
            ]),
            ("What the rest of the market does", [
                "Promo nights also move cards that aren't in the promo. Players sell to fund packs, and new SBCs can lift demand for specific fodder ratings. Ezzcoins records how fodder and the Top 100 index move from just before 6 PM to about 8 PM UK on every evening, with Fridays measured separately; the latest record is below.",
            ]),
            ("A falling price is not a bargain", [
                "A promo card that drops 30% in an evening can drop another 30% by Sunday. Wait until two price updates agree and the fall flattens before buying, and buy cards you will play rather than cards you hope will bounce back.",
            ]),
        ],
        "live": ("promo", "The 6 PM drop record"),
        "related": ["skip-the-hype", "midweek-specials"],
    },
    {
        "slug": "small-budget-bidding",
        "num": "05",
        "short": "Small-budget bidding",
        "title": "FC 27 Trading on a Small Budget: Bidding, the 5% Tax and Break-Even Prices",
        "h1": "Small-budget bidding",
        "desc": "How to trade FC 27 cards on a small budget: the 5% EA tax, break-even and max-buy prices, market price steps, and how to bid below the lowest Buy Now.",
        "lead": "On a small budget the 5% tax decides almost everything. A flip that looks like 300 coins of profit can be a loss once EA takes its cut, so start from the margin and only then bid.",
        "steps": [("Target", "Cards with demand and plenty of listings."),
                  ("Calculate", "Sale price × 0.95 − purchase price."),
                  ("Check", "Use the calculator before buying.")],
        "sections": [
            ("The tax maths", [
                "EA keeps 5% of every sale. What you receive is the sale price × 0.95, rounded down, so your profit is that minus what you paid. To break even you must sell for at least your purchase price ÷ 0.95, about 5.3% more than you paid. Try your numbers in the calculator below.",
            ]),
            ("Price steps matter", [
                "Prices on the Transfer Market move in fixed steps: 50 coins below 1,000, 100 up to 10,000, 250 up to 50,000, 500 up to 100,000 and 1,000 above that. On a cheap card one step is a big share of the price, which is why break-even and max-buy prices on Ezzcoins are rounded to the market's steps.",
            ]),
            ("How to bid", [
                "Pick cards with steady demand and plenty of listings, so you can sell again quickly. Bid below the lowest Buy Now, decide your top bid from the max-buy price for the margin you want, and don't chase an auction past it. Spread your coins over several cheap cards rather than one: a single bad buy then can't wipe out your budget.",
            ]),
            ("Stay safe", [
                "Trade by hand. Buying coins and automated trading tools break EA's rules and can get an account banned, and spreading large purchases across sessions looks like normal play.",
            ]),
        ],
        "live": ("calc", "Profit after tax"),
        "related": ["fodder-value", "skip-the-hype"],
    },
    {
        "slug": "skip-the-hype",
        "num": "06",
        "short": "Skip the hype",
        "title": "FC 27 Market Hype: What Really Creates Demand for a Card",
        "h1": "Skip the hype",
        "desc": "Why trending FC 27 cards often fall back, which demand actually removes cards from the market (SBCs) and which doesn't (Gallery collecting), and how Ezzcoins grades its sell-the-spike calls.",
        "lead": "A card that jumps 20% in a day is exciting, and that is the problem: by the time it is trending, most of the move is usually over. Ask what is creating the demand before you buy.",
        "steps": [("Prefer", "Demand from SBCs that remove cards from circulation."),
                  ("Avoid", "Buying only because a card is trending."),
                  ("Check", "Gallery collecting does not consume the cards.")],
        "sections": [
            ("Demand that lasts", [
                "When an SBC needs a card, every one handed in leaves the market for good. That is real, lasting demand, and it is why fodder rises when big SBCs land. Demand that doesn't remove cards, such as collecting for the FUT Gallery, can fade as fast as it came, because the cards stay in the game.",
            ]),
            ("Spikes often give part of it back", [
                "A sharp one-day rise is often followed by a partial fall as sellers rush in. Ezzcoins' desk tests this with graded \"Sell the spike\" calls: a card worth 10,000+ coins that rose 15% or more in a day, checked two days later. Its record is public, and the desk pauses the strategy if its recent calls lose.",
            ]),
            ("Before you buy a trending card", [
                "Check why it is moving, how much it has already risen, and whether you would still want it at the price before the jump. If the only reason is that it is trending, let it go: there is always another card.",
            ]),
        ],
        "live": ("hype", "Biggest rises in the last day"),
        "related": ["promo-night", "small-budget-bidding"],
    },
]
BY_SLUG = {g["slug"]: g for g in GUIDES}


def guide_html(g):
    up = "../../"
    steps = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in g["steps"])
    secs = "".join(f"<h2>{e(h)}</h2>" + "".join(f"<p>{e(p)}</p>" for p in ps) for h, ps in g["sections"])
    kind, heading = g["live"]
    live = (f'<section class="live" data-live="{kind}" aria-live="polite"><h2>{e(heading)}</h2>'
            f'<div class="live-body"><p class="muted">Loading the latest Ezzcoins data…</p></div></section>')
    rel = "".join(f'<a href="{up}guides/{r}/"><span class="o">{BY_SLUG[r]["num"]}</span><span class="n">{e(BY_SLUG[r]["short"])}</span></a>' for r in g["related"])
    body = (f'<article class="guide"><p class="kicker">Ezzcoins trading guide {g["num"]}</p><h1>{e(g["h1"])}</h1><p class="lead">{e(g["lead"])}</p>'
            f'<dl class="steps">{steps}</dl>{secs}{live}'
            f'<p class="tools-link"><a class="btn" href="{up}#tools">Open the Ezzcoins calculators</a></p></article>'
            f'<nav class="related" aria-label="Related guides"><h2>Related guides</h2><div class="rel">{rel}</div>'
            f'<p><a href="{up}guides/">All trading guides ›</a></p></nav>')
    path = f"guides/{g['slug']}/"
    schema = [{"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["desc"],
               "dateModified": UPDATED, "datePublished": UPDATED, "inLanguage": "en", "author": PUBLISHER, "publisher": PUBLISHER,
               "mainEntityOfPage": BASE + path, "image": BASE + "icon-512.png"}]
    return path, page(title=f"{g['title']} · Ezzcoins", desc=g["desc"], path=path, up=up, body=body,
                      crumbs=[("Ezzcoins", ""), ("Guides", "guides/"), (g["h1"], None)], schema=schema,
                      scripts=("market-data.js?v=20261021-lean", "guides.js?v=20261021-paper"))


def hub_html():
    up = "../"
    cards = "".join(f'<a class="guide-card" href="{g["slug"]}/"><span class="o">{g["num"]}</span><span class="n">{e(g["h1"])}</span>'
                    f'<span class="d">{e(g["lead"])}</span></a>' for g in GUIDES)
    body = (f'<p class="kicker">The Ezzcoins playbook</p><h1>FC 27 trading guides</h1>'
            f'<p class="lead">Six short guides to the setups Ezzcoins trades and grades: fodder value, the Thursday rewards dip, midweek buying, promo nights, small-budget bidding and market hype. Each one shows live data from the site.</p>'
            f'<div class="guide-grid">{cards}</div><p class="more-links"><a href="{up}recap/">This week\'s market recap ›</a></p>')
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "FC 27 trading guides", "url": BASE + "guides/",
               "hasPart": [{"@type": "Article", "headline": g["title"], "url": BASE + f"guides/{g['slug']}/"} for g in GUIDES]}]
    return "guides/", page(title="FC 27 Trading Guides · Ezzcoins", path="guides/", up=up, body=body, schema=schema,
                           desc="Free FC 27 Ultimate Team trading guides: SBC fodder value, the Rivals rewards dip, midweek buying, promo nights, small-budget bidding and market hype.",
                           crumbs=[("Ezzcoins", ""), ("Guides", None)])


def main():
    written = 0
    for g in GUIDES:
        path, text = guide_html(g)
        written += write(ROOT, path, text)
    path, text = hub_html()
    written += write(ROOT, path, text)
    print(f"Guides: {len(GUIDES)} pages and the hub, {written} written")


if __name__ == "__main__":
    main()
