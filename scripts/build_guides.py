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
UPDATED = "2026-10-28"   # bump when a guide's text changes
FIRST = "2026-10-13"     # first six guides published; later ones carry their own "published" date

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
            ("Evenings: buy after 6 PM, not before", [
                "EA's daily content drop at 6 PM UK moves fodder too. Across the 23 evenings Ezzcoins measured in October 2026, the cheapest 85 was 3.8% cheaper at about 8 PM than just before 6 PM on average, and the cheapest 86 3.2% cheaper. 84s barely moved (+0.8%), because they sit at a hard floor. If you need 85s or 86s in the evening and can wait two hours, waiting has usually been cheaper.",
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
            ("What the last three Thursdays looked like", [
                {"table": {"head": ["Thursday", "Before the payout", "Lowest that morning", "Saturday noon"],
                           "rows": [["8 Oct", "5,600", "4,500", "4,200"], ["15 Oct", "4,700", "3,500", "4,000"], ["22 Oct", "4,800", "3,800", "5,400"]],
                           "note": "Cheapest 86-rated card on console, from Ezzcoins' hourly price snapshots (UK time). \"Lowest that morning\" is the lowest hourly reading between 8 AM and 2 PM."}},
                "The dip came every week, but it wasn't the same size and didn't bottom out at the same time: at 9 AM on 15 October, at around midday on 22 October. Buying at the morning low and selling on Saturday would have made money after tax in two of the three weeks (about +9% and +35%) and lost in one (8 October), when Saturday's price was below the Thursday low.",
                "Ezzcoins' own call on 22 October bought the cheapest 86 at 4,600 coins at 8 AM UK, before the bottom, and was graded on Saturday at 5,800: +19.8% after tax. Buying a couple of hours later would have been better still, which is why patience on Thursday morning pays.",
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
            ("What October 2026 showed", [
                "Ezzcoins replayed this setup on its own hourly prices: the ten meta cards worth 8,000 to 150,000 coins that the desk's rule ranks best, bought at 8 PM UK on Tuesday, Wednesday and Thursday and sold on Friday at 8 PM UK, with the 5% tax counted.",
                {"table": {"head": ["Week", "Buys", "Made money", "Average after tax"],
                           "rows": [["5 to 9 Oct", "30", "4", "−19.7%"], ["12 to 16 Oct", "30", "7", "−14.5%"], ["19 to 23 Oct", "30", "15", "+3.4%"]],
                           "note": "Each row: 10 cards on each of three evenings, sold on that week's Friday at 8 PM UK."}},
                "In the first two weeks after launch, new packs pushed prices down all week, and buying midweek lost heavily. By the third week supply had settled and the weekend lift was back. The lesson: the weekly rhythm is real, but early in a game cycle or in a heavy promo week it is swamped by falling prices. Buy midweek for your own squad; as a trade, wait until prices stop falling week on week.",
                "That record is also why the desk's \"Buy before the weekend\" strategy is switched off at the moment: it is re-tested every 10 minutes on recent prices and comes back on by itself when it starts winning.",
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
            ("How new cards were priced in October 2026", [
                "Ezzcoins followed 129 new promo cards worth 10,000 coins or more (Team of the Week, Future Stars, Ultimate Scream, Star Performer and others) that arrived on the market between 6 and 26 October 2026, from each card's first hourly price reading:",
                {"table": {"head": ["Time after first price", "Typical change", "Cheaper than first price"],
                           "rows": [["1 hour", "−9%", "76%"], ["3 hours", "−18%", "83%"], ["6 hours", "−24%", "93%"], ["24 hours", "−34%", "97%"], ["3 days", "−44%", "97%"]],
                           "note": "Median change of each card's console price, compared with its first reading after release."}},
                "A third of the price was gone within a day, and almost every card was cheaper after 24 hours. Team of the Week cards levelled off after their first evening, while other promo cards kept falling for several days (see the Team of the Week guide). If you want a new promo card, waiting at least a day has been worth about a third of its price. If you pack one you don't need, the first hours are the best time to sell it.",
                "The most common arrival times were 6 PM UK on Wednesdays and Fridays, when new promos and Team of the Week usually land.",
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
            ("Break-even prices at a glance", [
                {"table": {"head": ["You paid", "Sell for at least", "Rise needed", "Sell for +10% profit"],
                           "rows": [["1,000", "1,100", "10.0%", "1,200"], ["2,500", "2,700", "8.0%", "2,900"], ["5,000", "5,300", "6.0%", "5,800"],
                                    ["10,000", "10,750", "7.5%", "11,750"], ["25,000", "26,500", "6.0%", "29,000"], ["50,000", "53,000", "6.0%", "58,000"],
                                    ["100,000", "106,000", "6.0%", "116,000"], ["250,000", "264,000", "5.6%", "290,000"], ["1,000,000", "1,053,000", "5.3%", "1,158,000"]],
                           "note": "The lowest market price that gives back at least what you paid after the 5% tax, rounded up to the market's price steps."}},
                "Notice the cheap end: because of the price steps, a 1,000-coin card has to rise 10% just to break even, and a card just above 10,000 needs 7.5%. That is why flipping cheap cards so rarely works. For context, a typical card worth 10,000+ coins moved less than 1% over two days in October 2026, and buying one and reselling it two days later lost 3.8% after tax on average.",
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
            ("What the data says", [
                "Ezzcoins checked this on three weeks of its own hourly prices (5 to 26 October 2026): 77% of cards worth 10,000+ coins that rose 15% or more in a day were cheaper two days later, and the typical one gave back about half of its jump. Buying a spiking card and reselling it two days later lost 13.5% after tax on average. The full study is in the Dips and spikes guide.",
            ]),
        ],
        "live": ("hype", "Biggest rises in the last day"),
        "related": ["promo-night", "small-budget-bidding"],
    },
    {
        "slug": "dips-and-spikes",
        "published": "2026-10-26",
        "num": "07",
        "short": "Dips and spikes",
        "title": "Buy the Dip or Sell the Spike? What Three Weeks of FC 27 Prices Show",
        "h1": "Dips and spikes: the data",
        "desc": "Ezzcoins followed every FC 27 card worth 10,000+ coins hour by hour from 5 to 26 October 2026: what happened two days after a 10% fall or a 15% jump, and what it means for buying dips and selling spikes.",
        "lead": "Two of the oldest pieces of trading advice pull in opposite directions: buy cards that just fell, and sell cards that just jumped. Ezzcoins records the price of every tradeable card every hour, so instead of guessing, we checked what actually happened next.",
        "steps": [("Sell", "Into a sharp one-day jump: most gave half of it back."),
                  ("Skip", "Big dips on meta cards: they mostly kept falling."),
                  ("Remember", "A small bounce rarely beats the 5% tax.")],
        "sections": [
            ("How we measured it", [
                "From 5 to 26 October 2026 Ezzcoins saved a console price snapshot of the whole Transfer Market every hour: 479 snapshots, each with about 2,000 cards that cost 1,000 coins or more. This study uses the cards worth at least 10,000 coins.",
                "A dip is a card whose price fell 10% or more compared with about a day earlier; a spike is one that rose 15% or more. To keep out wrong readings, the move also had to show in the reading an hour earlier, and the \"day earlier\" price is the middle of several readings around that time. Each card counted at most once every two days. That left 1,969 dips and 1,445 spikes.",
                "We then looked at the same card's price 48 hours later and counted the 5% tax for anyone who bought and sold again.",
            ]),
            ("After a spike, the price usually came back", [
                "77% of spiking cards were cheaper two days later, and the typical one gave back about half of its jump. Selling at the spike instead of holding saved 8.9% on average. Buying the spike and selling two days later lost 13.5% after tax, and only 12% of those trades made money.",
                {"table": {"head": ["Size of the jump", "Cases", "Cheaper 48 h later", "Average saved by selling"],
                           "rows": [["15 to 25%", "1,061", "73%", "+4.2%"], ["25 to 40%", "199", "88%", "+14.0%"], ["40% or more", "185", "88%", "+30.6%"]],
                           "note": "Cards worth 10,000+ coins, console, 5 to 26 October 2026."}},
                "The bigger the jump, the more reliably it faded. Five days later, 73% of spiking cards were still below their spike price.",
            ]),
            ("After a dip, a bounce, but rarely enough", [
                "Dips are less clear-cut. 65% of cards that fell 10% or more were a little higher two days later, so the old advice is half right: prices often bounce. But the bounce was usually smaller than the tax. Buying the dip and selling 48 hours later made money only 41% of the time, for an average of −1.3%.",
                {"table": {"head": ["Size of the fall", "Cases", "Higher 48 h later", "Average after tax if bought"],
                           "rows": [["10 to 15%", "1,376", "65%", "−0.6%"], ["15 to 25%", "301", "58%", "+1.1%"], ["25% or more", "292", "43%", "−7.0%"]],
                           "note": "Same cards and period. The 15 to 25% row averages slightly positive, but its typical (median) trade still lost 2.9%."}},
                "The deepest falls were the worst buys: after a fall of 25% or more, fewer than half of the cards recovered at all within two days.",
            ]),
            ("Falling meta cards were the worst buys", [
                "The dips that look most tempting, popular meta cards falling sharply, were the most expensive mistakes. Buying those dips lost 6.5% on average and only 35% made money, against roughly break-even for other cards.",
                "A likely reason is that a meta card often falls because a better version of the same player, or a cheaper card that plays as well, has just arrived in packs. That isn't a blip; it is the market re-pricing the card.",
            ]),
            ("The tax is the real hurdle", [
                "For comparison, a random card worth 10,000+ coins moved only +0.7% (median) over the same two-day windows, and buying any card and reselling it two days later lost 3.8% after tax on average. Most short flips fail not because the prediction is wrong, but because the move is smaller than the tax.",
            ]),
            ("What this means for you", [
                {"list": ["If you own a card that has just jumped 25% or more and you don't need it, selling into the jump was the better move nearly 9 times in 10.",
                          "Don't buy a card because it is trending: buying a spike lost money nearly 9 times in 10.",
                          "Treat a dip as a reason to look, not a reason to buy. If you need the card for your squad, a dip is a fine time to get it; as a trade it rarely beats the tax.",
                          "Be most careful with falling meta cards."]},
            ]),
            ("How the Ezzcoins desk uses this", [
                "These results are why the desk's \"Sell the spike\" strategy stays in use while \"Buy the dip\" is switched off. The desk replays its strategies on the latest recorded prices every 10 minutes and turns one off as soon as its paper calls stop working, so this page describes October 2026, and the live scoreboard shows what is working now.",
            ]),
            ("Limits of this study", [
                "Three weeks at the start of FC 27 is a short window, during the busiest launch period and several promos. Prices are console quotes of the lowest Buy Now listing read once an hour, so very short moves are missed, and PC prices can behave differently. Past moves don't guarantee future ones.",
            ]),
        ],
        "live": ("hype", "Biggest rises in the last day"),
        "related": ["skip-the-hype", "price-glitches"],
    },
    {
        "slug": "price-glitches",
        "published": "2026-10-26",
        "num": "08",
        "short": "Price glitches",
        "title": "FC 27 Price Glitches: Why One Price Reading Can Fool You",
        "h1": "Price glitches",
        "desc": "One wrong FC 27 price can make a card look like a steal or a rocket. How often single-reading glitches happened in October 2026, what causes them, and the two-reading rule that protects you.",
        "lead": "Every price you see on a FUT site is a reading of the lowest listing at one moment. Almost all readings are right. A few are wildly wrong for one update, and those are exactly the ones that make a card look like a steal or a rocket.",
        "steps": [("Wait", "For a second price update before acting."),
                  ("Compare", "With the card's range over the last day."),
                  ("Ignore", "Prices at the market's maximum.")],
        "sections": [
            ("How often it happens", [
                "Ezzcoins checked about 928,500 hourly price readings from 5 to 26 October 2026. 497 of them were one-off outliers: more than 2.5 times higher or lower than the readings an hour before and an hour after, which agreed with each other. That is about 5 in every 10,000 readings, or roughly two dozen a day across the market. 272 were too high and 225 too low.",
            ]),
            ("What glitches look like", [
                {"list": ["A card trading at about 1.45 million coins showed 15,000,000, the market's maximum, for one hour, then 1.44 million again.",
                          "A card worth about 197,000 coins showed 39,000 for one reading and was back at 199,000 an hour later.",
                          "Ezzcoins' own Trending row once listed Ruud Gullit at 15,000,000 coins (+92%) and Aitana Bonmatí at +847%. Aitana's price hadn't moved: one reading a day earlier said 27,000 instead of about 255,000, so the comparison was wrong.",
                          "Low-rated cards worth about 1,000 coins showed exactly 10,000 for a single update.",
                          "An hour after Rivals rewards paid out, the cheapest 86 showed 750 coins. Within the hour it was back at 4,200."]},
            ]),
            ("Why they happen", [
                "A price reading is the cheapest Buy Now listing at that moment. If one player lists a card far too cheaply by mistake, that listing is the price until someone buys it, usually within seconds. If a card has almost no listings, the cheapest one can be far above its real value, and a card with none at all can show the maximum price. Price sites also read the market at slightly different times, so one site can catch a listing another never saw.",
            ]),
            ("The two-reading rule", [
                "Before you act on a price that surprises you, wait for the next update. If two readings in a row agree, the price is probably real.",
                "Ezzcoins uses the same rule everywhere. A trade call is only made when the current price agrees with the reading about an hour earlier. A move over a day is measured from the middle of several readings around a day ago, so one wrong old reading can't create a move, and a card only appears in Trending if its rise already showed in the reading an hour before. Those last two checks were added after the Gullit and Bonmatí cases above.",
            ]),
            ("Other quick checks", [
                {"list": ["Look at the price graph, not just the number: a glitch is a single spike or hole.",
                          "Compare with the card's price a day ago and with similar cards.",
                          "Distrust round numbers at the extremes, such as 10,000 on a low-rated card or 15,000,000 on anything.",
                          "In the game, check how many listings there are: one cheap listing isn't a price."]},
            ]),
            ("Can you buy a glitch?", [
                "Sometimes a too-cheap listing is real and someone buys it. That is sniping, and it is fine when you do it by hand. But by the time a price site shows the listing it is almost always gone, so never plan a trade around a price you have only seen once.",
            ]),
        ],
        "live": None,
        "related": ["dips-and-spikes", "rivals-rewards-dip"],
    },
    {
        "slug": "meta-rating",
        "published": "2026-10-26",
        "num": "09",
        "short": "The meta rating",
        "title": "How the Ezzcoins Meta Rating Works in FC 27",
        "h1": "The meta rating",
        "desc": "How Ezzcoins estimates how well an FC 27 card plays: position weights for the six face stats, skill moves, weak foot, low pace and PlayStyles+, with a worked example and its limits.",
        "lead": "An 87 isn't always better than an 85. A fast 85 winger with 5-star skills can play far above a slow 87. The Ezzcoins meta rating is a simple, open estimate of how well a card plays in the position you use it, worked out from the card itself.",
        "steps": [("Read", "The meta rating next to the overall."),
                  ("Compare", "Cards for the same position."),
                  ("Remember", "It can't see height or how a card feels.")],
        "sections": [
            ("Position by position", [
                "For every position a card can play, the six face stats are weighted by what matters there: a striker's score leans on pace and shooting, a centre-back's on defending, pace and physical. Each position is calibrated so that an average card rated 75 or more scores its own overall rating at its own position. The card's meta rating is its score at its best position.",
                {"table": {"head": ["Position", "Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"],
                           "rows": [["ST", "30", "30", "5", "22", "0", "13"], ["LW, RW", "33", "20", "12", "30", "0", "5"], ["CAM", "22", "20", "25", "30", "0", "3"],
                                    ["CM", "18", "10", "28", "22", "10", "12"], ["CDM", "18", "0", "20", "10", "30", "22"], ["CB", "30", "0", "7", "3", "40", "20"],
                                    ["LB, RB", "33", "0", "15", "14", "26", "12"]],
                           "note": "Share of the score, in %, that comes from each face stat. Goalkeepers use their six goalkeeping stats instead."}},
            ]),
            ("Skill moves, weak foot and pace", [
                "Each star of skill moves or weak foot above 3 adds a point for attackers, and each star below 3 takes one away. In midfield and defence they count for less, and skill moves don't count for centre-backs at all.",
                "In positions where pace matters most, a card loses 0.15 points for every point of pace below 70, because slow players struggle there whatever their other stats.",
            ]),
            ("PlayStyles+", [
                "Each PlayStyle+ adds to the score: 2 points for the ones that change matches most (for example Quick Step+, Rapid+, Finesse Shot+, Technical+, Power Shot+, Trickster+, Intercept+, Anticipate+, Jockey+, Bruiser+ and the main goalkeeping ones), half a point for set-piece ones such as Dead Ball+ and Long Throw+, and 1 point for the rest.",
            ]),
            ("A worked example", [
                "Lionel Messi's 89-rated CAM card has 76 pace, 87 shooting, 89 passing, 90 dribbling, 33 defending and 63 physical, 4-star skill moves and weak foot, and Incisive Pass+. He scores 89 at CAM, 86 at RM and ST, and 85 at RW: the card is at its best where EA put it, and his modest pace counts against him most on the wing, where pace carries a third of the score.",
            ]),
            ("What it can't see", [
                "The meta rating only knows what is on the card. It doesn't know height and body type, acceleration types or how a card feels in your hands, and it doesn't know your formation or tactics. Two cards a point apart are effectively the same. Use it to shortlist, then trust your own games.",
            ]),
            ("Using it to find value", [
                "The most useful comparison is meta rating against price within one position: a card that scores within a point or two of your target often plays almost as well for a fraction of the coins. In the Ezzcoins player database you can sort by meta rating or by price, and every player page shows the score at each position the card can play.",
            ]),
        ],
        "live": None,
        "related": ["midweek-specials", "small-budget-bidding"],
    },
    {
        "slug": "how-calls-are-graded",
        "published": "2026-10-26",
        "num": "10",
        "short": "How calls are graded",
        "title": "How Ezzcoins Grades Its FC 27 Trade Calls, Misses Included",
        "h1": "How calls are graded",
        "desc": "Every Ezzcoins trade call has a fixed entry price, check time and grading rule, with the 5% tax counted. How the desk grades, pauses and paper-tests its strategies, and how to judge anyone's trading tips.",
        "lead": "Plenty of people post FC 27 trading tips. Very few tell you afterwards how those tips worked out. Every call Ezzcoins makes is written down before the result is known and graded automatically, including the ones that lose.",
        "steps": [("Fixed", "Entry price, check time and rule, set when the call is made."),
                  ("Counted", "The 5% tax on every buy call."),
                  ("Public", "Every hit and every miss.")],
        "sections": [
            ("What a call contains", [
                "Each call names one card, or the cheapest card at a rating, says whether to buy or sell, and records the price at that moment and a check time: usually two days later, or a fixed time such as Friday at 8 PM UK. Prices come from the Ezzcoins console price feed, and a call is only made when two readings about an hour apart agree on the price.",
            ]),
            ("How it is graded", [
                "At the check time the desk reads the price again. A buy call is a hit only if selling at that price, after EA's 5% tax, gives back more than the entry price. A sell call is a hit if the price is lower than when the call was made. Each result is stored once, as a percentage, and the totals are rebuilt from those stored results on every update, so a call can't be graded twice or quietly dropped.",
            ]),
            ("Strategies, not hunches", [
                "Every call follows one of a few written strategies: the Rivals rewards dip, buying before the 6 PM drop, buying before the weekend, buying the dip, selling the spike and selling the slide. Each has its own public record. A strategy is judged on its last 12 graded calls: under 50% hits or a negative average after tax pauses it for a week, after which it gets one low-confidence retest.",
            ]),
            ("Paper tests", [
                "Waiting for real calls to fail is slow and public. So every 10 minutes the desk also replays its price-move strategies and its weekend strategy on the prices it recorded recently, grading those paper calls exactly like real ones. A strategy whose paper calls hit half the time or less, or lose after tax, is switched off before it can make another call, and a new strategy must pass the paper test before it is used at all.",
            ]),
            ("The record so far", [
                "By 26 October 2026 the desk had graded 20 calls: 7 hits and 13 misses. That isn't a flattering number, and it is the reason the paper tests exist: 7 of the 13 misses came from buying dips and buying before the weekend in the falling launch market, the two strategies the paper tests then switched off.",
                "The best call so far was a sell call: Alphadjo Cissè's Star Performer card at 101,000 coins, which was down to 65,500 two days later (35.1% lower). The best buy call bought 86-rated fodder after the Rivals rewards on 22 October at 4,600 coins and was graded on Saturday at 5,800: +19.8% after tax. The worst bought a meta card for the weekend at 9,400 coins; by Friday it was worth 6,400.",
            ]),
            ("How to judge anyone's tips", [
                {"list": ["Was the call written down before the result, with a price and a time?",
                          "Is the 5% tax counted?",
                          "Are the misses shown, not just the wins?",
                          "Is there a rule for when a strategy is dropped?"]},
                "If the answer to any of these is no, you are looking at a highlight reel, not a track record.",
            ]),
        ],
        "live": ("board", "Every strategy's record right now"),
        "related": ["dips-and-spikes", "rivals-rewards-dip"],
    },
    {
        "slug": "first-100k",
        "published": "2026-10-26",
        "num": "11",
        "short": "Your first 100K",
        "title": "FC 27 Trading for Beginners: A Step-by-Step Plan to Your First 100K Coins",
        "h1": "Your first 100K",
        "desc": "A practical FC 27 trading plan built on what Ezzcoins' price data showed in October 2026: count the tax, skip first-hour promo prices, sell spikes, use the Thursday rewards dip and trade by hand.",
        "lead": "There is no secret method that turns 10,000 coins into a million overnight. There are a handful of habits that stop you losing coins, and a few moments in the FC 27 week when the market repeatedly gives you an edge. This plan puts them in order.",
        "steps": [("Protect", "Your coins from the tax and from hype."),
                  ("Use", "The moments the market repeats each week."),
                  ("Keep", "A record of every trade.")],
        "sections": [
            ("Step 1: count the tax on every trade", [
                "EA keeps 5% of every sale, so a card must rise more than 5% before you make a single coin, and cheap cards need more because of the market's price steps. In October 2026 a typical card worth 10,000+ coins moved less than 1% over two days, which is why most quick flips lose. Before every buy, write down the price you must sell at for a profit worth your time. The break-even table in the small-budget guide does the maths.",
            ]),
            ("Step 2: never pay first-hour promo prices", [
                "New promo cards start expensive and fall fast. Of the 129 new promo cards worth 10,000+ coins that Ezzcoins followed in October, the typical one was 18% cheaper three hours after its first price and 34% cheaper a day later, and 97% were cheaper after 24 hours. If you want a new card, wait at least a day. If you pack one you don't need, the first hours are the best time to sell it.",
            ]),
            ("Step 3: sell into spikes, don't buy them", [
                "When a card you own jumps 25% or more in a day and you don't need it, selling paid off nearly 9 times in 10 in Ezzcoins' data. Buying a card because it is trending lost money nearly 9 times in 10.",
            ]),
            ("Step 4: buy fodder in the Thursday rewards dip", [
                "When Rivals rewards pay out on Thursday morning (UK time), packs flood the market and fodder dips for a few hours. On 22 October the cheapest 86 went from 4,800 before the payout to about 3,800 at midday, and was 5,400 by Saturday. Buy the fodder your SBCs need then, not on Friday night. The dip isn't the same every week, so buy what you would use anyway.",
            ]),
            ("Step 5: buy squad cards early in the week", [
                "If you want a card for Champions weekend, early in the week is usually cheaper than Friday evening. As a trade it is less reliable: in the first two weeks of October, meta cards bought midweek were worth less by Friday as new packs flooded the market; in the third week they were worth more. Buy for your squad, not to flip.",
            ]),
            ("Step 6: spread your coins and trade by hand", [
                "Spread a small budget over several cards so one bad buy can't wipe you out. Bid below the lowest Buy Now and set your maximum before the auction starts. Don't buy coins and don't use automated trading tools: both break EA's rules and can get your account banned.",
            ]),
            ("Step 7: keep a log", [
                "Write down every trade: the card, what you paid, what you sold for and why you bought it. After 20 trades you will know which of your habits make coins and which lose them. The My Trades tool on Ezzcoins does this for you and counts the tax.",
            ]),
        ],
        "live": ("calc", "Profit after tax"),
        "related": ["small-budget-bidding", "promo-night"],
    },
    {
        "slug": "fodder-by-day",
        "num": "12",
        "published": "2026-10-26",
        "short": "Fodder by day",
        "title": "When to Buy SBC Fodder in FC 27: Prices by Day of the Week",
        "h1": "Fodder by day",
        "desc": "Which day of the week FC 27 SBC fodder (85 to 88 rated) was cheapest and most expensive in October 2026, from Ezzcoins' hourly price records, and how much the day mattered compared with the hour.",
        "lead": "If you do a lot of SBCs, the day you buy your fodder matters more than most players think. Ezzcoins tracked the cheapest card at every rating every hour for three weeks. One day stood out as cheap, and one as expensive.",
        "steps": [("Buy", "On Thursday, after Rivals rewards."),
                  ("Avoid", "Wednesday, the most expensive day."),
                  ("Plan", "Stock up for the week, not the evening.")],
        "sections": [
            ("How we measured it", [
                "From 5 to 26 October 2026, Ezzcoins read the console price of the cheapest 85, 86, 87 and 88-rated card every hour. Fodder prices also drift up and down from week to week, so each reading is compared with the middle price over the surrounding seven days. That shows which days were cheap or expensive within their own week.",
            ]),
            ("The days compared", [
                {"table": {"head": ["Day", "85", "86", "87", "88"],
                           "rows": [["Monday", "0%", "+2.2%", "+0.8%", "+2.3%"], ["Tuesday", "+2.2%", "+6.7%", "+1.6%", "+4.7%"],
                                    ["Wednesday", "+13.6%", "+7.5%", "+7.8%", "+2.1%"], ["Thursday", "−8.3%", "−6.0%", "−5.0%", "−7.0%"],
                                    ["Friday", "0%", "−1.0%", "0%", "+2.3%"], ["Saturday", "0%", "−4.1%", "−1.5%", "−1.1%"], ["Sunday", "0%", "0%", "0%", "0%"]],
                           "note": "Median price of the cheapest card at each rating on that day, compared with the median over the surrounding week. Console, 5 to 26 October 2026."}},
                "Thursday was the cheapest day for every rating, 5 to 8% below the week's typical price: Rivals rewards pay out that morning and players list the fodder from their reward packs. Wednesday was the most expensive day for 85s to 87s, up to 14% above the week. Tuesday was also on the high side.",
            ]),
            ("Day matters more than hour", [
                "Within a day, the hour made less difference. Most hours were within a few percent of the day's typical price, with no time that was reliably cheap. The one evening effect worth knowing is EA's 6 PM UK content drop: across 23 evenings, the cheapest 85 was 3.8% cheaper and the cheapest 86 3.2% cheaper two hours later than just before 6 PM.",
            ]),
            ("Fodder can get dearer from week to week", [
                {"table": {"head": ["Week starting", "Cheapest 86", "Cheapest 87", "Cheapest 88"],
                           "rows": [["5 Oct", "4,500", "6,500", "10,800"], ["12 Oct", "4,100", "5,950", "10,600"], ["19 Oct", "5,000", "6,900", "12,000"]],
                           "note": "Median of each week's hourly readings, in coins, console."}},
                "Fodder got cheaper in the second week and then 15 to 20% dearer in the third, most likely because new SBCs needed high-rated cards. A big SBC can move fodder prices far more than the day of the week, so check the live board before a large purchase.",
            ]),
            ("What to do", [
                {"list": ["Buy the fodder you will need for the coming week on Thursday, once the rewards dip has come through.",
                          "Avoid buying large amounts on Tuesday and Wednesday unless an SBC you want is about to end.",
                          "In the evening, wait until after the 6 PM drop if you can.",
                          "Only stock up on fodder you are fairly sure to use: reselling costs 5% and the dip isn't guaranteed every week."]},
                "This is three weeks of data at the start of FC 27, so each weekday appears only three times. Treat it as a pattern worth knowing, not a law; Ezzcoins will update it as the season goes on.",
            ]),
        ],
        "live": ("fodder", "Cheapest fodder right now"),
        "related": ["rivals-rewards-dip", "fodder-value"],
    },
    {
        "slug": "launch-market",
        "num": "13",
        "published": "2026-10-26",
        "short": "The launch market",
        "title": "The FC 27 Launch Market: What Rose and What Fell in the First Three Weeks",
        "h1": "The launch market",
        "desc": "How FC 27 card prices moved from early to late October 2026, from Ezzcoins' hourly records: Icons and Heroes up about 21%, the most expensive cards up most, cheap gold cards flat, and fodder swinging week to week.",
        "lead": "The first weeks of a new FC are when the market changes fastest. Ezzcoins compared the price of every card on the market in early October with its price three weeks later. The winners and losers weren't the ones most players expect.",
        "steps": [("Rose", "Icons, Heroes and the most expensive cards."),
                  ("Flat", "Ordinary gold cards up to 82."),
                  ("Fell", "New promo cards, right after release.")],
        "sections": [
            ("How we measured it", [
                "For every card worth 1,000 coins or more, Ezzcoins took the middle of its hourly console prices on 6 and 7 October and on 24 and 25 October 2026, and compared the two. Only cards that were on the market at both times count, so this shows how existing cards held their value, not how new promo cards priced in.",
            ]),
            ("What happened, by type of card", [
                {"table": {"head": ["Cards", "Number", "Typical change", "Share that rose"],
                           "rows": [["Gold 75 to 82", "419", "0%", "45%"], ["Gold 83 to 84", "82", "+8.3%", "66%"], ["Gold 85 to 86", "88", "+3.4%", "60%"],
                                    ["Gold 87 to 88", "46", "+12.6%", "72%"], ["Gold 89 and up", "27", "−2.4%", "30%"],
                                    ["Promo cards already out on 6 Oct", "118", "+9.8%", "76%"], ["Icons", "131", "+20.8%", "98%"], ["Heroes", "89", "+22.0%", "96%"]],
                           "note": "Median change from 6 and 7 October to 24 and 25 October 2026, console. \"Gold\" means base rare cards."}},
                "Icons and Heroes were the clearest story: almost every one rose, by about a fifth. Promo cards that were already out at the start of October also gained. Ordinary gold cards rated up to 82 went nowhere on balance, and the very top base golds, 89 and up, slipped.",
            ]),
            ("The more expensive the card, the more it rose", [
                {"table": {"head": ["Price on 6 to 7 Oct", "Number", "Typical change", "Share that fell"],
                           "rows": [["1,000 to 10,000", "920", "+6.7%", "35%"], ["10,000 to 50,000", "192", "+7.0%", "29%"], ["50,000 to 250,000", "176", "+9.5%", "36%"],
                                    ["250,000 to 1 million", "270", "+23.5%", "13%"], ["1 million and up", "123", "+16.2%", "9%"]],
                           "note": "Same cards and dates, grouped by their starting price."}},
                "Cards above 250,000 coins rose the most and fell the least. A likely reason is that coins keep entering the game as players earn rewards and sell their packs, while the supply of the rarest cards grows slowly, so more coins chase the same few cards.",
            ]),
            ("Icons and Heroes week by week", [
                "The rise wasn't a single jump. The typical Icon was about 1% above its early-October price on 8 October, 5% on the 10th, 12% on the 16th, 15% from the 18th to the 22nd and 21% by the 24th. Heroes followed almost the same path.",
                "Not every one rose: John Arne Riise's Hero card fell 15% and Zico's Icon about 9%. The biggest risers were Aya Miyama (from about 540,000 to 940,000 coins), Marinette Pichon (+55%) and Jay-Jay Okocha (+48%).",
            ]),
            ("Fodder swung, new cards fell", [
                "Mid-rated gold cards moved with SBC demand rather than steadily: the typical 83 or 84 was 35% below its early-October price on 18 October and 8% above it on the 24th. And new promo cards behaved completely differently from the cards above: the typical new one lost about a third of its price in its first day (see Promo-night patience).",
            ]),
            ("What it means and what it doesn't", [
                {"list": ["In these weeks, holding Icons, Heroes and high-end cards preserved coins better than holding cheap gold cards.",
                          "Buying new promo cards at release lost coins; buying established cards didn't.",
                          "Three weeks at the start of a game is not a season. Big promos or new versions of popular players can turn a rising card around quickly, and every sale costs 5%."]},
            ]),
        ],
        "live": None,
        "related": ["promo-night", "dips-and-spikes"],
    },
    {
        "slug": "console-vs-pc",
        "num": "14",
        "published": "2026-10-26",
        "short": "Console vs PC",
        "title": "FC 27 Console vs PC Prices: Why One Price Doesn't Fit Both",
        "h1": "Console vs PC prices",
        "desc": "How different FC 27 Transfer Market prices were on console and PC in October 2026, which cards differed most, and why you should always check the price for your own platform.",
        "lead": "Ultimate Team has separate Transfer Markets: console (PlayStation and Xbox) and PC. Price sites show both, but many players read whichever comes first. Ezzcoins compared the two for every card, and the gap is bigger than most people think.",
        "steps": [("Check", "The price for your own platform."),
                  ("Expect", "PC to be dearer for the most expensive cards."),
                  ("Don't", "Assume a gap stays the same.")],
        "sections": [
            ("The overall gap changed week to week", [
                {"table": {"head": ["Date", "Cards compared", "PC vs console (typical)", "Cheaper on PC"],
                           "rows": [["8 Oct", "2,033", "−5.0%", "53%"], ["12 Oct", "2,143", "0%", "47%"], ["16 Oct", "1,884", "+4.5%", "37%"],
                                    ["20 Oct", "2,051", "0%", "45%"], ["24 Oct", "1,998", "+7.0%", "33%"], ["26 Oct", "2,159", "+8.3%", "32%"]],
                           "note": "Cards worth 1,000+ coins on console with a price on both platforms, read at about 8 AM UK each day."}},
                "In early October PC was slightly cheaper than console for just over half of the cards. By late October it had turned around: the typical card was about 8% dearer on PC, and only a third were cheaper there. The two markets have different players, different pack openings and different coin supplies, so they drift apart.",
            ]),
            ("Which cards differ most", [
                {"table": {"head": ["Console price", "Cards", "PC vs console (typical)", "Dearer on PC", "Within 10%"],
                           "rows": [["1,000 to 10,000", "1,316", "+8.3%", "59%", "27%"], ["10,000 to 50,000", "263", "−1.9%", "36%", "65%"],
                                    ["50,000 to 250,000", "193", "+5.6%", "60%", "39%"], ["250,000 to 1 million", "270", "+13.8%", "86%", "33%"],
                                    ["1 million and up", "117", "+26.3%", "96%", "13%"]],
                           "note": "26 October 2026, about 8 AM UK."}},
                "The most expensive cards showed the biggest and most consistent gap: above 1 million coins, almost every card was dearer on PC, typically by about a quarter. Mid-priced cards from 10,000 to 50,000 coins were the closest, with two in three within 10%. Cheap cards were the least predictable: one in seven was either at least twice as expensive or at most half the price on PC.",
            ]),
            ("Why it matters", [
                "If you play on PC and plan a trade or an SBC from console prices, you can be out by a quarter on a big card, and the 5% tax leaves no room for that. The same goes the other way. A gap between the two markets is not a trading opportunity either: coins can't move between platforms.",
            ]),
            ("How to use Ezzcoins on PC", [
                "Every price graph on a player page has a platform switch, and the price table can show PC prices. Set it once to your platform. The trade desk's calls and the guides use console prices, so on PC treat them as a guide to the pattern, not to the exact numbers.",
            ]),
        ],
        "live": None,
        "related": ["small-budget-bidding", "launch-market"],
    },
    {
        "slug": "team-of-the-week",
        "num": "15",
        "published": "2026-10-26",
        "short": "Team of the Week",
        "title": "Team of the Week Cards in FC 27: When to Buy and When to Sell",
        "h1": "Team of the Week",
        "desc": "How FC 27 Team of the Week card prices moved after release in October 2026 compared with other promo cards: when they bottomed out, how far they fell, and when to buy or sell.",
        "lead": "A new Team of the Week arrives every Wednesday at 6 PM UK. Ezzcoins followed every TOTW card from its first price and compared them with the other promo cards released in October. They behave very differently.",
        "steps": [("Sell", "A packed TOTW card in its first hours."),
                  ("Buy", "TOTW from Thursday evening, not on Wednesday."),
                  ("Wait", "Several days for other promo cards.")],
        "sections": [
            ("How we measured it", [
                "Between 6 and 26 October 2026 three Teams of the Week were released, on 7, 14 and 21 October, each at 6 to 7 PM UK. Ezzcoins followed the 71 TOTW cards priced at 1,000 coins or more, and 57 cards from other promos (Future Stars, Ultimate Scream, Star Performer and others), from each card's first hourly console price. The typical TOTW card started at about 14,500 coins.",
            ]),
            ("TOTW drops on the first evening, then levels off", [
                {"table": {"head": ["After release", "TOTW (typical)", "Other promos (typical)"],
                           "rows": [["1 hour", "−6%", "−15%"], ["6 hours", "−17%", "−40%"], ["1 day", "−17%", "−49%"], ["2 days", "−19%", "−53%"],
                                    ["3 days", "−18%", "−57%"], ["6 days", "−18%", "−63%"]],
                           "note": "Median change from each card's first price. Console, October 2026. Fewer cards have 6-day prices because the last release was on 21 October."}},
                "Team of the Week cards lost about a sixth of their price in the first six hours and then hardly moved for the rest of the week. Other promo cards fell much further and for much longer: about half their price in a day, and close to two thirds by day six.",
            ]),
            ("When the bottom came", [
                "For TOTW cards, the lowest price of the week typically came about one day after release, and by day seven the typical card was about 9% above that low. Other promo cards kept falling: their lowest point typically came almost five days after release, and they were about 17% above it by day seven.",
            ]),
            ("What to do", [
                {"list": ["If you pack a TOTW card you don't need, sell it on the first evening: most of the fall happens in the first six hours.",
                          "If you want a TOTW card, buy it from Thursday evening onwards. Waiting longer saved little, and the price often edged up again later in the week.",
                          "For other promo cards, patience paid much more: waiting four or five days typically saved more than half the release price.",
                          "Remember that TOTW cards can rise when the player keeps playing well and gets another in-form, or fall when demand moves on. A single week's pattern is a guide, not a promise."]},
            ]),
        ],
        "live": None,
        "related": ["promo-night", "launch-market"],
    },
    {
        "slug": "big-cards-by-day",
        "published": "2026-10-28",
        "num": "16",
        "short": "Big cards by day",
        "title": "When to Buy and Sell Expensive FC 27 Cards: The Weekend Premium",
        "h1": "Big cards by day",
        "desc": "Which days and hours FC 27 cards worth 10,000 and 100,000+ coins were cheapest and dearest in October 2026: a small weekend premium, a midweek low, and why the swing is smaller than the 5% tax.",
        "lead": "Fodder is cheapest on Thursday, but most players also buy and sell bigger cards for their squads. Ezzcoins measured how the price of cards worth 10,000 and 100,000+ coins moved through the week, hour by hour.",
        "steps": [("Buy", "Squad cards from Tuesday to Thursday."),
                  ("Sell", "Cards you don't need on Friday evening or Saturday."),
                  ("Remember", "The swing is smaller than the tax: don't flip it.")],
        "sections": [
            ("How we measured it", [
                "For every card worth 10,000 coins or more on console, Ezzcoins compared each hourly price from 9 to 25 October 2026 with the same card's median over the surrounding week, three and a half days either side. That removes the slow rise or fall of a card over the month and leaves the weekly rhythm. We then averaged across 988 cards, 593 of them worth 100,000 coins or more.",
            ]),
            ("The week, day by day", [
                {"table": {"head": ["Day (UK)", "Cards 10K+", "Cards 100K+"],
                           "rows": [["Monday", "+0.5%", "+0.5%"], ["Tuesday", "−0.2%", "−0.5%"], ["Wednesday", "+0.1%", "−0.5%"], ["Thursday", "−1.2%", "−0.5%"],
                                    ["Friday", "+0.6%", "+1.5%"], ["Saturday", "+1.1%", "+1.7%"], ["Sunday", "+0.9%", "+1.3%"]],
                           "note": "Average price compared with the same card's typical price that week. Console, 9 to 25 October 2026."}},
                "Expensive cards were cheapest from Tuesday to Thursday and dearest from Friday to Sunday, when players build their squads for Champions weekend. Cards worth 10,000+ coins as a whole were also cheapest on Thursday (−1.2%), the same dip fodder shows when Rivals reward packs are opened and listed.",
            ]),
            ("The dearest and cheapest hours", [
                "For cards worth 100,000+ coins, the most expensive four-hour slots were Friday 8 PM to midnight and Saturday 4 AM to noon UK, about 2.5% above the week's typical price. The cheapest was Wednesday evening, about 1.4% below, followed by the early hours of Thursday. Across a whole day the hour made little difference: every four-hour block averaged within about 1% of typical.",
            ]),
            ("Why you can't flip the weekly rhythm", [
                "The gap between the cheapest and the dearest moment of the week was about 4% for cards worth 100,000+ coins. EA's tax takes 5% of every sale, so buying on Wednesday evening and selling on Saturday morning would still have lost coins on a typical card. On a 500,000-coin card the weekly swing is worth about 20,000 coins, but the tax on the sale is 25,000.",
                "Where the rhythm does pay is when you were going to trade anyway. If you are buying a card to play with, buying it midweek instead of at the weekend saved about 2%. If you are selling a card you no longer use, listing it on Friday evening or Saturday morning fetched a little more.",
            ]),
            ("When the pattern breaks", [
                "Promos override the weekly rhythm. A strong Friday promo floods the market with new cards and can push prices down at exactly the moment they would normally peak, and a big SBC can lift one card on any day. Treat the weekly pattern as a tie-breaker, not as a reason to trade on its own.",
                "These figures cover two full weeks early in FC 27. Ezzcoins will rerun them as more weeks are recorded.",
            ]),
        ],
        "live": None,
        "related": ["fodder-by-day", "midweek-specials"],
    },
    {
        "slug": "daily-moves",
        "published": "2026-10-28",
        "num": "17",
        "short": "Normal price moves",
        "title": "How Much Do FC 27 Prices Move in a Day? What Counts as a Real Move",
        "h1": "Normal price moves",
        "desc": "How much FC 27 card prices normally move in an hour and in a day, by price range, measured on every card in October 2026, and how big a move has to be before it means anything.",
        "lead": "A card is 10% cheaper than yesterday. Is that a bargain, or just a normal day? It depends almost entirely on what the card costs. Ezzcoins measured how far every card's price normally moves, so you can tell a real move from noise.",
        "steps": [("Know", "What a normal day looks like for the card's price range."),
                  ("Ignore", "Moves inside that normal range."),
                  ("Act", "Only on moves well outside it, confirmed twice.")],
        "sections": [
            ("How we measured it", [
                "Ezzcoins compared every card's console price with its price an hour later and a day later, for every card worth 1,000 coins or more, from 5 to 28 October 2026: about 2,100 cards in all. The tables show how big a move was typical, and how big a move only happened on the busiest days.",
            ]),
            ("A normal day, by price", [
                {"table": {"head": ["Card price", "Typical move in a day", "1 day in 4, at least", "1 day in 10, at least"],
                           "rows": [["1,000 to 5,000", "12%", "26%", "50%"], ["5,000 to 20,000", "5%", "11%", "24%"], ["20,000 to 100,000", "5%", "9%", "16%"],
                                    ["100,000 to 500,000", "4%", "7%", "12%"], ["500,000 and up", "3%", "6%", "11%"]],
                           "note": "Size of the change in console price over 24 hours, up or down. 5 to 28 October 2026."}},
                "For a card worth half a million coins, a 3% move in a day is ordinary and 11% happens about one day in ten. For a card worth 3,000 coins, a 12% move is ordinary and a 50% move happens about one day in ten. The same 10% fall can be news on an Icon and nothing at all on cheap fodder.",
            ]),
            ("Hour by hour", [
                {"table": {"head": ["Card price", "Price unchanged after an hour", "Typical hourly move", "1 hour in 20, at least"],
                           "rows": [["1,000 to 5,000", "35%", "6%", "31%"], ["5,000 to 20,000", "32%", "2%", "15%"], ["20,000 to 100,000", "14%", "2%", "9%"],
                                    ["100,000 to 500,000", "9%", "2%", "8%"], ["500,000 and up", "12%", "2%", "10%"]],
                           "note": "Change in console price from one hourly reading to the next."}},
                "About a third of cheap cards didn't move at all from one hour to the next, and the rest often jumped by a whole price step. Expensive cards moved a little almost every hour.",
            ]),
            ("Why cheap cards look so jumpy", [
                "Much of it is the market's price steps. Below 10,000 coins prices move in steps of 100, so a 1,200-coin card that moves a single step has changed by more than 8%. A 600,000-coin card moves in steps of 1,000, a sixth of a percent. Cheap cards also have many listings at the floor price, and the cheapest one can disappear and come back within minutes.",
            ]),
            ("How to use this", [
                {"list": ["Before reacting to a move, check what a normal day looks like for that price range in the table above.",
                          "For cards under 5,000 coins, ignore anything below about 25% unless it lasts for more than a day.",
                          "For cards worth 100,000+ coins, a move of more than about 12% in a day is unusual and worth a closer look.",
                          "Always wait for a second price update: an unusual move from a single reading is often a glitch (see Price glitches).",
                          "Remember the 5% tax: a move smaller than about 6% can't be traded profitably, however real it is."]},
            ]),
            ("How Ezzcoins uses it", [
                "This is why Ezzcoins' Trending list only includes cards worth 5,000+ coins, why the trade desk only calls moves on cards worth 10,000+, and why both need a move to show in two readings an hour apart before they treat it as real.",
            ]),
        ],
        "live": ("hype", "Biggest rises in the last day"),
        "related": ["price-glitches", "dips-and-spikes"],
    },
    {
        "slug": "trading-glossary",
        "published": "2026-10-28",
        "num": "18",
        "short": "Trading glossary",
        "title": "FC 27 Ultimate Team Trading Glossary: The Terms Explained",
        "h1": "Trading glossary",
        "desc": "Plain-English explanations of the FC 27 Ultimate Team trading terms used on Ezzcoins and across the community: BIN, sniping, the EA tax, floors, fodder, SBCs, Evolutions, meta cards, TOTW, extinct cards and more.",
        "lead": "Trading talk is full of shorthand. This glossary explains the terms used on Ezzcoins and across the FC community in plain English, with what each one means for your coins.",
        "steps": [("Read", "The terms you meet most: BIN, tax, floor, fodder."),
                  ("Learn", "How the market's rules shape every trade."),
                  ("Use", "The guides linked here to go deeper.")],
        "sections": [
            ("Buying and selling", [
                {"list": ["Buy Now (BIN): the fixed price at which a seller lets you buy a card instantly. Price sites, Ezzcoins included, show the lowest current Buy Now.",
                          "Bid: an offer in a card's auction. The highest bid when the timer runs out wins, unless someone uses Buy Now first.",
                          "Sniping: searching for cards listed far below their usual price and buying them before anyone else. Done by hand, it is a normal part of trading.",
                          "Mass bidding: placing many low bids on the same card, hoping to win some below the Buy Now price.",
                          "Flip: buying a card and selling it again for a profit, usually quickly.",
                          "Margin: the difference between what you receive after tax and what you paid.",
                          "Relist: putting an unsold card back on the market, often at a new price."]},
            ]),
            ("The market's rules", [
                {"list": ["EA tax: EA keeps 5% of every sale. You receive the sale price × 0.95, rounded down, so a card must rise about 5.3% before you break even (see Small-budget bidding).",
                          "Price steps: prices move in fixed steps, 50 coins below 1,000, 100 up to 10,000, 250 up to 50,000, 500 up to 100,000 and 1,000 above that.",
                          "Price range: EA sets a minimum and maximum price for each card, and you can't list it outside that range.",
                          "Maximum price: the highest price the market allows, 15,000,000 coins. A price site showing exactly that usually means there were no real listings.",
                          "Break-even price: the lowest sale price that gives back what you paid after tax.",
                          "Max buy: the highest price you can pay for a card and still make the margin you want when you sell."]},
            ]),
            ("Prices and movements", [
                {"list": ["Floor: the cheapest price a card, or the cheapest card at a rating, currently sells for.",
                          "Extinct: a card with no listings at all. Its price shows as the maximum, or not at all.",
                          "Price glitch: a single wrong price reading, often from one mispriced listing (see Price glitches).",
                          "Dip and spike: a sharp fall or rise in a card's price, usually measured over a day (see Dips and spikes).",
                          "Market crash: a broad fall in prices, often when a big promo floods the market with new cards.",
                          "Supply: how many copies of a card are being listed. Rewards and pack openings raise supply and push prices down."]},
            ]),
            ("Cards and squads", [
                {"list": ["Fodder: cheap cards bought to hand in for SBCs, usually rated 83 to 88.",
                          "SBC (Squad Building Challenge): a task where you hand in a squad that meets set rules in return for a reward. Handed-in cards leave the game, which is why SBCs create lasting demand.",
                          "Evolutions (Evos): upgrades that improve a card that meets certain requirements, which can raise demand for those cards.",
                          "Meta card: a card that plays far better than its overall rating suggests, usually fast with good skill moves and weak foot. Ezzcoins' meta rating estimates this (see The meta rating).",
                          "PlayStyle and PlayStyle+: special abilities on a card. A PlayStyle+ is the stronger version and can add a lot to a card's value.",
                          "Chemistry: how well the players in a squad link through club, league and nation. Chemistry styles boost certain stats.",
                          "Tradeable and untradeable: untradeable cards can't be sold on the market, so their price doesn't matter for trading.",
                          "Quick sell: discarding a card to EA for a small fixed amount of coins instead of selling it on the market."]},
            ]),
            ("Promos and the weekly cycle", [
                {"list": ["Team of the Week (TOTW): upgraded cards for players who played well in real matches, released every Wednesday at 6 PM UK (see Team of the Week).",
                          "In-form: a boosted version of a player's card, such as a TOTW card.",
                          "Promo: a themed set of special cards released over a week or more, usually on Friday at 6 PM UK.",
                          "Content drop: new content EA releases every evening at 6 PM UK.",
                          "Icons and Heroes: cards of retired legends. They are among the most expensive cards and behaved very differently from ordinary cards in October 2026 (see The launch market).",
                          "Rivals rewards: weekly rewards for Division Rivals, paid on Thursday morning UK time. Their packs cause the Thursday dip.",
                          "Champions (FUT Champions): the weekend competition, which lifts demand for meta cards from Friday evening."]},
            ]),
            ("Ezzcoins' own terms", [
                {"list": ["Meta rating: Ezzcoins' estimate of how well a card plays at each position it can play, from its stats, skill moves, weak foot and PlayStyles+.",
                          "Two-reading rule: Ezzcoins only trusts a price, a move or a call when two readings about an hour apart agree.",
                          "Trade call: a written buy or sell suggestion from the Ezzcoins desk, with an entry price and a check time, graded automatically after tax (see How calls are graded).",
                          "Paper test: replaying a strategy on recorded prices to see whether its calls would have made coins, before using it for real."]},
            ]),
        ],
        "live": ("calc", "Profit after tax"),
        "related": ["small-budget-bidding", "first-100k"],
    },
    {
        "slug": "trading-safely",
        "published": "2026-10-28",
        "num": "19",
        "short": "Trading safely",
        "title": "Trading Safely in FC 27: How to Avoid Scams, Bans and Lost Coins",
        "h1": "Trading safely",
        "desc": "How to protect your FC 27 Ultimate Team account and coins while trading: why buying coins and using bots puts your account at risk, how coin and login scams work, and the habits that keep your club safe.",
        "lead": "The fastest way to lose a club isn't a bad trade. It's handing your account to someone else, buying coins, or using a tool that trades for you. Here's how to trade without putting your club at risk.",
        "steps": [("Never", "Share your EA login or buy coins."),
                  ("Protect", "Your account with EA's login verification."),
                  ("Trade", "By hand, at a human pace.")],
        "sections": [
            ("Don't buy coins", [
                "Buying FC coins from a website or a seller breaks EA's rules. The coins usually reach you through deliberately overpriced trades, which EA can spot: the coins can be removed, your Transfer Market access can be restricted, and the account can be banned. Some sellers also ask for your EA login to \"deliver\" the coins, which hands them your whole club.",
                "No legitimate coin seller exists in EA's eyes. Ezzcoins never sells coins, accounts or boosting, and never links to anyone who does.",
            ]),
            ("Don't let anything trade for you", [
                "Bots, auto-buyers and browser extensions that search, bid or buy automatically also break EA's rules, whatever they promise. They need access to your account, they trade at a pace no person can, and that is exactly what EA's systems look for. Searching or bidding at a very high pace for a long time, even by hand, can lead to a temporary block on the Transfer Market.",
            ]),
            ("How scams usually work", [
                {"list": ["Free coins or packs: a message, video or giveaway asks you to log in on a page that looks like EA's. It isn't, and it records your password.",
                          "Account checks: someone claims to work for EA or a big site and asks for your login or a verification code. EA staff never ask for your password.",
                          "Coin \"investments\": someone offers to double your coins if you buy their cards at a high price. You pay, they keep the coins.",
                          "Account selling: buying or sharing a club is against EA's rules, and the original owner can often take it back."]},
            ]),
            ("Protect your account", [
                {"list": ["Turn on login verification for your EA account, so a new device needs a code as well as your password.",
                          "Use a password you don't use anywhere else.",
                          "Only log in through the game, the official app or EA's own website, never through a link someone sent you.",
                          "Never share a login code, even with friends."]},
                "If you think someone has got into your account, change your password straight away and contact EA's help service through EA's official website.",
            ]),
            ("Protect your coins", [
                "Most coins are lost to ordinary mistakes rather than scams. Count the 5% tax before every buy, don't chase a card in the first hour of a promo, don't buy a card just because it is trending, and spread your coins over more than one card. The Ezzcoins guides show how each of these played out in October 2026.",
                "Keep it a game. Never spend money you need on FC Points to chase a card, and take a break if trading stops being fun.",
            ]),
            ("Ezzcoins and your account", [
                "Ezzcoins never asks for your EA login and never needs it. Signing in on Ezzcoins, which is only needed to save a watchlist, uses a Google account and has no connection to your EA account. Anyone messaging you in Ezzcoins' name and asking for EA details is not us.",
            ]),
        ],
        "live": None,
        "related": ["first-100k", "how-calls-are-graded"],
    },
]
BY_SLUG = {g["slug"]: g for g in GUIDES}


def block(p):
    """A paragraph, or {"table": {"head", "rows", "note"}} or {"list": [...]}."""
    if isinstance(p, str):
        return f"<p>{e(p)}</p>"
    if "list" in p:
        return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in p["list"]) + "</ul>"
    t = p["table"]
    head = "".join(f"<th>{e(h)}</th>" for h in t["head"])
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in t["rows"])
    note = f'<figcaption>{e(t["note"])}</figcaption>' if t.get("note") else ""
    return f'<figure class="data"><div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>{note}</figure>'


def guide_html(g):
    up = "../../"
    steps = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in g["steps"])
    secs = "".join(f"<h2>{e(h)}</h2>" + "".join(block(p) for p in ps) for h, ps in g["sections"])
    live = ""
    if g.get("live"):
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
               "dateModified": UPDATED, "datePublished": g.get("published", FIRST), "inLanguage": "en", "author": PUBLISHER, "publisher": PUBLISHER,
               "mainEntityOfPage": BASE + path, "image": BASE + "icon-512.png"}]
    return path, page(title=f"{g['title']} · Ezzcoins", desc=g["desc"], path=path, up=up, body=body,
                      crumbs=[("Ezzcoins", ""), ("Guides", "guides/"), (g["h1"], None)], schema=schema,
                      scripts=("market-data.js?v=20261021-lean", "guides.js?v=20261026-content"))


def hub_html():
    up = "../"
    cards = "".join(f'<a class="guide-card" href="{g["slug"]}/"><span class="o">{g["num"]}</span><span class="n">{e(g["h1"])}</span>'
                    f'<span class="d">{e(g["lead"])}</span></a>' for g in GUIDES)
    body = (f'<p class="kicker">The Ezzcoins playbook</p><h1>FC 27 trading guides</h1>'
            f'<p class="lead">Nineteen guides to trading FC 27 Ultimate Team with your eyes open. The first six cover the setups Ezzcoins trades and grades; most of the rest are built on the site\'s own hourly price records, from what happens after dips and spikes to when fodder and big cards are cheapest, how Team of the Week cards are priced and how console and PC prices differ. There is also a glossary of trading terms and a guide to trading safely.</p>'
            f'<div class="guide-grid">{cards}</div><p class="more-links"><a href="{up}recap/">This week\'s market recap ›</a></p>')
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "FC 27 trading guides", "url": BASE + "guides/",
               "hasPart": [{"@type": "Article", "headline": g["title"], "url": BASE + f"guides/{g['slug']}/"} for g in GUIDES]}]
    return "guides/", page(title="FC 27 Trading Guides · Ezzcoins", path="guides/", up=up, body=body, schema=schema,
                           desc="Free FC 27 Ultimate Team trading guides built on real price data: SBC fodder timing, the Rivals rewards dip, promo and Team of the Week prices, the 5% tax, dips and spikes, normal price moves, console vs PC, the meta rating, a glossary and trading safely.",
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
