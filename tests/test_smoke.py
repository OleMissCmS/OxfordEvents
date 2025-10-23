import json
from lib.aggregator import window
from dateutil import parser as dtp

def test_window():
    data = json.loads(open('data/sample_events.json','r').read())
    res = window([{
        "title": d["title"],
        "start_iso": d["start"],
        "end_iso": d.get("end"),
        "location": d.get("location"),
        "cost": d.get("cost"),
        "link": d.get("link"),
        "source": d.get("source"),
        "category": d.get("category")
    } for d in data], days=365)
    assert len(res) >= 1