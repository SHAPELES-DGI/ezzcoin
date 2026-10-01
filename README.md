# Ezzcoins

An EA SPORTS FC 27 Ultimate Team trading desk: the weekly market cycle, fodder prices, SBC demand, content drops and graded trade calls.

## How it works

- `index.html` is the whole site. It needs no build step and runs on GitHub Pages.
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
