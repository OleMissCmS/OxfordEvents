# OxfordEvents v4.3

**What's new**
- Caching: event collection is cached for 2 hours, so changing filters **does not** re-collect data.
- Duplicates: if two events share the **same start datetime (minute precision)** and **same location**, we keep the one with the **longer title**.
- Window filter more tolerant (handles date-only ICS entries) — helps Ole Miss Football/other athletics appear.
- All safety & UI improvements from v4.2 remain.

You can manually refresh in the sidebar using **🔄 Refresh events**.