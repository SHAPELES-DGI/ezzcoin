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
UPDATED = "2026-10-26"   # bump when a guide's text changes
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
                "Ezzcoins saw 255 new special cards worth 10,000 coins or more arrive on the market between 6 and 26 October 2026 and followed each from its first hourly price reading:",
                {"table": {"head": ["Time after first price", "Typical change", "Cheaper than first price"],
                           "rows": [["1 hour", "−10%", "76%"], ["3 hours", "−24%", "82%"], ["6 hours", "−29%", "91%"], ["24 hours", "−51%", "97%"], ["3 days", "−56%", "97%"]],
                           "note": "Median change of each card's console price, compared with its first reading after release."}},
                "Half of the price was gone within a day, and almost every card was cheaper after 24 hours. If you want a new promo card, waiting a day has been worth about half its price. If you pack one you don't need, the first hours are the best time to sell it.",
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
                "New promo cards start expensive and fall fast. Of the 255 new special cards worth 10,000+ coins that Ezzcoins saw arrive in October, the typical one was 24% cheaper three hours after its first price and 51% cheaper a day later, and 97% were cheaper after 24 hours. If you want a new card, wait at least a day. If you pack one you don't need, the first hours are the best time to sell it.",
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
            f'<p class="lead">Eleven guides to trading FC 27 Ultimate Team with your eyes open. The first six cover the setups Ezzcoins trades and grades; the rest are built on the site\'s own hourly price records, from what happens after dips and spikes to how often a single price reading is wrong. Most show live data from the site.</p>'
            f'<div class="guide-grid">{cards}</div><p class="more-links"><a href="{up}recap/">This week\'s market recap ›</a></p>')
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "FC 27 trading guides", "url": BASE + "guides/",
               "hasPart": [{"@type": "Article", "headline": g["title"], "url": BASE + f"guides/{g['slug']}/"} for g in GUIDES]}]
    return "guides/", page(title="FC 27 Trading Guides · Ezzcoins", path="guides/", up=up, body=body, schema=schema,
                           desc="Free FC 27 Ultimate Team trading guides: SBC fodder value, the Rivals rewards dip, midweek buying, promo nights, the 5% tax, dips and spikes, price glitches, the meta rating and a beginner's plan.",
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
