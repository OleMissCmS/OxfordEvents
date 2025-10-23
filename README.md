# Upcoming in Oxford — OxfordEvents

A Streamlit app that consolidates upcoming events in Oxford, MS and Ole Miss from public sources (RSS/ICS/HTML). No database — just fetch and merge at page load, with fuzzy de‑dupe and add‑to‑calendar links. A small map is included for venues we can geocode.

## Quickstart

```bash
git clone https://github.com/your-username/OxfordEvents.git
cd OxfordEvents
python -m venv .venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public is fine).
2. Go to https://share.streamlit.io → **New app** → pick your repo/branch → `streamlit_app.py` → **Deploy**.
3. Subsequent pushes auto‑redeploy.

## How it works

- **Sources** live in `data/sources.yaml`. Each has a `type` (rss, ics, html) and a `parser` if needed.
- On load, the app fetches sources (with caching), normalizes fields, **fuzzy de‑dupes** near‑duplicate titles on the same date, filters to the next **3 weeks**, and renders a clean table and cards.
- **Filters:** category and date range.
- **Calendar buttons:** creates an `.ics` file on the fly, plus a prefilled Google link.
- **Map:** uses a tiny venue dictionary in `data/venues.csv` and falls back to best‑effort geocoding when missing (optional).

## Limitations

- Sites change often. If a parser breaks, the app will fall back to any remaining sources and display a friendly message. Keep `sources.yaml` up to date.
- Some sites render events with JavaScript; those may need manual parsers or RSS/ICS when available.

## Customize

- Add or disable sources in `data/sources.yaml`.
- Update categories in `lib/normalize.py` (CATEGORY_MAP) if you want a different taxonomy.
- Brand colors live in `.streamlit/config.toml`.

## Repo layout

See the FILETREE below (mirrors the code on disk).

## License

MIT