# Upcoming in Oxford — OxfordEvents

A Streamlit app that consolidates upcoming events around Oxford, MS and Ole Miss from public sources (RSS, ICS, HTML). It deduplicates near-duplicate listings, shows a **month calendar** with hover tooltips, renders clean **event cards with descriptions**, and includes **Google/Apple calendar** buttons. Mobile-friendly design (sidebar collapsed, responsive chart, stacked cards).

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud
- New app → pick this repo → **Main file:** `streamlit_app.py` → Deploy.
- If you edit `requirements.txt`, go to **Manage app → Restart** to rebuild.

## Customize
- Add/disable sources in `data/sources.yaml` (Eventbrite + Ole Miss Athletics ICS already added).
- Edit categories in `lib/normalize.py` (ordered regex rules).
- Add venue markers in `data/venues.csv`.

## Notes on social sources
This repo includes entries for social accounts/groups as placeholders. Most social platforms require API keys or permissions; the app links to them but does not ingest posts automatically.