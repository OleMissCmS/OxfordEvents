/**
 * Event aggregation + smart image enrichment demo server.
 * - Prioritises source-provided artwork (Ticketmaster, SeatGeek, Bandsintown)
 * - Falls back to Unsplash / Pexels using contextual keywords with caching
 * - Returns events with a normalized image_url field for the frontend grid.
 */
require('dotenv').config();
const path = require('path');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const keywordExtractor = require('keyword-extractor');
const { Low } = require('lowdb');
const { JSONFile } = require('lowdb/node');

const PORT = process.env.PORT || 5000;
const DAY_IN_MS = 24 * 60 * 60 * 1000;
const UNSPLASH_ACCESS_KEY = process.env.UNSPLASH_ACCESS_KEY;
const PEXELS_API_KEY = process.env.PEXELS_API_KEY;

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'assets')));

const dbFile = path.join(__dirname, 'cache.json');
const adapter = new JSONFile(dbFile);
const db = new Low(adapter, { images: {} });

async function initDb() {
  await db.read();
  db.data = db.data || { images: {} };
  await db.write();
}
const dbReady = initDb();

const CATEGORY_FALLBACKS = {
  Education: '/assets/education.jpg',
  University: '/assets/education.jpg',
  'Arts & Culture': '/assets/arts.jpg',
  Music: '/assets/music.jpg',
  Sports: '/assets/sports.jpg',
  Community: '/assets/community.jpg',
  default: '/assets/generic.jpg'
};

