import { useMemo, useState } from 'react';
import { getLogoUrl, HOME_TEAM_NAME } from '../lib/teamLogos';

const SIZE_CONFIG = {
  sm: { gap: 'gap-4', at: 'text-4xl', badge: 'w-16 h-16 text-xl' },
  md: { gap: 'gap-6', at: 'text-6xl', badge: 'w-20 h-20 text-3xl' },
  lg: { gap: 'gap-8', at: 'text-7xl', badge: 'w-24 h-24 text-4xl' }
};

const getInitials = (name = '') =>
  name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 3)
    .toUpperCase() || '??';

function LogoBadge({ teamName, badgeClass, isHome }) {
  const [hasError, setHasError] = useState(false);
  const logoUrl = getLogoUrl(teamName);
  const initials = useMemo(() => getInitials(teamName), [teamName]);

  if (!logoUrl || hasError) {
    return (
      <div
        className={`flex items-center justify-center rounded-full ${badgeClass} font-semibold uppercase ${
          isHome ? 'bg-rose-600 text-white' : 'bg-white/70 text-slate-700 border border-slate-200'
        }`}
      >
        {initials}
      </div>
    );
  }

  return (
    <img
      src={logoUrl}
      alt={`${teamName} logo`}
      className={`${badgeClass} object-contain drop-shadow-lg`}
      loading="lazy"
      onError={() => setHasError(true)}
    />
  );
}

function MatchupLogos({ awayTeam, size = 'md' }) {
  const { gap, at, badge } = SIZE_CONFIG[size] || SIZE_CONFIG.md;
  const sanitizedAway = awayTeam || 'Opponent';

  return (
    <div
      className={`w-full h-full flex items-center justify-center ${gap} px-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white`}
    >
      <LogoBadge teamName={sanitizedAway} badgeClass={badge} />
      <span className={`${at} font-black text-rose-400 drop-shadow`}>@</span>
      <LogoBadge teamName={HOME_TEAM_NAME} badgeClass={badge} isHome />
    </div>
  );
}

export default MatchupLogos;


