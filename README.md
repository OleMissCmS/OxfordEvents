# OxfordEvents v4.4

- Header: **What's happening, Oxford?**
- Spinner replaces status while fetching (it disappears after load).
- Cached event collection (2h) so filters don't re-fetch; manual **Refresh events** button.
- **Football schedule fallback** via HTML parser on https://olemisssports.com/sports/football/schedule
- Dedup: same minute + normalized location (case-insensitive, punctuation/extra spaces stripped) → keep longer title.