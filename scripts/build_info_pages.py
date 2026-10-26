#!/usr/bin/env python3
"""Ezzcoins' About and Contact pages (about/index.html, contact/index.html).

The text lives here. Run after editing:  python3 scripts/build_info_pages.py [site root]
scripts/build_pages.py lists both pages in sitemap.xml. Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_page import BASE, e, page, write  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
UPDATED = "26 October 2026"
ORG = {"@type": "Organization", "name": "Ezzcoins", "url": BASE, "logo": {"@type": "ImageObject", "url": BASE + "icon-512.png"}}


def about():
    up = "../"
    li = lambda items: "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    body = (
        '<article class="guide info-page"><p class="kicker">About</p><h1>About Ezzcoins</h1>'
        '<p class="lead">Ezzcoins is a free, independent trading desk for EA SPORTS FC 27 Ultimate Team. It watches the Transfer Market '
        'around the clock, explains what the numbers mean, and grades its own trade calls in public, losses included.</p>'
        '<h2>What you will find here</h2>'
        + li([
            "Live console and PC prices for about 20,000 tradeable cards, checked every few minutes, and price graphs for about 3,000 popular cards.",
            f'A <a href="{up}#players">player database</a> with every FC 27 player, filters, and Ezzcoins\' own '
            f'<a href="{up}guides/meta-rating/">meta rating</a> for each position a card can play.',
            f'<a href="{up}tools.html">SBC and Evolution builders</a>, a fodder board, a flip calculator that counts the 5% tax, and a log for your own trades.',
            "A market read on the home page: the weekly cycle, the 6 PM content drop, Rivals rewards, and the day's biggest risers and fallers.",
            f'<a href="{up}guides/">Trading guides</a> and a <a href="{up}recap/">weekly market recap</a>, written from Ezzcoins\' own price records.',
            f'An automatic trade desk whose every call is <a href="{up}guides/how-calls-are-graded/">graded in public</a>.',
        ])
        + '<h2>Where the numbers come from</h2>'
        '<p>Prices are Buy Now quotes read from FUT.GG, and from FUTBIN when it can be reached. Every price on the site says which source it '
        'came from and when it was read, and the site checks for new prices every minute. Player ratings and stats are EA SPORTS FC 27\'s own.</p>'
        '<p>Ezzcoins also keeps an hourly snapshot of the whole market. That record is what the trading guides, the weekly recap and the '
        'trade desk\'s tests are built on: when a guide says that 77% of cards that jumped 15% in a day were cheaper two days later, it is '
        f'counting Ezzcoins\' own snapshots (see <a href="{up}guides/dips-and-spikes/">Dips and spikes</a>).</p>'
        '<h2>How the trade desk works</h2>'
        '<p>The desk makes at most two calls a day, each following one of a few written strategies, such as buying fodder after the Thursday '
        'Rivals rewards or selling a card after a sharp one-day jump. Every call records the price and a check time when it is made. At the '
        'check time it is graded automatically, with EA\'s 5% tax counted on every buy. A strategy that starts losing is paused, and every '
        '10 minutes the desk replays its strategies on recent prices and switches off any whose paper calls lose, before they cost anyone '
        f'coins. The full rules and the record are in <a href="{up}guides/how-calls-are-graded/">How calls are graded</a>.</p>'
        '<p>Calls are information, not advice. Prices move fast; check the in-game market before you buy, and only trade coins you can afford to lose.</p>'
        '<h2>What Ezzcoins will never do</h2>'
        + li(["Sell coins, accounts or boosting, or link to anyone who does.",
              "Ask for your EA account details. Signing in to Ezzcoins (only needed for a watchlist) uses Google and never touches your EA account.",
              "Use bots on EA's Transfer Market, or recommend tools that do. Both break EA's rules.",
              "Let advertisers or anyone else pay for a card or a call to be featured."])
        + '<h2>Ads and independence</h2>'
        '<p>Ezzcoins is free and is paid for by advertising. Advertisers have no say over what the site says, and the trade desk\'s calls '
        'are made by fixed rules from price data alone. Ezzcoins is an independent fan project. It is not endorsed by or affiliated with EA '
        'or its licensors, and it is not affiliated with FUTBIN, FUT.GG, FUTWIZ or EasySBC.</p>'
        '<h2>Corrections and contact</h2>'
        '<p>Spotted a wrong price or card detail? Every player page has a link to report it, which sends the card\'s details with your note. '
        f'For anything else, including questions and ideas, use the <a href="{up}contact/">contact page</a>. How the site handles your data '
        f'is explained in <a href="{up}privacy.html">Privacy and cookies</a>.</p>'
        f'<p class="muted">Last updated {e(UPDATED)}.</p></article>'
    )
    schema = [{"@context": "https://schema.org", "@type": "AboutPage", "name": "About Ezzcoins", "url": BASE + "about/", "publisher": ORG}]
    return "about/", page(title="About Ezzcoins: the FC 27 Trading Desk and How It Works", path="about/", up=up, body=body, schema=schema,
                          desc="What Ezzcoins is, where its FC 27 prices come from, how the trade desk makes and grades its calls, and what the site will never do.",
                          crumbs=[("Ezzcoins", ""), ("About", None)])


def contact():
    up = "../"
    topics = "".join(f'<option>{t}</option>' for t in ("Question", "Correction", "Idea", "Business", "Other"))
    body = (
        '<article class="guide info-page"><p class="kicker">Contact</p><h1>Contact Ezzcoins</h1>'
        '<p class="lead">Questions, corrections, ideas or business enquiries: send a message here and it comes straight to the person who runs Ezzcoins.</p>'
        '<form class="contact-form" id="contact-form" novalidate>'
        f'<label>Topic<select name="topic">{topics}</select></label>'
        '<label>Your message<textarea name="message" rows="6" maxlength="400" required></textarea><small data-count></small></label>'
        '<label>Your email, if you would like a reply <small>(optional)</small><input type="email" name="email" autocomplete="email" maxlength="80"></label>'
        '<button type="submit">Send message</button><p class="msg" aria-live="polite"></p></form>'
        '<h2>Wrong price on a player page?</h2>'
        '<p>Use the report link on that player\'s page instead: it sends the card number and the price you saw along with your note, which makes it much quicker to fix.</p>'
        '<h2>What happens to your message</h2>'
        '<p>Your message, and your email address if you give one, are stored in Ezzcoins\' database and used only to read and answer it. '
        f'Nothing is shared or used for marketing. See <a href="{up}privacy.html">Privacy and cookies</a> for details.</p>'
        '<p class="muted">Ezzcoins never asks for your EA account details and never sells coins. Anyone claiming otherwise in Ezzcoins\' name is not us.</p></article>'
    )
    schema = [{"@context": "https://schema.org", "@type": "ContactPage", "name": "Contact Ezzcoins", "url": BASE + "contact/", "publisher": ORG}]
    return "contact/", page(title="Contact Ezzcoins", path="contact/", up=up, body=body, schema=schema, ads=False,
                            scripts=("contact.js?v=20261026",),
                            desc="Send Ezzcoins a question, correction, idea or business enquiry.",
                            crumbs=[("Ezzcoins", ""), ("Contact", None)])


def main():
    n = 0
    for build in (about, contact):
        path, text = build()
        n += write(ROOT, path, text)
    print(f"About and Contact pages: {n} written")


if __name__ == "__main__":
    main()
