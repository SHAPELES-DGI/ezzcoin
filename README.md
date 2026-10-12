# Ezzcoins

An EA SPORTS FC 27 Ultimate Team trading desk: the weekly market cycle, fodder prices, SBC demand, content drops and graded trade calls.

## How it works

- `index.html` is the site entry point. `ezzcoins-upgrade.js` and `ezzcoins-upgrade.css` add the Now dashboard. It needs no build step and runs on GitHub Pages.
- `data/snapshot.json`, `data/history.json` and `data/ledger.json` hold the market data. `scripts/desk.py` (the automatic desk) rewrites them on every run of the market workflow, with no AI involved. The page reloads them every 5 minutes.
- If the data files are missing or out of date, the weekly clock, the Flip calculator and the Playbook still work. The status pill turns "Stale" once the data is more than 3 hours old.

## Hosting on GitHub Pages

Settings → Pages → Build and deployment → Source: **Deploy from a branch**, Branch: **main**, folder **/ (root)** → Save.

The site is then live at `https://<your-username>.github.io/<repo-name>/`.

## Custom domain (optional)

Buy a domain from any registrar, then go to Settings → Pages → Custom domain and follow GitHub's DNS instructions.

## License

All rights reserved. See [LICENSE](LICENSE). This code is public only so GitHub Pages can host it; it may not be copied or reused.

Ezzcoins is a free, fan-made site, not endorsed by or affiliated with EA or its licensors. It is not affiliated with FUTBIN or FUT.GG and never sells coins, accounts or boosting.


## Dashboard

The Now tab includes market calls, confidence indices (not probabilities), a ledger-based record, local budget presets, player details, browser price alerts and a compact playbook. It refreshes every five minutes and with Refresh. Stale data pauses alert triggers and holds the budget in cash. Coach shortcuts show stored market calls when no Coach input is configured. Alerts work while the site is open and do not send background notifications.

## Lowest player prices

`prices.html` searches FC 27 prices from FUT.GG's public bulk feed, including console and PC markets, exact EA item IDs, base cards and special versions. It supports cheapest-first sorting, budget/rating filters, unavailable-card filtering and a CSV download of the current results. The main player database also uses the feed for exact base-card IDs.

`scripts/update_market_prices.py` fetches the FC 27 manifest, item index and two platform price files. It validates ID/array alignment and publication times before writing `data/live-prices.json`. Only status 0 with a positive price is treated as a market quote; SBC costs and reward cards never become market prices. No EA account, password, automated game client or private EA API is involved.

The `FC 27 market prices` workflow refreshes snapshots every 30 minutes and on manual dispatch. Metadata for IDs absent from the EA base roster is saved in `data/market-cards.json`; unmatched source IDs remain visibly unidentified. The browser loads the public data files from GitHub's main branch, with a deployed-copy fallback, because commits made with `GITHUB_TOKEN` do not trigger Pages builds. This keeps data refreshes independent of site builds. The page polls every five minutes while visible and labels feeds older than 90 minutes as delayed.

Run locally with Python 3: `python scripts/update_market_prices.py`. Initial metadata collection can use `--metadata-batches 60 --workers 3`; normal updates fetch at most six batches. The feed is undocumented and may change. Update failures keep the previous snapshot, and per-card observation times are not supplied, so feed publication time is never represented as the time each auction was checked.

## Live prices (fast lane)

GitHub runs the scheduled market workflow 10-25 minutes late, while FUT.GG publishes new prices about every 5 minutes. The `Live prices (fast lane)` workflow closes that gap: the Ezzcoins server starts it every 3 minutes, `scripts/live_prices.py` checks FUT.GG's public manifest, and only when new prices exist does it publish `live-prices.json` (same format as `data/live-prices.json`) to the `live` branch. That branch always holds a single replaced commit, so price history does not build up and the site is not rebuilt. `market-data.js` and the player pages read the live copy first and use it only while FUT.GG's publication time is under 30 minutes old; otherwise they fall back to the main-branch copies. Pages poll every minute. A 10-minute schedule is a backup if the server is down.

## Prices in the page HTML

`scripts/build_pages.py` writes each card's console price from `data/live-prices.json` into its player page, so search engines and link previews see a real price; the browser then swaps in the newest one. A page keeps its baked price until the market moves more than 20% and at least 1,000 coins, so a price refresh doesn't rewrite thousands of pages. `scripts/prerender_home.py` does the same for the home page's market read, SBC list and news (between the `<!--pre:...-->` markers in `index.html`); the market workflow runs it every time.

## Ads

`ezz-ads.js` holds the AdSense publisher ID and the ad unit's slot number (`SLOT`). While `SLOT` is empty no ad boxes appear; once it is set, ads show in the boxes marked `ezz-ad` on the home page, the price page and every player page (phones included), plus the side rails on very wide screens. The EU/UK consent message is managed in AdSense under Privacy & messaging.

## Automatic desk

`scripts/desk.py` runs in the `FC 27 market prices` workflow after the price scripts and keeps the whole site going on its own:

- **Market read:** verdict, moves, fodder board, SBC list, biggest risers and fallers, cheap meta cards (from Ezzcoins' own meta rating), the weekly calendar (Team of the Week, Rivals rewards) and data news, all from Ezzcoins' own price feed and files.
- **Trade calls:** at most 2 a day (Zurich calendar day), 3 hours apart, from four written strategies: buy before the weekend, buy the dip, sell the spike and the Rivals rewards dip. Each call is graded on the same feed at its check time (5% tax counted on buy calls), and each grade adds a lesson.
- **Learning:** a strategy with 3+ graded calls and under 50% hits is paused for 7 days, then retested at low confidence; one with 70%+ hits is used first, at high confidence.
- **Watched and top cards:** `data/prices.json` follows the 25 most-watched cards in the public watchlists (read about once an hour) and `data/topprices.json` every base card rated 84+.

`.github/workflows/players.yml` rebuilds `data/players.json` from EA's ratings once a day. Leaks from FUT Sheriff and FifaTradingRomania are not followed any more: the calendar lists only official, recurring events and promos that have actually gone live.

