# Oxford Events

A clean, professional event aggregator for Oxford, Mississippi featuring events from Ole Miss athletics, community events, and local venues.

## Features

- 📅 **Ole Miss Athletics**: All sports including football, basketball, baseball, soccer, tennis, and more
- 🏛️ **University Events**: Academic and cultural events from Ole Miss
- 🌆 **Community Events**: Local events from Visit Oxford and other sources
- 🎫 **Ticket Platforms**: SeatGeek and Ticketmaster integration
- 📱 **Responsive Design**: Clean interface that works on desktop and mobile
- 🔍 **Smart Filtering**: Search and filter by date, category, and venue

## Live App

Visit [oxfordevents.streamlit.app](https://oxfordevents.streamlit.app) to see upcoming events in Oxford, MS.

## Data Sources

- Ole Miss Athletics (ICS calendars)
- Ole Miss Central Events (RSS)
- Visit Oxford (HTML parsing)
- SeatGeek API
- Ticketmaster API

## Tech Stack

- **Frontend**: Streamlit
- **Data Processing**: Python
- **APIs**: SeatGeek, Ticketmaster
- **Parsing**: RSS, ICS, HTML
- **Deployment**: Streamlit Cloud

## Development

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
