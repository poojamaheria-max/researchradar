# ResearchRadar — free personal research feed

A static Android-friendly website updated by GitHub Actions every six hours, with optional Android notifications using ntfy. No paid API keys required. Inspired by the structure of Will's Research Hub, but implemented independently.

## Setup (10–20 minutes)

1. Sign in to GitHub and create a **public** repository named `researchradar` (GitHub Pages free hosting for public repos). Upload **all files and folders** from this package, preserving `.github/workflows/update.yml`.
2. Edit `config.json` to customize your research topics. Each `query` uses [Europe PMC search syntax](https://europepmc.org/RestfulWebService). For example: `(embedding OR embeddings) AND clinical`. The default includes AI Embeddings and Long-acting PrEP.
3. Open **Actions → Update ResearchRadar → Run workflow**. This first run imports existing research but **does not send alerts**.
4. Go to **Settings → Pages → Build and deployment**. Select **Deploy from a branch**, branch `main`, folder `/docs`, then Save. After publication, open `https://YOUR-USERNAME.github.io/researchradar/`.
5. On Android, open that URL in Chrome → menu (⋮) → **Add to Home screen**.

## Android notifications (optional, free)

1. Install the **ntfy** Android app from https://ntfy.sh/.
2. Generate a long random topic string (e.g. with a password manager). Subscribe in ntfy to `https://ntfy.sh/YOUR-LONG-RANDOM-TOPIC`.
3. In your GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**. Name it `NTFY_TOPIC_URL`, with value `https://ntfy.sh/YOUR-LONG-RANDOM-TOPIC`.
4. Run the workflow again after newly matching research is indexed. Later runs notify you about new IDs (up to 10 per run). The first run deliberately sends no notifications.

**Privacy:** ntfy.sh public topics are not authenticated by default. Anyone who guesses or learns the topic URL may receive messages. Use a long random name and never send sensitive data. This app sends only public research titles and links.

## Important limits

- **Historical papers:** The site shows the newest ~70 matching records per topic, not every paper ever published. Increase pagination in `scripts/collect.py` to build a larger archive.
- **New paper alerts:** Scheduled checks run about every six hours, subject to GitHub Actions delays. They are not instant release-time notifications.
- **Search:** Europe PMC query matching is **not semantic embeddings**. Queries include synonyms; true vector similarity requires a future enhancement.
- **Conferences:** Not included in this first version; conferences need separate public feeds and access/embargo handling.
- **Saved papers:** Stored only in this phone/browser's local storage; they don't sync between devices.
- **Topic edits:** Edit `config.json` in GitHub; a website topic-editing feature requires a writable backend.
- **Source updates:** Feed records may arrive after original publication. Notification means newly detected, not necessarily published that day.
- **Public repo:** Your topics and feed are public. Do not enter sensitive research information.
- **Cost:** GitHub's free-tier usage and abuse limits apply. This is intended for small personal use.

## Local test

Run `python scripts/collect.py`, then `cd docs && python -m http.server 8000` and open `http://localhost:8000`. Live collection needs internet access.

## Project layout

- `config.json` — your monitored topics
- `scripts/collect.py` — Europe PMC collection and ntfy alerts
- `docs/index.html` — mobile-friendly website
- `docs/data.json` — generated research feed
- `state.json` — generated seen-ID tracking (created on first run)
- `.github/workflows/update.yml` — scheduled collection
