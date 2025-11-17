import { useEffect, useState } from 'react';
import axios from 'axios';
import EventCard from './components/EventCard';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000'
});

function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function fetchEvents() {
      try {
        const { data } = await api.get('/api/events');
        if (isMounted) {
          setEvents(data);
        }
      } catch (err) {
        setError(err.response?.data?.message || 'Unable to load events');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchEvents();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4">
      <header className="max-w-6xl mx-auto text-center mb-8">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-500 font-semibold">Oxford, Mississippi</p>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mt-2">Discover What&apos;s Happening</h1>
        <p className="text-slate-600 mt-3 max-w-3xl mx-auto">
          Aggregated from Ticketmaster, SeatGeek, Bandsintown, and local community submissions — now with meaningful event
          artwork powered by Unsplash and Pexels search fallbacks.
        </p>
      </header>

      <main className="max-w-6xl mx-auto">
        {loading && (
          <div className="text-center text-slate-600 animate-pulse">Fetching Oxford happenings...</div>
        )}
        {error && (
          <div className="text-center text-red-600 font-semibold">{error}</div>
        )}
        {!loading && !error && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