const MOCK_EVENTS = [
  {
    id: '1',
    date: '2025-11-17T18:30:00Z',
    title: 'Nov 17, 2025: Indian American Law Event at Law School',
    location: 'Law School',
    type: 'Free Education',
    description:
      'The event will host speakers who specialize in Indian Law and give a deep-dive into major Supreme Court decisions that have recently come out regarding this area of the legal practice.',
    category: 'Education',
    source: 'University'
  },
  {
    id: '2',
    date: '2025-11-17T23:00:00Z',
    title: 'Nov 17, 2025: Moral Mondays at Bryant Hall',
    location: 'Bryant Hall',
    type: 'Free Arts & Culture',
    description:
      'Looking for a chill space to explore big ideas, challenge perspectives, and maybe catch a thought-provoking film? Moral Mondays are your weekly dose of open discussions, engaging debates, and movie nights.',
    category: 'Arts & Culture',
    source: 'Community'
  },
  {
    id: '3',
    date: '2025-11-18T01:30:00Z',
    title: 'Nov 17, 2025: ARTEMIS at Gertrude C. Ford Center for the Performing Arts',
    location: 'Gertrude C. Ford Center',
    type: 'Free Music',
    description:
      'Founded by pianist and composer Renee Rosnes, ARTEMIS is a powerful ensemble of instrumental virtuosos. Along with Rosnes, the quintet consists of trumpeter Ingrid Jensen, saxophonist Nicole Glover.',
    category: 'Music',
    source: 'Ticketmaster',
    images: [{ url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=900&q=80' }]
  },
  {
    id: '4',
    date: '2025-11-18T06:00:00Z',
    title: 'Nov 18, 2025: Intramural 3V3 Basketball Tournament Registration at Turner Center',
    location: 'Turner Center',
    type: 'Free Sports',
    description:
      '3v3 Basketball Tournament December 1-7. Register on the OleMissCR App and show your skills in our week-long tournament on courts 3 & 4.',
    category: 'Sports',
    source: 'Ole Miss Athletics'
  },
  {
    id: '5',
    date: '2025-11-19T00:00:00Z',
    title: 'SeatGeek Presents: Delta Blues Revival at Proud Larry’s',
    location: 'Proud Larry’s',
    type: 'Paid Music',
    description: 'A SeatGeek curated music night celebrating the roots of Delta Blues with modern twists.',
    category: 'Music',
    source: 'SeatGeek',
    performers: [{ image: 'https://images.unsplash.com/photo-1508979827776-3c228f7324a1?auto=format&fit=crop&w=900&q=80' }]
  },
  {
    id: '6',
    date: '2025-11-19T20:00:00Z',
    title: 'Bandsintown Spotlight: Yola Carter Live',
    location: 'The Lyric Oxford',
    type: 'Paid Music',
    description: 'Soulful evening on the Square featuring chart-topping vocalist Yola Carter.',
    category: 'Arts & Culture',
    source: 'Bandsintown',
    artist: { image_url: 'https://images.unsplash.com/photo-1487215078519-e21cc028cb29?auto=format&fit=crop&w=900&q=80' }
  },
  {
    id: '7',
    date: '2025-11-20T15:00:00Z',
    title: 'Oxford Farmers Market at the Pavilion',
    location: 'Oxford Pavilion',
    type: 'Free Community',
    description: 'Weekly market with local produce, artisans, acoustic sets, and chef demos every Saturday.',
    category: 'Community',
    source: 'Community'
  },
  {
    id: '8',
    date: '2025-11-21T16:00:00Z',
    title: 'STEM Learning Lab Open House',
    location: 'STEM Learning Center',
    type: 'Free Education',
    description: 'Hands-on demos covering robotics, AR/VR, and collaborative lab tours for students and faculty.',
    category: 'Education',
    source: 'University'
  },
  {
    id: '9',
    date: '2025-11-22T18:30:00Z',
    title: 'Holiday Artisan Market Preview Night',
    location: 'Powerhouse Community Arts Center',
    type: 'Paid Arts & Culture',
    description: 'Shop curated makers, sip on hot cider, and listen to live jazz ahead of the weekend rush.',
    category: 'Arts & Culture',
    source: 'Community'
  },
  {
    id: '10',
    date: '2025-11-23T01:00:00Z',
    title: 'Oxford Square Holiday Lights Kickoff Concert',
    location: 'Oxford Square',
    type: 'Free Music',
    description: 'Downtown lighting ceremony with marching bands, choirs, and a fireworks finale.',
    category: 'Music',
    source: 'Community'
  }
];

function pickRandom(list = []) {
  if (!list.length) return null;
  const index = Math.floor(Math.random() * list.length);
  return list[index];
}

function extractKeywords(event) {
  const haystack = `${event.title || ''} ${event.description || ''} ${event.category || ''}`;
  const rawKeywords = keywordExtractor.extract(haystack, {
    language: 'english',
    remove_digits: true,
    return_changed_case: true,
    remove_duplicates: true
  });

  const blocked = new Set(['the', 'this', 'that', 'with', 'from', 'event', 'free', 'paid', 'oxford', 'mississippi']);
  return rawKeywords.filter((word) => word.length > 3 && !blocked.has(word)).slice(0, 5);
}

function buildQuery(event) {
  const keywords = extractKeywords(event);
  const base = keywords.length ? keywords.join(' ') : `${event.category || ''} happenings`;
  return {
    query: `${base} oxford mississippi`.trim(),
    keywords
  };
}

function getCategoryFallback(category = '') {
  return CATEGORY_FALLBACKS[category] || CATEGORY_FALLBACKS.default;
}

async function getCachedImage(eventId) {
  await dbReady;
  await db.read();
  db.data = db.data || { images: {} };
  const cached = db.data.images[eventId];

  if (cached && Date.now() - cached.updatedAt < DAY_IN_MS) {
    console.log(`[cache] hit for ${eventId}`);
    return cached.url;
  }
  return null;
}

async function setCachedImage(eventId, url) {
  await dbReady;
  await db.read();
  db.data = db.data || { images: {} };
  db.data.images[eventId] = { url, updatedAt: Date.now() };
  await db.write();
}

async function queryUnsplash(query) {
  if (!UNSPLASH_ACCESS_KEY) return null;
  console.log(`[unsplash] searching "${query}"`);
  try {
    const response = await axios.get('https://api.unsplash.com/search/photos', {
      params: { query, per_page: 10, orientation: 'landscape' },
      headers: { Authorization: `Client-ID ${UNSPLASH_ACCESS_KEY}` }
    });
    const results = response.data.results || [];
    console.log(`[unsplash] ${results.length} results`);
    const pick = pickRandom(results);
    return pick?.urls?.regular || null;
  } catch (error) {
    console.error('[unsplash] error', error.response?.status, error.message);
    return null;
  }
}

async function queryPexels(query) {
  if (!PEXELS_API_KEY) return null;
  console.log(`[pexels] searching "${query}"`);
  try {
    const response = await axios.get('https://api.pexels.com/v1/search', {
      params: { query, per_page: 10, orientation: 'landscape' },
      headers: { Authorization: PEXELS_API_KEY }
    });
    const results = response.data.photos || [];
    console.log(`[pexels] ${results.length} results`);
    const pick = pickRandom(results);
    return pick?.src?.medium || pick?.src?.large || null;
  } catch (error) {
    console.error('[pexels] error', error.response?.status, error.message);
    return null;
  }
}

async function resolveDynamicImage(event) {
  const { query, keywords } = buildQuery(event);
  console.log(`[image] ${event.id} - ${event.title}`);
  console.log(`[image] keywords: ${keywords.join(', ') || 'none'}`);
  console.log(`[image] query: ${query}`);

  let url = await queryUnsplash(query);
  if (!url) {
    url = await queryPexels(query);
  }
  if (!url) {
    url = getCategoryFallback(event.category);
    console.log(`[image] fell back to category asset: ${url}`);
  } else {
    console.log(`[image] selected remote url: ${url}`);
  }

  return url;
}

async function enrichEventWithImage(event) {
  if (!event || !event.id) return event;

  // Cache first
  const cachedUrl = await getCachedImage(event.id);
  if (cachedUrl) {
    event.image_url = cachedUrl;
    return event;
  }

  // Source provided imagery
  const ticketmasterImage = event.images?.[0]?.url;
  const seatGeekImage = event.performers?.[0]?.image;
  const bandsintownImage = event.artist?.image_url;

  let finalUrl = ticketmasterImage || seatGeekImage || bandsintownImage;

  if (finalUrl) {
    console.log(`[image] using source image for ${event.id}`);
  } else {
    finalUrl = await resolveDynamicImage(event);
  }

  event.image_url = finalUrl;
  await setCachedImage(event.id, finalUrl);
  return event;
}

async function loadEvents() {
  const enriched = [];
  for (const event of MOCK_EVENTS) {
    // eslint-disable-next-line no-await-in-loop
    enriched.push(await enrichEventWithImage({ ...event }));
  }
  return enriched;
}

app.get('/api/events', async (req, res) => {
  try {
    const events = await loadEvents();
    res.json(events);
  } catch (error) {
    console.error('[api] /api/events failed', error);
    res.status(500).json({ message: 'Unable to load events', details: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Event image enrichment API running on http://localhost:${PORT}`);
});

