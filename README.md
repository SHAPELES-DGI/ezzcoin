# Ezzcoins

An EA SPORTS FC 27 Ultimate Team trading desk: the weekly market cycle, fodder prices, SBC demand, content drops and graded trade calls.

## How it works

- `index.html` is the site entry point. `ezzcoins-upgrade.js` and `ezzcoins-upgrade.css` add the Now dashboard. It needs no build step and runs on GitHub Pages.
- `data/snapshot.json`, `data/history.json` and `data/ledger.json` hold the market data. An hourly job rewrites them and pushes them here. The page reloads them every 5 minutes.
- If the data files are missing or out of date, the weekly clock, the Flip calculator and the Playbook still work. The status pill turns "Stale" once the data is more than 3 hours old.

## Hosting on GitHub Pages

Settings → Pages → Build and deployment → Source: **Deploy from a branch**, Branch: **main**, folder **/ (root)** → Save.

The site is then live at `https://<your-username>.github.io/<repo-name>/`.

## Custom domain (optional)

Buy a domain from any registrar, then go to Settings → Pages → Custom domain and follow GitHub's DNS instructions.

## License

All rights reserved. See [LICENSE](LICENSE). This code is public only so GitHub Pages can host it; it may not be copied or reused.

Not affiliated with EA SPORTS, FUTBIN or FUT.GG.


## Dashboard

The Now tab includes market calls, confidence indices (not probabilities), a ledger-based record, local budget presets, player details, browser price alerts and a compact playbook. It refreshes every five minutes and with Refresh. Stale data pauses alert triggers and holds the budget in cash. Coach shortcuts show stored market calls when no Coach input is configured. Alerts work while the site is open and do not send background notifications.

## Lowest player prices

`prices.html` searches FC 27 prices from FUT.GG's public bulk feed, including console and PC markets, exact EA item IDs, base cards and special versions. It supports cheapest-first sorting, budget/rating filters, unavailable-card filtering and a CSV download of the current results. The main player database also uses the feed for exact base-card IDs.

`scripts/update_market_prices.py` fetches the FC 27 manifest, item index and two platform price files. It validates ID/array alignment and publication times before writing `data/live-prices.json`. Only status 0 with a positive price is treated as a market quote; SBC costs and reward cards never become market prices. No EA account, password, automated game client or private EA API is involved.

The `FC 27 market prices` workflow refreshes snapshots every 30 minutes and on manual dispatch. Metadata for IDs absent from the EA base roster is saved in `data/market-cards.json`; unmatched source IDs remain visibly unidentified. The browser loads the public data files from GitHub's main branch, with a deployed-copy fallback, because commits made with `GITHUB_TOKEN` do not trigger Pages builds. This keeps data refreshes independent of site builds. The page polls every five minutes while visible and labels feeds older than 90 minutes as delayed.

Run locally with Python 3: `python scripts/update_market_prices.py`. Initial metadata collection can use `--metadata-batches 60 --workers 3`; normal updates fetch at most six batches. The feed is undocumented and may change. Update failures keep the previous snapshot, and per-card observation times are not supplied, so feed publication time is never represented as the time each auction was checked.
