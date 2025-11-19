const SPORTS_CATEGORY_KEYWORDS = ['sports', 'athletics', 'football', 'basketball', 'baseball', 'softball'];

const BLACKLISTED_NAMES = ['ole miss', 'rebels', 'university of mississippi', 'mississippi'];

const VS_REGEXES = [
  /(?:vs\.?|vs)\s+(?:the\s+)?([A-Za-z0-9&.'\-\s]+)/i,
  /([A-Za-z0-9&.'\-\s]+)\s+at\s+(?:ole miss|university of mississippi|the pavilion|vaught hemingway)/i,
  /host(?:ing)?\s+(?:the\s+)?([A-Za-z0-9&.'\-\s]+)/i,
  /welcomes?\s+(?:the\s+)?([A-Za-z0-9&.'\-\s]+)/i
];

const sanitizeOpponent = (value = '') =>
  value
    .replace(/vs\.?/gi, '')
    .replace(/\bat\b/gi, '')
    .replace(/\bthe\b/gi, '')
    .replace(/home\s+team/gi, '')
    .replace(/Ole Miss/gi, '')
    .trim();

const titleCase = (value = '') =>
  value
    .split(' ')
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase())
    .join(' ');

export const isSportsEvent = (event = {}) => {
  const category = (event.category || '').toLowerCase();
  if (SPORTS_CATEGORY_KEYWORDS.some((keyword) => category.includes(keyword))) return true;

  const eventType = (event.type || '').toLowerCase();
  if (SPORTS_CATEGORY_KEYWORDS.some((keyword) => eventType.includes(keyword))) return true;

  const combined = `${event.title || ''} ${event.description || ''}`.toLowerCase();
  return combined.includes('ole miss') && (combined.includes(' vs') || combined.includes(' at ') || combined.includes(' versus'));
};

const isValidOpponent = (value = '') => {
  if (!value) return false;
  const normalized = value.toLowerCase();
  return !BLACKLISTED_NAMES.some((bad) => normalized === bad || normalized.includes(bad));
};

export const getOpponentFromEvent = (event = {}) => {
  const { title = '', description = '' } = event;
  const haystack = `${title} ${description}`;

  for (const regex of VS_REGEXES) {
    const match = haystack.match(regex);
    if (match && match[1]) {
      const cleaned = titleCase(sanitizeOpponent(match[1]));
      if (isValidOpponent(cleaned)) {
        return cleaned;
      }
    }
  }

  return '';
};



