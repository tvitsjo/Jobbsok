import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getJobs, triggerSearch } from '../api/jobs';
import { getProfile } from '../api/profile';
import { useState } from 'react';

export default function DashboardPage() {
  const [searching, setSearching] = useState(false);

  const { data: jobs } = useQuery({
    queryKey: ['jobs', { limit: 5 }],
    queryFn: () => getJobs({ limit: 5 }).then((r) => r.data),
  });

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => getProfile().then((r) => r.data),
  });

  const handleSearch = async () => {
    setSearching(true);
    try {
      await triggerSearch();
    } finally {
      setTimeout(() => setSearching(false), 3000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Profil</h3>
          <p className="text-lg font-semibold">
            {profile?.extraction_status === 'completed' ? 'Komplett' : 'Ufullstendig'}
          </p>
          <Link to="/profile" className="text-sm text-blue-600 hover:underline">Rediger profil</Link>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Jobbmatcher</h3>
          <p className="text-lg font-semibold">{jobs?.length ?? 0} nyeste</p>
          <Link to="/jobs" className="text-sm text-blue-600 hover:underline">Se alle jobber</Link>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Sok</h3>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="mt-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {searching ? 'Soker...' : 'Sok na'}
          </button>
        </div>
      </div>

      {jobs && jobs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Siste treff</h2>
          <div className="space-y-3">
            {jobs.map((result) => (
              <Link
                key={result.id}
                to={`/jobs/${result.id}`}
                className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{result.job_listing.title}</h3>
                    <p className="text-sm text-gray-500">
                      {result.job_listing.company_name ?? 'Ukjent firma'} — {result.job_listing.location ?? 'Ukjent sted'}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium text-white ${
                      result.relevance_score >= 0.7 ? 'bg-green-500' : result.relevance_score >= 0.5 ? 'bg-yellow-500' : 'bg-gray-400'
                    }`}
                  >
                    {Math.round(result.relevance_score * 100)}%
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
