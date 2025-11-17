/* eslint-disable react/prop-types */
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

  return (
    <article className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow duration-200 overflow-hidden border border-slate-100">
      <img
        src={imageUrl || '/placeholder.jpg'}
        alt={title}
        className="w-full h-40 object-cover rounded-t-lg"
        loading="lazy"
      />
      <div className="p-5 flex flex-col gap-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{category}</div>
        <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-600 line-clamp-3">{description}</p>
        <div className="text-sm text-slate-500">
          <div>{new Date(date).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}</div>
          <div className="font-medium text-slate-700">{location}</div>
        </div>
        <div className="text-xs font-semibold text-slate-500">Source: {source}</div>
      </div>
    </article>
  );
}

export default EventCard;

