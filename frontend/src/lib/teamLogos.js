const TEAM_LOGOS = {
  'ole miss': 'https://a.espncdn.com/i/teamlogos/ncaa/500/145.png',
  alabama: 'https://a.espncdn.com/i/teamlogos/ncaa/500/333.png',
  arkansas: 'https://a.espncdn.com/i/teamlogos/ncaa/500/8.png',
  auburn: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2.png',
  florida: 'https://a.espncdn.com/i/teamlogos/ncaa/500/57.png',
  georgia: 'https://a.espncdn.com/i/teamlogos/ncaa/500/61.png',
  kentucky: 'https://a.espncdn.com/i/teamlogos/ncaa/500/96.png',
  lsu: 'https://a.espncdn.com/i/teamlogos/ncaa/500/99.png',
  'mississippi state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/344.png',
  missouri: 'https://a.espncdn.com/i/teamlogos/ncaa/500/142.png',
  'south carolina': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2579.png',
  tennessee: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2633.png',
  'texas a&m': 'https://a.espncdn.com/i/teamlogos/ncaa/500/245.png',
  vanderbilt: 'https://a.espncdn.com/i/teamlogos/ncaa/500/238.png',
  texas: 'https://a.espncdn.com/i/teamlogos/ncaa/500/251.png',
  oklahoma: 'https://a.espncdn.com/i/teamlogos/ncaa/500/201.png',
  baylor: 'https://a.espncdn.com/i/teamlogos/ncaa/500/239.png',
  tcu: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2628.png',
  houston: 'https://a.espncdn.com/i/teamlogos/ncaa/500/248.png',
  'texas tech': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2641.png',
  'oklahoma state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/197.png',
  kansas: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2305.png',
  'kansas state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2306.png',
  'iowa state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/66.png',
  cincinnati: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2132.png',
  ucf: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2116.png',
  byu: 'https://a.espncdn.com/i/teamlogos/ncaa/500/252.png',
  arizona: 'https://a.espncdn.com/i/teamlogos/ncaa/500/12.png',
  'arizona state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/9.png',
  colorado: 'https://a.espncdn.com/i/teamlogos/ncaa/500/38.png',
  utah: 'https://a.espncdn.com/i/teamlogos/ncaa/500/254.png',
  washington: 'https://a.espncdn.com/i/teamlogos/ncaa/500/264.png',
  'washington state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/265.png',
  ucla: 'https://a.espncdn.com/i/teamlogos/ncaa/500/26.png',
  'southern california': 'https://a.espncdn.com/i/teamlogos/ncaa/500/30.png',
  'oregon state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/204.png',
  oregon: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2483.png',
  michigan: 'https://a.espncdn.com/i/teamlogos/ncaa/500/130.png',
  'michigan state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/127.png',
  'ohio state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/194.png',
  'penn state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/213.png',
  wisconsin: 'https://a.espncdn.com/i/teamlogos/ncaa/500/275.png',
  illinois: 'https://a.espncdn.com/i/teamlogos/ncaa/500/356.png',
  indiana: 'https://a.espncdn.com/i/teamlogos/ncaa/500/84.png',
  iowa: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2294.png',
  minnesota: 'https://a.espncdn.com/i/teamlogos/ncaa/500/135.png',
  nebraska: 'https://a.espncdn.com/i/teamlogos/ncaa/500/158.png',
  northwestern: 'https://a.espncdn.com/i/teamlogos/ncaa/500/77.png',
  purdue: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2509.png',
  rutgers: 'https://a.espncdn.com/i/teamlogos/ncaa/500/164.png',
  maryland: 'https://a.espncdn.com/i/teamlogos/ncaa/500/120.png',
  'notre dame': 'https://a.espncdn.com/i/teamlogos/ncaa/500/87.png',
  clemson: 'https://a.espncdn.com/i/teamlogos/ncaa/500/228.png',
  'florida state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/52.png',
  miami: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2390.png',
  'north carolina': 'https://a.espncdn.com/i/teamlogos/ncaa/500/153.png',
  'nc state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/152.png',
  duke: 'https://a.espncdn.com/i/teamlogos/ncaa/500/150.png',
  virginia: 'https://a.espncdn.com/i/teamlogos/ncaa/500/258.png',
  'virginia tech': 'https://a.espncdn.com/i/teamlogos/ncaa/500/259.png',
  pitt: 'https://a.espncdn.com/i/teamlogos/ncaa/500/221.png',
  'georgia tech': 'https://a.espncdn.com/i/teamlogos/ncaa/500/59.png',
  louisville: 'https://a.espncdn.com/i/teamlogos/ncaa/500/97.png',
  syracuse: 'https://a.espncdn.com/i/teamlogos/ncaa/500/183.png',
  'boston college': 'https://a.espncdn.com/i/teamlogos/ncaa/500/103.png',
  'wake forest': 'https://a.espncdn.com/i/teamlogos/ncaa/500/154.png',
  memphis: 'https://a.espncdn.com/i/teamlogos/ncaa/500/235.png',
  tulane: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2653.png',
  'southern miss': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2572.png',
  'uab': 'https://a.espncdn.com/i/teamlogos/ncaa/500/5.png',
  liberty: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2335.png',
  'boise state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/68.png',
  fresno: 'https://a.espncdn.com/i/teamlogos/ncaa/500/278.png',
  'san diego state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/21.png',
  smu: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2567.png',
  'texas state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/326.png',
  'utsa': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2636.png',
  'louisiana tech': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2348.png',
  'louisiana lafayette': 'https://a.espncdn.com/i/teamlogos/ncaa/500/309.png',
  troy: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2652.png',
  'georgia southern': 'https://a.espncdn.com/i/teamlogos/ncaa/500/290.png',
  'coastal carolina': 'https://a.espncdn.com/i/teamlogos/ncaa/500/324.png',
  army: 'https://a.espncdn.com/i/teamlogos/ncaa/500/349.png',
  navy: 'https://a.espncdn.com/i/teamlogos/ncaa/500/2426.png',
  'air force': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2005.png',
  stanford: 'https://a.espncdn.com/i/teamlogos/ncaa/500/24.png',
  cal: 'https://a.espncdn.com/i/teamlogos/ncaa/500/25.png',
  'texas southern': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2640.png',
  'jackson state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/55.png',
  'west virginia': 'https://a.espncdn.com/i/teamlogos/ncaa/500/277.png',
  'mississippi valley state': 'https://a.espncdn.com/i/teamlogos/ncaa/500/2400.png'
};

