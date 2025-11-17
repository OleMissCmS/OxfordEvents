/**
 * Event aggregation + smart image enrichment demo server.
 * - Prioritises source-provided artwork (Ticketmaster, SeatGeek, Bandsintown)
 * - Falls back to Unsplash / Pexels using contextual keywords
 * - Returns events with a normalized image_url field for the frontend grid.
 */
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const keywordExtractor = require('keyword-extractor');

const PORT = process.env.PORT || 5000;
const FALLBACK_IMAGE = process.env.FALLBACK_IMAGE_URL || '/fallback.jpg';
const UNSPLASH_ACCESS_KEY = process.env.UNSPLASH_ACCESS_KEY;
const PEXELS_API_KEY = process.env.PEXELS_API_KEY;

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Simple in-memory cache to avoid hammering Unsplash/Pexels during development.
const imageCache = new Map();

/**
 * Mock fetchers – replace with real upstream calls when API credentials are available.
 */
async function fetchTicketmasterEvents() {
  return [
    {
      id: 'tm-1',
      title: 'Ole Miss vs Alabama - SEC Showdown',
      description: 'Home game at Vaught-Hemingway Stadium.',
      category: 'Sports',
      location: 'Vaught-Hemingway Stadium',
      date: '2025-11-21T19:00:00Z',
      source: 'Ticketmaster',
      images: [{ url: 'https://placehold.co/600x400/13294B/FFFFFF?text=Ticketmaster' }]
    }
  ];
}

async function fetchSeatGeekEvents() {
  return [
    {
      id: 'sg-1',
      title: 'Indie Night at Proud Larry’s',
      description: 'SeatGeek curated music night.',
      category: 'Music',
      location: 'Proud Larry’s',
      date: '2025-11-18T02:00:00Z',
      source: 'SeatGeek',
      performers: [{ image: 'https://placehold.co/600x400/CE1126/FFFFFF?text=SeatGeek' }]
    }
  ];
}

async function fetchBandsintownEvents() {
  return [
    {
      id: 'bit-1',
      title: 'Yola Carter Live',
      description: 'Soulful evening on the Square.',
      category: 'Arts & Culture',
      location: 'The Lyric Oxford',
      date: '2025-11-30T01:00:00Z',
      source: 'Bandsintown',
      artist: { image_url: 'https://placehold.co/600x400/00CEC8/FFFFFF?text=Bandsintown' }
    }
  ];
}

async function fetchCommunityEvents() {
  return [
    {
      id: 'comm-1',
      title: 'Digital Scholarship Interest Group November Meeting at J.D. Williams Library',
      description:
        'The Digital Scholarship Interest Group (DSIG) is an informal group of University of Mississippi faculty, staff, and students who...',
      category: 'University',
      location: 'J.D. Williams Library',
      date: '2025-11-14T17:00:00Z',
      source: 'Community'
    },
    {
      id: 'comm-2',
      title: 'Oxford Farmers Market at the Pavilion',
      description: 'Weekly market with produce, artisans, and live demos.',
      category: 'Community',
      location: 'Oxford Pavilion',
      date: '2025-11-16T14:00:00Z',
      source: 'Community'
    }
  ];
}

/**
 * Keyword extraction for Unsplash/Pexels queries.
 */
function buildKeywordQuery(event) {
  const haystack = `${event.title || ''} ${event.description || ''} ${event.category || ''}`;
  const keywords = keywordExtractor.extract(haystack, {
    language: 'english',
    remove_digits: true,
    return_changed_case: true,
    remove_duplicates: true
  });

  const filtered = keywords.filter((word) => word.length > 3 && !['oxford', 'mississippi'].includes(word));
  const topKeywords = filtered.slice(0, 5);
  const baseQuery = topKeywords.join(' ');

  return baseQuery ? `${baseQuery} oxford mississippi` : 'oxford mississippi events';
}

async function fetchUnsplashImage(query) {
  if (!UNSPLASH_ACCESS_KEY) return null;
  try {
    const response = await axios.get('https://api.unsplash.com/search/photos', {
      params: { query, per_page: 1, orientation: 'landscape' },
      headers: { Authorization: `Client-ID ${UNSPLASH_ACCESS_KEY}` }
    });
    const [photo] = response.data.results || [];
    return photo?.urls?.regular || null;
  } catch (error) {
    console.warn('Unsplash lookup failed:', error.message);
    return null;
  }
}

async function fetchPexelsImage(query) {
  if (!PEXELS_API_KEY) return null;
  try {
    const response = await axios.get('https://api.pexels.com/v1/search', {
      params: { query, per_page: 1, orientation: 'landscape' },
      headers: { Authorization: PEXELS_API_KEY }
    });
    const [photo] = response.data.photos || [];
    return photo?.src?.medium || null;
  } catch (error) {
    console.warn('Pexels lookup failed:', error.message);
    return null;
  }
}

async function getFallbackImage(query) {
  const cacheKey = query.toLowerCase();
  if (imageCache.has(cacheKey)) {
    return imageCache.get(cacheKey);
  }

  let imageUrl = await fetchUnsplashImage(query);
  if (!imageUrl) {
    imageUrl = await fetchPexelsImage(query);
  }
  if (!imageUrl) {
    imageUrl = FALLBACK_IMAGE;
  }

  imageCache.set(cacheKey, imageUrl);
  return imageUrl;
}

async function enrichEventWithImage(event) {
  if (!event) return event;

  if (event.source === 'Ticketmaster' && event.images?.length) {
    event.image_url = event.images[0].url;
    return event;
  }

  if (event.source === 'SeatGeek' && event.performers?.length && event.performers[0]?.image) {
    event.image_url = event.performers[0].image;
    return event;
  }

  if (event.source === 'Bandsintown' && event.artist?.image_url) {
    event.image_url = event.artist.image_url;
    return event;
  }

  const query = buildKeywordQuery(event);
  event.image_url = await getFallbackImage(query);
  return event;
}

async function loadEvents() {
  try {
    const [ticketmaster, seatGeek, bandsintown, community] = await Promise.all([
      fetchTicketmasterEvents(),
      fetchSeatGeekEvents(),
      fetchBandsintownEvents(),
      fetchCommunityEvents()
    ]);

    const merged = [...ticketmaster, ...seatGeek, ...bandsintown, ...community];
    const enriched = [];

    for (const event of merged) {
      // eslint-disable-next-line no-await-in-loop
      enriched.push(await enrichEventWithImage({ ...event }));
    }

    return enriched;
  } catch (error) {
    console.error('Failed to load events:', error);
    throw error;
  }
}

app.get('/api/events', async (req, res) => {
  try {
    const events = await loadEvents();
    res.json(events);
  } catch (error) {
    res.status(500).json({ message: 'Unable to load events', details: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Event image enrichment API running on http://localhost:${PORT}`);
});

