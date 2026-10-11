# Ezzcoins price service

Runs price collection every five minutes independently of GitHub Actions. GitHub Pages continues to host Ezzcoins. The browser merges service prices with existing snapshots by source timestamp, retaining newer FUTBIN quotes and falling back when the service is unavailable.

## Activate

The implementation is prepared, not deployed. Cloudflare account access and R2 activation are required. Verify permission to reuse the existing FUT.GG feed before enabling production collection. This service uses that same upstream; it does not create independent EA market observations or guarantee per-card freshness.

From this directory, with current Wrangler installed and signed into the intended Cloudflare account:

```sh
wrangler r2 bucket create ezzcoins-prices
wrangler deploy
```

If the bucket already exists, retain it. No credentials belong in source or browser configuration. Cloudflare cron changes may take up to 15 minutes to propagate. After the first successful cron run, check `/health` and `/live-prices.json` on the returned Worker URL. Confirm a second successful refresh and compare source publication times with the upstream; publication time is not each card's observation time.

Only after live readback succeeds, put the literal `https://...workers.dev/live-prices.json` URL in `data/price-service.json` under `endpoint`, and publish that configuration through the existing GitHub Pages workflow. Until then, the empty endpoint preserves the current updater and fallback behavior. Keep the GitHub job enabled for card metadata, artwork, and fallback snapshots.

## Behavior and validation

Read-only public endpoints expose price data and health, with no account credentials or trading operations. Only the scheduled handler writes snapshots. A failed request, access denial, stale feed, invalid card status, or regressing source timestamp retains the last good data. No retries or access-control workarounds are used. Last refresh failures remain visible through `/health` and Worker logs.

Run `node --test services/prices/worker.test.mjs` and `node scripts/test_market_sync.cjs` from the repository root. Deployment, R2 access, upstream access from Cloudflare, and browser CORS must still be verified after deployment. Hosting plans and provider policies can change; a five-minute cron is a target cadence, not a timing SLA.
