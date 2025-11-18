# Event Image Enrichment Demo (Node + React)

This sample shows how to enrich Oxford event data with high-quality imagery using Express on the backend and React + Tailwind on the frontend.

## Overview

```
backend/        # Express API with smart image logic
  ├─ server.js
  ├─ package.json
  └─ public/fallback.jpg

frontend/       # React grid consuming /api/events
  ├─ public/
  └─ src/
      └─ components/EventCard.js
```

## Prerequisites

- Node.js 18+
- Two API keys:
  - `UNSPLASH_ACCESS_KEY`
  - `PEXELS_API_KEY`

Create a `backend/.env` file:

```
UNSPLASH_ACCESS_KEY=your-unsplash-key
PEXELS_API_KEY=your-pexels-key
# Optional: override fallback image
# FALLBACK_IMAGE_URL=https://...
```

## Backend

```bash
cd backend
npm install
npm run dev    # or npm start
```

Key features:

- Aggregates Ticketmaster, SeatGeek, Bandsintown, and community submissions (mocked in demo).
- Prefers source-provided images.
- Falls back to Unsplash, then Pexels, then `/fallback.jpg`.
- Caches keyword lookups in-memory to respect rate limits.
- Returns normalized `image_url` in `/api/events`.

## Frontend

```bash
cd frontend
npm install
npm start
```

Optional `.env` in `frontend/`:

```
REACT_APP_API_URL=http://localhost:5000
```

The React app fetches `GET /api/events`, then renders cards with Tailwind styling and lazy-loaded `<img>` tags.

## Testing With Mock Data

The backend ships with sample data (Digital Scholarship Interest Group, Oxford Farmers Market, etc.) so you can verify the pipeline without real upstream calls. Update the mock fetchers in `backend/server.js` with live API responses when ready.

## Production Considerations

- Swap the mock fetchers with real Ticketmaster/SeatGeek/Bandsintown collectors.
- Persist `image_url` in your database to avoid recomputing on every request.
- Add rate limiting + retry logic around Unsplash/Pexels calls.
- Consider background jobs to pre-enrich events on ingestion instead of per-request.



