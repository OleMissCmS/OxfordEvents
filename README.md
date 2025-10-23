# Upcoming in Oxford — OxfordEvents

Streamlit app that consolidates upcoming events around Oxford, MS & Ole Miss. Sources include Visit Oxford, Ole Miss Localist (RSS/ICS), Chamber, Local Voice, Eventbrite, venue pages, and athletics ICS (football/baseball/softball/men's & women's basketball).

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud)
New app → repo → main branch → `streamlit_app.py` → Deploy.

## Customize
- Add sources in `data/sources.yaml`
- Category rules in `lib/normalize.py`
- Venue map markers in `data/venues.csv`