const ALIASES = {
  rebels: 'ole miss',
  'ole miss rebels': 'ole miss',
  'mississippi rebels': 'ole miss',
  'crimson tide': 'alabama',
  'razorbacks': 'arkansas',
  'war eagle': 'auburn',
  gators: 'florida',
  dawgs: 'georgia',
  bulldogs: 'mississippi state',
  aggies: 'texas a&m',
  commodores: 'vanderbilt',
  longhorns: 'texas',
  sooners: 'oklahoma',
  bears: 'baylor',
  horned: 'tcu',
  hornedfrogs: 'tcu',
  'texas christian': 'tcu',
  cougars: 'houston',
  jayhawks: 'kansas',
  wildcats: 'kentucky',
  cyclones: 'iowa state',
  bearcats: 'cincinnati',
  knights: 'ucf',
  broncos: 'boise state',
  tigers: 'lsu',
  seminoles: 'florida state',
  hurricanes: 'miami',
  wolfpack: 'nc state',
  tarheels: 'north carolina',
  bluedevils: 'duke',
  cavaliers: 'virginia',
  hokies: 'virginia tech',
  panthers: 'pitt',
  jackets: 'georgia tech',
  cardinals: 'louisville',
  orange: 'syracuse',
  deacons: 'wake forest',
  'mississippi state bulldogs': 'mississippi state',
  'lsu tigers': 'lsu',
  'miami hurricanes': 'miami',
  'florida gators': 'florida',
  'tennessee volunteers': 'tennessee',
  volunteers: 'tennessee',
  'university of memphis': 'memphis',
  'texas a and m': 'texas a&m',
  'tcu horned frogs': 'tcu',
  'usc': 'southern california',
  'southern cal': 'southern california',
  'washington huskies': 'washington',
  'washington state cougars': 'washington state',
  'arizona wildcats': 'arizona',
  'arizona state sun devils': 'arizona state',
  'stanford cardinal': 'stanford',
  'cal golden bears': 'cal',
  'uab blazers': 'uab',
  'utsa road runners': 'utsa',
  'texas san antonio': 'utsa',
  'coastal carolina': 'coastal carolina',
  'georgia southern eagles': 'georgia southern',
  'west virginia': 'west virginia',
  mountaineers: 'west virginia',
  'south carolina gamecocks': 'south carolina'
};

const HOME_TEAM_NAME = 'Ole Miss';

const normalizeTeamName = (name = '') => name.toLowerCase().replace(/[^a-z0-9& ]/g, ' ').replace(/\s+/g, ' ').trim();

export const getLogoUrl = (teamName = '') => {
  if (!teamName) return undefined;
  const normalized = normalizeTeamName(teamName);
  if (!normalized) return undefined;

  if (TEAM_LOGOS[normalized]) {
    return TEAM_LOGOS[normalized];
  }

  const alias = ALIASES[normalized];
  if (alias && TEAM_LOGOS[alias]) {
    return TEAM_LOGOS[alias];
  }

  const fallbackKey = Object.keys(TEAM_LOGOS).find(
    (key) => normalized.includes(key) || key.includes(normalized)
  );

  if (fallbackKey) {
    return TEAM_LOGOS[fallbackKey];
  }

  return undefined;
};

export { TEAM_LOGOS, HOME_TEAM_NAME, normalizeTeamName };
export default TEAM_LOGOS;

