/* eslint-disable react/prop-types */
import MatchupLogos from './MatchupLogos';
import { isSportsEvent, getOpponentFromEvent } from '../lib/sportsUtils';

const formatDate = (value) => {
  try {
    return new Date(value).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  } catch (error) {
    return value;
  }
};

function EventCard({ event }) {
  const {
    title,
    description,
    location,
    date,
    category,
    source,
    image_url: imageUrl
  } = event;

  const sportsEvent = isSportsEvent(event);
  const opponent = sportsEvent ? getOpponentFromEvent(event) : '';
  const showMatchup = Boolean(sportsEvent && opponent);

  return (
    <article className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow duration-200 overflow-hidden border border-slate-100 flex flex-col">
      <div className="w-full h-48 bg-slate-100 dark:bg-slate-800 rounded-t-xl overflow-hidden">
        {showMatchup ? (
          <MatchupLogos awayTeam={opponent} size="md" />
        ) : (
          <img
            src={imageUrl || '/placeholder.jpg'}
            alt={title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        )}
      </div>
      <div className="p-5 flex flex-col gap-3 flex-1">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{category}</div>
        <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
        {showMatchup && (
          <div className="text-sm font-semibold text-rose-600">
            Hosting <span className="text-slate-900">{opponent}</span>
          </div>
        )}
        <p className="text-sm text-slate-600 line-clamp-3">{description}</p>
        <div className="text-sm text-slate-500">
          <div>{formatDate(date)}</div>
          <div className="font-medium text-slate-700">{location}</div>
        </div>
        <div className="mt-auto text-xs font-semibold text-slate-500">Source: {source}</div>
      </div>
    </article>
  );
}

export default EventCard;

